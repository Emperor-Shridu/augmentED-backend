from fastapi.responses import FileResponse
from fastapi import HTTPException
import json
import os
import time
from glob import glob

def serve_book(filepath: str):
    try:
        return FileResponse(filepath, media_type='application/pdf', filename='book_file.pdf')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))


timestr = lambda: time.strftime("%Y%m%d-%H%M%S")
DATA_PATH = "data/user_doc"
MODEL_PATH = os.path.join(os.getcwd(), "chatbot", "models", "zephyr-7b-beta-Q2_K.gguf")
UPLOAD_STATE_PATH = os.path.join(DATA_PATH, "upload_state.json")

def get_file_path(file_name):
    file_path = os.path.abspath(file_name)  # Join the directory and file name
    return file_path

def get_flie_path_from_name(file_name):
    files = glob(os.path.join(DATA_PATH, "**", file_name), recursive=True)
    if not files:
        raise HTTPException(status_code=404, detail="File not found")
    return get_file_path(files[0])


def get_file_path_from_name(file_name):
    return get_flie_path_from_name(file_name)


def read_upload_state():
    state_path = get_file_path(UPLOAD_STATE_PATH)
    if not os.path.exists(state_path):
        return {"uploads": [], "active_document": None}
    try:
        with open(state_path, "r", encoding="utf-8") as state_file:
            state = json.load(state_file)
    except (json.JSONDecodeError, OSError):
        return {"uploads": [], "active_document": None}
    state.setdefault("uploads", [])
    state.setdefault("active_document", None)
    return state


def record_upload(original_filename, stored_filename, file_path):
    os.makedirs(get_file_path(DATA_PATH), exist_ok=True)
    state = read_upload_state()
    upload = {
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "uploaded_at": timestr(),
        "size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
    }
    state["uploads"].append(upload)
    state["active_document"] = upload
    with open(get_file_path(UPLOAD_STATE_PATH), "w", encoding="utf-8") as state_file:
        json.dump(state, state_file, indent=2)
    return state


def get_admin_stats():
    upload_dir = get_file_path(DATA_PATH)
    pdf_files = glob(os.path.join(upload_dir, "**", "*.pdf"), recursive=True)
    total_bytes = sum(os.path.getsize(path) for path in pdf_files if os.path.exists(path))
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    state = read_upload_state()
    uploads = state.get("uploads", [])
    unique_original_filenames = sorted(
        {
            upload.get("original_filename")
            for upload in uploads
            if upload.get("original_filename")
        }
    )
    return {
        "active_document": state.get("active_document"),
        "active_document_count": 1 if state.get("active_document") else 0,
        "total_upload_events": len(uploads) or len(pdf_files),
        "unique_uploaded_document_count": len(unique_original_filenames) or len(pdf_files),
        "unique_uploaded_document_names": unique_original_filenames,
        "uploaded_pdf_storage_mb": round(total_bytes / (1024 * 1024), 2),
        "upload_directory_exists": os.path.isdir(upload_dir),
        "one_active_document_limit": True,
        "ai_provider": "gemini" if gemini_configured else "local",
        "gemini_configured": gemini_configured,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        "model_file_present": os.path.exists(MODEL_PATH),
        "model_filename": os.path.basename(MODEL_PATH),
        "vectorstore_directory_present": os.path.isdir(get_file_path("chatbot/vectorstore")),
    }


    
