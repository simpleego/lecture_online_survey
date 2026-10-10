# questions.py 백엔드 매뉴얼

- 대상: 4차 버전 `v4/questions.py`
- 작성 기준일: 2026-10-09
- 소스: [questions.py](./questions.py)
- 관련 문서: [main.md](./main.md)

## 1. 파일의 역할

4차 버전 동적 문항 관리, 버전 충돌 검사, 설문 응답 스냅샷 저장, 기존 통계 형식 변환을 담당한다. 문항이 수정·삭제되어도 응답 당시 문항과 선택지는 저장된 스냅샷에 남는다.

## 2. 요청 모델

### QuestionInput

| 필드 | 타입 | 필수/기본값 | 검증·의미 |
|---|---|---|---|
| topic | str | 필수 | 1~200자, 앞뒤 공백 제거, 공백만 입력 불가 |
| section | str | 추가 설문 | 1~100자, 앞뒤 공백 제거 |
| kind | Literal | 필수 | text, single, multiple |
| options | list[str] | [] | 최대 50개; 선택형은 서로 다른 2~50개, 각 1~200자 |
| required | bool | False | 답변 필수 여부 |
| allow_comment | bool | False | 별도 의견 허용 여부 |
| sort_order | int | 1000 | 0~100000 |
| revision | int 또는 None | None | 지정하면 1 이상; 수정 시 현재 문항 버전 필요 |

### AnswerInput

| 필드 | 타입 | 필수/기본값 | 의미 |
|---|---|---|---|
| question_id | int | 필수 | 1 이상인 문항 ID |
| value | str 또는 list[str] 또는 None | None | 텍스트·단일 선택은 문자열, 복수 선택은 리스트 |
| comment | str 또는 None | None | 최대 5000자, 별도 의견 |

### ResponseInput

| 필드 | 타입 | 필수/기본값 | 의미 |
|---|---|---|---|
| student_name | str | 필수 | 1~50자, 공백 제거 후 비어 있으면 거부 |
| team_name | str 또는 None | None | 최대 50자; 비어 있지 않으면 team 테이블에 존재해야 함 |
| form_revision | int | 필수 | 1 이상, 화면에서 받은 전체 설문 버전 |
| answers | list[AnswerInput] | 필수 | 최대 500개; 개수의 최소 제한은 없으나 필수 문항 검사 수행 |

모델 제약 위반은 FastAPI에서 HTTP 422로 응답한다. `value`의 문항별 형식과 필수 여부는 별도 `validate_answers()`에서 검사한다.

## 3. API

| 메서드 | 경로 | 인증 | 정상 결과 |
|---|---|---|---|
| GET | /api/v4/questions | 공개 | revision, questions |
| POST | /api/v4/surveys | 공개 | 201, id, message |
| GET | /api/admin/questions | 관리자 | revision, questions |
| POST | /api/admin/questions | 관리자 | 201, id |
| PUT | /api/admin/questions/{question_id} | 관리자 | status: updated |
| DELETE | /api/admin/questions/{question_id}?revision=현재버전 | 관리자 | status: deleted |

`form_revision`은 설문 전체의 버전, 문항의 `revision`은 해당 문항의 버전이다. 생성·수정·삭제 때 전체 버전이 증가한다. 수정·삭제는 문항 버전도 증가한다. 전체 버전 행을 FOR UPDATE로 잠가 조회·변경·제출이 일관된 문항 구성을 사용하도록 한다.

## 함수별 설명

### `QuestionInput.trim(cls, value)`

**기능:** 제목과 섹션 앞뒤 공백을 제거한다.

**전달값:** cls: 모델 클래스. value: topic 또는 section 문자열.

**반환값:** 정리된 문자열.

**추가 설명:** field_validator로 자동 실행한다. 결과가 비면 ValueError이며 API에서는 422로 변환된다.

### `QuestionInput.choices(self)`

**기능:** 문항 유형에 맞게 선택지를 검증·정리한다.

**전달값:** self: 필드 검증이 끝난 QuestionInput.

**반환값:** 정리된 self.

**추가 설명:** 선택지 공백을 제거한다. text는 options=[]로 정리한다. 선택형은 최소 2개, 빈 값·200자 초과·중복을 거부한다. 최대 50개 제약은 모델 필드 검증에서 먼저 적용된다.

### `ResponseInput.name(cls, value)`

**기능:** 학생 이름 앞뒤 공백을 제거한다.

**전달값:** cls: 모델 클래스. value: 이름 문자열.

**반환값:** 정리된 이름.

**추가 설명:** 공백만 있으면 ValueError. 이름의 실제 존재 여부는 검사하지 않는다.

### `decode_question(row)`

**기능:** 문항 DB 행을 API용 딕셔너리로 변환한다.

**전달값:** DB 행 Mapping.

**반환값:** options 리스트, required·allow_comment bool이 포함된 딕셔너리.

**추가 설명:** options_json은 JSON 파싱 후 options로 교체한다. 나머지 id, legacy_key, section, revision, deleted 등의 필드는 유지한다. 잘못된 JSON은 별도 복구하지 않는다.

