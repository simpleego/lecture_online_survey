CREATE DATABASE IF NOT EXISTS counsel_survey
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE counsel_survey;

CREATE TABLE IF NOT EXISTS team (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO team (team_name) VALUES ('A팀'), ('B팀'), ('C팀'), ('D팀')
ON DUPLICATE KEY UPDATE team_name = VALUES(team_name);

CREATE TABLE IF NOT EXISTS category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    category_value VARCHAR(50) NOT NULL UNIQUE,
    sort_order INT NOT NULL
);

-- 화면 표시명과 기존 설문 저장값을 구분하여 기존 데이터와 호환합니다.
INSERT INTO category (category_name, category_value, sort_order) VALUES
    ('Python', 'Python', 1),
    ('DB / SQL', 'DB/SQL', 2),
    ('FastAPI', 'FastAPI', 3),
    ('HTML / CSS', 'HTML/CSS', 4),
    ('JavaScript', 'JavaScript', 5),
    ('Git / GitHub', 'Git/GitHub', 6)
ON DUPLICATE KEY UPDATE category_name = VALUES(category_name), sort_order = VALUES(sort_order);

CREATE TABLE IF NOT EXISTS practice (
    id INT AUTO_INCREMENT PRIMARY KEY,
    practice_status VARCHAR(30) NOT NULL UNIQUE,
    sort_order INT NOT NULL
);

INSERT INTO practice (practice_status, sort_order) VALUES
    ('예제를 보면서 따라 할 수 있다', 1),
    ('예제를 조금 수정할 수 있다', 2),
    ('요구사항을 보고 혼자 작성할 수 있다', 3),
    ('기능을 응용하여 확장할 수 있다', 4),
    ('다른 사람에게 설명할 수 있다', 5)
ON DUPLICATE KEY UPDATE sort_order = VALUES(sort_order);

CREATE TABLE IF NOT EXISTS study_problem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    problem_name VARCHAR(50) NOT NULL UNIQUE,
    sort_order INT NOT NULL
);

INSERT INTO study_problem (problem_name, sort_order) VALUES
    ('문법 이해', 1),
    ('에러 해결', 2),
    ('코드 작성 순서', 3),
    ('개념 연결', 4),
    ('학습 속도', 5),
    ('프로젝트 적용', 6)
ON DUPLICATE KEY UPDATE sort_order = VALUES(sort_order);

CREATE TABLE IF NOT EXISTS review_frequency (
    id INT AUTO_INCREMENT PRIMARY KEY,
    frequency_name VARCHAR(30) NOT NULL UNIQUE,
    sort_order INT NOT NULL
);

INSERT INTO review_frequency (frequency_name, sort_order) VALUES
    ('거의 하지 않는다', 1),
    ('주 1~2회', 2),
    ('주 3~4회', 3),
    ('거의 매일', 4),
    ('수업 당일 반드시 복습한다', 5)
ON DUPLICATE KEY UPDATE sort_order = VALUES(sort_order);

CREATE TABLE IF NOT EXISTS preffered_occupation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    occupation_name VARCHAR(50) NOT NULL,
    occupation_value VARCHAR(50) NOT NULL UNIQUE,
    sort_order INT NOT NULL
);

INSERT INTO preffered_occupation (occupation_name, occupation_value, sort_order) VALUES
    ('백엔드', '백엔드', 1),
    ('프론트엔드', '프론트엔드', 2),
    ('데이터베이스', '데이터베이스', 3),
    ('데이터 분석', '데이터 분석', 4),
    ('AI 서비스 개발', 'AI 서비스 개발', 5),
    ('DevOps / 배포', 'DevOps/배포', 6)
ON DUPLICATE KEY UPDATE occupation_name=VALUES(occupation_name), sort_order=VALUES(sort_order);

