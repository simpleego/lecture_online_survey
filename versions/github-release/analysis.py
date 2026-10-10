"""설문 응답을 상담 참고 자료로 요약합니다. 종합점수나 순위를 만들지 않습니다."""
from collections import Counter, defaultdict

SCORES = {
    "understanding_level": "수업 이해도", "practice_level": "실습 수준",
    "ai_tool_level": "AI 도구 활용", "course_career_fit": "진로 적합도",
}
SATISFACTION = {"매우 불만족": 1, "불만족": 2, "보통": 3, "만족": 4, "매우 만족": 5}


def split_choices(value):
    return [part for part in (value or "").split(",") if part]


def counseling_flags(row):
    flags = []
    for key in ("understanding_level", "practice_level"):
        if row[key] <= 2:
            flags.append(f"{SCORES[key]} {row[key]}점: 추가 설명·실습 지원 확인")
    if row["review_frequency"] == "거의 하지 않는다":
        flags.append("복습이 거의 없음: 복습 시간과 학습 방법 확인")
    if row["ai_tool_level"] >= 4 and row["code_understanding"] in (
        "거의 이해하지 못하고 사용한다", "일부만 이해한다"
    ):
        flags.append("AI 활용 수준과 코드 이해 차이: 설명·수정·검증 연습 확인")
    if row["class_speed"] in ("조금 빠르다", "많이 빠르다") and row["understanding_level"] <= 2:
        flags.append("빠른 수업 속도와 낮은 이해도: 보충 설명 확인")
    for key, title in (("learn_env_answers", "학습환경"), ("facillities_answers", "시설")):
        for answer in row.get(key, []):
            if SATISFACTION.get(answer["satisfaction"], 0) in (1, 2):
                flags.append(f"{title} 항목 #{answer['item_id']} 불만족: 개별 의견 확인")
    return flags


def summarize(row):
    return {
        "scores": {label: row[key] for key, label in SCORES.items()},
        "practice_status": row["practice_status"],
        "review_frequency": row["review_frequency"],
        "understanding_areas": split_choices(row["understanding_areas"]),
        "hardest_points": split_choices(row["hardest_points"]),
        "career_fields": split_choices(row["career_fields"]),
        "strength": row["project_strength"],
        "support_request": row["instructor_support"],
        "flags": counseling_flags(row),
    }


def distribution(values):
    counts = Counter(values)
    total = sum(counts.values())
    return [{"label": label, "count": count, "percent": round(count / total * 100, 1)}
            for label, count in counts.most_common()]


def choice_distribution(rows, field):
    counts = Counter(p for r in rows for p in set(split_choices(r[field])))
    return [{"label": label, "count": count, "percent": round(count / len(rows) * 100, 1)}
            for label, count in counts.most_common()]


def score_stats(rows):
    return {key: {"label": label, "count": len(rows),
                  "average": round(sum(r[key] for r in rows) / len(rows), 2) if rows else None,
                  "distribution": [{"label": str(score), "count": sum(r[key] == score for r in rows)}
                                   for score in range(1, 6)]}
            for key, label in SCORES.items()}


def evaluation_stats(rows, field, items):
    result = []
    known = {item["id"]: item["item_name"] for item in items}
    ids = list(known)
    for row in rows:
        for answer in row.get(field, []):
            if answer["item_id"] not in ids:
                ids.append(answer["item_id"])
    for item_id in ids:
        answers = [(r, a) for r in rows for a in r.get(field, []) if a["item_id"] == item_id]
        numeric = [SATISFACTION[a["satisfaction"]] for _, a in answers if a["satisfaction"] in SATISFACTION]
        result.append({"item_id": item_id, "item_name": known.get(item_id, f"이전 항목 #{item_id}"),
                       "answered": len(answers), "missing": len(rows) - len(answers),
                       "rated": len(numeric), "excluded": len(answers) - len(numeric),
                       "average": round(sum(numeric) / len(numeric), 2) if numeric else None,
                       "distribution": distribution(a["satisfaction"] for _, a in answers),
                       "comments": [{"survey_id": r["id"], "student_name": r["student_name"],
                                     "satisfaction": a["satisfaction"], "comment": a["comment"]}
                                    for r, a in answers if a.get("comment")]})
    return result


def statistics(rows, env_items, facility_items):
    teams = defaultdict(list)
    for row in rows:
        teams[row["team_name"] or "팀 미선택"].append(row)
    return {
        "response_count": len(rows),
        "flagged_count": sum(bool(counseling_flags(r)) for r in rows),
        "scores": score_stats(rows),
        "review_frequency": distribution(r["review_frequency"] for r in rows),
        "hardest_points": choice_distribution(rows, "hardest_points"),
        "career_fields": choice_distribution(rows, "career_fields"),
        "teams": [{"team_name": name, "response_count": len(group), "scores": score_stats(group)}
                  for name, group in sorted(teams.items())],
        "learn_env": evaluation_stats(rows, "learn_env_answers", env_items),
        "facillities": evaluation_stats(rows, "facillities_answers", facility_items),
    }
