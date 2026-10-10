from pathlib import Path
import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from admin import build_admin_router, require_admin

# Cloud Run은 연결된 Cloud SQL 인스턴스의 Unix 소켓을 사용합니다.
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "survey_app")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "counsel_survey_prod")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "")
if INSTANCE_CONNECTION_NAME:
    DATABASE_URL = URL.create(
        "postgresql+psycopg", username=DB_USER, password=DB_PASSWORD,
        database=DB_NAME,
        query={"host": f"/cloudsql/{INSTANCE_CONNECTION_NAME}", "port": str(DB_PORT)},
    )
else:
    DATABASE_URL = URL.create(
        "postgresql+psycopg", username=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
    )

engine = create_engine(
    DATABASE_URL, pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "0")),
    connect_args={"connect_timeout": 10}, echo=False,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(title="수강생 상담 설문 API", version="1.0.0")


@app.middleware("http")
async def protect_private_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/api/admin", "/api/surveys")):
        response.headers["Cache-Control"] = "no-store"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ItemAnswer(BaseModel):
    item_id: int = Field(ge=1)
    satisfaction: str = Field(min_length=1, max_length=30)
    comment: str | None = Field(default=None, max_length=5000)


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

    learn_env_answers: list[ItemAnswer] = Field(default_factory=list)
    facillities_answers: list[ItemAnswer] = Field(default_factory=list)


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


@app.get("/admin")
def admin_page():
    return FileResponse(BASE_DIR / "static" / "admin.html")


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="DB 연결에 실패했습니다. 서버 설정을 확인해 주세요.")


@app.get("/api/teams")
def get_teams(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, team_name FROM team ORDER BY team_name")).mappings().all()
    return [dict(row) for row in rows]


@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, category_name, category_value FROM category ORDER BY sort_order, id"
    )).mappings().all()
    return [dict(row) for row in rows]


@app.get("/api/practices")
def get_practices(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, practice_status FROM practice ORDER BY sort_order, id"
    )).mappings().all()
    return [dict(row) for row in rows]


@app.get("/api/study-problems")
def get_study_problems(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, problem_name FROM study_problem ORDER BY sort_order, id"
    )).mappings().all()
    return [dict(row) for row in rows]


@app.get("/api/review-frequencies")
def get_review_frequencies(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, frequency_name FROM review_frequency ORDER BY sort_order, id"
    )).mappings().all()
    return [dict(row) for row in rows]


@app.get("/api/preffered-occupations")
def get_preffered_occupations(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, occupation_name, occupation_value FROM preffered_occupation ORDER BY sort_order, id"
    )).mappings().all()
    return [dict(row) for row in rows]


def read_evaluation_items(db: Session, table: str):
    # 호출하는 함수에서 고정한 테이블명만 사용합니다.
    rows = db.execute(text(f"SELECT id, item_name, options_json, comment_hint FROM {table} ORDER BY sort_order, id")).mappings().all()
    return [dict(id=r['id'], item_name=r['item_name'], options=json.loads(r['options_json']), comment_hint=r['comment_hint']) for r in rows]


@app.get("/api/learn-env")
def get_learn_env(db: Session = Depends(get_db)):
    return read_evaluation_items(db, "learn_env")


@app.get("/api/facillities")
def get_facillities(db: Session = Depends(get_db)):
    return read_evaluation_items(db, "facillities")


def validate_item_answers(answers: list[ItemAnswer], items: list[dict]):
    # 기존 1~8번만 보내는 요청도 계속 저장할 수 있습니다.
    if not answers:
        return
    allowed = {item['id']: item['options'] for item in items}
    ids = [answer.item_id for answer in answers]
    if len(ids) != len(set(ids)) or set(ids) != set(allowed):
        raise HTTPException(status_code=422, detail="평가 항목을 빠짐없이 선택해 주세요.")
    if any(answer.satisfaction not in allowed[answer.item_id] for answer in answers):
        raise HTTPException(status_code=422, detail="등록된 만족도 응답을 선택해 주세요.")


