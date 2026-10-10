# analysis.py 백엔드 매뉴얼

- 대상: 4차 버전 `v4/analysis.py`
- 작성 기준일: 2026-10-09
- 소스: [analysis.py](./analysis.py)
- 관련 문서: [main.md](./main.md)

## 1. 파일의 역할

정규화된 설문 데이터를 받아 상담 참고사항과 통계 딕셔너리를 계산한다. DB 연결과 HTTP 처리는 하지 않는다. 관리자 API에서 이 파일의 계산 결과를 사용한다.

## 2. 상수와 입력 규약

| 상수 | 내용 |
|---|---|
| `SCORES` | understanding_level: 수업 이해도, practice_level: 실습 수준, ai_tool_level: AI 도구 활용, course_career_fit: 진로 적합도 |
| `SATISFACTION` | 매우 불만족=1, 불만족=2, 보통=3, 만족=4, 매우 만족=5 |

`rows`는 기존 응답의 `decode_response()` 또는 4차 응답의 `normalize_response()`가 만든 딕셔너리 목록이다. 점수, 복습·수업속도·코드이해 필드, 복수 선택 필드, `learn_env_answers`, `facillities_answers` 등의 키를 사용한다. 임의의 불완전한 딕셔너리는 KeyError를 일으킬 수 있다.

## 3. 통계 계산 원칙

- 점수 평균: 1~5 범위의 숫자만 반영, 소수 둘째 자리 반올림. 유효 점수가 없으면 None.
- 단일 분포: 전달된 값의 발생 횟수 합계를 분모로 사용.
- 복수 선택 분포: 설문 응답 건수를 분모로 사용하며 한 응답의 같은 선택지는 한 번만 계산. 비율 합계가 100%를 넘을 수 있음.
- 환경·시설 평균: 만족도 1~5로 변환 가능한 답변만 반영. 해당 없음 등은 평균에서 제외.
- 같은 이름의 반복 응답도 별도 응답으로 집계. 학생별 중복 제거는 하지 않음.

차트의 표시 방식은 프런트엔드에서 결정한다. 복수 선택 API의 응답자 기준 비율과 파이차트의 선택 횟수 합계 기준 조각 비율은 다를 수 있다.

## 함수별 설명

### `split_choices(value)`

**기능:** 복수 선택 값을 리스트로 변환한다.

**전달값:** 리스트, 쉼표로 구분된 문자열 또는 None.

**반환값:** 선택지 리스트.

**추가 설명:** 리스트이면 같은 객체를 그대로 반환한다. 문자열은 쉼표로 분리하고 빈 항목만 제거한다. 공백 제거·중복 제거는 하지 않는다. 문자열 선택지 안의 쉼표는 구분자로 처리되므로 4차 스냅샷은 리스트를 유지한다.

### `counseling_flags(row)`

**기능:** 상담에서 추가 확인할 사항을 찾는다.

**전달값:** 정규화된 설문 딕셔너리 한 건.

**반환값:** 참고사항 문자열 리스트. 해당 사항이 없으면 [].

**추가 설명:** 이해도·실습수준 각각 2 이하, 복습을 거의 하지 않음, AI 활용 4 이상이면서 코드를 일부만 또는 거의 이해하지 못함, 빠른 수업속도와 이해도 2 이하, 환경·시설의 불만족 또는 매우 불만족을 각각 확인한다. 점수 누락은 낮은 점수로 간주하지 않는다. 종합 점수나 순위를 만들지 않는다. 여러 조건은 동시에 추가된다.

### `summarize(row)`

**기능:** 목록·상세 화면에 필요한 응답 요약을 만든다.

**전달값:** 정규화된 설문 한 건.

**반환값:** scores, practice_status, review_frequency, understanding_areas, hardest_points, career_fields, strength, support_request, flags 딕셔너리.

