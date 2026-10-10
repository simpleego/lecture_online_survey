"""Create 20 clearly marked synthetic responses through the local survey API."""
import base64
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import main
from sqlalchemy import text

BASE = "http://127.0.0.1:8002"
PREFIX = "테스트_분석용_"
REPORT = ROOT / "deploy" / "test_surveys_20261009.json"


def api(path, payload=None, admin=False):
    headers = {"Content-Type": "application/json"}
    if admin:
        token = f"{os.environ['ADMIN_USER']}:{os.environ['ADMIN_PASSWORD']}"
        headers["Authorization"] = "Basic " + base64.b64encode(token.encode()).decode()
    request = Request(BASE + path, data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(), headers=headers)
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def run():
    assert not REPORT.exists(), "Batch report already exists; stopped to prevent duplicate generation"
    teams = [x["team_name"] for x in api("/api/teams")] + [None]
    categories = [x["category_value"] for x in api("/api/categories")]
    practices = [x["practice_status"] for x in api("/api/practices")]
    problems = [x["problem_name"] for x in api("/api/study-problems")]
    frequencies = [x["frequency_name"] for x in api("/api/review-frequencies")]
    careers = [x["occupation_value"] for x in api("/api/preffered-occupations")]
    env_items, facilities = api("/api/learn-env"), api("/api/facillities")
    assert len(teams) == 5 and len(practices) == 5 and len(frequencies) == 5
    names = [f"{PREFIX}{i+1:02d}" for i in range(20)]
    with main.engine.connect() as connection:
        before = connection.execute(text("SELECT COUNT(*) FROM survey_responses")).scalar()
        existing = connection.execute(text("SELECT student_name FROM survey_responses")).scalars().all()
    assert not set(names).intersection(existing), "Test names already exist; stopped to prevent duplicates"
    understanding = [1, 2, 3, 4, 5]
    practice = [1, 2, 3, 4, 5]
    ai = [2, 5, 3, 4, 5]
    fit = [2, 3, 4, 4, 5]
    comprehension = ["거의 이해하지 못하고 사용한다", "일부만 이해한다", "전체 흐름은 이해한다", "수정해서 사용할 수 있다", "검증하고 개선할 수 있다"]
    speed = ["많이 빠르다", "조금 빠르다", "적당하다", "조금 느리다", "많이 느리다"]
    amount = ["매우 많다", "조금 많다", "적당하다", "조금 부족하다", "매우 부족하다"]
    strengths = ["오류 상황을 기록하고 질문하려고 노력합니다.", "AI를 활용해 시제품을 빠르게 만들 수 있습니다.", "팀의 작업 진행 상황을 정리합니다.", "API와 DB 연결을 구현할 수 있습니다.", "코드 리뷰와 테스트 작성에 자신이 있습니다."]
    support = ["기초 문법 보충 수업과 짧은 단계별 예제가 필요합니다.", "AI 생성 코드를 직접 설명하고 수정하는 연습을 도와주세요.", "프로젝트 구조와 디버깅 순서를 설명해 주세요.", "실제 서비스의 배포 예제를 보고 싶습니다.", "심화 과제와 포트폴리오 피드백을 부탁드립니다."]
    records = []
    for i, name in enumerate(names):
        p = i // 4
        def evaluations(items, offset):
            answers = []
            for j, item in enumerate(items):
                options = item["options"]
                rating = options[(i + j + offset) % len(options)] if p < 3 else options[3 + (i+j) % 2]
                comment = None
                if rating in ("매우 불만족", "불만족"):
                    comment = f"{item['item_name']} 이용에 불편함이 있어 점검과 개선을 요청합니다."
                elif (i+j) % 3 == 0:
                    comment = "현재 상태에 만족합니다." if rating in ("만족", "매우 만족") else "사용 경험이 적어 평가하기 어렵습니다."
                answers.append(dict(item_id=item["id"], satisfaction=rating, comment=comment))
            return answers
        payload = dict(
            student_name=name, team_name=teams[i % 5],
            understanding_level=understanding[p], understanding_good=f"{categories[i % len(categories)]} 예제를 따라갈 수 있습니다.",
            understanding_difficult="개념을 실제 코드로 연결하는 과정이 어렵습니다." if p < 3 else None,
            understanding_areas=list(dict.fromkeys([categories[i % len(categories)], categories[(i+1) % len(categories)]])),
            practice_level=practice[p], practice_status=practices[p], practice_comment=support[p],
            hardest_points=list(dict.fromkeys([problems[i % len(problems)], problems[(i+2) % len(problems)]])) if p < 4 else [],
            hardest_comment="에러 원인을 찾는 순서를 연습하고 싶습니다." if p < 3 else None,
            review_frequency=frequencies[p], ai_learning_usage="개념 설명과 오류 원인 확인에 활용합니다.",
            improvement_method=["하루 20분 기초 예제 반복", "AI 코드의 각 줄을 설명하기", "수업 노트 정리와 복습", "작은 서비스 직접 구현", "테스트 작성과 코드 리뷰"][p],
            project_role=["자료 조사", "화면 구현", "진행 상황 정리", "백엔드 API 구현", "테스트 및 배포"][p],
            desired_role=["프론트엔드 개발", "백엔드 개발", "데이터 분석", "DB 설계", "배포 자동화"][i % 5],
            collaboration_difficulty="Git 충돌 해결과 역할 분담에 시간이 걸립니다." if i % 3 == 0 else None,
            project_strength=strengths[p], project_burden="일정과 학습을 함께 관리하기 어렵습니다." if p < 3 else None,
            ai_tool_level=ai[p], ai_tool_usage=["코드 생성", "코드 설명"] if p < 3 else ["오류 분석", "리팩터링", "테스트 생성"],
            code_understanding=comprehension[p], ai_tool_comment="생성된 코드를 실행하고 결과를 확인합니다.",
            desired_job=careers[i % len(careers)] + " 관련 직무",
            career_fields=list(dict.fromkeys([careers[i % len(careers)], careers[(i+1) % len(careers)]])),
            course_career_fit=fit[p], career_comment="취업에 필요한 포트폴리오 수준이 궁금합니다." if i % 2 == 0 else None,
            class_speed=speed[p], need_more_explanation=support[p] if p < 3 else None,
            practice_amount=amount[p], instructor_support=support[p],
            learn_env_answers=evaluations(env_items, 0), facillities_answers=evaluations(facilities, 2),
        )
        main.SurveyCreate(**payload)
        result = api("/api/surveys", payload)
        records.append({"id": result["id"], "payload": payload})
        REPORT.write_text(json.dumps({"synthetic": True, "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Created", name, "ID", result["id"], flush=True)
    filtered = api("/api/admin/surveys?name=" + __import__('urllib.parse', fromlist=['quote']).quote(PREFIX), admin=True)
    stats = api("/api/admin/statistics?name=" + __import__('urllib.parse', fromlist=['quote']).quote(PREFIX), admin=True)
    with main.engine.connect() as connection:
        after = connection.execute(text("SELECT COUNT(*) FROM survey_responses")).scalar()
    assert after == before + 20 and filtered["total"] == 20 and stats["response_count"] == 20
    assert len({r['id'] for r in records}) == 20
    for record in records:
        detail = api(f"/api/admin/surveys/{record['id']}", admin=True)["response"]
        for key, expected in record['payload'].items():
            actual = detail[key]
            if key in ('understanding_areas', 'hardest_points', 'ai_tool_usage', 'career_fields'):
                expected = ','.join(expected)
            assert actual == expected, (record['id'], key)
    report = {"synthetic": True, "created_count": 20, "before_count": before, "after_count": after,
              "records": records, "verified_statistics": stats}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print('Verified total:', after, 'Test responses:', stats['response_count'], 'Flagged:', stats['flagged_count'])
    print('Teams:', [(t['team_name'], t['response_count']) for t in stats['teams']])
    print('Averages:', {v['label']: v['average'] for v in stats['scores'].values()})


if __name__ == "__main__":
    run()
