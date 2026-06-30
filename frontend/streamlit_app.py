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
    active_doc = ai_status.get("active_document")
    if active_doc:
        st.sidebar.caption(f"Active doc: {active_doc}")
    else:
        st.sidebar.caption("No active document")

st.title("AugmentED Learning Assistant")
st.caption("Upload PDFs, chat with them, summarize text, and inspect demo stats.")

tab_descriptions = {
    "Upload": "Upload a PDF. Once uploaded, it becomes the **active document** for Chat, Search, and document-based AI features.",
    "Chat": "Ask questions about the **active uploaded PDF**. Works with both Gemini (hosted) and local AI modes.",
    "Summarize": "Paste any text and generate concise summary bullet points. Uses text input directly — no PDF required.",
    "Notes": "Paste any text and generate clean revision notes with headings and bullet points. Uses text input directly — no PDF required.",
    "Search": "Find semantically similar passages in the **active uploaded PDF**. Consistent across Gemini and local modes.",
    "Admin": "View demo stats like uploaded PDF count, storage used, and AI provider configuration.",
}

upload_tab, chat_tab, summarize_tab, notes_tab, search_tab, admin_tab = st.tabs(
    list(tab_descriptions.keys())
)

for tab, desc in zip([upload_tab, chat_tab, summarize_tab, notes_tab, search_tab, admin_tab], tab_descriptions.values()):
    with tab:
        st.caption(desc)

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

    col1, col2 = st.columns([2, 1])
    with col1:
        admin_password = st.text_input("Admin password", type="password")
    with col2:
        st.write("")
        st.write("")
        load_stats = st.button("Load Stats", type="primary", use_container_width=True)

    if load_stats:
        if not admin_password:
            st.warning("Enter the admin password to view stats.")
        else:
                stats, stats_error = request_json("GET", "/admin/stats/", params={"password": admin_password})
                if stats_error:
                    st.error(stats_error)
                elif stats:
                    st.success("Stats loaded successfully")

                    pdf_count = stats.get("uploaded_pdf_count", 0)
                    storage_mb = stats.get("uploaded_pdf_storage_mb", 0.0)
                    ai_provider = stats.get("ai_provider", "unknown")

                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric("Uploaded PDFs", pdf_count, label_visibility="visible")
                    metric_col2.metric("Storage Used", f"{storage_mb} MB", label_visibility="visible")
                    metric_col3.metric("AI Provider", ai_provider, label_visibility="visible")

                with st.expander("Detailed Configuration", expanded=True):
                    config_col1, config_col2 = st.columns(2)
                    with config_col1:
                        st.write(f"**Upload directory exists:** {stats['upload_directory_exists']}")
                        st.write(f"**Model file present:** {stats['model_file_present']}")
                        st.write(f"**Model filename:** {stats['model_filename'] if stats['model_file_present'] else 'Not found'}")
                    with config_col2:
                        st.write(f"**Gemini configured:** {stats['gemini_configured']}")
                        st.write(f"**Gemini model:** {stats['gemini_model']}")
                        st.write(f"**Vectorstore present:** {stats['vectorstore_directory_present']}")

                with st.expander("Raw JSON Response"):
                    st.json(stats)
