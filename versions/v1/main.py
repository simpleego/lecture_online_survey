from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "CHANGE_ME")
DB_NAME = os.getenv("DB_NAME", "counsel_survey")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(title="수강생 상담 설문 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class SurveyCreate(BaseModel):
    student_name: str = Field(min_length=1, max_length=50)
    team_name: str | None = Field(default=None, max_length=50)

    understanding_level: int = Field(ge=1, le=5)
    understanding_good: str | None = None
    understanding_difficult: str | None = None
    understanding_areas: list[str] = []

    practice_level: int = Field(ge=1, le=5)
    practice_status: str = Field(min_length=1, max_length=30)
    practice_comment: str | None = None

    hardest_points: list[str] = []
    hardest_comment: str | None = None

    review_frequency: str = Field(min_length=1, max_length=30)
    ai_learning_usage: str | None = None
    improvement_method: str | None = None

    project_role: str | None = Field(default=None, max_length=100)
    desired_role: str | None = Field(default=None, max_length=100)
    collaboration_difficulty: str | None = None
    project_strength: str | None = None
    project_burden: str | None = None

    ai_tool_level: int = Field(ge=1, le=5)
    ai_tool_usage: list[str] = []
    code_understanding: str = Field(min_length=1, max_length=30)
    ai_tool_comment: str | None = None

    desired_job: str | None = Field(default=None, max_length=100)
    career_fields: list[str] = []
    course_career_fit: int = Field(ge=1, le=5)
    career_comment: str | None = None

    class_speed: str = Field(min_length=1, max_length=30)
    need_more_explanation: str | None = None
    practice_amount: str = Field(min_length=1, max_length=30)
    instructor_support: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def join_list(values: list[str]) -> str:
    return ",".join(values)


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {e}")


@app.post("/api/surveys", status_code=201)
def create_survey(data: SurveyCreate, db: Session = Depends(get_db)):
    sql = text("""
        INSERT INTO survey_responses (
            student_name, team_name,
            understanding_level, understanding_good,
            understanding_difficult, understanding_areas,
            practice_level, practice_status, practice_comment,
            hardest_points, hardest_comment,
            review_frequency, ai_learning_usage, improvement_method,
            project_role, desired_role, collaboration_difficulty,
            project_strength, project_burden,
            ai_tool_level, ai_tool_usage, code_understanding, ai_tool_comment,
            desired_job, career_fields, course_career_fit, career_comment,
            class_speed, need_more_explanation, practice_amount, instructor_support
        ) VALUES (
            :student_name, :team_name,
            :understanding_level, :understanding_good,
            :understanding_difficult, :understanding_areas,
            :practice_level, :practice_status, :practice_comment,
            :hardest_points, :hardest_comment,
            :review_frequency, :ai_learning_usage, :improvement_method,
            :project_role, :desired_role, :collaboration_difficulty,
            :project_strength, :project_burden,
            :ai_tool_level, :ai_tool_usage, :code_understanding, :ai_tool_comment,
            :desired_job, :career_fields, :course_career_fit, :career_comment,
            :class_speed, :need_more_explanation, :practice_amount, :instructor_support
        )
    """)

    params = data.model_dump()
    params["understanding_areas"] = join_list(data.understanding_areas)
    params["hardest_points"] = join_list(data.hardest_points)
    params["ai_tool_usage"] = join_list(data.ai_tool_usage)
    params["career_fields"] = join_list(data.career_fields)

    try:
        result = db.execute(sql, params)
        db.commit()
        return {
            "message": "상담 설문이 정상적으로 저장되었습니다.",
            "id": result.lastrowid
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"설문 저장 실패: {e}")


@app.get("/api/surveys")
def get_surveys(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    sql = text("""
        SELECT *
        FROM survey_responses
        ORDER BY id DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


@app.get("/api/surveys/{survey_id}")
def get_survey(survey_id: int, db: Session = Depends(get_db)):
    sql = text("""
        SELECT *
        FROM survey_responses
        WHERE id = :survey_id
    """)
    row = db.execute(sql, {"survey_id": survey_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="설문을 찾을 수 없습니다.")

    return dict(row)
