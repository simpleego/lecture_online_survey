# Cloud Run + Cloud SQL for PostgreSQL 설정

## 1. Cloud SQL 생성

- PostgreSQL 16, 서울(asia-northeast3), 인스턴스명 예: `survey-db`.
- DB: `counsel_survey_prod`. 앱용 사용자: `survey_app`.
- 자동 백업과 삭제 보호를 설정합니다. 고가용성은 비용·운영 요구에 따라 선택합니다.
- Cloud Run과 같은 프로젝트/리전을 권장합니다.
- Cloud Run 통합 Cloud SQL 연결(Unix 소켓)을 사용합니다. 일반 인터넷에 DB 접속을 공개하지 않습니다.
- Cloud SQL Admin API를 활성화하고 Cloud Run 실행 서비스 계정에 `Cloud SQL Client` 역할을 부여합니다.

## 2. 데이터 준비: 둘 중 하나만 선택

### 새 데이터로 시작

Cloud SQL의 생성한 DB에 관리자 계정으로 접속해 `database.sql`을 실행합니다.
테이블 9개와 기본 선택 목록이 생성됩니다. 반복 실행해도 기존 선택 항목을 덮어쓰지 않습니다.

### 기존 응답 이전

별도로 준비한 `migration-private/counsel_survey_postgresql.sql`을 비공개 경로로 전달해
**빈 운영 DB**에 복원합니다. 이 SQL 자체에 구조와 실제 데이터를 포함합니다.
`database.sql`을 먼저 실행하지 않습니다. 기존 테이블에 합치거나 덮어쓰는 용도가 아닙니다.

```bash
psql -h 127.0.0.1 -p 5432 -U postgres -d counsel_survey_prod -W -v ON_ERROR_STOP=1 -f counsel_survey_postgresql.sql
```

위 TCP 예시는 Cloud SQL Auth Proxy를 로컬 5432에서 실행한 경우입니다.
Cloud Shell 등 관리자 접속 환경에 맞춰 호스트/사용자를 지정합니다.
MariaDB의 `.sql` 덤프는 PostgreSQL에 직접 복원할 수 없습니다.
변환 SQL과 manifest에는 기존 응답이 포함되므로 GitHub에 올리지 않습니다.

## 3. 앱 사용자 권한

스키마/데이터 복원은 관리자 계정으로 수행합니다. 앱 계정에 다음 권한을 부여합니다.
Cloud SQL 콘솔에서 `survey_app`을 만들었다면 아래 GRANT만 실행하면 됩니다.

```sql
GRANT CONNECT ON DATABASE counsel_survey_prod TO survey_app;
GRANT USAGE ON SCHEMA public TO survey_app;
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO survey_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO survey_app;
```

향후 테이블을 추가하면 관리자 계정으로 해당 테이블/시퀀스 권한도 부여합니다.

## 4. Cloud Run 수정 및 새 버전 배포

- 컨테이너 포트 8080. Dockerfile 기본 명령을 사용합니다.
- Cloud SQL 연결에 위 인스턴스를 추가합니다.
- 환경변수:

| 이름 | 값 |
|---|---|
| INSTANCE_CONNECTION_NAME | 프로젝트ID:asia-northeast3:survey-db |
| DB_PORT | 5432 |
| DB_NAME | counsel_survey_prod |
| DB_USER | survey_app |
| DB_POOL_SIZE | 5 |
| DB_MAX_OVERFLOW | 0 |
| ADMIN_USER | admin |

`DB_PASSWORD`, `ADMIN_PASSWORD`는 서로 다른 새 비밀번호를 Secret Manager에서 연결합니다.
실행 서비스 계정에는 해당 비밀에 대한 `Secret Manager Secret Accessor` 역할이 필요합니다.
INSTANCE_CONNECTION_NAME이 설정되면 DB_HOST 대신 `/cloudsql/연결이름` 소켓을 사용합니다.
인스턴스 연결 이름만 환경변수에 넣어서는 부족하며 **Cloud Run Cloud SQL 연결 설정**도 해야 합니다.

처음에는 Cloud Run 최대 인스턴스를 2로 제한하고 DB 연결 한도를 확인합니다.
각 컨테이너는 최대 5개 DB 연결을 사용합니다. Uvicorn은 기본 단일 프로세스로 실행합니다.

## 5. 확인

- `/api/health`가 database=connected인지 확인.
- 설문 선택 목록 및 9·10번 문항 확인.
- 실제 테스트 설문을 제출하고 접수번호, 관리자 조회/분석 확인.
- 인증 없는 조회가 차단되는지 확인.

로컬 검증:
```bash
pip install -r requirements.txt
python -m unittest test_analysis -v
# TEST_DATABASE_URL에 테스트용 PostgreSQL URL 지정 후:
python -m unittest test_postgresql -v
```

## 최종 이전 다시 생성

접수를 잠시 중지하고 저장 중인 요청이 끝난 후:
```bash
pip install -r requirements-migration.txt
python export_postgresql.py --source-env /private/source.env --output migration-private/final.sql
```

원본 MariaDB는 유지됩니다. 최신 변환 SQL을 새 빈 DB에 복원하고 manifest와 행 수를 비교합니다.
현재 변환 파일은 생성 시점까지의 응답만 포함합니다.

공식 연결 안내: https://docs.cloud.google.com/sql/docs/postgres/connect-run
