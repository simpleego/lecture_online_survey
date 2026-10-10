"""Rename the first synthetic batch and add 40 Korean-named responses."""
import copy
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from create_test_surveys import api, main, ROOT

SOURCE = ROOT / 'deploy/test_surveys_20261009.json'
OUTPUT = ROOT / 'deploy/test_surveys_20261009_60.json'
NAMES = '''김도윤 이서준 박하준 최예준 정도현 강시우 조지호 윤준우 장민준 임건우
한지훈 오유준 서현우 신정우 권우진 황선우 안준서 송연우 전수호 홍승우
김서연 이지우 박서윤 최하윤 정지민 강수아 조하은 윤지아 장서현 임채원
한민서 오다은 서예은 신유나 권수빈 황소율 안예린 송지유 전나은 홍시아
김태윤 이준혁 박성민 최지성 정민재 강승현 조재윤 윤현준 장동현 임태민
한수진 오혜원 서유진 신소윤 권채은 황다인 안은서 송가은 전보민 홍아린'''.split()


def run():
    assert len(NAMES) == len(set(NAMES)) == 60 and all(len(n) == 3 for n in NAMES)
    assert not OUTPUT.exists(), 'Batch report already exists; stopped to avoid duplicates'
    original = json.loads(SOURCE.read_text(encoding='utf-8'))
    records = original['records']
    assert len(records) == 20
    admin_engine = create_engine(URL.create('mysql+pymysql', username='root', password=main.DB_PASSWORD,
        host=main.DB_HOST, port=int(main.DB_PORT), database=main.DB_NAME, query={'charset': 'utf8mb4'}))
    with admin_engine.begin() as connection:
        before = connection.execute(text('SELECT COUNT(*) FROM survey_responses')).scalar()
        current_names = connection.execute(text('SELECT student_name FROM survey_responses')).scalars().all()
        assert not set(NAMES[20:]).intersection(current_names), 'Name collision; stopped'
        for index, record in enumerate(records):
            previous = record['payload']['student_name']
            if previous == NAMES[index]:
                assert connection.execute(text('SELECT student_name FROM survey_responses WHERE id=:id'), {'id':record['id']}).scalar() == previous
                continue
            result = connection.execute(text('UPDATE survey_responses SET student_name=:new WHERE id=:id AND student_name=:old'),
                dict(new=NAMES[index], id=record['id'], old=previous))
            assert result.rowcount == 1, 'Existing test record mismatch'
            record['previous_student_name'] = previous
            record['payload']['student_name'] = NAMES[index]
    admin_engine.dispose()
    # Keep the original audit data in step with the SQL updates, including comment names.
    name_map = {r['previous_student_name']: r['payload']['student_name'] for r in records}
    def rename_nested(value):
        if isinstance(value, dict):
            for k,v in value.items():
                if k == 'student_name' and v in name_map: value[k] = name_map[v]
                else: rename_nested(v)
        elif isinstance(value, list):
            for v in value: rename_nested(v)
    rename_nested(original)
    SOURCE.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Renamed existing test records: 20', flush=True)
    teams = [x['team_name'] for x in api('/api/teams')] + [None]
    practices = [x['practice_status'] for x in api('/api/practices')]
    frequencies = [x['frequency_name'] for x in api('/api/review-frequencies')]
    categories = [x['category_value'] for x in api('/api/categories')]
    careers = [x['occupation_value'] for x in api('/api/preffered-occupations')]
    problems = [x['problem_name'] for x in api('/api/study-problems')]
    items_by_field = {'learn_env_answers':api('/api/learn-env'), 'facillities_answers':api('/api/facillities')}
    new_records = []
    def save():
        OUTPUT.write_text(json.dumps({'synthetic':True,'renamed_count':20,'created_count':len(new_records),
            'records':records+new_records},ensure_ascii=False,indent=2),encoding='utf-8')
    save()
    for i in range(40):
        payload = copy.deepcopy(records[(i*7+3)%20]['payload'])
        payload['student_name'] = NAMES[i+20]
        payload['team_name'] = teams[i%len(teams)]
        u, p = 1+i%5, 1+(i//5+i)%5
        payload.update(understanding_level=u, practice_level=p, practice_status=practices[p-1],
            ai_tool_level=1+(i*3)%5, course_career_fit=1+(i*2+1)%5,
            review_frequency=frequencies[(i//5+i)%5])
        payload['code_understanding'] = ['거의 이해하지 못하고 사용한다','일부만 이해한다','전체 흐름은 이해한다','수정해서 사용할 수 있다','검증하고 개선할 수 있다'][(i//4+i)%5]
        payload['class_speed'] = '많이 빠르다' if u==1 else '조금 빠르다' if u==2 else '적당하다' if u==3 else '조금 느리다' if u==4 else '많이 느리다'
        payload['understanding_areas'] = [categories[i%len(categories)]] if i%3==0 else list(dict.fromkeys([categories[i%len(categories)],categories[(i+3)%len(categories)]]))
        payload['hardest_points'] = [] if i%7==0 else list(dict.fromkeys([problems[i%len(problems)],problems[(i+1)%len(problems)]]))
        payload['career_fields'] = [careers[i%len(careers)]] if i%2==0 else list(dict.fromkeys([careers[i%len(careers)],careers[(i+2)%len(careers)]]))
        payload['desired_job'] = careers[i%len(careers)]+' 관련 직무'
        payload['understanding_good'] = categories[i%len(categories)]+'의 기본 예제와 흐름은 이해합니다.'
        payload['understanding_difficult'] = '여러 개념을 연결해서 기능을 만드는 과정이 어렵습니다.' if u<=3 else None
        payload['practice_comment'] = '단계별 예제를 더 연습하고 싶습니다.' if p<=2 else '혼자 구현한 코드를 검토받고 싶습니다.'
        payload['instructor_support'] = '보충 설명과 개별 질문 시간을 부탁드립니다.' if u<=2 else '실무 사례와 포트폴리오 피드백을 부탁드립니다.'
        payload['need_more_explanation'] = 'DB 연결과 오류 메시지를 해석하는 순서가 궁금합니다.' if u<=3 else None
        for field, items in items_by_field.items():
            payload[field] = []
            for j,item in enumerate(items):
                rating=item['options'][(i*3+j)%len(item['options'])]
                comment = None if (i+j)%3==0 else (item['item_name']+'의 상태를 점검해 주시면 좋겠습니다.' if rating in ['매우 불만족','불만족'] else '현재 상태는 무난합니다.' if rating=='보통' else '사용하기 편리합니다.' if rating in ['만족','매우 만족'] else '아직 이용 경험이 없습니다.')
                payload[field].append(dict(item_id=item['id'],satisfaction=rating,comment=comment))
        main.SurveyCreate(**payload)
        result=api('/api/surveys',payload)
        new_records.append({'id':result['id'],'payload':payload})
        save()
    all_records=records+new_records
    for record in all_records:
        actual=api(f"/api/admin/surveys/{record['id']}",admin=True)['response']
        for key,expected in record['payload'].items():
            if key in ('understanding_areas','hardest_points','ai_tool_usage','career_fields'): expected=','.join(expected)
            assert actual[key]==expected,(record['id'],key)
    with main.engine.connect() as connection:
        after=connection.execute(text('SELECT COUNT(*) FROM survey_responses')).scalar()
    assert after==before+40 and len(new_records)==40
    stats=api('/api/admin/statistics',admin=True)
    assert stats['response_count']==after
    OUTPUT.write_text(json.dumps({'synthetic':True,'renamed_count':20,'created_count':40,
        'before_count':before,'after_count':after,'records':all_records,'verified_all_statistics':stats},
        ensure_ascii=False,indent=2),encoding='utf-8')
    print('Created: 40; synthetic total: 60; database total:',after)
    print('New ID range:',new_records[0]['id'],new_records[-1]['id'])
    print('All 60 responses verified against submitted fields')


if __name__=='__main__':
    run()
