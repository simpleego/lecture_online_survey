"""관리자 API. 비밀번호는 .env에서 읽고 브라우저 메모리에만 유지합니다."""
import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import text
from analysis import summarize, statistics

security = HTTPBasic(auto_error=False)


def require_admin(credentials: HTTPBasicCredentials | None = Depends(security)):
    username = os.getenv("ADMIN_USER", "admin")
    password = os.getenv("ADMIN_PASSWORD", "")
    if not password:
        raise HTTPException(status_code=503, detail="관리자 접속 설정이 필요합니다.")
    if credentials is None or not (
        secrets.compare_digest(credentials.username.encode(), username.encode())
        and secrets.compare_digest(credentials.password.encode(), password.encode())
    ):
        raise HTTPException(status_code=401, detail="관리자 아이디 또는 비밀번호를 확인해 주세요.")
    return credentials.username


def build_admin_router(get_db, decode, get_env, get_facilities):
    router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])

    @router.get("/session")
    def session():
        return {"status": "ok"}

    def read_rows(db, name, team):
        clauses = []
        params = {}
        if name:
            clauses.append("strpos(student_name, :name) > 0")
            params["name"] = name
        if team:
            clauses.append("team_name = :team")
            params["team"] = team
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = db.execute(text("SELECT * FROM survey_responses" + where + " ORDER BY id DESC"), params).mappings().all()
        return [decode(row) for row in rows]

    @router.get("/surveys")
    def responses(name: str = Query(default="", max_length=50), team: str = Query(default="", max_length=50),
                  page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
                  db=Depends(get_db)):
        rows = read_rows(db, name.strip(), team)
        start = (page - 1) * page_size
        return {"total": len(rows), "page": page, "page_size": page_size,
                "items": [{"id": r["id"], "student_name": r["student_name"], "team_name": r["team_name"],
                           "created_at": r["created_at"], "summary": summarize(r)} for r in rows[start:start + page_size]]}

    @router.get("/surveys/{survey_id}")
    def detail(survey_id: int, db=Depends(get_db)):
        row = db.execute(text("SELECT * FROM survey_responses WHERE id=:id"), {"id": survey_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="설문을 찾을 수 없습니다.")
        result = decode(row)
        return {"response": result, "summary": summarize(result),
                "learn_env_items": get_env(db), "facillities_items": get_facilities(db)}

    @router.get("/statistics")
    def stats(name: str = Query(default="", max_length=50), team: str = Query(default="", max_length=50), db=Depends(get_db)):
        return statistics(read_rows(db, name.strip(), team), get_env(db), get_facilities(db))

    return router
