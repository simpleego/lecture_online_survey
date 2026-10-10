"""실제 PostgreSQL 검증: TEST_DATABASE_URL 설정 후 실행. 테스트 스키마는 롤백합니다."""
import os
from pathlib import Path
import unittest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
import main


@unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "TEST_DATABASE_URL이 필요합니다.")
class PostgreSQLTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(os.environ["TEST_DATABASE_URL"])
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        schema = "test_" + uuid.uuid4().hex
        self.connection.exec_driver_sql(f"CREATE SCHEMA {schema}")
        self.connection.exec_driver_sql(f"SET LOCAL search_path TO {schema}")
        ddl = Path(__file__).with_name("database.sql").read_text(encoding="utf-8")
        self.connection.exec_driver_sql(ddl.replace("BEGIN;", "").replace("COMMIT;", ""))
        self.db = Session(bind=self.connection)

    def tearDown(self):
        self.db.close()
        self.transaction.rollback()
        self.connection.close()
        self.engine.dispose()

    def payload(self):
        return dict(student_name="테스트학생", team_name="A팀", understanding_level=2,
            practice_level=2, practice_status=main.get_practices(self.db)[0]["practice_status"],
            review_frequency=main.get_review_frequencies(self.db)[0]["frequency_name"],
            ai_tool_level=4, code_understanding="일부만 이해한다", course_career_fit=3,
            class_speed="많이 빠르다", practice_amount="적당하다", career_fields=["DevOps/배포"])

    def test_save_lookup_search_statistics(self):
        payload = self.payload()
        payload["learn_env_answers"] = [dict(item_id=i["id"], satisfaction="해당 없음", comment="한글 ' 의견")
                                        for i in main.get_learn_env(self.db)]
        saved = main.create_survey(main.SurveyCreate(**payload), self.db)
        row = main.get_survey(saved["id"], self.db)
        self.assertEqual(row["learn_env_answers"][0]["comment"], "한글 ' 의견")
        routes = {r.path: r.endpoint for r in main.app.routes if hasattr(r, "endpoint")}
        listing = routes["/api/admin/surveys"](name="학생", team="A팀", page=1, page_size=1, db=self.db)
        self.assertEqual(listing["total"], 1)
        stats = routes["/api/admin/statistics"](name="학생", team="A팀", db=self.db)
        self.assertEqual(stats["flagged_count"], 1)
        self.assertIsNone(stats["learn_env"][0]["average"])

    def test_seed_repeat_and_validation(self):
        ddl = Path(__file__).with_name("database.sql").read_text(encoding="utf-8")
        self.connection.exec_driver_sql(ddl.replace("BEGIN;", "").replace("COMMIT;", ""))
        self.assertEqual(len(main.get_teams(self.db)), 4)
        payload = self.payload()
        payload["career_fields"] = ["등록되지 않은 분야"]
        with self.assertRaises(HTTPException) as error:
            main.create_survey(main.SurveyCreate(**payload), self.db)
        self.assertEqual(error.exception.status_code, 422)
