# migrate_v4.py 백엔드 매뉴얼

- 대상: 4차 버전 `v4/migrate_v4.py`
- 작성 기준일: 2026-10-09
- 소스: [migrate_v4.py](./migrate_v4.py)
- 관련 문서: [main.md](./main.md)

## 1. 파일의 역할

기존 DB에 4차 버전 전용 테이블과 초기 문항을 추가하고 애플리케이션 계정에 접근 권한을 부여하는 실행 스크립트이다. 기존 설문을 4차 응답으로 복사하지 않는다.

## 2. 연결 설정과 사전 조건

`main`을 import하여 같은 폴더의 .env와 DB 설정을 사용한다.

| 환경변수 | 기본값/용도 |
|---|---|
| DB_MIGRATION_USER | root; 마이그레이션 실행 계정 |
| DB_MIGRATION_PASSWORD | main.DB_PASSWORD; 실행 계정 비밀번호 |
| DB_HOST, DB_PORT, DB_NAME | main의 DB 설정 사용 |
| DB_USER | 권한을 부여할 기존 앱 계정 |

기존 DB·survey_responses·옵션 테이블·환경/시설 테이블과 앱 계정이 존재해야 한다. 실행 계정에는 테이블 생성과 GRANT 권한이 필요하다. DB 백업을 생성하는 기능은 이 스크립트에 없다.

## 3. 생성 테이블

| 테이블 | 주요 컬럼 |
|---|---|
| v4_form_state | id INT PK, revision INT NOT NULL |
| v4_questions | id INT 자동증가 PK, legacy_key VARCHAR(100) NULL UNIQUE, topic VARCHAR(200), section VARCHAR(100), kind VARCHAR(20), options_json LONGTEXT, required·allow_comment BOOLEAN 기본 False, sort_order INT 기본 1000, revision INT 기본 1, deleted BOOLEAN 기본 False |
| v4_responses | id BIGINT 자동증가 PK, student_name VARCHAR(50), team_name VARCHAR(50) NULL, form_revision INT, snapshot_json LONGTEXT, created_at DATETIME 기본 CURRENT_TIMESTAMP |

세 테이블은 InnoDB를 사용한다. 문항·응답 테이블은 utf8mb4/utf8mb4_unicode_ci이다. JSON은 LONGTEXT에 저장되며 별도 JSON 컬럼·외래키 제약은 정의하지 않는다.

## 함수별 설명

### `seeds(db)`

**기능:** 기존 옵션과 고정 설문 구성을 4차 초기 문항으로 변환한다.

**전달값:** SQL을 실행할 DB Connection.

**반환값:** INSERT용 문항 딕셔너리 리스트. 각 원소는 legacy_key, section, topic, kind, options_json, required, allow_comment, sort_order를 포함한다.

**추가 설명:** 고정 필드 29개와 learn_env·facillities의 현재 항목 수만큼 만든다. 총개수는 29+환경 항목 수+시설 항목 수로 DB에 따라 달라진다. 점수 선택지는 문자열 1~5이다. 일반 문항의 별도 의견은 False, 환경·시설은 단일 선택/필수/의견 허용이다. sort_order는 생성 순서대로 10씩 증가한다. 조회·구성만 하고 INSERT는 run에서 수행한다.

### `seeds.values(table, column)`

**기능:** 기존 선택지 테이블에서 값을 순서대로 읽는다.

**전달값:** table: 내부에서 정한 테이블 이름. column: 내부에서 정한 컬럼 이름.

**반환값:** 선택지 값 리스트.

**추가 설명:** seeds 내부 함수이다. sort_order,id 순으로 SELECT한다. 식별자는 SQL 문자열에 삽입되며 외부 사용자 입력을 받지 않는 고정 호출이다. category, practice, study_problem, review_frequency, preffered_occupation 등의 옵션을 사용한다.

### `run()`

**기능:** 전용 테이블 생성, 초기 문항 삽입, 권한 부여와 확인 출력을 수행한다.

**전달값:** 직접 인자 없음. 환경변수 및 main의 설정 사용.

**반환값:** None. 콘솔에 Definitions와 Legacy responses preserved를 출력한다.

**추가 설명:** URL.create로 mysql+pymysql 연결 주소를 구성한다. CREATE TABLE IF NOT EXISTS 후 v4_form_state의 id=1 행이 없을 때만 seeds와 초기 revision=1을 삽입한다. 기존 survey_responses 건수가 전후 동일한지 assert로 확인한다. 앱 계정 localhost에 문항·상태 SELECT/INSERT/UPDATE, 응답 SELECT/INSERT만 부여한다. 기존 테이블 권한은 변경하지 않는다. 정상 종료 시 engine.dispose를 호출한다.

## 실행 방법

v4 폴더에서 필요한 라이브러리가 설치된 Python으로 실행한다. 현재 프로젝트에서 v3의 가상환경을 사용하는 예:

```powershell
..3\.venv\Scripts\python.exe migrate_v4.py
```

관리자 DB 계정이 앱 계정과 다르면 DB_MIGRATION_USER·DB_MIGRATION_PASSWORD를 실행 환경에 설정한다. 비밀번호는 이 문서에 기재하지 않는다.

## 재실행과 확인 범위

- 상태 행 id=1이 있으면 문항을 다시 심지 않으므로 수정·삭제한 문항을 원상 복구하지 않는다.
- CREATE TABLE IF NOT EXISTS는 기존 테이블 구조를 수정하지 않는다. 부분적으로 실패한 상태를 자동 복구하는 기능도 없다.
- 기존 응답 보존 검사는 건수 비교이다. 각 행 내용의 동일성이나 체크섬을 검사하지 않는다. Python 최적화 모드에서는 assert가 생략되므로 일반 실행을 사용한다.
- MySQL/MariaDB의 DDL 및 GRANT는 암묵적 commit이 발생할 수 있어 전체 실행을 하나의 원자적 rollback 작업으로 볼 수 없다.
- GRANT 대상은 '앱계정'@'localhost'이다. 원격 DB 이전 시 실제 계정의 Host 구성에 맞는 권한 설정이 별도로 필요하다.

직접 SQL을 사용하는 스키마 준비 스크립트이며 ORM 기반 마이그레이션이나 Alembic을 사용하지 않는다.
