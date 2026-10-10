# test_analysis.py 백엔드 매뉴얼

- 대상: 4차 버전 `v4/test_analysis.py`
- 작성 기준일: 2026-10-09
- 소스: [test_analysis.py](./test_analysis.py)
- 관련 문서: [main.md](./main.md)

## 1. 파일의 역할

analysis.py의 순수 계산 규칙을 unittest로 확인하는 단위 테스트 파일이다. 실제 DB나 웹 서버 없이 실행할 수 있다.

## 2. 실행 방법

v4 폴더에서 실행:

```powershell
..3\.venv\Scripts\python.exe -B -m unittest test_analysis -v
```

총 5개 테스트이다. 분석 모듈이 표준 라이브러리만 사용하므로 별도 앱 의존성이 없는 Python에서도 이 파일 자체는 실행할 수 있다. 성공 시 OK, 실패 시 assertion 위치가 출력된다.

## 함수별 설명

### `response(**changes)`

**기능:** 분석 테스트의 기본 응답 딕셔너리를 만든다.

**전달값:** changes: 기본 필드를 덮어쓸 키워드 인자.

**반환값:** 수정된 응답 딕셔너리.

**추가 설명:** 기본 점수는 모두 3, 팀은 A팀, 환경·시설 답변은 빈 배열이다. 분석에 필요한 필드를 제공하는 테스트 fixture이며 실제 설문 API 요청 모델 전체는 아니다.

### `AnalysisTests.test_empty(self)`

**기능:** 빈 응답의 통계를 검증한다.

**전달값:** self: unittest 테스트 인스턴스.

**반환값:** None; assertion 실패 시 테스트 실패.

**추가 설명:** 응답 수 0, 수업 이해도 평균 None을 확인한다.

### `AnalysisTests.test_exclusions_and_missing(self)`

**기능:** 평균 제외 답변과 누락 답변의 차이를 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 만족·해당 없음·답변 누락의 3건으로 평균 4, rated=1, excluded=1, missing=1, 의견 1개를 확인한다.

### `AnalysisTests.test_multiple_choice_response_denominator(self)`

**기능:** 복수 선택의 분모와 한 응답 내 중복 제거를 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 문법 이해 중복 선택을 한 번만 집계하고 응답자 기준 문법 이해 100%, 에러 해결 50%를 확인한다.

### `AnalysisTests.test_flags_and_boundaries(self)`

**기능:** 상담 참고 조건과 점수 경계를 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 기본 응답의 flags가 없고 여러 조건을 넣은 응답에서 6개가 생성됨을 확인한다. AI 활용 3인 경우 코드 이해가 일부여도 AI 관련 조건이 생기지 않는지 확인한다.

### `AnalysisTests.test_repeated_responses_and_teams(self)`

**기능:** 반복 응답과 팀 미선택의 집계를 검증한다.

**전달값:** self.

**반환값:** None.

**추가 설명:** 같은 기본 이름의 2건이 별도로 집계되고 이해도 평균 2, 팀 그룹 2개가 되는지 확인한다.

## 테스트 범위

파일 끝의 unittest.main()은 직접 실행할 때 테스트를 시작한다. 모든 테스트는 메모리 데이터만 사용하므로 DB 내용에 영향을 주지 않는다. API 인증·HTTP 직렬화·차트 렌더링·모든 가능한 입력 조합까지 검증하는 파일은 아니다. 계산 함수의 사용 규약은 [analysis.md](./analysis.md)에 정리되어 있다.
