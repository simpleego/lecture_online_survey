# main.py 백엔드 매뉴얼

- 대상: 4차 버전 `v4/main.py` — FastAPI 애플리케이션 버전 `4.0.0`
- 작성 기준일: 2026-10-09
- 소스: [main.py](./main.py)
- 설명 범위: 이 파일에 정의된 모든 함수, 요청 모델, 초기 설정 및 외부 라우터 연결

## 1. 파일의 역할

`main.py`는 FastAPI 서버의 진입점이다. 웹 화면과 정적 파일을 제공하고, DB 세션을 준비하며, 기존 고정형 설문의 선택 목록·저장·조회 API를 정의한다. 관리자 기능과 4차 동적 설문 기능은 각각 `admin.py`, `questions.py`에서 만든 라우터를 등록하여 연결한다.

현재 설문 작성 화면은 **`questions.py`의 `POST /api/v4/surveys`**를 사용한다. 이 파일의 **`POST /api/surveys`는 기존 고정형 설문과의 호환을 위해 유지한 API**이다. 두 저장 API의 요청 형식과 저장 테이블이 다르므로 구분해서 사용해야 한다.

| 구분 | 주요 구현 파일 | 저장/조회 대상 |
|---|---|---|
| 기존 고정형 설문 | `main.py` | `survey_responses` |
| 4차 동적 설문 | `questions.py` | `v4_questions`, `v4_form_state`, `v4_responses` |
| 관리자 통합 조회·분석 | `admin.py` + `analysis.py` + `questions.py` | 기존 응답과 4차 응답을 합산 |
| 화면과 차트 | `static/` | HTML/CSS/JavaScript |

## 2. 초기 설정과 주요 객체

### 2.1 환경 설정

`BASE_DIR = Path(__file__).resolve().parent`로 소스 파일이 있는 폴더를 구하고, `load_dotenv(BASE_DIR / ".env")`로 해당 폴더의 환경 설정을 읽는다. 따라서 실행 명령의 작업 폴더와 별개로 `v4/.env`를 지정해 읽는다.

| 이름 | 용도 | 환경변수가 없을 때 코드 기본값 |
|---|---|---|
| `DB_HOST` | DB 서버 주소 | `127.0.0.1` |
| `DB_PORT` | DB 포트 | 문자열 `3306` |
| `DB_USER` | DB 접속 사용자 | `root` |
| `DB_PASSWORD` | DB 접속 비밀번호 | 소스에 정의된 기본값 사용; 실제 값은 이 문서에 기재하지 않음 |
| `DB_NAME` | 사용할 DB 이름 | `counsel_survey` |
| `BASE_DIR` | `.env`, 정적 파일, HTML 경로의 기준 | `main.py`가 있는 폴더 |

관리자 계정의 `ADMIN_USER`, `ADMIN_PASSWORD`도 `.env`에서 읽힌 환경 설정을 사용하지만, 인증 처리는 `admin.py`의 `require_admin()`에서 수행한다.

### 2.2 DB 연결 객체

| 객체 | 기능 | 추가 설명 |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy의 DB 연결 주소 | `mysql+pymysql://사용자:비밀번호@호스트:포트/DB?charset=utf8mb4` 형식 |
| `engine` | DB 연결 및 커넥션 풀 관리 | `pool_pre_ping=True`: 풀의 연결을 사용하기 전 연결 상태 확인. `echo=False`: SQL 로그 출력 비활성화 |
| `SessionLocal` | 요청에서 사용할 `Session` 생성 | `autoflush=False`, `autocommit=False`. 저장 함수에서 명시적으로 `commit()` 실행 |

이 파일은 DB나 테이블을 자동 생성하지 않는다. 기존 테이블과 4차 전용 테이블은 DB 구성 및 `migrate_v4.py` 실행으로 준비해야 한다. 연결 주소는 문자열로 조립하므로 DB 비밀번호에 URL 예약 문자가 포함되면 연결 주소 해석에 주의해야 한다.

### 2.3 애플리케이션 객체

`app = FastAPI(title="수강생 상담 설문 API", version="4.0.0")`로 서버를 생성한다.

- `/static` 경로를 `BASE_DIR / "static"` 폴더에 연결한다.
- CORS는 모든 출처·메서드·헤더를 허용하고 `allow_credentials=False`로 설정되어 있다.
- 아래의 캐시 제어 미들웨어와 관리자/동적 설문 라우터를 등록한다.
- 포트는 이 파일에 지정되어 있지 않다. 실행 명령의 `--port 8003` 또는 `run.ps1`에서 결정한다.

