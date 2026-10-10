# 온라인 수강생 설문조사 · 3차 버전

수강생 상담 설문과 관리자 조회·분석을 제공하는 웹 앱입니다.

- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: FastAPI
- Database: PostgreSQL 16 이상, SQLAlchemy + Psycopg
- 배포: Cloud Run + Cloud SQL for PostgreSQL

## 제공 기능

설문 1~10번, DB 기반 선택 목록, 관리자 로그인, 이름·팀 검색, 페이지 이동,
개인별 요약·상세 응답, 전체·팀별 통계, 상담 확인 표시, 환경·시설 만족도와 의견을 제공합니다.
기존 설문 항목과 API 응답 구조는 유지합니다. 조회 API는 관리자 인증이 필요합니다.

## Google Cloud 배포

[CLOUD_RUN_POSTGRESQL.md](CLOUD_RUN_POSTGRESQL.md)의 단계에 따라 Cloud SQL DB 생성,
스키마/데이터 복원, 앱 사용자 권한, Cloud Run 인스턴스 연결과 환경변수를 설정합니다.
컨테이너 기본 포트는 8080이며 PORT 환경변수를 지원합니다.
GitHub 연결은 코드 배포용이며 DB를 자동 생성하거나 기존 응답을 자동 이전하지 않습니다.

INSTANCE_CONNECTION_NAME이 설정되면 Cloud SQL Unix 소켓으로 연결합니다.
설정하지 않으면 DB_HOST와 DB_PORT로 TCP 연결합니다.
DB 비밀번호와 관리자 비밀번호는 Secret Manager에 서로 다른 값으로 설정합니다.

## 로컬 실행

```bash
python -m venv .venv
# 가상환경을 활성화한 후:
pip install -r requirements.txt
cp .env.example .env
# .env에 PostgreSQL 접속 정보와 관리자 비밀번호를 설정합니다.
python run.py
```

설문: http://localhost:8080/ · 관리자: http://localhost:8080/admin
새 DB 초기화는 해당 PostgreSQL DB에 접속해 database.sql을 실행합니다.
기존 응답 이전은 별도 변환 SQL을 빈 DB에 복원합니다. 두 방법을 동시에 실행하지 않습니다.

## 테스트

```bash
python -m unittest test_analysis -v
# TEST_DATABASE_URL에 테스트용 PostgreSQL 연결 URL을 설정한 후:
python -m unittest test_postgresql -v
```

실제 PostgreSQL 테스트는 임시 스키마를 만들어 실행하고 롤백합니다.

## MariaDB 데이터 이전

원본 MariaDB 코드는 로컬 v3 폴더에 보존되어 있습니다.
이 저장소의 배포 코드는 PostgreSQL용입니다.

```bash
pip install -r requirements-migration.txt
python export_postgresql.py --source-env /private/source.env --output migration-private/final.sql
```

변환 파일은 실제 상담 응답을 포함하며 Git에서 제외합니다. 원본 DB는 수정하지 않습니다.
생성 SQL에는 전체 구조, 실제 관리 목록/응답, 접수번호 시퀀스 보정이 포함됩니다.

## 통계 해석

반복 제출은 각각 응답 1건으로 집계합니다. 복수 선택 비율은 전체 응답 수 기준입니다.
환경·시설 평균은 1~5점만 포함하고 미이용/제공 없음/해당 없음과 미응답을 구분합니다.
상담 확인은 추가 확인을 위한 참고이며 학생 순위나 확정 평가가 아닙니다.
