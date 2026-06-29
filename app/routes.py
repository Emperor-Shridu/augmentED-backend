from fastapi import APIRouter

from fastapi import HTTPException
from fastapi import UploadFile, File
from fastapi.responses import FileResponse

import os
from app import functions
from app import gemini_service


router = APIRouter()

DATA_STORE_PATH = "data/user_doc"


def get_ai_functions():
    try:
        from chatbot import functions as ai_functions

        return ai_functions
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "AI service is not available. Install the local model/vector "
                f"dependencies and verify chatbot startup. Error: {exc}"
            ),
        )


def use_gemini() -> bool:
    return gemini_service.is_configured()


@router.get("/")
async def root():
    return {"name": "AugmentED Backend", "status": "running"}


@router.get("/health/")
async def health():
    return {"status": "ok"}


@router.get("/ai/status/")
async def ai_status():
    return gemini_service.status()


@router.get("/admin/stats/")
async def admin_stats():
    return functions.get_admin_stats()


@router.post("/uploadbook/")
async def up_and_down(text: str, file: UploadFile = File(...)):
    file_path = functions.get_file_path(file.filename)
    if file.content_type != "application/pdf":
        raise HTTPException(400, detail=f"Invalid document type: {file_path}")
    else:
        os.makedirs(functions.get_file_path(DATA_STORE_PATH), exist_ok=True)
        data = file.file.read()
        new_fileName = "{}_{}.pdf".format(
            os.path.splitext(str(file.filename))[0], functions.timestr()
        )
        save_file_path = functions.get_file_path(os.path.join(DATA_STORE_PATH, new_fileName))
        print(save_file_path)
        with open(save_file_path, "wb") as f:
            f.write(data)
        functions.record_upload(file.filename, new_fileName, save_file_path)
        ai_status = "ready"
        ai_detail = "Document chat context prepared."
        if use_gemini():
            gemini_service.set_active_document(save_file_path, new_fileName)
            ai_detail = "Gemini document mode is ready."
        else:
            try:
                ai_functions = get_ai_functions()
                ai_functions.set_document_chat_engine(save_file_path)
            except HTTPException as exc:
                ai_status = "unavailable"
                ai_detail = exc.detail
        return {
            "filename": new_fileName,
            "original_filename": file.filename,
            "text": text,
            "ai_status": ai_status,
            "ai_detail": ai_detail,
            "ai_provider": "gemini" if use_gemini() else "local",
        }


@router.post("/getbook/")
async def get_file(filename: str):
    return functions.serve_book(functions.get_flie_path_from_name(filename))



@router.post("/reindex/")
def reindex(passwd: str):
    if passwd != "recreate":
        raise HTTPException(400, detail=f"Invalid password: {passwd}")
    else:
        ai_functions = get_ai_functions()
        ai_functions.recreate_indexes(passwd)
        return {"status": "indexes recreated"}
        

@router.post("/documentchat/")
async def read_conversation(
    query: str,
):
    if use_gemini():
        response = gemini_service.chat_with_document(query)
        return {"text": response}
    ai_functions = get_ai_functions()
    response = ai_functions.chat_with_document(query=query)
    return ai_functions.generate_text_from_response(response)

@router.post("/summarizer/")
async def summarize(
    para: str,
):
    if use_gemini():
        response = gemini_service.summarize_text(para)
        return {"text": response}
    ai_functions = get_ai_functions()
    response = ai_functions.plain_text_summarizer(para)
    return ai_functions.generate_text_from_response(response)

@router.post("/notemaker/")
async def make_notes(
    para: str,
):
    if use_gemini():
        response = gemini_service.make_notes(para)
        return {"text": response}
    ai_functions = get_ai_functions()
    response = ai_functions.note_maker_summarize(para, n_paras=2)
    return ai_functions.generate_text_from_response(response)

@router.post("/similaritysearch/")
async def search_similar_para(
    para: str,
):
    if use_gemini():
        responses = gemini_service.search_passages(para)
        return {"paragraphs": responses}
    ai_functions = get_ai_functions()
    responses = ai_functions.search_passages(passage=para, top_k=4)
    response = {"paragraphs": responses}
    return response