## 3. 요청 데이터 모델

### 3.1 `ItemAnswer`

학습환경 또는 시설의 한 평가 항목을 표현한다.

| 필드 | 전달 타입 | 필수/기본값 | 검증 및 의미 |
|---|---|---|---|
| `item_id` | `int` | 필수 | 1 이상. 해당 평가 항목 ID |
| `satisfaction` | `str` | 필수 | 1~30자. 만족도 또는 해당 없음 등의 선택값 |
| `comment` | `str \| None` | `None` | 선택 의견, 최대 5,000자 |

```json
{"item_id": 1, "satisfaction": "만족", "comment": "사용하기 편리합니다."}
```

문자열 길이와 ID 범위는 모델에서 검사한다. 항목 ID와 만족도가 실제 DB에 등록되어 있는지는 `validate_item_answers()`에서 검사한다.

### 3.2 `SurveyCreate`

기존 `POST /api/surveys`의 JSON 요청 본문이다. 아래 표에서 **필수**는 기본값이 없어서 요청에 반드시 포함해야 하는 필드다. `None`과 `[]` 기본값이 있는 필드는 생략 가능하다.

| 필드 | 타입 | 필수/기본값 | 의미와 모델 검증 |
|---|---|---|---|
| `student_name` | `str` | 필수 | 이름, 1~50자 |
| `team_name` | `str \| None` | `None` | 팀명, 최대 50자 |
| `understanding_level` | `int` | 필수 | 수업 이해도, 1~5 |
| `understanding_good` | `str \| None` | `None` | 잘 이해되는 부분 |
| `understanding_difficult` | `str \| None` | `None` | 어려운 부분 |
| `understanding_areas` | `list[str]` | `[]` | 이해가 잘 되는 분야, 복수 선택 |
| `practice_level` | `int` | 필수 | 실습 수준, 1~5 |
| `practice_status` | `str` | 필수 | 실습 단계, 1~30자 |
| `practice_comment` | `str \| None` | `None` | 실습 의견 |
| `hardest_points` | `list[str]` | `[]` | 학습 어려움, 복수 선택 |
| `hardest_comment` | `str \| None` | `None` | 어려움 상세 의견 |
| `review_frequency` | `str` | 필수 | 복습 빈도, 1~30자 |
| `ai_learning_usage` | `str \| None` | `None` | AI 도구의 학습 활용 방법 |
| `improvement_method` | `str \| None` | `None` | 부족한 부분 보완 방법 |
| `project_role` | `str \| None` | `None` | 현재 역할, 최대 100자 |
| `desired_role` | `str \| None` | `None` | 희망 역할, 최대 100자 |
| `collaboration_difficulty` | `str \| None` | `None` | 협업 어려움 |
| `project_strength` | `str \| None` | `None` | 프로젝트 강점 |
| `project_burden` | `str \| None` | `None` | 프로젝트 부담 |
| `ai_tool_level` | `int` | 필수 | AI 도구 활용 수준, 1~5 |
| `ai_tool_usage` | `list[str]` | `[]` | AI 활용 목적, 복수 선택 |
| `code_understanding` | `str` | 필수 | AI 생성 코드 이해 수준, 1~30자 |
| `ai_tool_comment` | `str \| None` | `None` | AI 도구 의견 |
| `desired_job` | `str \| None` | `None` | 희망 직무, 최대 100자 |
| `career_fields` | `list[str]` | `[]` | 관심 분야, 복수 선택 |
| `course_career_fit` | `int` | 필수 | 진로 적합도, 1~5 |
| `career_comment` | `str \| None` | `None` | 진로 고민 |
| `class_speed` | `str` | 필수 | 수업 속도, 1~30자 |
| `need_more_explanation` | `str \| None` | `None` | 추가 설명 요청 |
| `practice_amount` | `str` | 필수 | 실습량, 1~30자 |
| `instructor_support` | `str \| None` | `None` | 강사 지원 요청 |
| `learn_env_answers` | `list[ItemAnswer]` | `[]` | 학습환경 평가 배열 |
| `facillities_answers` | `list[ItemAnswer]` | `[]` | 시설 평가 배열 |

#### 모델 사용 시 알아둘 점