def decode_survey_answers(row):
    result = dict(row)
    for field in ("learn_env_answers", "facillities_answers"):
        result[field] = json.loads(result[field]) if result.get(field) else []
    return result


@app.post("/api/surveys", status_code=201)
def create_survey(data: SurveyCreate, db: Session = Depends(get_db)):
    # 기존 team_name 저장 구조를 유지하면서 등록된 팀인지 확인합니다.
    if data.team_name is not None:
        team = db.execute(
            text("SELECT id FROM team WHERE team_name = :team_name"),
            {"team_name": data.team_name}
        ).first()
        if not team:
            raise HTTPException(status_code=422, detail="등록된 팀을 선택해 주세요.")

    if data.understanding_areas:
        allowed_categories = set(db.execute(text("SELECT category_value FROM category")).scalars().all())
        if any(area not in allowed_categories for area in data.understanding_areas):
            raise HTTPException(status_code=422, detail="등록된 이해도 분야를 선택해 주세요.")

    practice = db.execute(
        text("SELECT id FROM practice WHERE practice_status = :practice_status"),
        {"practice_status": data.practice_status}
    ).first()
    if not practice:
        raise HTTPException(status_code=422, detail="등록된 실습 단계를 선택해 주세요.")

    if data.hardest_points:
        allowed_problems = set(db.execute(text("SELECT problem_name FROM study_problem")).scalars().all())
        if any(point not in allowed_problems for point in data.hardest_points):
            raise HTTPException(status_code=422, detail="등록된 학습 어려움 항목을 선택해 주세요.")

    frequency = db.execute(
        text("SELECT id FROM review_frequency WHERE frequency_name = :frequency_name"),
        {"frequency_name": data.review_frequency}
    ).first()
    if not frequency:
        raise HTTPException(status_code=422, detail="등록된 복습 빈도를 선택해 주세요.")

    if data.career_fields:
        allowed_occupations = set(db.execute(text("SELECT occupation_value FROM preffered_occupation")).scalars().all())
        if any(field not in allowed_occupations for field in data.career_fields):
            raise HTTPException(status_code=422, detail="등록된 관심 분야를 선택해 주세요.")

    validate_item_answers(data.learn_env_answers, get_learn_env(db))
    validate_item_answers(data.facillities_answers, get_facillities(db))

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
            class_speed, need_more_explanation, practice_amount, instructor_support,
            learn_env_answers, facillities_answers
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
            :class_speed, :need_more_explanation, :practice_amount, :instructor_support,
            :learn_env_answers, :facillities_answers
        ) RETURNING id
    """)

    params = data.model_dump()
    for field in ("learn_env_answers", "facillities_answers"):
        params[field] = json.dumps(params[field], ensure_ascii=False)
    params["understanding_areas"] = join_list(data.understanding_areas)
    params["hardest_points"] = join_list(data.hardest_points)
    params["ai_tool_usage"] = join_list(data.ai_tool_usage)
    params["career_fields"] = join_list(data.career_fields)

    try:
        result = db.execute(sql, params)
        survey_id = result.scalar_one()
        db.commit()
        return {
            "message": "상담 설문이 정상적으로 저장되었습니다.",
            "id": survey_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="설문 저장에 실패했습니다. 잠시 후 다시 시도해 주세요.")


@app.get("/api/surveys", dependencies=[Depends(require_admin)])
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
    return [decode_survey_answers(row) for row in rows]


@app.get("/api/surveys/{survey_id}", dependencies=[Depends(require_admin)])
def get_survey(survey_id: int, db: Session = Depends(get_db)):
    sql = text("""
        SELECT *
        FROM survey_responses
        WHERE id = :survey_id
    """)
    row = db.execute(sql, {"survey_id": survey_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="설문을 찾을 수 없습니다.")

    return decode_survey_answers(row)


app.include_router(build_admin_router(get_db, decode_survey_answers, get_learn_env, get_facillities))
