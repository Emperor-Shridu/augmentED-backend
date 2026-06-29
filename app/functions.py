from fastapi.responses import FileResponse
from fastapi import HTTPException
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


def get_admin_stats():
    upload_dir = get_file_path(DATA_PATH)
    pdf_files = glob(os.path.join(upload_dir, "**", "*.pdf"), recursive=True)
    total_bytes = sum(os.path.getsize(path) for path in pdf_files if os.path.exists(path))
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "uploaded_pdf_count": len(pdf_files),
        "uploaded_pdf_storage_mb": round(total_bytes / (1024 * 1024), 2),
        "upload_directory_exists": os.path.isdir(upload_dir),
        "ai_provider": "gemini" if gemini_configured else "local",
        "gemini_configured": gemini_configured,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        "model_file_present": os.path.exists(MODEL_PATH),
        "model_filename": os.path.basename(MODEL_PATH),
        "vectorstore_directory_present": os.path.isdir(get_file_path("chatbot/vectorstore")),
    }


    