### `definitions(db, include_deleted=False)`

**기능:** 문항 정의를 표시 순서대로 읽는다.

**전달값:** db: Session. include_deleted: 삭제 표시 문항 포함 여부.

**반환값:** 문항 딕셔너리 리스트.

**추가 설명:** 기본은 deleted=0만 조회하며 sort_order,id 순으로 정렬한다. 조회 자체는 commit하지 않는다.

### `form_revision(db, lock=False)`

**기능:** 전체 설문 현재 버전을 조회한다.

**전달값:** db: Session. lock: True이면 FOR UPDATE 사용.

**반환값:** v4_form_state의 id=1 행 revision 숫자.

**추가 설명:** 값을 증가시키는 함수가 아니다. 잠금은 호출자가 commit하거나 트랜잭션을 종료할 때 해제된다. 초기 상태 행이 없으면 scalar_one 조회 오류가 발생한다.

### `validate_answers(questions, answers)`

**기능:** 현재 문항 기준으로 답변을 검증하고 스냅샷 구조를 만든다.

**전달값:** questions: 현재 정의 목록. answers: AnswerInput 목록.

**반환값:** 각 현재 문항에 대해 question, value, comment를 가진 배열.

**추가 설명:** 중복 문항 ID·존재하지 않는 ID를 거부한다. 복수 선택은 리스트·선택지 중복 없음·등록된 값이어야 한다. 단일/텍스트는 문자열 또는 None이어야 하며 앞뒤 공백을 제거한다. 텍스트 최대 5000자, 필수 답변의 빈 값, 의견 비허용 문항의 의견을 검사한다. 위반은 HTTP 422. 누락된 선택 문항도 None 또는 []로 스냅샷에 포함된다. 의견만으로 필수 답변을 충족하지 않는다. 복수 선택 값 자체의 공백은 제거하지 않는다.

### `normalize_response(row)`

**기능:** 4차 저장 응답을 기존 분석 함수와 호환되는 구조로 변환한다.

**전달값:** v4_responses 행: id, student_name, team_name, created_at, snapshot_json 포함.

**반환값:** 공통 분석 필드, id=v4-숫자, source=v4, question_answers를 가진 딕셔너리.

**추가 설명:** legacy_key로 기존 필드에 연결한다. 4개 점수는 단일 선택 문자열 1~5만 숫자로 변환하고 나머지는 None으로 유지한다. 환경·시설 키는 learn_env:ID, facillities:ID를 답변 배열로 변환한다. 복수 선택 리스트를 유지하므로 선택지 내부 쉼표가 보존된다. legacy_key가 없는 새 문항도 question_answers에는 남는다. DB 내용을 수정하지 않는다.

### `read_new_responses(db, name="", team="")`

**기능:** 4차 응답을 이름·팀 조건으로 조회한다.

**전달값:** db: Session. name: 부분 검색. team: 완전 일치. 빈 문자열은 필터 생략.

**반환값:** normalize_response를 적용한 응답 리스트.

**추가 설명:** 값은 SQL 파라미터 바인딩을 사용한다. 내부에서 이름 공백 제거, 정렬, 페이지 제한을 하지 않는다. admin의 통합 조회에서 정렬한다.

### `build_question_router(get_db, require_admin)`

**기능:** 공개 설문과 관리자 문항 관리 라우터를 만든다.

**전달값:** get_db: DB 세션 의존성. require_admin: 인증 의존성.

**반환값:** APIRouter.

**추가 설명:** 아래 public_form부터 submit까지는 이 함수 내부 함수이다. 관리자 경로에만 인증 의존성을 적용한다.

### `public_form(db=Depends(get_db))`

**기능:** 일관된 전체 버전과 현재 문항을 제공한다.

**전달값:** 요청 DB 세션.

**반환값:** `{"revision": 숫자, "questions": 문항목록}`.

**추가 설명:** 전체 버전 행을 잠근 뒤 문항을 조회하고 commit하여 잠금을 해제한다. 읽기 함수이지만 잠금 종료를 위해 commit한다.

### `list_questions(db=Depends(get_db))`

**기능:** 관리자에게 현재 문항 목록을 제공한다.

**전달값:** 요청 DB 세션.

**반환값:** public_form과 동일한 객체.

**추가 설명:** 관리자 인증 후 public_form(db)를 직접 호출한다. 삭제된 문항은 목록에서 제외된다.

### `question_values(data)`

**기능:** 문항 입력을 SQL 바인딩 딕셔너리로 변환한다.

**전달값:** QuestionInput.

**반환값:** revision·options를 제외하고 options_json을 추가한 딕셔너리.

**추가 설명:** json.dumps(..., ensure_ascii=False)로 한국어 선택지를 저장한다. 수정할 때 개별 revision은 별도 조건 검사에 사용한다.

### `add_question(data, db=Depends(get_db))`

**기능:** 새 문항을 저장한다.

**전달값:** data: QuestionInput. db: Session.

**반환값:** `{"id": 생성된 문항ID}`; HTTP 201.

