# admin.js 프런트엔드 매뉴얼

- 대상: 4차 버전 `v4/static/admin.js`
- 작성 기준일: 2026-10-09
- 소스: [admin.js](./admin.js)

## 1. 파일의 역할

관리자 로그인, 설문 검색·상세·통계, 동적 문항 생성·수정·삭제와 관리/분석 탭을 처리한다. 집계 데이터의 차트는 SurveyCharts에 맡긴다.

## 2. 상태·의존성·화면 연결

`admin.html`에서 charts.js 다음에 로드한다. app.js와는 별도 화면에서 사용하며 둘 다 전역 $를 선언하므로 같은 페이지에 함께 로드하지 않는다.

| 상태·상수 | 내용 |
|---|---|
| authorization | Basic 인증 헤더 문자열, 초기 빈 값; 브라우저 메모리에만 저장 |
| page | 현재 목록 페이지, 초기 1 |
| activeFilters | 검색 조건 URLSearchParams |
| managedQuestions | 현재 활성 문항 배열 |
| editingQuestion | 수정 중 문항 또는 null |
| labels | 기존 응답 키에 대응하는 한국어 표시 이름 |
| kindLabels | text=기술형, single=단일선택, multiple=다중선택 |
| scoreAxisLabels | 숫자 1~5를 1 매우 낮음~5 매우 높음으로 변환 |

주요 DOM은 loginForm/loginPanel/dashboard, message, username/password, managementTab/analysisTab 및 대응 Panel, filterForm/nameFilter/teamFilter, statistics/evaluations/questionAnalysis, responseRows/pageInfo/previous/next, detail/detailPanel, questionRows/questionForm/questionEditor 및 문항 편집 입력들이다. 정확한 ID는 admin.html과 함께 유지한다.

api()에서 호출하는 관리자 API는 매 요청마다 Basic 인증을 사용한다. /api/teams는 공개 경로지만 이 파일의 api로 호출하므로 헤더도 함께 보낸다.

## 3. 함수별 설명

### `$ (id)`

**기능:** DOM ID를 조회한다.

**전달값:** id 문자열.

**반환값:** 요소 또는 null.

**추가 설명:** 해당 요소가 존재하는 화면에서 사용한다.

### `el(tag, text, className)`

**기능:** 텍스트·CSS 클래스가 있는 요소를 만든다.

**전달값:** 태그명, 선택적 내용, 선택적 클래스.

**반환값:** 새 DOM 요소.

**추가 설명:** textContent를 사용한다. undefined인 text는 설정하지 않는다.

### `message(text, type="error")`

**기능:** 안내 메시지 내용을 표시한다.

**전달값:** 문자열, 상태 CSS 이름.

**반환값:** undefined.

**추가 설명:** message 요소의 textContent와 className을 변경한다.

### `logout()`

**기능:** 인증 상태와 관리자 화면을 초기화한다.

**전달값:** 없음.

**반환값:** undefined.

**추가 설명:** authorization·managedQuestions를 비우고 편집기를 초기화한다. 비밀번호 입력, 통계·목록·상세·평가·문항 영역을 비운다. dashboard를 숨기고 로그인 패널을 표시한다. 서버 로그아웃 API는 호출하지 않으며 진행 중 요청을 abort하지 않는다.

### `api(url, method="GET", payload)`

**기능:** 인증된 JSON 요청을 실행한다.

**전달값:** url 주소, method HTTP 메서드, 선택적 payload 객체.

**반환값:** Promise<JSON>; 실패 시 Error.

**추가 설명:** Authorization·Content-Type 헤더, cache:no-store 사용. payload가 undefined면 body 생략한다. 요청 전 인증 문자열을 저장하고 응답 후 값이 달라지면 상태 변경 오류를 throw한다. HTTP 401이면 logout한다. 문자열 detail을 오류 메시지로 쓰며 네트워크/JSON 파싱 오류도 전파된다.

### `date(value)`

**기능:** 날짜 문자열을 간단히 표시한다.

**전달값:** 날짜 문자열 또는 빈 값.

**반환값:** T를 공백으로 바꾼 문자열 또는 —.

**추가 설명:** 시간대 변환·날짜 객체 파싱은 하지 않는다.

### `flags(parent, entries)`

**기능:** 상담 참고사항 리스트를 표시한다.

**전달값:** 부모 DOM, 문자열 배열.

**반환값:** undefined.

**추가 설명:** 빈 배열은 기준에 해당하는 항목이 없다는 문구를 표시한다. 나머지는 ul.flags의 li로 추가한다.