- `learn_env_answers`, `facillities_answers`는 `Field(default_factory=list)`로 기본 배열을 만든다.
- 길이 제한이 표시되지 않은 자유 서술 필드에는 이 모델에 별도의 최대 길이 제한이 없다. DB 컬럼의 제한은 별도로 적용된다.
- `student_name`은 문자열 길이를 검사하지만 공백 제거·공백만 있는 이름 거부를 별도로 구현하지 않았다.
- `ai_tool_usage`, `code_understanding`, `class_speed`, `practice_amount`는 이 저장 함수에서 화면 선택지와 대조하지 않는다. 타입·모델 조건과 DB 제약만 적용된다.
- 4차 동적 설문은 이 모델이 아닌 `questions.py`의 `ResponseInput`을 사용한다.

## 4. 함수와 API 목록

| 함수 | HTTP 경로/호출 방식 | 인증 | 정상 반환 |
|---|---|---|---|
| `protect_private_cache` | HTTP 미들웨어 | 해당 요청의 정책 적용 | 헤더를 처리한 응답 객체 |
| `get_db` | `Depends(get_db)` | 해당 없음 | `Session`을 `yield` |
| `join_list` | 내부 호출 | 해당 없음 | 쉼표로 연결한 문자열 |
| `index` | `GET /` | 공개 | 설문 HTML 파일 |
| `admin_page` | `GET /admin` | 공개 | 관리자 HTML 파일 |
| `health` | `GET /api/health` | 공개 | 연결 상태 딕셔너리 |
| `get_teams` | `GET /api/teams` | 공개 | 팀 배열 |
| `get_categories` | `GET /api/categories` | 공개 | 이해 분야 배열 |
| `get_practices` | `GET /api/practices` | 공개 | 실습 단계 배열 |
| `get_study_problems` | `GET /api/study-problems` | 공개 | 학습 어려움 배열 |
| `get_review_frequencies` | `GET /api/review-frequencies` | 공개 | 복습 빈도 배열 |
| `get_preffered_occupations` | `GET /api/preffered-occupations` | 공개 | 관심 분야 배열 |
| `read_evaluation_items` | 내부 호출 | 해당 없음 | 가공한 평가 항목 배열 |
| `get_learn_env` | `GET /api/learn-env` | 공개 | 학습환경 항목 배열 |
| `get_facillities` | `GET /api/facillities` | 공개 | 시설 항목 배열 |
| `validate_item_answers` | 내부 호출 | 해당 없음 | 성공 시 `None` |
| `decode_survey_answers` | 내부 호출 | 해당 없음 | 평가 JSON을 배열로 바꾼 응답 딕셔너리 |
| `create_survey` | `POST /api/surveys` | 공개 | 저장 안내와 정수 접수번호, HTTP 201 |
| `get_surveys` | `GET /api/surveys` | 관리자 | 기존 응답 배열 |
| `get_survey` | `GET /api/surveys/{survey_id}` | 관리자 | 기존 응답 1건 |

`db: Session = Depends(get_db)`는 HTTP 요청 본문이나 쿼리로 전달하는 값이 아니다. FastAPI가 DB 세션을 주입한다. 아래 함수 설명의 `db`는 모두 같은 의미다.

## 5. 함수별 상세 설명

### 5.1 `protect_private_cache(request, call_next)`

**기능:** 실제 요청 처리를 실행한 뒤 HTML·정적 파일·관련 API 응답에 캐시 금지 헤더를 추가한다. 비동기 HTTP 미들웨어다.

| 전달값 | 의미 |
|---|---|
| `request` | 현재 HTTP 요청 객체. `request.url.path`에서 요청 경로 확인 |
| `call_next` | 다음 미들웨어 또는 라우트 처리를 호출하는 함수. `await call_next(request)`로 응답 획득 |

**반환값:** 헤더 처리 후의 HTTP 응답 객체.

**추가 설명:** 정확히 `/`, `/admin`인 경로 또는 `/api/admin`, `/api/surveys`, `/api/v4`, `/static/`으로 시작하는 경로에 `Cache-Control: no-store`를 설정한다. 관리자 정보 저장을 막고 이전 JavaScript가 재사용되는 문제를 줄인다. HTTP 응답 헤더를 다룰 뿐, 관리자 인증 자체를 수행하지 않는다.

### 5.2 `get_db()`

**기능:** 요청 처리용 DB 세션을 생성하고 종료 시 정리한다.

