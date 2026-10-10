# test_questions.py 백엔드 매뉴얼

- 대상: 4차 버전 `v4/test_questions.py`
- 작성 기준일: 2026-10-09
- 소스: [test_questions.py](./test_questions.py)
- 관련 문서: [main.md](./main.md)

## 1. 파일의 역할

동적 문항 모델·답변 검증·스냅샷 변환을 검사하는 단위 테스트와 선택적으로 실행하는 DB 통합 테스트를 포함한다.

## 2. 실행 방법

기본 실행(단위 테스트 5개, DB 테스트 1개 생략):

```powershell
..3\.venv\Scripts\python.exe -B -m unittest test_questions -v
```

DB 통합 테스트를 포함한 실행:

```powershell
$env:RUN_DB_TESTS = "1"
..3\.venv\Scripts\python.exe -B -m unittest test_questions -v
Remove-Item Env:RUN_DB_TESTS
```

FastAPI·Pydantic·SQLAlchemy·PyMySQL 등 프로젝트 의존성이 필요하다. 통합 테스트는 기존 DB와 migrate_v4.py로 준비된 테이블을 사용한다. RUN_DB_TESTS가 정확히 문자열 1일 때만 DatabaseTests가 활성화된다.

## 3. 테스트 클래스

| 클래스 | 테스트 수 | DB 사용 |
|---|---|---|
| QuestionTests | 5 | 없음 |
| DatabaseTests | 1 | 조건부, 외부 트랜잭션 rollback |

DB 테스트는 root 계정과 main.DB_PASSWORD로 연결한다. DB_MIGRATION_USER·DB_MIGRATION_PASSWORD를 사용하지 않으므로 root 계정 설정이 다르면 연결 설정을 조정해야 한다.

## 함수별 설명

### `question(**changes)`

**기능:** 기본 문항 딕셔너리를 생성한다.

**전달값:** changes: 기본 필드를 덮어쓸 키워드 인자.

**반환값:** 문항 정의 딕셔너리.

**추가 설명:** 기본은 id=1, 복수 선택, 선택지 Python/SQL, 필수=True, 의견 허용=False, revision=1이다.

### `QuestionTests.test_options_and_blank_titles(self)`

**기능:** 문항 제목과 선택지 모델 제약을 검증한다.

**전달값:** self: 테스트 인스턴스.

**반환값:** None; assertion 실패 시 실패.

**추가 설명:** 선택지 1개·중복·공백 항목·빈 제목을 거부하고 text 유형의 options가 []로 정리되는지 확인한다.

### `QuestionTests.test_multiple_required_duplicate_unknown(self)`

**기능:** 필수 복수 선택과 잘못된 ID/선택지 입력을 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 답변 누락·빈 리스트·중복 선택·미등록 선택지·존재하지 않는 문항 ID·중복 문항 ID는 HTTPException이어야 한다. 정상 2개 선택은 그대로 반환되는지 확인한다.

### `QuestionTests.test_text_limits_and_comments(self)`

**기능:** 텍스트 길이·의견 허용·학생 이름 규칙을 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 5001자 텍스트, 의견 비허용 문항의 의견은 HTTPException, 공백 이름은 ValidationError인지 확인한다.

### `QuestionTests.test_absent_score_never_becomes_default_three(self)`

**기능:** 점수 없는 스냅샷의 누락 처리를 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 빈 스냅샷 정규화 후 이해도 평균 None, missing=1, flagged_count=0을 확인한다. 미응답 점수를 임의로 3으로 채우지 않는다는 회귀 검증이다.

### `QuestionTests.test_snapshot_preserves_comma_choices(self)`

**기능:** 쉼표가 들어간 선택지의 리스트 보존을 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 데이터, 분석이라는 한 선택지가 쉼표로 분리되지 않고 백엔드와 함께 총 2개로 유지되는지 정규화·통계를 검사한다.

### `DatabaseTests.test_crud_submission_history_and_legacy_statistics(self)`

**기능:** DB 문항 CRUD, 제출 충돌, 과거 스냅샷 보존, 기존 통합 통계를 검증한다.

**전달값:** self. 환경변수 RUN_DB_TESTS=1 및 접근 가능한 준비된 DB 필요.

**반환값:** None. 종료 후 응답 건수와 전체 버전이 원래 값인지 assertion으로 확인한다.

**추가 설명:** 외부 트랜잭션과 Session의 create_savepoint를 사용한다. 텍스트·단일·복수 문항 생성, 오래된 전체 버전 제출 409, 최신 설문 제출, 문항 수정 및 오래된 개별 버전 수정 409, 논리 삭제, 저장 스냅샷 동일성, 과거 문항 통계·기존 응답 건수 보존을 확인한다. finally에서 세션을 닫고 외부 트랜잭션을 rollback한다.

## DB 테스트의 동작과 한계

통합 테스트는 main.app에 등록된 라우트의 endpoint 함수를 직접 호출한다. FastAPI 요청 처리·인증 의존성·HTTP 직렬화·브라우저 화면을 검증하는 테스트는 아니다.

실제 문항·응답 INSERT 및 UPDATE가 트랜잭션 안에서 실행된다. 정상적인 InnoDB 환경에서는 테스트 후 내용이 rollback된다. 자동 증가 ID는 rollback으로 되돌아가지 않을 수 있으므로 ID에 빈 번호가 생길 수 있다. 테이블 생성이나 스키마 수정은 이 테스트에서 하지 않는다.

main.py import 시 환경 설정과 앱 초기화가 수행된다. DB 테스트는 현존 활성 문항에 값을 채워 제출하므로 선택형 문항에 올바른 선택지가 있어야 한다. 테스트 성공은 위에서 명시한 시나리오의 검증이며 모든 오류·동시성 조합을 포괄하지 않는다.

직접 실행 시 파일 끝 unittest.main()이 테스트를 시작한다. 기능 문서는 [questions.md](./questions.md), 통합 API 문서는 [admin.md](./admin.md)를 참고한다.
