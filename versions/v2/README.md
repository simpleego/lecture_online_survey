# 수강생 상담 온라인 설문

관심 분야는 `preffered_occupation` 테이블과 `GET /api/preffered-occupations`를 사용합니다.
기존 6개 항목과 순서, 복수 선택을 유지하며 `survey_responses.career_fields`에 기존 값으로 저장합니다.
표시명 `DevOps / 배포`의 저장값은 기존과 같은 `DevOps/배포`입니다.

## 9·10번 환경 및 시설 평가
- `learn_env`: 컴퓨터·노트북, 주변 소음, 빔프로젝터 가시성, 마이크·음향 시스템.
- `facillities`: 화장실, 음료수 제공, 간식 제공. 테이블명은 요청한 철자를 사용합니다.
- 각 테이블은 평가 항목, 만족도 선택지, 의견 안내, 표시 순서를 관리합니다.
- `GET /api/learn-env`, `GET /api/facillities`에서 목록을 불러옵니다.
- 화면에서 항목별 만족도는 필수이며 기본값이 없습니다. 의견은 선택 사항으로 최대 5,000자입니다.
- 설문 응답은 `survey_responses.learn_env_answers`, `facillities_answers`에 JSON 문자열로 저장하며 조회 API에서는 배열로 반환합니다.
- 기존 설문과 1~8번만 제출하는 요청은 새 평가 항목을 빈 배열로 처리합니다.
- `database.sql` 실행 시 기존 테이블에도 새 응답 컬럼을 추가하며 기존 설문 데이터는 보존합니다.

## 2차 버전: 팀 선택
- `team` 테이블에 A팀~D팀을 준비합니다. `database.sql`은 다시 실행해도 팀이 중복되지 않습니다.
- `GET /api/teams`에서 팀 목록을 가져와 설문 화면의 선택 상자에 표시합니다.
- 팀은 기존처럼 선택 사항이며, 선택한 팀명은 `survey_responses.team_name`에 저장합니다.
- 현재 1차 버전과 같은 DB를 사용합니다.
- 프로젝트 루트에서 2차 버전 실행: `.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir v2 --port 8001`
- 2차 버전 화면: http://127.0.0.1:8001

## 구성
분야 선택은 `category` 테이블과 `GET /api/categories`를 사용합니다.
6개 분야를 기존 순서대로 표시하며 복수 선택과 기존 저장값을 유지합니다.
현재 실습 단계는 `practice` 테이블과 `GET /api/practices`를 사용합니다.
기존 5개 선택지와 순서, 필수 선택을 유지하며 `survey_responses.practice_status`에 저장합니다.
학습 중 가장 어려운 점은 `study_problem` 테이블과 `GET /api/study-problems`를 사용합니다.
기존 6개 항목과 순서, 복수 선택을 유지하며 `survey_responses.hardest_points`에 저장합니다.
모든 선택 목록을 불러온 뒤 제출 버튼이 활성화됩니다.
수업 후 복습 빈도는 `review_frequency` 테이블과 `GET /api/review-frequencies`를 사용합니다.
기존 5개 항목과 순서, 필수 선택을 유지하며 `survey_responses.review_frequency`에 저장합니다.

- Frontend: HTML + CSS + Vanilla JavaScript
- Backend: FastAPI
- Database: MariaDB
- DB 접속: SQLAlchemy + PyMySQL

## 1. MariaDB 데이터베이스 생성
MariaDB 또는 HeidiSQL에서 `database.sql`을 실행합니다.

## 2. 가상환경 생성
Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. 환경변수 설정
`.env.example` 파일을 복사하여 `.env`로 저장합니다.

예시:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=CHANGE_ME
DB_NAME=counsel_survey
```

## 4. 서버 실행
```powershell
uvicorn main:app --reload
```

## 5. 브라우저 접속
- 설문지: http://127.0.0.1:8000
- API 문서: http://127.0.0.1:8000/docs
- 저장된 설문 조회: http://127.0.0.1:8000/api/surveys
- DB 상태 확인: http://127.0.0.1:8000/api/health

## 주요 API
- POST `/api/surveys` : 설문 저장
- GET `/api/surveys` : 설문 목록 조회
- GET `/api/surveys/{id}` : 특정 설문 조회
