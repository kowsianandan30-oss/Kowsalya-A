from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(min_length=1)


class QuizRequest(TextRequest):
    num_questions: int = Field(default=5, ge=1, le=20)


class ApiResponse(BaseModel):
    success: bool
    result: object
