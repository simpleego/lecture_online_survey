# 수강생 상담 온라인 설문

## 구성
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