### `bars(parent, title, values, percent=false, kind="column", multiple=false)`

**기능:** 공통 차트 렌더러를 호출한다.

**전달값:** 차트 부모·제목·분포 값, 표 비율 여부, 차트 종류, 복수 선택 여부.

**반환값:** undefined.

**추가 설명:** SurveyCharts.render로 그대로 전달한다. 이름은 bars지만 pie도 처리한다.

### `scoreDistribution(values)`

**기능:** 점수 분포 라벨을 설명형으로 변환한다.

**전달값:** label/count 등을 가진 배열.

**반환값:** 각 항목을 복사한 새 배열.

**추가 설명:** 1~5의 label만 설명형으로 바꾸고 기타 필드는 유지한다. 매핑 없는 라벨은 원래 값이다.

### `renderStats(data)`

**기능:** 통계·팀 비교·문항별 분석·환경 평가를 화면에 표시한다.

**전달값:** 관리자 통계 JSON.

**반환값:** undefined; 통계 DOM 교체.

**추가 설명:** 응답 수·상담 건수·4개 평균, 점수 수직 막대, 복습/어려움/관심 분야 파이를 만든다. 팀별 표는 백엔드 순서를 따른다. 동적 문항은 응답이 없고 현재 legacy_key가 있는 초기 문항이면 생략한다. text는 의견, 선택형은 분포를 표시한다. 환경/시설은 평균·rated·missing·excluded와 의견을 표시한다. managedQuestions를 먼저 불러와야 기존 점수 문항 연결을 판단할 수 있다.

### `showDetail(id)`

**기능:** 응답 상세와 상담 요약을 읽어 표시한다.

**전달값:** 숫자 또는 v4-숫자 응답 ID.

**반환값:** Promise<void>. 오류는 message로 처리.

**추가 설명:** GET /api/admin/surveys/{id}. 4차 question_answers가 있으면 작성 당시 제목·값·의견을 우선 표시한다. 기존 응답이면 labels와 환경/시설 이름을 사용하는 전체 응답을 표시한다. 상세 패널을 열고 부드럽게 이동한다.

### `loadList()`

**기능:** 현재 검색 조건과 페이지로 목록을 표시한다.

**전달값:** 없음; activeFilters·page 사용.

**반환값:** Promise<void>; 오류는 호출자로 전파.

**추가 설명:** GET /api/admin/surveys?검색조건&page=현재페이지. ID·이름·팀·제출일·점수·참고사항 수·상세 버튼을 만든다. 빈 목록은 안내 행, 페이지 정보와 이전/다음 disabled를 갱신한다. page_size는 보내지 않아 서버 기본값을 쓴다.

### `refresh()`

**기능:** 검색 조건의 목록과 통계를 함께 갱신한다.

**전달값:** 없음.

**반환값:** Promise<void>; 내부 catch에서 message 표시.

**추가 설명:** 상세와 기존 안내를 숨긴 뒤 Promise.all로 통계 GET과 loadList를 병렬 실행한다. 완료 후 renderStats. 문항 목록을 다시 읽지는 않는다.

### `selectTab(tab)`

**기능:** 관리/분석 탭을 전환한다.

**전달값:** management 또는 analysis 문자열.

**반환값:** undefined.

**추가 설명:** aria-selected·tabIndex·hidden 클래스를 갱신한다. 분석 탭이면 requestAnimationFrame에서 SurveyCharts.redraw를 실행해 숨겨졌던 차트를 그린다. URL 변경은 없다.

### `optionsVisibility()`

**기능:** 문항 유형에 맞춰 선택지 입력을 표시한다.

**전달값:** 없음; questionKind 값 사용.

**반환값:** undefined.

**추가 설명:** text면 optionsField 숨김·questionOptions.required=False, 선택형이면 표시·required=True.

### `resetEditor()`

**기능:** 편집기를 신규 문항 모드로 초기화한다.

**전달값:** 없음.

**반환값:** undefined.

**추가 설명:** editingQuestion=null, 폼 reset, 제목/저장 버튼/삭제 표시/기존 연결 안내를 초기화한다. 선택 행 표시도 제거한다.

### `editQuestion(q)`

**기능:** 선택한 문항을 편집기에 채운다.

**전달값:** 현재 문항 딕셔너리.

**반환값:** undefined.

**추가 설명:** 문항을 editingQuestion으로 보관하여 revision과 ID를 사용한다. 선택지는 줄바꿈으로 넣고 필수·의견 플래그와 순서를 채운다. 기존 연결 문항의 과거 응답 보존 안내를 표시한다. 행 강조 후 편집기로 이동·제목 포커스.

