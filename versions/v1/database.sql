CREATE DATABASE IF NOT EXISTS counsel_survey
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE counsel_survey;

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
