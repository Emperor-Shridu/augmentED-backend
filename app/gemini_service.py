import base64
import os
from typing import Any

import requests
from fastapi import HTTPException


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
ACTIVE_DOCUMENT: dict[str, Any] = {}


def api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY")


def model_name() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def is_configured() -> bool:
    return bool(api_key())


def status() -> dict[str, Any]:
    return {
        "provider": "gemini" if is_configured() else "local",
        "gemini_configured": is_configured(),
        "gemini_model": model_name(),
        "active_document": ACTIVE_DOCUMENT.get("filename"),
    }


def set_active_document(file_path: str, filename: str) -> dict[str, Any]:
    ACTIVE_DOCUMENT.clear()
    ACTIVE_DOCUMENT.update(
        {
            "file_path": file_path,
            "filename": filename,
            "mime_type": "application/pdf",
        }
    )
    return status()


def _extract_text(data: Any) -> str:
    if isinstance(data, dict):
        candidates = data.get("candidates")
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            return "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        if isinstance(data.get("text"), str):
            return data["text"]
        for value in data.values():
            text = _extract_text(value)
            if text:
                return text
    if isinstance(data, list):
        for item in data:
            text = _extract_text(item)
            if text:
                return text
    return ""


def _document_part() -> dict[str, str]:
    file_path = ACTIVE_DOCUMENT.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=400,
            detail="No active PDF is available. Upload a PDF before using document chat.",
        )
    with open(file_path, "rb") as handle:
        encoded_pdf = base64.b64encode(handle.read()).decode("utf-8")
    return {
        "inline_data": {
            "mime_type": ACTIVE_DOCUMENT.get("mime_type", "application/pdf"),
            "data": encoded_pdf,
        }
    }


def generate_text(prompt: str, include_document: bool = False) -> str:
    key = api_key()
    if not key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Set it to use hosted Gemini AI mode.",
        )

    input_parts = []
    if include_document:
        input_parts.append(_document_part())
    input_parts.append({"text": prompt})

    response = requests.post(
        GEMINI_API_URL.format(model=model_name()),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={"contents": [{"role": "user", "parts": input_parts}]},
        timeout=120,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {"text": response.text}

    if not response.ok:
        raise HTTPException(status_code=response.status_code, detail=payload)

    text = _extract_text(payload)
    if not text:
        raise HTTPException(status_code=502, detail={"message": "Gemini returned no text.", "response": payload})
    return text


def chat_with_document(query: str) -> str:
    prompt = (
        "Answer the learner's question using the uploaded PDF. "
        "If the answer is not supported by the PDF, say so clearly.\n\n"
        f"Question: {query}"
    )
    return generate_text(prompt, include_document=True)


def summarize_text(text: str) -> str:
    prompt = (
        "Summarize the following study material into concise bullet points. "
        "Keep the explanation useful for exam revision.\n\n"
        f"{text}"
    )
    return generate_text(prompt)


def make_notes(text: str) -> str:
    prompt = (
        "Turn the following study material into clean revision notes with headings, "
        "key ideas, and short bullet points.\n\n"
        f"{text}"
    )
    return generate_text(prompt)


def search_passages(query: str) -> list[str]:
    prompt = (
        "From the uploaded PDF, find up to four passages or sections most relevant "
        "to the search text. Return concise quoted or paraphrased snippets as a numbered list. "
        "If the PDF does not contain matching content, say that clearly.\n\n"
        f"Search text: {query}"
    )
    return [generate_text(prompt, include_document=True)]