**전달값:** 없음.

**반환값:** 일반 `return` 반환값 대신 `yield db`로 `Session`을 전달하는 제너레이터다.

**추가 설명:** `SessionLocal()`로 세션을 생성하고, 처리 성공·실패와 관계없이 `finally`에서 `db.close()`를 실행한다. 이 함수는 저장을 자동 커밋하지 않는다. 저장 함수가 `commit()` 또는 `rollback()`을 담당한다.

### 5.3 `join_list(values: list[str]) -> str`

**기능:** 복수 선택 답변을 DB의 문자열 컬럼에 저장할 형태로 변환한다.

**전달값:** `values` — 문자열 배열.

**반환값:** `",".join(values)`의 결과 문자열.

```python
join_list(["Python", "DB/SQL"])  # "Python,DB/SQL"
join_list([])                    # ""
```

**추가 설명:** 항목의 순서를 유지하며 중복 제거나 쉼표 이스케이프는 하지 않는다. 쉼표가 들어간 선택값을 정확하게 보존하는 일반 JSON 저장 함수가 아니다. 기존 고정형 설문의 네 복수 선택 필드에서 사용한다.

### 5.4 `index()`

**기능:** 설문 작성 화면을 제공한다.

**전달값:** 없음. HTTP 요청은 `GET /`.

**반환값:** `FileResponse(BASE_DIR / "static" / "index.html")`.

**추가 설명:** Python 함수가 HTML을 생성하지 않고 파일을 전달한다. 화면에서 불러오는 설문항목과 저장 API는 `static/app.js`에 의해 결정되며 현재는 4차 동적 설문 API를 사용한다.

### 5.5 `admin_page()`

**기능:** 관리자 화면 파일을 제공한다.

**전달값:** 없음. HTTP 요청은 `GET /admin`.

**반환값:** `FileResponse(BASE_DIR / "static" / "admin.html")`.

**추가 설명:** HTML 자체는 로그인 없이 열 수 있다. 응답·통계 조회와 설문항목 변경은 별도 API에서 관리자 인증을 검사한다. 로그인, 탭 전환, 차트 표시는 `static/admin.js`, `static/charts.js`의 역할이다.

### 5.6 `health(db: Session = Depends(get_db))`

**기능:** DB에 `SELECT 1`을 실행하여 기본 연결 상태를 확인한다.

**전달값:** 주입된 DB 세션 `db`. HTTP 요청은 `GET /api/health`.

**반환값:** 정상 시 HTTP 200과 아래 딕셔너리.

```json
{"status": "ok", "database": "connected"}
```

**추가 설명:** 실패하면 HTTP 500, `detail="DB 연결 실패: {예외 내용}"`을 반환한다. 개별 설문 테이블·스키마·데이터·권한 전체를 검사하는 함수는 아니다. 따라서 이 API가 성공해도 누락된 테이블이나 특정 INSERT 권한 문제는 별도로 확인해야 한다.

### 5.7 `get_teams(db: Session = Depends(get_db))`

**기능:** `team` 테이블의 팀 목록을 조회한다.

**전달값:** `db`. HTTP 요청은 `GET /api/teams`; 사용자 입력 파라미터 없음.

**반환값:** `list[dict]`. 각 항목에 `id`, `team_name` 포함.

```json
[{"id": 1, "team_name": "A팀"}]
```

**추가 설명:** `ORDER BY team_name`으로 정렬한다. 조회 결과가 없으면 `[]`이다.

### 5.8 `get_categories(db: Session = Depends(get_db))`

**기능:** `category` 테이블에서 이해 분야 목록을 가져온다.

**전달값:** `db`. HTTP 요청은 `GET /api/categories`.

**반환값:** 각 항목이 `id`, `category_name`, `category_value`를 가진 배열.

```json
[{"id": 2, "category_name": "DB / SQL", "category_value": "DB/SQL"}]
```

**추가 설명:** `sort_order, id` 순으로 정렬한다. 화면 표시용 이름과 DB 저장용 값을 구분한다. 설문 제출에는 `category_value`를 사용한다.

### 5.9 `get_practices(db: Session = Depends(get_db))`

**기능:** `practice` 테이블의 실습 단계 목록을 가져온다.

**전달값:** `db`. HTTP 요청은 `GET /api/practices`.

**반환값:** 각 항목이 `id`, `practice_status`를 가진 배열.