**추가 설명:** 전체 버전 행 잠금 후 INSERT, 전체 버전 +1, commit한다. 개별 revision은 DB 기본값 1, legacy_key는 NULL이다. 입력 revision은 생성 시 사용하지 않는다.

### `edit_question(question_id, data, db=Depends(get_db))`

**기능:** 현재 버전과 일치하는 문항을 수정한다.

**전달값:** question_id: 경로 int. data: 전체 QuestionInput, 현재 revision 필수. db: Session.

**반환값:** `{"status": "updated"}`.

**추가 설명:** 삭제되었거나 없는 문항은 404, revision 누락·불일치는 409이다. 문항 내용 갱신과 개별·전체 revision 증가 후 commit한다. PUT은 부분 수정이 아니므로 생략한 선택적 필드는 모델 기본값으로 덮어쓴다. legacy_key는 변경하지 않으며 과거 스냅샷도 변경하지 않는다.

### `delete_question(question_id, revision, db=Depends(get_db))`

**기능:** 문항을 삭제 표시한다.

**전달값:** question_id: 경로 int. revision: 필수 쿼리 int. db: Session.

**반환값:** `{"status": "deleted"}`.

**추가 설명:** id·revision·deleted=0 조건으로 deleted=1 및 개별 revision+1을 적용한다. 갱신 행이 없으면 409이며 존재하지 않는 ID도 409이다. 전체 버전 증가 후 commit한다. SQL DELETE를 하지 않아 과거 응답을 유지한다. revision 누락은 422이다.

### `submit(data, db=Depends(get_db))`

**기능:** 현재 문항 버전의 답변을 스냅샷으로 저장한다.

**전달값:** data: ResponseInput. db: Session.

**반환값:** `{"id": "v4-숫자", "message": "설문이 저장되었습니다."}`; HTTP 201.

**추가 설명:** 전체 버전을 잠그고 화면의 form_revision과 다르면 409이다. 팀 값이 있으면 등록 여부를 확인한다(없으면 422). 답변 검증 후 현재 문항 전체와 답변을 snapshot_json에 저장하고 commit한다. 빈 팀 문자열은 NULL로 저장된다. 409 발생 시 화면을 새로 받아 입력을 확인해야 한다.

### `question_statistics(rows, questions)`

**기능:** 저장된 문항 내용별로 답변 분포와 의견을 집계한다.

**전달값:** rows: 필터링된 기존+4차 응답 목록. questions: 삭제 표시 포함 문항 정의.

**반환값:** question_id, topic, kind, options, answered, missing, distribution, comments를 가진 배열.

**추가 설명:** 그룹 키는 문항 ID·제목·유형·선택지 튜플이다. revision 자체로 나누지 않으므로 같은 내용의 버전은 합쳐지고 제목·유형·선택지 구성/순서가 다르면 나뉜다. 활성 문항은 응답 0건이어도 그룹을 만든다. 과거 삭제 문항은 저장된 답변에서 복원한다. 실제 답변은 source=v4의 스냅샷에서만 가져오지만 missing과 선택 비율 분모는 기존 응답까지 포함한 전체 len(rows)이다. text는 분포가 없고 텍스트 답변을 comments로 제공한다. 선택형은 별도 의견이 있는 답변만 comments에 포함한다.

### `question_statistics.add(q, value, comment, row)`

**기능:** 문항 내용별 그룹을 만들고 비어 있지 않은 답변을 모은다.

**전달값:** q: 저장 문항. value: 답변. comment: 의견. row: 해당 응답(빈 그룹 초기화 시 None).

**반환값:** None; 바깥 groups 딕셔너리를 변경한다.

**추가 설명:** 내부 보조 함수이다. None, 빈 문자열, 빈 리스트는 답변 수에 포함하지 않는다. 의견만 있고 답변이 비면 해당 그룹의 comments에도 포함하지 않는다.

## 저장 구조와 트랜잭션

| 테이블 | 용도 | 주요 SQL |
|---|---|---|
| v4_questions | 현재 문항·버전·삭제 표시 | SELECT, INSERT, UPDATE |
| v4_form_state | 전체 설문 버전, id=1 | SELECT FOR UPDATE, UPDATE |
| v4_responses | 응답 당시 문항 및 답변 JSON | SELECT, INSERT |
| team | 팀 유효성 검사 | SELECT |

SQLAlchemy 세션에서 `text()` SQL과 바인딩 파라미터를 사용한다. ORM 매핑 모델을 사용하지 않는다. 저장 성공 시 명시적으로 commit한다. 이 모듈에는 별도 rollback 예외 처리 블록이 없으며 요청 세션 종료는 main.get_db에서 처리한다.

스냅샷 항목 예시:

```json
{
  "question": {"id": 1, "topic": "관심 기술", "kind": "multiple", "options": ["Python", "SQL"], "revision": 1},
  "value": ["Python", "SQL"],
  "comment": null
}
```

실제 question에는 전체 문항 정의 필드가 포함된다. 예시는 구조 설명을 위해 일부 필드만 표시했다. 신규 테이블 준비는 [migrate_v4.md](./migrate_v4.md), 동작 검증 범위는 [test_questions.md](./test_questions.md)를 참고한다.
