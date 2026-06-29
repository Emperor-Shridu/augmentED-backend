import os
from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = os.getenv("AUGMENTED_API_URL", "http://127.0.0.1:5555")


st.set_page_config(page_title="AugmentED", page_icon="AE", layout="wide")


def api_url() -> str:
    return st.session_state.get("api_url", DEFAULT_API_URL).rstrip("/")


def request_json(method: str, path: str, **kwargs: Any) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.request(method, f"{api_url()}{path}", timeout=90, **kwargs)
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
        else:
            data = {"text": response.text}
        if response.ok:
            return data, None
        detail = data.get("detail", data)
        return None, f"{response.status_code}: {detail}"
    except requests.RequestException as exc:
        return None, str(exc)


def show_result(data: dict[str, Any] | None, error: str | None) -> None:
    if error:
        st.error(error)
        return
    if not data:
        st.info("No response returned.")
        return
    if "text" in data:
        st.markdown(data["text"])
    elif "paragraphs" in data:
        for index, paragraph in enumerate(data["paragraphs"], start=1):
            st.markdown(f"**Passage {index}**")
            st.write(paragraph)
    else:
        st.json(data)


st.sidebar.title("AugmentED")
st.sidebar.text_input("Backend URL", value=DEFAULT_API_URL, key="api_url")

health, health_error = request_json("GET", "/health/")
if health_error:
    st.sidebar.error("Backend offline")
else:
    st.sidebar.success("Backend online")

ai_status, ai_status_error = request_json("GET", "/ai/status/")
if ai_status_error:
    st.sidebar.warning("AI status unavailable")
elif ai_status:
    st.sidebar.caption(f"AI provider: {ai_status['provider']}")
    st.sidebar.caption(f"Model: {ai_status['gemini_model']}")

st.title("AugmentED Learning Assistant")
st.caption("Upload one active PDF context, ask questions, summarize text, and inspect demo stats.")

upload_tab, chat_tab, summarize_tab, notes_tab, search_tab, admin_tab = st.tabs(
    ["Upload", "Chat", "Summarize", "Notes", "Search", "Admin"]
)

with upload_tab:
    st.subheader("Upload Active PDF")
    st.info("Only one PDF is active for chat/search at a time. Uploading another PDF replaces the active context.")
    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])
    upload_note = st.text_input("Short label", value="demo upload")
    if st.button("Upload PDF", type="primary", disabled=uploaded_file is None):
        with st.status("Uploading PDF and preparing document chat...", expanded=True) as status:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf",
                )
            }
            st.write("Saving PDF")
            data, error = request_json(
                "POST",
                "/uploadbook/",
                params={"text": upload_note},
                files=files,
            )
            if error:
                status.update(label="Upload failed", state="error")
            else:
                status.update(label="Upload complete", state="complete")
        show_result(data, error)

with chat_tab:
    st.subheader("Ask the Active Document")
    st.caption("Answers use the most recently uploaded PDF.")
    query = st.text_area("Question", placeholder="What is this document about?")
    if st.button("Ask", type="primary", disabled=not query.strip()):
        with st.spinner("Reading the active PDF and preparing an answer..."):
            data, error = request_json("POST", "/documentchat/", params={"query": query})
        show_result(data, error)

with summarize_tab:
    st.subheader("Summarize Text")
    paragraph = st.text_area("Text to summarize", height=220, key="summary_text")
    if st.button("Summarize", type="primary", disabled=not paragraph.strip()):
        with st.spinner("Summarizing..."):
            data, error = request_json("POST", "/summarizer/", params={"para": paragraph})
        show_result(data, error)

with notes_tab:
    st.subheader("Create Study Notes")
    note_text = st.text_area("Text for notes", height=220, key="notes_text")
    if st.button("Make Notes", type="primary", disabled=not note_text.strip()):
        with st.spinner("Creating notes..."):
            data, error = request_json("POST", "/notemaker/", params={"para": note_text})
        show_result(data, error)

with search_tab:
    st.subheader("Semantic Passage Search")
    st.caption("Search runs against the most recently uploaded PDF.")
    search_text = st.text_area("Search text", height=160)
    if st.button("Find Similar Passages", type="primary", disabled=not search_text.strip()):
        with st.spinner("Searching the active PDF..."):
            data, error = request_json("POST", "/similaritysearch/", params={"para": search_text})
        show_result(data, error)

with admin_tab:
    st.subheader("Demo Stats")
    stats, stats_error = request_json("GET", "/admin/stats/")
    if stats_error:
        st.error(stats_error)
    elif stats:
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Document", stats["active_document_count"])
        col2.metric("Unique Documents", stats["unique_uploaded_document_count"])
        col3.metric("AI Provider", stats["ai_provider"])
        st.metric("Total Upload Events", stats["total_upload_events"])
        active_document = stats.get("active_document")
        if active_document:
            st.write(f"Active file: {active_document['original_filename']}")
        st.json(stats)
