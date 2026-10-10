import unittest
from analysis import statistics, counseling_flags


def response(**changes):
    row = dict(id=1, student_name="테스트", team_name="A팀", understanding_level=3,
               practice_level=3, ai_tool_level=3, course_career_fit=3,
               review_frequency="거의 매일", code_understanding="전체 흐름은 이해한다",
               class_speed="적당하다", hardest_points="문법 이해,에러 해결", career_fields="백엔드",
               learn_env_answers=[], facillities_answers=[])
    row.update(changes)
    return row


class AnalysisTests(unittest.TestCase):
    def test_empty(self):
        data = statistics([], [], [])
        self.assertEqual(data["response_count"], 0)
        self.assertIsNone(data["scores"]["understanding_level"]["average"])

    def test_exclusions_and_missing(self):
        items = [{"id": 1, "item_name": "장비"}]
        rows = [response(learn_env_answers=[dict(item_id=1, satisfaction="만족", comment="좋음")]),
                response(id=2, learn_env_answers=[dict(item_id=1, satisfaction="해당 없음", comment=None)]),
                response(id=3)]
        item = statistics(rows, items, [])["learn_env"][0]
        self.assertEqual((item["average"], item["rated"], item["excluded"], item["missing"]), (4, 1, 1, 1))
        self.assertEqual(len(item["comments"]), 1)

    def test_multiple_choice_response_denominator(self):
        data = statistics([response(), response(id=2, hardest_points="문법 이해,문법 이해")], [], [])
        values = {r["label"]: r for r in data["hardest_points"]}
        self.assertEqual(values["문법 이해"]["percent"], 100)
        self.assertEqual(values["에러 해결"]["percent"], 50)

    def test_flags_and_boundaries(self):
        self.assertEqual(counseling_flags(response()), [])
        row = response(understanding_level=2, practice_level=1, review_frequency="거의 하지 않는다",
                       ai_tool_level=4, code_understanding="일부만 이해한다", class_speed="많이 빠르다",
                       facillities_answers=[dict(item_id=2, satisfaction="불만족", comment=None)])
        self.assertEqual(len(counseling_flags(row)), 6)
        self.assertEqual(len(counseling_flags(response(ai_tool_level=3, code_understanding="일부만 이해한다"))), 0)

    def test_repeated_responses_and_teams(self):
        data = statistics([response(), response(id=2, team_name=None, understanding_level=1)], [], [])
        self.assertEqual(data["response_count"], 2)
        self.assertEqual(data["scores"]["understanding_level"]["average"], 2)
        self.assertEqual(len(data["teams"]), 2)


if __name__ == "__main__":
    unittest.main()