### `loadQuestions()`

**기능:** 활성 문항 목록과 관리 표를 갱신한다.

**전달값:** 없음.

**반환값:** Promise<void>; 오류 전파.

**추가 설명:** GET /api/admin/questions. managedQuestions를 갱신하고 개수·순서·섹션·제목·유형·필수 여부를 표시한다. 각 행에 수정·삭제 콜백을 연결한다. 빈 목록은 안내 행이다. 응답의 전체 revision은 별도 상태로 저장하지 않는다.

### `removeQuestion(q)`

**기능:** 확인 후 문항을 삭제 표시한다.

**전달값:** 삭제 대상 문항: id, topic, revision 포함.

**반환값:** Promise<void>; 취소 시 즉시 종료.

**추가 설명:** confirm 승인 후 DELETE /api/admin/questions/{id}?revision={revision}. 성공하면 편집기 reset→문항 재조회→통계/목록 refresh→성공 안내. 오류는 message로 표시한다. 실제 논리 삭제는 서버가 수행한다.

## 4. 이벤트와 실행 흐름

| 이벤트 대상 | 전달값·처리 | 반환값 |
|---|---|---|
| loginForm submit | Event.preventDefault. ID:비밀번호를 UTF-8 대응 Base64로 인코딩하여 Basic 헤더 구성. session 인증→팀 로딩→dashboard 표시→검색 초기화→문항 로딩→분석 탭→refresh. 실패는 logout 및 안내 | async Promise<void> |
| filterForm submit | 이름 trim·팀을 URLSearchParams에 저장, page=1, refresh | undefined |
| previous/next click | page 감소/증가 후 loadList, 실패 안내 | async Promise<void> |
| logout click | logout 후 성공 안내 | undefined |
| closeDetail click | detailPanel 숨김 | undefined |
| managementTab/analysisTab click | selectTab 호출 | undefined |
| 탭 keydown | 좌/우/Home/End에서 기본 동작 방지. Home은 관리, End는 분석, 좌/우는 다른 탭으로 이동하고 focus | undefined |
| questionKind change | optionsVisibility | undefined |
| newQuestion click | resetEditor 후 편집기 스크롤·제목 포커스 | undefined |
| cancelQuestion click | resetEditor | undefined |
| reloadQuestions click | 편집기 reset, 목록 재조회, 안내 | async Promise<void> |
| deleteQuestion click | editingQuestion이 있으면 removeQuestion | undefined |
| questionForm submit | 아래 저장 흐름 수행 | async Promise<void> |

### 문항 저장 submit 콜백

선택지 입력을 줄 단위로 나누고 trim·빈 줄 제거한다. 선택형에서 2개 미만 또는 중복이면 API 요청 전에 오류를 표시한다. payload는 topic, section, kind, options, required, allow_comment, sort_order이다. 수정 중이면 현재 revision을 추가한다. 신규는 POST /api/admin/questions, 수정은 PUT /api/admin/questions/{id}이다.

저장 버튼을 잠그고 성공하면 편집기 초기화→목록 재조회→refresh→성공 안내를 수행한다. finally에서 버튼을 활성화한다. 서버의 최대 선택지 개수·길이 등 추가 제약은 API가 검사한다.

각 forEach/map/filter 콜백은 DOM 생성 또는 값 변환을 수행한다. 목록의 상세 보기 버튼은 해당 item.id를 캡처하고 수정·삭제 버튼은 해당 문항 객체를 캡처한다. 파일 마지막에서 optionsVisibility를 한 번 실행한다.

## 5. 추가 설명과 유지보수

Basic 헤더는 메모리에 유지하고 입력 비밀번호는 인증 성공 후 지운다. localStorage·세션 토큰을 사용하지 않는다. 문항 변경 충돌(409)은 서버 메시지만 표시하므로 목록을 새로 불러온 뒤 다시 수정해야 한다.

api의 인증 상태 비교는 로그인 전환 뒤 늦게 도착한 응답을 막기 위한 처리이며 모든 요청 경합을 취소하는 기능은 아니다. 연속 검색이나 상세 선택의 응답 순서를 제어하는 별도 취소 로직은 없다. refresh는 내부에서 오류를 처리하므로 호출자는 오류를 별도로 받지 않는다.

화면에는 textContent로 응답과 의견을 표시한다. 차트에는 집계된 label/count만 전달한다. 분석 계산은 백엔드에서 수행하며 JS는 반환값을 표시한다. 관련 문서는 [admin.md](../admin.md), [questions.md](../questions.md), [charts.md](./charts.md)이다.
