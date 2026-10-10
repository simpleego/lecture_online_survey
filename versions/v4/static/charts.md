# charts.js 프런트엔드 매뉴얼

- 대상: 4차 버전 `v4/static/charts.js`
- 작성 기준일: 2026-10-09
- 소스: [charts.js](./charts.js)

## 1. 파일의 역할

집계 데이터를 Google Charts 수직 막대·3D 파이로 표시하고 동일 데이터의 HTML 표를 제공한다. 파이 내부 비율과 가까운 굵은 라벨, 90도 꺾인 연결선을 구성한다.

## 2. 상태·의존성·화면 연결

SurveyCharts는 즉시 실행 함수(IIFE)의 반환 객체이며 공개 메서드는 render와 redraw이다. 관리자 페이지에서 admin.js보다 먼저 로드한다.

| 내부 상태 | 용도 |
|---|---|
| palette | 8개 차트 색상; 항목 수가 많으면 순환 |
| ready | Google Charts corechart 로딩 완료 여부 |
| failed | 외부 loader script 다운로드 실패 여부 |
| tasks | 그릴 차트 작업을 보관하는 Set |
| timer | resize 재그리기 지연 타이머 |

동적으로 https://www.gstatic.com/charts/loader.js를 로드하고 current/corechart, 한국어, safeMode를 사용한다. DataTable에는 집계 라벨과 응답 수를 넣으며 이름·개인별 자유 답변을 넣지 않는다. 차트 로딩 실패 시에도 이미 생성된 표를 유지한다.

## 3. 함수별 설명

### `SurveyCharts 즉시 실행 함수`

**기능:** 차트 상태를 생성하고 외부 라이브러리·이벤트를 초기화한다.

**전달값:** 없음.

**반환값:** render와 redraw 함수를 가진 객체.

**추가 설명:** 내부 함수와 상태는 클로저로 유지한다. script 로딩과 resize/toggle 핸들러 등록은 파일 실행 시 한 번 수행된다.

### `status(text)`

**기능:** 전체 차트 상태 안내를 표시한다.

**전달값:** text 문자열.

**반환값:** undefined.

**추가 설명:** chartStatus 요소가 있으면 textContent를 설정하고 없으면 아무 작업도 하지 않는다.

### `drawPie(task, data, options)`

**기능:** 3D 파이와 맞춤 SVG 라벨·연결선을 그린다.

**전달값:** task: container/values/kind 작업. data: Google DataTable. options: 차트 옵션 객체.

**반환값:** undefined. chart.draw 실행과 DOM 변경.

**추가 설명:** count>0만 사용한다. 표시 폭은 컨테이너 폭과 840 중 작은 값, 지름은 폭의 40%를 기준으로 90~300이다. 라벨은 최대 지름 밖 18px 위치에 두며 굵기 700, 비율은 라벨에 추가하지 않는다. options를 width/height/is3D/legend:none/chartArea 등으로 변경한다. 조각 비율은 Google Charts가 계산한다.

### `drawPie.wrap(label)`

**기능:** 파이 라벨을 사용 가능한 폭에 맞춰 줄바꿈한다.

**전달값:** label 문자열.

**반환값:** 문자열 줄 배열.

**추가 설명:** 내부 함수. canvas measureText로 굵은 Arial 글자 폭을 측정하며 한 글자씩 누적한다. 폭 500 미만에서는 12px, 그 이상은 14px 라벨 글꼴이다.

### `drawPie.shape(tag, attrs)`

**기능:** SVG 요소와 속성을 만든다.

**전달값:** SVG 태그명, 속성 객체.

**반환값:** SVG DOM 요소.

**추가 설명:** 파이 ready 콜백 내부 함수. createElementNS로 만들고 Object.entries를 순회하여 속성을 설정한다.

### `draw(task)`

**기능:** 차트 작업 한 건을 현재 상태에 맞춰 그린다.

**전달값:** container DOM, values 배열, kind를 가진 작업 객체.

**반환값:** undefined.

**추가 설명:** DOM에서 제거된 작업은 Set에서 삭제한다. ready가 아니거나 숨겨져 폭이 없으면 그리지 않는다. DataTable 기본 열은 항목 문자열·응답 수 숫자이다. pie는 양수 항목과 흰색 굵은 percentage 조각 텍스트를 사용하고 drawPie 호출. 다른 kind는 ColumnChart에 색상 style·건수 annotation 열을 추가한다. 동기 오류는 컨테이너 안내 문구로 바꾼다.

### `redraw()`

**기능:** 등록된 모든 차트를 다시 그린다.

**전달값:** 없음.

**반환값:** undefined.

**추가 설명:** tasks를 순회하여 draw를 호출한다. 숨겨진 차트는 건너뛰고 다음 재그리기 시도까지 기다린다.

