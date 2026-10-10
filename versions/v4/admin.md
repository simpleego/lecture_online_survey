# admin.py 백엔드 매뉴얼

- 대상: 4차 버전 `v4/admin.py`
- 작성 기준일: 2026-10-09
- 소스: [admin.py](./admin.py)
- 관련 문서: [main.md](./main.md)

## 1. 파일의 역할

관리자 인증과 설문 목록·상세·통계 API를 구성한다. 기존 `survey_responses`와 4차 `v4_responses`를 통합하여 조회한다. 이 파일은 설문 데이터를 변경하지 않는다.

## 2. 인증과 의존성

`security = HTTPBasic(auto_error=False)`로 Basic 인증 정보를 받고, `require_admin()`에서 환경변수와 비교한다. 환경변수는 `main.py`가 `.env`에서 읽어 둔다.

| 설정 | 기본값/용도 |
|---|---|
| `ADMIN_USER` | 미설정 시 `admin` |
| `ADMIN_PASSWORD` | 미설정 시 빈 문자열; 관리자 API는 503 반환 |
| `get_db` | 요청별 SQLAlchemy 세션 제공 |
| `decode` | 기존 설문 DB 행을 공통 응답으로 변환 |
| `get_env`, `get_facilities` | 학습환경·시설 평가 항목 조회 |

비밀번호 실제 값은 문서에 기재하지 않는다. 인증 성공은 로그인 토큰이나 서버 세션을 발급하는 동작이 아니다. 각 관리자 요청에 인증 정보가 필요하다.

## 3. API 목록

| 메서드 | 경로 | 주요 입력 | 결과 |
|---|---|---|---|
| GET | `/api/admin/session` | Basic 인증 | 인증 확인 |
| GET | `/api/admin/surveys` | `name`, `team`, `page`, `page_size` | 통합 목록 |
| GET | `/api/admin/surveys/{survey_id}` | 기존 숫자 ID 또는 `v4-숫자` | 설문 상세 |
| GET | `/api/admin/statistics` | `name`, `team` | 통합 통계 |

모든 경로에 `require_admin` 의존성이 적용된다. 아래 `session`부터 `stats`까지의 함수는 `build_admin_router()` 내부 함수이다.

## 함수별 설명

### `require_admin(credentials=Depends(security))`

**기능:** 관리자 ID와 비밀번호를 확인한다.

**전달값:** `credentials`: HTTPBasicCredentials 또는 None. FastAPI가 Authorization 헤더에서 제공한다.

**반환값:** 성공하면 관리자 사용자 이름 문자열.

**추가 설명:** `secrets.compare_digest()`로 UTF-8 바이트를 비교한다. 비밀번호 설정이 없으면 HTTP 503, 인증 누락·불일치는 HTTP 401이다.

### `build_admin_router(get_db, decode, get_env, get_facilities)`

**기능:** 외부에서 전달받은 DB·변환 함수를 사용하여 관리자 라우터를 생성한다.

**전달값:** 세션 의존성, 기존 응답 변환 함수, 학습환경 조회 함수, 시설 조회 함수. 각 조회 함수는 세션을 받는다.

**반환값:** `APIRouter`: `/api/admin` 접두사와 관리자 인증 의존성이 설정된 라우터.

**추가 설명:** `main.py`에서 반환된 라우터를 등록한다. 내부 함수들이 전달된 의존성을 공유한다.

### `session()`

**기능:** 인증된 관리자 요청인지 확인한다.

**전달값:** 직접 전달값 없음. 라우터 인증 의존성이 먼저 실행된다.

**반환값:** `{"status": "ok"}`.

**추가 설명:** DB를 조회하지 않으며 세션이나 토큰을 만들지 않는다.

### `read_rows(db, name, team)`

**기능:** 기존·4차 응답을 검색하고 최신순으로 합친다.

**전달값:** `db`: Session. `name`: 이름 부분 검색 문자열. `team`: 팀 이름 완전 일치 문자열. 빈 문자열이면 해당 필터 생략.

**반환값:** 정규화된 설문 딕셔너리 목록.

**추가 설명:** 기존 테이블은 `LOCATE(:name, student_name)>0`, `team_name=:team`로 조회한다. 사용자 값은 바인딩한다. 4차 응답은 `read_new_responses()`를 사용한다. 생성 시각 내림차순, 동일 시각에는 4차 응답 우선, 다음으로 숫자 ID 내림차순이다. SQL LIMIT 없이 검색 결과 전체를 메모리로 읽는다.

### `responses(name="", team="", page=1, page_size=20, db=Depends(get_db))`

**기능:** 검색 결과의 한 페이지와 전체 건수를 반환한다.

**전달값:** `name`, `team`: 최대 50자. `page`: 1 이상. `page_size`: 1~100, 기본 20. `db`: 요청 세션.

**반환값:** `total`, `page`, `page_size`, `items`를 가진 객체. 각 item은 `id`, `student_name`, `team_name`, `created_at`, `summary`를 포함한다.

**추가 설명:** 이름은 앞뒤 공백을 제거하지만 팀은 그대로 사용한다. `(page-1)*page_size`부터 Python 슬라이싱으로 페이지를 나눈다. 범위를 벗어난 페이지는 빈 items를 반환한다. 기존 ID는 숫자, 4차 ID는 `v4-123` 형식 문자열이다. 쿼리 제약 위반은 HTTP 422이다.

### `detail(survey_id, db=Depends(get_db))`

**기능:** 출처에 맞는 테이블에서 설문 한 건을 읽는다.

**전달값:** `survey_id`: 경로 문자열. `db`: Session.

**반환값:** `response`, `summary`, `learn_env_items`, `facillities_items`를 포함하는 객체.

**추가 설명:** 숫자 문자열은 기존 테이블, `v4-` 다음이 숫자인 문자열은 4차 테이블로 조회한다. 4차 응답은 저장된 스냅샷을 정규화한다. 잘못된 ID 형식·없는 설문은 모두 HTTP 404이다. `facillities` 철자는 코드와 API의 기존 이름을 따른다.

### `stats(name="", team="", db=Depends(get_db))`

**기능:** 검색 조건에 맞는 통합 통계와 동적 문항 통계를 반환한다.

**전달값:** `name`, `team`: 각각 최대 50자. `db`: Session.

**반환값:** `analysis.statistics()` 결과에 `questions` 배열을 추가한 객체.

**추가 설명:** 이름 공백 제거 후 전체 검색 결과를 사용한다. 문항 정의는 삭제된 항목까지 조회하여 과거 응답 분석에 활용한다. 문항별 상세 계산은 [questions.md](./questions.md), 공통 통계는 [analysis.md](./analysis.md)를 참고한다.

## DB 처리와 오류

SQLAlchemy `Session.execute(text(...), params)`로 직접 SQL을 실행한다. ORM 모델 조회 방식은 사용하지 않는다. 이 파일에는 INSERT·UPDATE·DELETE·commit이 없다. 세션 종료는 `main.py`의 `get_db()`가 담당한다. DB 연결·SQL 실행 오류는 이 모듈에서 별도로 처리하지 않는다.

`GET /api/admin/surveys?name=김&team=A팀&page=1&page_size=20`처럼 호출할 수 있다. API 응답의 날짜는 FastAPI 직렬화를 거쳐 전달된다. 검색 결과가 커지면 전체 로딩·정렬에 시간이 들 수 있다.