CREATE TABLE IF NOT EXISTS survey_responses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(50) NOT NULL,
    team_name VARCHAR(50) NULL,

    understanding_level TINYINT NOT NULL,
    understanding_good TEXT NULL,
    understanding_difficult TEXT NULL,
    understanding_areas VARCHAR(255) NULL,

    practice_level TINYINT NOT NULL,
    practice_status VARCHAR(30) NOT NULL,
    practice_comment TEXT NULL,

    hardest_points VARCHAR(255) NULL,
    hardest_comment TEXT NULL,

    review_frequency VARCHAR(30) NOT NULL,
    ai_learning_usage TEXT NULL,
    improvement_method TEXT NULL,

    project_role VARCHAR(100) NULL,
    desired_role VARCHAR(100) NULL,
    collaboration_difficulty TEXT NULL,
    project_strength TEXT NULL,
    project_burden TEXT NULL,

    ai_tool_level TINYINT NOT NULL,
    ai_tool_usage VARCHAR(255) NULL,
    code_understanding VARCHAR(30) NOT NULL,
    ai_tool_comment TEXT NULL,

    desired_job VARCHAR(100) NULL,
    career_fields VARCHAR(255) NULL,
    course_career_fit TINYINT NOT NULL,
    career_comment TEXT NULL,

    class_speed VARCHAR(30) NOT NULL,
    need_more_explanation TEXT NULL,
    practice_amount VARCHAR(30) NOT NULL,
    instructor_support TEXT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learn_env (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(50) NOT NULL UNIQUE,
    options_json TEXT NOT NULL,
    comment_hint VARCHAR(255) NOT NULL,
    sort_order INT NOT NULL
);

INSERT INTO learn_env (item_name, options_json, comment_hint, sort_order) VALUES
    ('컴퓨터·노트북', '["매우 불만족", "불만족", "보통", "만족", "매우 만족", "해당 없음"]', '장비 성능, 프로그램 실행 등 사용 중 불편한 점', 1),
    ('주변 소음', '["매우 불만족", "불만족", "보통", "만족", "매우 만족", "해당 없음"]', '소음의 종류, 발생 시간, 집중에 미치는 영향', 2),
    ('빔프로젝터 가시성', '["매우 불만족", "불만족", "보통", "만족", "매우 만족", "해당 없음"]', '글자 크기, 밝기, 좌석에 따른 화면 가시성', 3),
    ('마이크·음향 시스템', '["매우 불만족", "불만족", "보통", "만족", "매우 만족", "해당 없음"]', '음량, 잡음, 설명이 잘 들리지 않는 상황', 4)
ON DUPLICATE KEY UPDATE options_json=VALUES(options_json), comment_hint=VALUES(comment_hint), sort_order=VALUES(sort_order);

CREATE TABLE IF NOT EXISTS facillities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(50) NOT NULL UNIQUE,
    options_json TEXT NOT NULL,
    comment_hint VARCHAR(255) NOT NULL,
    sort_order INT NOT NULL
);

INSERT INTO facillities (item_name, options_json, comment_hint, sort_order) VALUES
    ('화장실', '["매우 불만족", "불만족", "보통", "만족", "매우 만족", "이용하지 않음"]', '청결, 비품, 혼잡도 등 이용 중 불편한 점', 1),
    ('음료수 제공', '["매우 불만족", "불만족", "보통", "만족", "매우 만족", "이용하지 않음", "제공 없음"]', '음료 종류, 수량, 제공 위치 등 개선 의견', 2),
    ('간식 제공', '["매우 불만족", "불만족", "보통", "만족", "매우 만족", "이용하지 않음", "제공 없음"]', '간식 종류, 수량, 제공 시간 등 개선 의견', 3)
ON DUPLICATE KEY UPDATE options_json=VALUES(options_json), comment_hint=VALUES(comment_hint), sort_order=VALUES(sort_order);

ALTER TABLE survey_responses
    ADD COLUMN IF NOT EXISTS learn_env_answers LONGTEXT NULL,
    ADD COLUMN IF NOT EXISTS facillities_answers LONGTEXT NULL;