```json
[{"id": 1, "practice_status": "예제를 보면서 따라 할 수 있다"}]
```

**추가 설명:** `sort_order, id` 순으로 정렬한다. 기존 설문의 필수 필드 `practice_status`와 같은 저장값을 제공한다.

### 5.10 `get_study_problems(db: Session = Depends(get_db))`

**기능:** `study_problem` 테이블의 학습 어려움 항목을 가져온다.

**전달값:** `db`. HTTP 요청은 `GET /api/study-problems`.

**반환값:** 각 항목이 `id`, `problem_name`을 가진 배열.

```json
[{"id": 1, "problem_name": "문법 이해"}]
```

**추가 설명:** `sort_order, id` 순으로 정렬한다. 기존 `hardest_points`의 허용값을 DB 기준으로 관리한다.

### 5.11 `get_review_frequencies(db: Session = Depends(get_db))`

**기능:** `review_frequency` 테이블에서 복습 빈도 선택지를 가져온다.

**전달값:** `db`. HTTP 요청은 `GET /api/review-frequencies`.

**반환값:** 각 항목이 `id`, `frequency_name`을 가진 배열.

```json
[{"id": 1, "frequency_name": "거의 하지 않는다"}]
```

**추가 설명:** `sort_order, id` 순으로 정렬하며 기존 설문의 `review_frequency` 필드에 사용할 문자열을 제공한다.

### 5.12 `get_preffered_occupations(db: Session = Depends(get_db))`

**기능:** `preffered_occupation` 테이블의 관심 직무·분야 목록을 가져온다.

**전달값:** `db`. HTTP 요청은 `GET /api/preffered-occupations`.

**반환값:** 각 항목이 `id`, `occupation_name`, `occupation_value`를 가진 배열.

```json
[{"id": 6, "occupation_name": "DevOps / 배포", "occupation_value": "DevOps/배포"}]
```

**추가 설명:** `sort_order, id` 순으로 정렬한다. 제출할 때는 `occupation_value`를 사용한다. 함수·API·테이블의 `preffered` 철자는 현재 구현과 DB 호환을 위해 그대로 표기했다.

### 5.13 `read_evaluation_items(db: Session, table: str)`

**기능:** 학습환경과 시설 항목의 공통 조회 처리를 수행한다.

| 전달값 | 의미 |
|---|---|
| `db` | 사용할 DB 세션 |
| `table` | 호출자가 지정하는 고정 테이블명: `learn_env` 또는 `facillities` |

**반환값:** 각 항목이 `id`, `item_name`, `options`, `comment_hint`를 가진 배열. DB의 `options_json` 문자열을 `json.loads()`로 변환하여 `options`로 반환한다.

```json
[{"id": 1, "item_name": "컴퓨터·노트북", "options": ["매우 불만족", "불만족", "보통", "만족", "매우 만족", "해당 없음"], "comment_hint": "장비 성능, 프로그램 실행 등 사용 중 불편한 점"}]
```

**추가 설명:** `sort_order, id` 순으로 정렬한다. SQL의 테이블명은 f-string으로 조립되므로 HTTP 사용자 입력을 전달하면 안 된다. 현재는 아래의 두 함수가 고정 문자열로 호출한다. 잘못된 `options_json`은 이 함수에서 별도 복구하지 않는다.

### 5.14 `get_learn_env(db: Session = Depends(get_db))`

**기능:** 학습환경 평가 항목을 가져온다.

**전달값:** `db`. HTTP 요청은 `GET /api/learn-env`.

**반환값:** `read_evaluation_items(db, "learn_env")`의 배열.

**추가 설명:** 컴퓨터·노트북, 주변 소음, 빔프로젝터, 음향 등의 현재 DB 항목을 제공한다. API 호출 외에도 기존 설문 저장 검증과 관리자 라우터의 항목 정보 조회에 사용된다.

### 5.15 `get_facillities(db: Session = Depends(get_db))`

**기능:** 시설 평가 항목을 가져온다.

**전달값:** `db`. HTTP 요청은 `GET /api/facillities`.

**반환값:** `read_evaluation_items(db, "facillities")`의 배열.

**추가 설명:** 화장실, 음료수, 간식 등의 현재 DB 항목을 제공한다. `facillities` 철자는 실제 테이블·API·필드와 동일하게 유지했다. 함수 호출 용도는 `get_learn_env()`와 같다.

### 5.16 `validate_item_answers(answers: list[ItemAnswer], items: list[dict])`

**기능:** 기존 설문의 환경·시설 답변이 현재 등록 항목과 선택지에 맞는지 검사한다.

| 전달값 | 의미 |
|---|---|
| `answers` | 제출된 `ItemAnswer` 배열 |
| `items` | `id`, `options` 등을 가진 DB 평가 항목 배열 |

**반환값:** 검증 성공 시 `None`; 데이터를 변환해 반환하지 않는다.

**검증 순서:**

1. `answers`가 빈 배열이면 즉시 종료한다.
2. 제출 ID에 중복이 없는지 검사한다.
3. 제출 ID의 집합과 현재 등록 ID의 집합이 같은지 검사한다.
4. 각 `satisfaction` 값이 해당 항목의 허용 선택지에 포함되는지 검사한다.

**실패 반환:**

| 조건 | HTTP 상태 | `detail` |
|---|---|---|
| 중복, 누락, 알 수 없는 ID | 422 | `평가 항목을 빠짐없이 선택해 주세요.` |
| 허용되지 않은 만족도 | 422 | `등록된 만족도 응답을 선택해 주세요.` |

**추가 설명:** 이전 1~8번만 제출하는 요청을 허용하기 위해 빈 배열은 통과한다. 하지만 한 항목이라도 답한다면 해당 그룹의 모든 현재 항목을 제출해야 한다. 학습환경과 시설 배열은 각각 독립적으로 검사한다. 의견 길이는 `ItemAnswer` 모델에서 검사한다.

### 5.17 `decode_survey_answers(row)`

**기능:** DB의 기존 응답 한 행을 API 응답용 딕셔너리로 변환한다.

**전달값:** `row` — `dict(row)`로 변환 가능한 DB 행 매핑.

**반환값:** 행의 전체 필드를 가진 딕셔너리. `learn_env_answers`, `facillities_answers`는 JSON 문자열에서 배열로 변환된다. 해당 값이 없거나 비어 있으면 `[]`로 처리한다.

**추가 설명:** 나머지 필드는 원래 값을 유지한다. `understanding_areas`, `hardest_points`, `ai_tool_usage`, `career_fields`의 쉼표 문자열은 이 함수에서 배열로 변환하지 않는다. 잘못된 JSON 문자열은 예외를 발생시키며 별도 복구 처리는 없다. 관리자 라우터에도 이 함수를 전달한다.

### 5.18 `create_survey(data: SurveyCreate, db: Session = Depends(get_db))`

**기능:** 기존 고정형 설문 한 건을 검증하여 `survey_responses`에 저장한다.

| 전달값 | 전달 위치 | 의미 |
|---|---|---|
| `data` | HTTP JSON 본문 | `SurveyCreate` 형식의 설문 |
| `db` | 의존성 주입 | DB 세션 |

**HTTP 요청:** `POST /api/surveys`. 관리자 인증을 요구하지 않는다.

**처리 과정:**

1. 요청 본문을 `SurveyCreate` 모델로 검증한다.
2. `team_name`이 `None`이 아니면 `team`에 존재하는지 확인한다.
3. 분야, 실습 단계, 학습 어려움, 복습 빈도, 관심 분야를 해당 기준 테이블과 대조한다.
4. 학습환경·시설 항목을 조회하고 `validate_item_answers()`로 검증한다.
5. `model_dump()`로 모델을 딕셔너리로 만든다.
6. 두 평가 배열은 `json.dumps(..., ensure_ascii=False)`로 JSON 문자열을 만든다.
7. 네 복수 선택 배열은 `join_list()`로 쉼표 문자열을 만든다.
8. 바인딩 파라미터로 INSERT를 실행하고 `db.commit()`한다.
9. 신규 행의 `lastrowid`를 반환한다.

**DB 대조 대상:**

| 요청 필드 | 기준 테이블/컬럼 |
|---|---|
| `team_name` | `team.team_name` |
| `understanding_areas` | `category.category_value` |
| `practice_status` | `practice.practice_status` |
| `hardest_points` | `study_problem.problem_name` |
| `review_frequency` | `review_frequency.frequency_name` |
| `career_fields` | `preffered_occupation.occupation_value` |
| `learn_env_answers` | `learn_env.id`, `options_json` |
| `facillities_answers` | `facillities.id`, `options_json` |

**반환값:** 정상 시 HTTP 201과 저장 안내·신규 접수번호를 가진 딕셔너리.

```json
{"message": "상담 설문이 정상적으로 저장되었습니다.", "id": 86}
```

위 접수번호는 형식 설명용 예시이며 실제 값은 DB에서 발급한다.

**오류 반환:** 모델 또는 선택지 검증 실패는 HTTP 422이다. INSERT 또는 commit 구간에서 실패하면 `db.rollback()` 후 HTTP 500과 `detail="설문 저장 실패: {예외 내용}"`을 반환한다. INSERT 이전의 조회 과정에서 발생한 DB 예외는 이 함수의 `try` 범위에 포함되지 않아 이 메시지로 변환되지 않는다.

**추가 설명:** `team_name=""`는 `None`이 아니므로 실제로 등록된 빈 팀명이 없다면 거부된다. 팀 미선택은 `null` 또는 필드 생략으로 전달한다. 이름을 기준으로 중복 제출을 막지 않는다. 이 함수는 4차 질문 스냅샷이나 `v4_responses`를 저장하지 않는다.

### 5.19 `get_surveys(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db))`

**기능:** 기존 설문 응답 목록을 조회한다.

| 전달값 | 전달 위치 | 기본값/조건 |
|---|---|---|
| `limit` | URL 쿼리 | 100, 1~500 사이 정수 |
| `db` | 의존성 주입 | DB 세션 |

**HTTP 요청:** `GET /api/surveys?limit=20`. `Depends(require_admin)`으로 관리자 인증을 검사한다.

**반환값:** HTTP 200, `survey_responses`의 전체 컬럼을 담은 응답 딕셔너리 배열. 각 행에 `decode_survey_answers()`를 적용한다. 응답이 없으면 `[]`.

**추가 설명:** `ORDER BY id DESC LIMIT :limit`로 정렬·제한한다. 페이지 번호·이름·팀 검색 기능은 이 API에 없다. 관리자 화면의 페이지 이동·검색·4차 응답 통합은 `admin.py`의 `/api/admin/surveys`에서 제공한다. `limit`이 유효하지 않으면 HTTP 422이다.

### 5.20 `get_survey(survey_id: int, db: Session = Depends(get_db))`

**기능:** 기존 설문 접수번호로 한 건을 조회한다.

| 전달값 | 전달 위치 | 의미 |
|---|---|---|
| `survey_id` | URL 경로 | 기존 `survey_responses.id`의 정수 값 |
| `db` | 의존성 주입 | DB 세션 |

**HTTP 요청:** `GET /api/surveys/26`. 관리자 인증이 필요하다.

**반환값:** 정상 시 HTTP 200과 `decode_survey_answers(row)` 결과 딕셔너리. 해당 ID가 없으면 HTTP 404.

```json
{"detail": "설문을 찾을 수 없습니다."}
```

**추가 설명:** SQL 값은 `:survey_id`로 바인딩한다. 이 경로에는 `v4-2` 같은 새 접수번호를 넣을 수 없다. 정수로 해석할 수 없는 경로값은 HTTP 422가 된다. 기존 정수 ID와 `v4-숫자` ID를 함께 지원하는 상세 조회는 `/api/admin/surveys/{survey_id}`이다.

## 6. 외부 라우터 등록

아래 함수는 `main.py`에 정의된 함수가 아니라 다른 파일에서 가져와 실행하는 라우터 생성 함수다.

### 6.1 `build_admin_router(get_db, decode_survey_answers, get_learn_env, get_facillities)`

- 구현 위치: [admin.py](./admin.py).
- 전달값: DB 세션 공급 함수, 기존 응답 변환 함수, 환경/시설 항목 조회 함수.
- 반환값: 관리자용 `APIRouter`.
- 사용: `app.include_router(...)`로 등록한다.
- 주요 경로: `/api/admin/session`, `/api/admin/surveys`, `/api/admin/surveys/{survey_id}`, `/api/admin/statistics`.
- 추가 설명: 관리자 인증, 기존·4차 응답 통합 검색, 페이지 이동, 개인별 요약과 통계는 이 라우터에서 처리한다.

### 6.2 `build_question_router(get_db, require_admin)`

