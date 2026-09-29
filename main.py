from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from models import TextRequest, QuizRequest, ApiResponse
from qna import answer_question
from explanation_module import explain_concept
from quiz_module import generate_quiz
from summary_module import summarize_text
from learning_path import get_learning_recommendations


# ---------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

# Your .env file is in the project root
load_dotenv(BASE_DIR / ".env")

templates = Jinja2Templates(
    directory=str(BASE_DIR / "Templates")
)


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="EduGenie",
    description="Google Gemini Powered Learning Assistant",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

cors_origins = os.getenv("CORS_ORIGINS", "*")

if cors_origins == "*":
    allowed_origins = ["*"]
    allow_credentials = False
else:
    allowed_origins = [
        origin.strip()
        for origin in cors_origins.split(",")
        if origin.strip()
    ]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Frontend
# ---------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html"
    )


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "EduGenie"
    }


# ---------------------------------------------------------
# Question Answering
# ---------------------------------------------------------

@app.post("/ask", response_model=ApiResponse)
async def ask_question(payload: TextRequest):

    try:
        result = answer_question(payload.text)

        return ApiResponse(
            success=True,
            result=result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


# ---------------------------------------------------------
# Question Answering - compatibility endpoint
# ---------------------------------------------------------

@app.post("/qa", response_model=ApiResponse)
async def question_answering(payload: TextRequest):

    try:
        result = answer_question(payload.text)

        return ApiResponse(
            success=True,
            result=result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


# ---------------------------------------------------------
# Concept Explanation
# ---------------------------------------------------------

@app.post("/explain", response_model=ApiResponse)
async def explain(payload: TextRequest):

    try:
        result = explain_concept(payload.text)

        return ApiResponse(
            success=True,
            result=result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


# ---------------------------------------------------------
# Quiz Generation
# ---------------------------------------------------------

@app.post("/quiz", response_model=ApiResponse)
async def quiz(payload: QuizRequest):

    try:
        result = generate_quiz(
            payload.text,
            payload.num_questions
        )

        return ApiResponse(
            success=True,
            result=result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


# ---------------------------------------------------------
# Summarization
# ---------------------------------------------------------

@app.post("/summarize", response_model=ApiResponse)
async def summarize(payload: TextRequest):

    try:
        result = summarize_text(payload.text)

        return ApiResponse(
            success=True,
            result=result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


# ---------------------------------------------------------
# Learning Path
# ---------------------------------------------------------

@app.post("/learning-path", response_model=ApiResponse)
async def learning_path(payload: TextRequest):

    try:
        result = get_learning_recommendations(
            payload.text
        )

        return ApiResponse(
            success=True,
            result=result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


# ---------------------------------------------------------
# Learning Path - compatibility endpoint
# ---------------------------------------------------------

@app.post("/learn/recommendations", response_model=ApiResponse)
async def learning_recommendations(payload: TextRequest):

    try:
        result = get_learning_recommendations(
            payload.text
        )

        return ApiResponse(
            success=True,
            result=result
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc