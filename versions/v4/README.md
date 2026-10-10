# 수강생 상담 온라인 설문 — 4차 버전

관리자 설문관리/설문분석 탭, 기준 설문항목 관리와 Google Charts 분석을 구현했습니다.
원본 요구사항은 `requirements_v4.txt`, 이전 안내는 `README_v3.md`입니다.

## 실행

v4 폴더에서 실행합니다.

```powershell
.\run.ps1
```

v4 가상환경이 있으면 우선 사용하고 없으면 v3 가상환경을 사용합니다.
직접 실행할 수도 있습니다.

```powershell
..\v3\.venv\Scripts\python.exe -m uvicorn main:app --port 8003
```

- 설문: http://127.0.0.1:8003/
- 관리자: http://127.0.0.1:8003/admin
- API 문서: http://127.0.0.1:8003/docs

관리자 로그인은 .env의 ADMIN_USER/ADMIN_PASSWORD를 사용합니다.
현재 테스트 서버는 8003에서 실행 중입니다. 소스 변경 후 서버를 재시작해 적용하세요.
개발 중 자동 재시작은 `.\run.ps1 -Reload`로 선택할 수 있습니다.

## 설문관리

설문관리 탭에서 기존 36개 항목을 선택해 수정·삭제하거나 새 항목을 추가합니다.
주제, 구분, 표시 순서, 필수 여부, 추가 의견 허용을 설정할 수 있습니다.
답변 유형은 기술형, 선택형 단일선택·다중선택이며 선택지는 한 줄에 하나씩 입력합니다.
저장한 구성은 설문 작성 화면에 적용됩니다. 삭제는 새 설문에서 제외하는 방식입니다.
과거 응답은 작성 당시 질문과 선택지를 함께 저장해 수정·삭제 후에도 유지됩니다.
작성 도중 질문이 변경되면 서버는 새 구성을 확인하도록 안내하고 입력 내용을 자동 삭제하지 않습니다.

## 설문분석

기존 응답과 새 4차 응답을 함께 검색·조회합니다.
복습 빈도, 학습 어려움, 관심 분야는 파이차트입니다.
점수 및 환경/시설 분포는 색상이 다른 수직 막대그래프입니다.
복수 선택의 표 비율은 전체 응답자 대비, 파이 조각의 크기는 전체 선택 횟수 대비입니다.
점수 미응답은 평균에서 제외하고, 환경/시설의 해당 없음·미이용·제공 없음도 평균에서 제외합니다.
새 질문의 응답과 자유 의견은 작성 당시 구성 기준으로 표시합니다.

Google Charts는 인터넷 연결이 필요합니다. 로딩 실패 시에도 표의 응답 수를 확인할 수 있습니다.
공식 참고: [로더](https://developers.google.com/chart/interactive/docs/basic_load_libs),
[파이차트](https://developers.google.com/chart/interactive/docs/gallery/piechart),
[수직 막대그래프](https://developers.google.com/chart/interactive/docs/gallery/columnchart).
차트에는 집계 항목과 건수만 전달하며 이름·자유 의견은 일반 HTML에 표시합니다.

## 데이터 구조와 이전

기존 survey_responses와 61건의 응답은 변경하지 않았습니다.
v4_questions, v4_form_state, v4_responses 테이블을 추가했습니다.
4차 응답 접수번호는 v4-숫자 형식이며 기존 접수번호와 구분됩니다.
v3는 기존 응답만, v4 관리자 화면은 기존 응답과 새 응답을 합산해 보여줍니다.
기존 테이블의 목록 API와 기존 설문 저장 API는 호환성을 위해 유지합니다.

새 서버에서는 기존 DB를 복원한 후 다음 마이그레이션을 실행합니다.

```powershell
..\v3\.venv\Scripts\python.exe migrate_v4.py
```

로컬 실행에서는 .env의 DB 비밀번호로 root 관리자 계정을 사용합니다.
다른 관리자 계정이면 DB_MIGRATION_USER/DB_MIGRATION_PASSWORD 환경변수를 지정하세요.
마이그레이션을 다시 실행해도 삭제한 질문을 재생성하거나 질문 수정을 덮어쓰지 않습니다.
앱 계정은 새 질문·버전 테이블에만 UPDATE 권한을 추가로 받습니다.

현재 61건 = 기존 응답 1건 + 테스트 60건(접수번호 26~85).
작업 전 백업은 deploy/before_v4_*.sql입니다.
2026-10-08 백업에는 이후 추가한 테스트 60건이 없습니다.
기존 DB에 database.sql을 다시 실행하지 마세요.

## 검증

```powershell
..\v3\.venv\Scripts\python.exe -B -m unittest discover -v
$env:RUN_DB_TESTS = '1'
..\v3\.venv\Scripts\python.exe -B -m unittest test_questions -v
```

DB 통합 테스트는 root 권한으로 트랜잭션을 열어 저장·수정·삭제를 검증한 뒤 롤백합니다.
기존 응답이나 질문 설정에 검증 데이터가 남지 않습니다.
브라우저 UI 검증은 deploy/qa/README.md를 참고하세요.

주요 코드: main.py(기존 API), questions.py(동적 설문), admin.py(통합 조회),
analysis.py(분석), static/(화면), migrate_v4.py(DB 이전), test_questions.py(검증).
.env, DB 백업, 데이터 JSON, 가상환경과 로그는 공개 저장소에 올리지 않습니다.