- 구현 위치: [questions.py](./questions.py).
- 전달값: DB 세션 공급 함수와 관리자 인증 함수.
- 반환값: 동적 설문용 `APIRouter`.
- 사용: `app.include_router(...)`로 등록한다.
- 주요 경로: `GET /api/v4/questions`, `POST /api/v4/surveys`, `/api/admin/questions`의 GET/POST, `/api/admin/questions/{question_id}`의 PUT/DELETE.
- 추가 설명: 4차 설문항목 관리·버전 충돌 검사·작성 당시 질문 스냅샷 저장은 `questions.py`에 구현되어 있다. 현재 설문 화면의 주요 API다.

### 6.3 `require_admin`

`admin.py`에서 가져온 인증 의존성이다. 기존 응답 목록·상세 API는 이 함수를 경로의 `dependencies`에 등록한다.

- 전달 방식: HTTP `Authorization` 헤더의 Basic 인증 정보.
- 정상 반환: 인증된 관리자 아이디.
- 로그인 정보 누락 또는 불일치: HTTP 401.
- 관리자 비밀번호 설정 없음: HTTP 503.
- 사용 예: `Authorization: Basic <아이디:비밀번호를 Base64 인코딩한 값>`.

실제 관리자 비밀번호는 이 문서에 기록하지 않는다.

## 7. 기존 설문 저장 예시

아래는 기존 저장 API의 필수 필드를 포함한 예시다. 선택값은 현재 기준 테이블에 실제로 존재해야 한다. 환경·시설 배열은 기존 요청과의 호환을 보여주기 위해 생략했다.

```http
POST /api/surveys
Content-Type: application/json
```

```json
{
  "student_name": "김도윤",
  "team_name": "A팀",
  "understanding_level": 3,
  "practice_level": 3,
  "practice_status": "요구사항을 보고 혼자 작성할 수 있다",
  "review_frequency": "거의 매일",
  "ai_tool_level": 4,
  "code_understanding": "전체 흐름은 이해한다",
  "course_career_fit": 4,
  "class_speed": "적당하다",
  "practice_amount": "적당하다"
}
```

요청 → 모델 검증 → 기준 테이블 검증 → 배열 저장 형식 변환 → INSERT → commit → HTTP 201의 순서로 처리한다.

조회 시 두 평가 JSON 필드는 배열로 복원하지만, 네 복수 선택 필드는 쉼표 문자열로 반환한다. 따라서 저장 요청 배열 형식과 조회 응답 형식이 모든 필드에서 동일한 것은 아니다.

## 8. 상태 코드와 현재 구현의 처리 범위

| 상태 코드 | 대표 발생 조건 |
|---|---|
| 200 | 화면 제공, 선택 목록 조회, 연결 확인, 응답 조회 성공 |
| 201 | 기존 또는 외부 라우터의 새 설문 저장 성공 |
| 401 | 관리자 인증 누락/실패; `require_admin`에서 발생 |
| 404 | 기존 응답 ID가 존재하지 않음 |
| 409 | 외부 `questions.py` 라우터의 설문 버전 충돌 등 |
| 422 | 모델 조건, 쿼리/경로 타입, 등록 선택값 검증 실패 |
| 500 | DB 연결 또는 저장 실패 등 |
| 503 | 관리자 인증 설정이 준비되지 않음 |

연결 확인과 저장 실패의 현재 메시지에는 원본 DB 예외 문자열이 포함된다. 선택 목록 조회와 JSON 변환 함수는 내부 예외를 별도 HTTP 메시지로 가공하지 않는다. 응답 모델을 별도로 지정하지 않았으므로 조회 응답은 DB 행 딕셔너리를 기준으로 구성된다.

## 9. 실행과 확인

v4 폴더에서 준비된 가상환경을 사용해 실행한다.

```powershell
..\v3\.venv\Scripts\python.exe -m uvicorn main:app --port 8003
```

또는 `run.ps1`을 사용한다.

```powershell
.\run.ps1
```

| 확인 항목 | 주소 |
|---|---|
| 설문 작성 화면 | `http://127.0.0.1:8003/` |
| 관리자 화면 | `http://127.0.0.1:8003/admin` |
| DB 기본 연결 | `http://127.0.0.1:8003/api/health` |
| 자동 생성 API 문서 | `http://127.0.0.1:8003/docs` |
| API 명세 JSON | `http://127.0.0.1:8003/openapi.json` |

자동 API 문서에는 이 파일에서 직접 정의한 API와 등록한 외부 라우터의 API가 함께 표시된다.