**추가 설명:** scores의 키는 한국어 점수 항목명이다. 복수 선택은 split_choices로 변환한다. strength는 project_strength, support_request는 instructor_support를 사용한다.

### `distribution(values)`

**기능:** 일반 범주형 값의 빈도·비율을 계산한다.

**전달값:** 해시 가능한 값의 iterable. generator도 가능.

**반환값:** `[{"label": 값, "count": 횟수, "percent": 비율}, ...]`.

**추가 설명:** Counter.most_common 순으로 정렬한다. 동률은 처음 등장한 순서를 따른다. 비율은 소수 첫째 자리로 반올림한다. 빈 입력은 []. None을 직접 전달하면 별도 범주로 센다.

### `choice_distribution(rows, field)`

**기능:** 복수 선택 문항의 응답자 기준 비율을 계산한다.

**전달값:** `rows`: 응답 목록. `field`: 대상 필드 이름.

**반환값:** label, count, percent를 가진 배열.

**추가 설명:** 한 응답 내 중복은 set으로 제거한다. 분모는 선택하지 않은 응답까지 포함한 len(rows)이다. 빈 입력은 []. 빈도가 같은 선택지의 순서는 set 순회 영향으로 일정하지 않을 수 있다.

### `score_stats(rows)`

**기능:** 4개 점수 항목의 평균·누락·분포를 계산한다.

**전달값:** 정규화된 응답 목록.

**반환값:** 점수 필드별 label, count, missing, average, distribution 객체.

**추가 설명:** count는 유효 숫자 개수, missing은 전체 건수에서 count를 뺀 값이다. distribution은 항상 문자열 라벨 1~5와 count를 포함한다. 정상 입력은 정수 점수이다. 구현상 범위 내 실수도 평균에 포함하지만 분포는 정확히 1~5와 일치하는 값만 센다. 누락을 3으로 대체하지 않는다.

### `evaluation_stats(rows, field, items)`

**기능:** 학습환경 또는 시설 항목별 만족도와 의견을 계산한다.

**전달값:** `rows`: 응답 목록. `field`: learn_env_answers 또는 facillities_answers. `items`: id, item_name을 가진 현재 항목 목록.

**반환값:** 항목별 item_id, item_name, answered, missing, rated, excluded, average, distribution, comments 배열.

**추가 설명:** answered는 해당 항목 답변 수, missing은 전체 응답 수-answered, rated는 점수 변환 가능 답변 수, excluded는 answered-rated이다. 분포는 평균 제외 답변도 포함하며 해당 항목 answered를 분모로 한다. 의견은 survey_id, student_name, satisfaction, comment를 포함한다. 현재 목록에 없는 과거 항목도 이전 항목 #ID로 추가한다. 정상 데이터는 한 설문·항목당 답변 한 개를 전제로 한다.

### `statistics(rows, env_items, facility_items)`

**기능:** 전체·팀별 점수와 상담 참고 건수 및 각종 분포를 계산한다.

**전달값:** 응답 목록, 학습환경 항목 목록, 시설 항목 목록.

**반환값:** response_count, flagged_count, scores, review_frequency, hardest_points, career_fields, teams, learn_env, facillities 객체.

**추가 설명:** flagged_count는 참고사항이 하나 이상인 응답 건수이며 참고사항 총개수가 아니다. 복습 누락은 미응답 범주로 포함한다. 팀 미선택은 팀 미선택으로 묶고 팀 이름순으로 정렬한다. 동적 문항 questions는 이 함수가 아닌 admin.stats에서 추가한다.

## 사용 예와 검증

```python
from analysis import statistics
result = statistics([], [], [])
assert result["response_count"] == 0
assert result["scores"]["understanding_level"]["average"] is None
```

계산 검증은 [test_analysis.md](./test_analysis.md)에 정리되어 있다. 이 모듈은 표준 라이브러리 collections만 사용하며 SQL·ORM·파일 저장을 수행하지 않는다.