### `render(parent, title, values, percent=false, kind="column", multiple=false)`

**기능:** 제목·차트·데이터 표를 생성하고 그리기 작업을 등록한다.

**전달값:** parent: DOM 부모. title: 제목. values: label/count/선택적 percent 배열. percent: 표 비율 열 여부. kind: pie 또는 column. multiple: 복수 선택 설명 표시 여부.

**반환값:** undefined. parent에 새 section 추가.

**추가 설명:** 양수 count가 하나도 없으면 응답 없음 문구만 만들고 작업 등록 없이 종료한다. 나머지는 chart-section, h3, google-chart, chart-data 표를 만든다. percent=True일 때 표에 서버의 percent를 그대로 표시한다. role=img와 aria-label을 설정한다. 작업 등록 후 draw한다. 이 함수는 기존 부모 내용을 비우지 않는다.

## 4. 이벤트와 실행 흐름

### 외부 스크립트 로딩

script.onload의 콜백은 google.charts.load(...).then()으로 corechart 준비를 기다린다. 완료 콜백은 ready=true, 상태 안내 제거, redraw를 수행한다. script.onerror는 failed=true와 오류 안내를 설정하고 등록된 차트 컨테이너 문구를 바꾼다. 두 이벤트 콜백에 의미 있는 반환값은 없다.

10초 setTimeout 콜백은 아직 ready가 아니면 지연 안내를 표시한다. 다운로드·라이브러리 준비를 강제로 중단하지 않는다. 패키지 로딩 Promise 거부에 대한 별도 catch는 없다.

### PieChart ready 콜백

전달값을 사용하지 않으며 반환값은 undefined이다. 차트 SVG의 첫 팔레트 색상 path에서 타원 중심·반경을 추정한다. 찾지 못하면 계산한 중심과 반경으로 대체한다. 선택 횟수 비중의 중간각으로 각 조각의 연결점을 정하고 좌우 그룹으로 나눈다.

각 그룹을 연결점 y순으로 정렬한 뒤 위→아래, 아래→위로 위치를 조정하여 라벨 겹침을 줄인다. 연결선은 조각 가장자리→수평→수직→수평으로 이어지는 polyline이며 조각과 같은 색을 쓴다. 연결점에는 작은 원을 표시한다. 라벨은 text/tspan으로 그리며 비율은 넣지 않는다. SVG overlay는 aria-hidden, pointer-events:none이라 차트 마우스 동작을 막지 않는다. 완료 시 container.dataset.drawn=true를 설정한다.

### 반응형 재그리기

window resize 콜백은 기존 타이머를 지우고 150ms 뒤 redraw한다. document의 toggle 이벤트는 캡처 단계에서 redraw를 호출하므로 details 펼침으로 보이는 차트를 그릴 수 있다. 관리/분석 탭 전환의 재그리기는 admin.js가 수행한다.

map/filter/reduce 콜백은 양수 항목·합계·중간각·라벨 배치 정보를 계산하고 forEach 콜백은 표·SVG 요소를 생성한다.

## 5. 추가 설명과 유지보수

### 비율과 출력 규약

```javascript
SurveyCharts.render(parent, '복습 빈도', [
  {label: '거의 매일', count: 6, percent: 60},
  {label: '주 1~2회', count: 4, percent: 40}
], true, 'pie');
```

파이 조각 비율은 양수 count 합계 기준이다. percent 인자는 파이 비율을 바꾸지 않고 HTML 표의 비율 열만 제어한다. 복수 선택은 표가 응답자 기준, 파이는 선택 횟수 기준이므로 서로 다른 비율이 될 수 있다. multiple=True이면 이 차이를 안내한다. 수직 막대는 percent=True여도 높이와 annotation이 건수이다.

values.label은 문자열, count는 정상적인 0 이상 숫자, percent=True이면 percent가 있는 입력을 전제로 한다. 잘못된 입력을 검증·보정하는 별도 로직은 없다. 점수의 설명형 x축 라벨은 [admin.md](./admin.md)의 scoreDistribution에서 변환한다.

3D 파이의 연결선은 Google Charts가 만든 SVG path 구조를 읽어 계산하므로 라이브러리 렌더링 구조가 바뀌면 위치 확인이 필요하다. 많은 선택지·긴 라벨은 차트 높이가 커질 수 있다. draw의 catch는 동기 오류를 처리하며 ready 이벤트 내부 오류를 모두 잡지는 않는다.

tasks의 제거된 DOM 정리는 draw 호출 시 수행한다. 기존 차트 컨테이너를 비우는 작업은 호출자 책임이다. 공개 API는 저장·검색·DB 작업을 수행하지 않는다.
