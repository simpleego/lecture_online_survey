# app.js 프런트엔드 매뉴얼

- 대상: 4차 버전 `v4/static/app.js`
- 작성 기준일: 2026-10-09
- 소스: [app.js](./app.js)

## 1. 파일의 역할

수강생 설문 화면에서 현재 문항과 팀을 불러오고 문항 유형에 맞는 입력 UI를 생성한다. 답변을 수집하여 전체 설문 버전과 함께 제출한다.

## 2. 상태·의존성·화면 연결

`index.html`의 본문 끝에서 로드되며 DOM이 준비된 상태를 전제로 한다. 외부 JavaScript 라이브러리는 사용하지 않는다.

| 상태 | 의미 |
|---|---|
| currentForm | 처음에는 null. GET /api/v4/questions 결과의 revision·questions 저장 |
| controls | 문항 ID를 키로 하는 Map. question, box, inputs, 선택적 comment DOM 참조 저장 |
| $ | ID로 DOM을 조회하는 화살표 함수 |

| DOM ID | 역할 |
|---|---|
| surveyForm | 설문 전체 form |
| student_name, team_name | 이름·팀 입력 |
| dynamicQuestions | 동적 문항 섹션 컨테이너 |
| submitBtn | 제출 버튼; 초기 비활성화 |
| message | 오류·저장 성공 안내 |

| API | 요청 | 용도 |
|---|---|---|
| /api/v4/questions | GET | 전체 버전·활성 문항 |
| /api/teams | GET | 팀 목록 |
| /api/v4/surveys | POST JSON | 응답 저장 |

GET은 cache:no-store를 사용한다. 관리자 인증은 필요하지 않다.

## 3. 함수별 설명

### `$ (id)`

**기능:** ID로 DOM 요소를 조회한다.

**전달값:** id: 문자열.

**반환값:** HTMLElement 또는 null.

**추가 설명:** document.getElementById를 호출한다. 호출부 대부분은 해당 DOM이 있다는 전제로 접근한다.

### `node(tag, text)`

**기능:** 텍스트를 가진 DOM 요소를 만든다.

**전달값:** tag: HTML 태그명. text: 선택적 표시 내용.

**반환값:** 생성한 요소.

**추가 설명:** text가 undefined가 아니면 textContent에 넣는다. 문자열을 HTML로 해석하지 않는다. DOM 부착은 호출자가 수행한다.

### `showMessage(text, type="error")`

**기능:** 오류·성공 안내를 표시한다.

**전달값:** text: 표시 문자열. type: CSS 상태 이름, 기본 error.

**반환값:** undefined.

**추가 설명:** message의 내용과 class를 변경하고 smooth 스크롤로 중앙에 이동한다. 성공은 success를 사용한다.

### `get(path)`

**기능:** JSON API를 GET으로 읽는다.

**전달값:** path: 상대 API 주소.

**반환값:** Promise<파싱된 JSON>.

**추가 설명:** HTTP 실패는 일반적인 목록 로딩 오류로 throw한다. 서버 detail을 읽지는 않는다. 네트워크·JSON 파싱 오류도 호출자 catch로 전달된다.

### `renderQuestion(q, section)`

**기능:** 문항 정의를 입력 DOM으로 변환한다.

**전달값:** q: id, topic, kind, required, options, allow_comment, legacy_key 등이 있는 문항. section: 부착할 DOM 요소.

**반환값:** undefined. section과 controls를 변경한다.

**추가 설명:** fieldset/legend를 생성하고 필수 문항에는 *를 붙인다. text는 최대 5000자 textarea, single은 빈 선택하세요 항목이 있는 select, multiple은 checkbox 목록이다. 4개 기존 점수 문항에는 1 매우 낮음~5 매우 높음 안내를 추가한다. 의견 허용 시 별도 최대 5000자 textarea를 만든다. 복수 선택의 필수 검사는 제출 이벤트에서 수행한다.

### `load()`

**기능:** 현재 문항과 팀 목록으로 화면을 초기화한다.

**전달값:** 없음.

**반환값:** Promise<void>. 내부에서 오류를 처리한다.

**추가 설명:** Promise.all로 두 API를 병렬 조회한다. 팀 선택을 활성화하고 기존 문항 DOM 및 controls를 비운다. 순회 중 section 문자열이 바뀔 때 새 카드와 제목을 만든다. 같은 section이 나중에 다시 나오면 별도 카드가 생긴다. 문항이 없으면 안내하고 제출 버튼을 활성화한다. 로딩 실패 시 메시지를 표시한다.

## 4. 이벤트와 실행 흐름

### 초기 실행

파일 마지막에서 load()를 호출한다. 문항·팀 로딩이 끝나면 팀 선택과 제출 버튼이 활성화된다. 재호출 시 기존 입력을 보존하거나 합치지 않고 화면을 다시 만든다.

### surveyForm submit의 익명 async 콜백

- 전달값: submit Event. 반환값: Promise<void>이며 이벤트 시스템에서 결과를 사용하지 않는다.
- preventDefault 후 currentForm이 없거나 제출 버튼이 비활성화되어 있으면 종료한다.
- controls를 순회하며 text/single은 앞뒤 공백 제거 후 빈 값이면 null, multiple은 체크된 값 리스트로 수집한다. 의견은 공백 제거 후 null 또는 문자열이다.
- 필수 복수 선택이 비어 있으면 메시지 표시·첫 체크박스 포커스 후 종료한다. reportValidity()로 HTML 이름·필수 단일/텍스트 등의 제약도 확인한다.
- 제출 버튼을 비활성화하고 저장 중...으로 변경한다. POST 본문은 아래 구조이다.

```json
{
  "student_name": "김민준",
  "team_name": "A팀",
  "form_revision": 1,
  "answers": [{"question_id": 1, "value": ["Python", "SQL"], "comment": null}]
}
```

성공하면 form.reset() 후 접수번호를 표시한다. 실패하면 서버 detail이 문자열일 때 그대로 표시하고, 아니면 일반 입력 오류를 표시한다. finally에서 버튼을 다시 활성화한다.

renderQuestion 내부의 forEach 콜백은 옵션 DOM 생성·배열 등록만 수행하며 의미 있는 반환값은 없다.

## 5. 추가 설명과 유지보수

문항 버전 불일치(409) 때 자동으로 load()를 호출하거나 입력을 버리지 않는다. 현재 값은 화면에 남으며 새로고침 전에 사용자가 내용을 보관해야 한다. 성공 후에도 currentForm.revision은 갱신되지 않으므로 관리자가 문항을 바꾸면 다음 제출에서 충돌할 수 있다.

이름 공백만 입력, 팀 등록 여부, 옵션 유효성 등 최종 검증은 백엔드가 수행한다. 입력은 브라우저 메모리에만 있고 localStorage에 보관하지 않는다. DB를 직접 조회하거나 SQL을 실행하지 않는다.

백엔드 모델과 버전 검사는 [questions.md](../questions.md), 서버 화면 연결은 [main.md](../main.md)를 참고한다.
