"""Versioned survey definitions and immutable response snapshots."""
import json
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import text


class QuestionInput(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    section: str = Field(default="추가 설문", min_length=1, max_length=100)
    kind: Literal["text", "single", "multiple"]
    options: list[str] = Field(default_factory=list, max_length=50)
    required: bool = False
    allow_comment: bool = False
    sort_order: int = Field(default=1000, ge=0, le=100000)
    revision: int | None = Field(default=None, ge=1)

    @field_validator("topic", "section")
    @classmethod
    def trim(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("공백만 입력할 수 없습니다.")
        return value

    @model_validator(mode="after")
    def choices(self):
        self.options = [v.strip() for v in self.options]
        if self.kind == "text":
            self.options = []
        elif len(self.options) < 2 or any(not v or len(v) > 200 for v in self.options) or len(set(self.options)) != len(self.options):
            raise ValueError("서로 다른 선택지를 2~50개 입력해 주세요. 선택지는 200자 이내입니다.")
        return self


class AnswerInput(BaseModel):
    question_id: int = Field(ge=1)
    value: str | list[str] | None = None
    comment: str | None = Field(default=None, max_length=5000)


class ResponseInput(BaseModel):
    student_name: str = Field(min_length=1, max_length=50)
    team_name: str | None = Field(default=None, max_length=50)
    form_revision: int = Field(ge=1)
    answers: list[AnswerInput] = Field(max_length=500)

    @field_validator("student_name")
    @classmethod
    def name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("이름을 입력해 주세요.")
        return value


def decode_question(row):
    result = dict(row)
    result["options"] = json.loads(result.pop("options_json"))
    result["required"] = bool(result["required"])
    result["allow_comment"] = bool(result["allow_comment"])
    return result


def definitions(db, include_deleted=False):
    where = "" if include_deleted else " WHERE deleted=0"
    return [decode_question(r) for r in db.execute(text("SELECT * FROM v4_questions" + where + " ORDER BY sort_order,id")).mappings()]


def form_revision(db, lock=False):
    return db.execute(text("SELECT revision FROM v4_form_state WHERE id=1" + (" FOR UPDATE" if lock else ""))).scalar_one()


def validate_answers(questions, answers):
    lookup = {q["id"]: q for q in questions}
    incoming = {a.question_id: a for a in answers}
    if len(incoming) != len(answers) or not set(incoming).issubset(lookup):
        raise HTTPException(422, "중복되거나 존재하지 않는 설문항목이 있습니다.")
    result = []
    for q in questions:
        answer = incoming.get(q["id"])
        value = answer.value if answer else None
        comment = answer.comment.strip() or None if answer and answer.comment else None
        if comment and not q["allow_comment"]:
            raise HTTPException(422, f"{q['topic']}: 의견을 입력할 수 없는 항목입니다.")
        if q["kind"] == "multiple":
            value = [] if value is None else value
            if not isinstance(value, list) or len(value) != len(set(value)) or any(v not in q["options"] for v in value):
                raise HTTPException(422, f"{q['topic']}: 등록된 선택지를 선택해 주세요.")
        else:
            if value is not None and not isinstance(value, str):
                raise HTTPException(422, f"{q['topic']}: 하나의 답변을 입력해 주세요.")
            value = value.strip() if isinstance(value, str) else None
            value = value or None
            if q["kind"] == "single" and value is not None and value not in q["options"]:
                raise HTTPException(422, f"{q['topic']}: 등록된 선택지를 선택해 주세요.")
            if q["kind"] == "text" and value is not None and len(value) > 5000:
                raise HTTPException(422, f"{q['topic']}: 답변은 5,000자 이내로 입력해 주세요.")
        if q["required"] and not value:
            raise HTTPException(422, f"{q['topic']}: 필수 항목을 작성해 주세요.")
        result.append({"question": q, "value": value, "comment": comment})
    return result


def normalize_response(row):
    row = dict(row)
    snapshot = json.loads(row["snapshot_json"])
    normalized = {key: None for key in (
        "understanding_level", "practice_level", "ai_tool_level", "course_career_fit", "practice_status",
        "review_frequency", "code_understanding", "class_speed", "project_strength", "instructor_support")}
    normalized.update(understanding_areas=[], hardest_points=[], career_fields=[], learn_env_answers=[], facillities_answers=[])
    normalized.update(id=f"v4-{row['id']}", student_name=row["student_name"], team_name=row["team_name"],
                      created_at=row["created_at"], question_answers=snapshot, source="v4")
    for answer in snapshot:
        q, value = answer["question"], answer["value"]
        key = q.get("legacy_key")
        if not key:
            continue
        if key.startswith(("learn_env:", "facillities:")):
            field, item_id = key.split(":")
            if q["kind"] == "single" and value:
                normalized[field + "_answers"].append({"item_id": int(item_id), "satisfaction": value, "comment": answer.get("comment")})
        elif key in ("understanding_level", "practice_level", "ai_tool_level", "course_career_fit"):
            if q["kind"] == "single" and value in ("1", "2", "3", "4", "5"):
                normalized[key] = int(value)
        elif key in ("understanding_areas", "hardest_points", "career_fields", "ai_tool_usage"):
            normalized[key] = value if isinstance(value, list) else [value] if value else []
        elif isinstance(value, str) or value is None:
            normalized[key] = value
    return normalized


def read_new_responses(db, name="", team=""):
    clauses, params = [], {}
    if name:
        clauses.append("LOCATE(:name,student_name)>0")
        params["name"] = name
    if team:
        clauses.append("team_name=:team")
        params["team"] = team
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return [normalize_response(r) for r in db.execute(text("SELECT * FROM v4_responses" + where), params).mappings()]


def build_question_router(get_db, require_admin):
    router = APIRouter()

    @router.get("/api/v4/questions")
    def public_form(db=Depends(get_db)):
        # Same lock as edits/submission: revision and definitions form one consistent snapshot.
        revision = form_revision(db, True)
        questions = definitions(db)
        db.commit()
        return {"revision": revision, "questions": questions}

    @router.get("/api/admin/questions", dependencies=[Depends(require_admin)])
    def list_questions(db=Depends(get_db)):
        return public_form(db)

    def question_values(data):
        values = data.model_dump(exclude={"revision", "options"})
        values["options_json"] = json.dumps(data.options, ensure_ascii=False)
        return values

    @router.post("/api/admin/questions", status_code=201, dependencies=[Depends(require_admin)])
    def add_question(data: QuestionInput, db=Depends(get_db)):
        form_revision(db, True)
        result = db.execute(text("INSERT INTO v4_questions(topic,section,kind,options_json,required,allow_comment,sort_order) VALUES(:topic,:section,:kind,:options_json,:required,:allow_comment,:sort_order)"), question_values(data))
        question_id = result.lastrowid
        db.execute(text("UPDATE v4_form_state SET revision=revision+1 WHERE id=1"))
        db.commit()
        return {"id": question_id}

    @router.put("/api/admin/questions/{question_id}", dependencies=[Depends(require_admin)])
    def edit_question(question_id: int, data: QuestionInput, db=Depends(get_db)):
        form_revision(db, True)
        existing = db.execute(text("SELECT revision FROM v4_questions WHERE id=:id AND deleted=0"), {"id": question_id}).scalar()
        if existing is None:
            raise HTTPException(404, "설문항목을 찾을 수 없습니다.")
        if data.revision is None or data.revision != existing:
            raise HTTPException(409, "다른 작업에서 수정된 항목입니다. 목록을 새로 불러와 주세요.")
        values = question_values(data)
        values["id"] = question_id
        db.execute(text("UPDATE v4_questions SET topic=:topic,section=:section,kind=:kind,options_json=:options_json,required=:required,allow_comment=:allow_comment,sort_order=:sort_order,revision=revision+1 WHERE id=:id"), values)
        db.execute(text("UPDATE v4_form_state SET revision=revision+1 WHERE id=1"))
        db.commit()
        return {"status": "updated"}

    @router.delete("/api/admin/questions/{question_id}", dependencies=[Depends(require_admin)])
    def delete_question(question_id: int, revision: int, db=Depends(get_db)):
        form_revision(db, True)
        result = db.execute(text("UPDATE v4_questions SET deleted=1,revision=revision+1 WHERE id=:id AND revision=:revision AND deleted=0"), {"id": question_id, "revision": revision})
        if result.rowcount != 1:
            raise HTTPException(409, "항목이 변경되거나 삭제되었습니다. 목록을 새로 불러와 주세요.")
        db.execute(text("UPDATE v4_form_state SET revision=revision+1 WHERE id=1"))
        db.commit()
        return {"status": "deleted"}

    @router.post("/api/v4/surveys", status_code=201)
    def submit(data: ResponseInput, db=Depends(get_db)):
        revision = form_revision(db, True)
        if revision != data.form_revision:
            raise HTTPException(409, "작성 중 설문항목이 변경되었습니다. 입력 내용을 보관한 뒤 새로고침해 주세요.")
        if data.team_name and not db.execute(text("SELECT id FROM team WHERE team_name=:team"), {"team": data.team_name}).first():
            raise HTTPException(422, "등록된 팀을 선택해 주세요.")
        snapshot = validate_answers(definitions(db), data.answers)
        result = db.execute(text("INSERT INTO v4_responses(student_name,team_name,form_revision,snapshot_json) VALUES(:name,:team,:revision,:snapshot)"),
                            {"name": data.student_name, "team": data.team_name or None, "revision": revision, "snapshot": json.dumps(snapshot, ensure_ascii=False)})
        response_id = result.lastrowid
        db.commit()
        return {"id": f"v4-{response_id}", "message": "설문이 저장되었습니다."}

    return router


def question_statistics(rows, questions):
    """Include archived questions and saved titles, without reinterpreting past answers."""
    groups = {}
    def add(q, value, comment, row):
        signature = (q['id'], q['topic'], q['kind'], tuple(q['options']))
        group = groups.setdefault(signature, {"question_id":q['id'], "topic":q['topic'], "kind":q['kind'], "options":q['options'], "answers":[]})
        if value not in (None, "", []):
            group['answers'].append((row, value, comment))
    for q in questions:
        if not q['deleted']:
            add(q, None, None, {})
    for row in rows:
        if row.get('source') == 'v4':
            for a in row['question_answers']:
                add(a['question'], a['value'], a.get('comment'), row)
    from collections import Counter
    result=[]
    for group in groups.values():
        answers=group.pop('answers')
        counts=Counter(v for _,value,_ in answers for v in (value if isinstance(value,list) else [value])) if group['kind']!='text' else Counter()
        group.update(answered=len(answers), missing=len(rows)-len(answers),
                     distribution=[{'label':label,'count':count,'percent':round(count/len(rows)*100,1) if rows else 0} for label,count in counts.most_common()],
                     comments=[{'survey_id':r['id'],'student_name':r['student_name'],'comment':value if group['kind']=='text' else comment} for r,value,comment in answers if group['kind']=='text' or comment])
        result.append(group)
    return result
