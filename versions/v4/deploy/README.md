# Google Cloud 배포 및 DB 이전 준비

## 선택할 서비스

- Compute Engine VM 1대: 서울 `asia-northeast3`, 영역 `asia-northeast3-a`.
- 머신 유형: E2의 `e2-medium`, 메모리 4GB, 공유 CPU. 전용 2코어 사양은 아닙니다.
- OS: Ubuntu 24.04 LTS. MariaDB는 원본과 같은 11.4 계열 서버/클라이언트를 설치합니다.
- 부팅 디스크: 균형 영구 디스크 80GB.
- 고정 외부 IPv4와 도메인, Nginx 및 HTTPS를 사용합니다.
- FastAPI는 내부 `127.0.0.1:8000`, MariaDB는 내부 `127.0.0.1:3306`만 수신합니다.
- HTTP/HTTPS만 공개하고 SSH는 IAP 또는 관리자의 접근 범위로 제한합니다.
- 백업 보관 서비스: Cloud Storage의 서울 리전 비공개 버킷. VM에서 매일 DB 덤프를 생성해 보관하고 복원도 정기 확인합니다.
- Cloud Billing 예산 알림을 설정합니다. 알림 전용 예산은 자동으로 사용료를 차단하지 않습니다.
- Cloud SQL로 DB를 변경하지 않습니다. 현재 MariaDB 엔진과 SQL을 유지합니다.

## 준비된 백업

`counsel_survey_20261008_125601.sql`은 2026-10-08 12:56 KST 기준 현재 MariaDB 11.4.13의 구조와 데이터 백업입니다.
`counsel_survey_20261008_125601_manifest.json`에 각 테이블 행 수와 SHA-256 해시가 있습니다.

총 9개 테이블: team, category, practice, study_problem, review_frequency,
preffered_occupation, learn_env, facillities, survey_responses.
현재 study_problem 7건, survey_responses 1건을 포함하여 실제 DB 내용을 그대로 가져왔습니다.
별도 임시 DB에 복원한 후 모든 행의 모든 컬럼 값을 원본과 비교해 일치 확인했습니다.
검증용 DB는 제거했으며 원본 DB는 변경하지 않았습니다.

백업은 DB 사용자/권한/비밀번호를 포함하지 않습니다. CREATE DATABASE/USE와 DROP TABLE도 포함하지 않아 대상 DB 이름을 별도로 지정할 수 있습니다.
설문 응답을 포함하므로 SQL과 manifest를 정적 파일 폴더나 공개 Git 저장소에 올리지 않습니다.

## 새 서버에서 복원 순서

1. MariaDB 11.4 계열 서버 및 클라이언트를 설치하고 실행합니다. 백업과 맞는 클라이언트를 사용합니다.
2. `create-production-db.sql.example`의 비밀번호를 새 값으로 교체하고 DB 관리자 계정으로 실행합니다. 빈 `counsel_survey_prod`를 생성합니다.
3. SQL 백업을 비공개 경로로 서버에 전송합니다. manifest의 SHA-256과 `sha256sum` 결과를 비교합니다.
4. **비어 있는 새 운영 DB에만** 관리자 계정으로 아래를 실행합니다. 비밀번호는 명령행에 쓰지 않고 프롬프트에 입력합니다.

```bash
mariadb --default-character-set=utf8mb4 -u root -p counsel_survey_prod < counsel_survey_20261008_125601.sql
```

Ubuntu의 root 소켓 인증을 사용하는 경우에는 `sudo mariadb counsel_survey_prod < ...`로 복원할 수 있습니다.

5. 테이블 수, 각 행 수, 한글 및 설문 JSON 응답을 확인합니다. manifest 행 수와 비교합니다.
6. `.env.production.example`을 서버 앱 디렉터리의 `.env`로 복사합니다. 두 비밀번호를 각각 새 값으로 설정하고 `chmod 600 .env`를 적용합니다.
7. 애플리케이션 파일과 requirements.txt를 배포하고 새 가상환경에 패키지를 설치합니다. 로컬 `.env`, `.venv`, __pycache__, DB 덤프는 공개 앱 배포물에서 제외합니다.
8. systemd로 FastAPI를 자동 실행하고 Nginx/HTTPS를 설정합니다. 관리자 로그인, 기존 응답 조회, 새 설문 저장, 통계를 확인합니다.

## 실제 전환 시 주의

이 파일은 현재 시점의 백업이며 이후 입력한 설문은 포함하지 않습니다.
최종 전환 직전에 기존 설문 접수를 잠시 중지하고 모든 실행 중인 저장 요청이 끝난 뒤 새 최종 덤프를 다시 생성합니다.
최종 덤프를 새 빈 운영 DB에 복원·검증한 뒤 도메인을 운영 서버로 연결합니다.
기존 서버와 DB는 초기 확인 기간 동안 보관하되 두 서버에서 동시에 접수하지 않습니다.

복원 후 `database.sql`을 다시 실행하지 마세요. 이 파일은 초기 데이터 준비용으로 기존 관리 목록/순서를 다시 설정할 수 있습니다.

현재 단계에서는 Google Cloud 리소스를 생성하거나 개인정보를 업로드하지 않았습니다.
외부 배포 전 기존 관리자/DB 비밀번호 교체, DB 원문 오류 응답 제거, CORS 허용 범위 제한을 완료해야 합니다.
