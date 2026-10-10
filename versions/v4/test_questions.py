import json
import os
import unittest
from fastapi import HTTPException
from pydantic import ValidationError
from questions import QuestionInput, AnswerInput, ResponseInput, validate_answers, normalize_response
from analysis import statistics


def question(**changes):
    value=dict(id=1,topic='배우고 싶은 기술',section='추가 설문',kind='multiple',options=['Python','SQL'],required=True,allow_comment=False,legacy_key=None,revision=1,deleted=False,sort_order=10)
    value.update(changes)
    return value


class QuestionTests(unittest.TestCase):
    def test_options_and_blank_titles(self):
        for options in [['한 개'],['중복','중복'],['공백',' ']]:
            with self.assertRaises(ValidationError):QuestionInput(topic='주제',kind='single',options=options)
        with self.assertRaises(ValidationError):QuestionInput(topic=' ',kind='text')
        self.assertEqual(QuestionInput(topic='주제',kind='text',options=['a','b']).options,[])

    def test_multiple_required_duplicate_unknown(self):
        for answers in [[],[AnswerInput(question_id=1,value=[])],[AnswerInput(question_id=1,value=['Python','Python'])],
                        [AnswerInput(question_id=1,value=['등록 안 됨'])],[AnswerInput(question_id=2,value=['Python'])],
                        [AnswerInput(question_id=1,value=['Python']),AnswerInput(question_id=1,value=['SQL'])]]:
            with self.assertRaises(HTTPException):validate_answers([question()],answers)
        self.assertEqual(validate_answers([question()],[AnswerInput(question_id=1,value=['Python','SQL'])])[0]['value'],['Python','SQL'])

    def test_text_limits_and_comments(self):
        with self.assertRaises(HTTPException):validate_answers([question(kind='text')],[AnswerInput(question_id=1,value='x'*5001)])
        with self.assertRaises(HTTPException):validate_answers([question()],[AnswerInput(question_id=1,value=['Python'],comment='의견')])
        with self.assertRaises(ValidationError):ResponseInput(student_name=' ',form_revision=1,answers=[])

    def test_absent_score_never_becomes_default_three(self):
        row=normalize_response(dict(id=1,student_name='가상인',team_name=None,created_at='2026-10-09',snapshot_json='[]'))
        result=statistics([row],[],[])
        self.assertIsNone(result['scores']['understanding_level']['average'])
        self.assertEqual(result['scores']['understanding_level']['missing'],1)
        self.assertEqual(result['flagged_count'],0)

    def test_snapshot_preserves_comma_choices(self):
        snapshot=[dict(question=question(legacy_key='career_fields'),value=['데이터, 분석','백엔드'],comment=None)]
        row=normalize_response(dict(id=2,student_name='가상인',team_name=None,created_at='2026-10-09',snapshot_json=json.dumps(snapshot)))
        self.assertEqual(row['career_fields'],['데이터, 분석','백엔드'])
        self.assertEqual(len(statistics([row],[],[])['career_fields']),2)


@unittest.skipUnless(os.getenv('RUN_DB_TESTS')=='1','Set RUN_DB_TESTS=1 for rollback-only DB integration tests')
class DatabaseTests(unittest.TestCase):
    def test_crud_submission_history_and_legacy_statistics(self):
        import main
        from sqlalchemy import create_engine,text
        from sqlalchemy.engine import URL
        from sqlalchemy.orm import Session
        from questions import definitions,form_revision
        engine=create_engine(URL.create('mysql+pymysql',username='root',password=main.DB_PASSWORD,host=main.DB_HOST,port=int(main.DB_PORT),database=main.DB_NAME,query={'charset':'utf8mb4'}))
        routes={(r.path,next(iter(r.methods))):r.endpoint for r in main.app.routes if hasattr(r,'methods') and r.path.startswith('/api/')}
        with engine.connect() as connection:
            outer=connection.begin()
            db=Session(bind=connection,join_transaction_mode='create_savepoint')
            try:
                before=connection.execute(text('SELECT COUNT(*) FROM survey_responses')).scalar()
                new_before=connection.execute(text('SELECT COUNT(*) FROM v4_responses')).scalar()
                initial_revision=form_revision(db)
                created=[]
                for kind,options in [('text',[]),('single',['기초','심화']),('multiple',['Python','SQL'])]:
                    result=routes[('/api/admin/questions','POST')](QuestionInput(topic='검증 항목 '+kind,kind=kind,options=options,required=True),db=db)
                    created.append(result['id'])
                form=routes[('/api/v4/questions','GET')](db=db)
                with self.assertRaises(HTTPException) as stale:
                    routes[('/api/v4/surveys','POST')](ResponseInput(student_name='검증용',form_revision=initial_revision,answers=[]),db=db)
                self.assertEqual(stale.exception.status_code,409)
                answers=[]
                for q in form['questions']:
                    value='검증 내용' if q['kind']=='text' else q['options'][:2] if q['kind']=='multiple' else q['options'][0]
                    answers.append(AnswerInput(question_id=q['id'],value=value))
                submitted=routes[('/api/v4/surveys','POST')](ResponseInput(student_name='검증용',form_revision=form['revision'],answers=answers),db=db)
                saved=routes[('/api/admin/surveys/{survey_id}','GET')](survey_id=submitted['id'],db=db)['response']
                target=next(q for q in definitions(db) if q['id']==created[1])
                edit=QuestionInput(topic='변경된 주제',kind='single',options=['새 선택1','새 선택2'],revision=target['revision'])
                routes[('/api/admin/questions/{question_id}','PUT')](target['id'],edit,db=db)
                with self.assertRaises(HTTPException) as conflict:routes[('/api/admin/questions/{question_id}','PUT')](target['id'],edit,db=db)
                self.assertEqual(conflict.exception.status_code,409)
                changed=next(q for q in definitions(db) if q['id']==target['id'])
                routes[('/api/admin/questions/{question_id}','DELETE')](changed['id'],revision=changed['revision'],db=db)
                after=routes[('/api/admin/surveys/{survey_id}','GET')](survey_id=submitted['id'],db=db)['response']
                self.assertEqual(saved['question_answers'],after['question_answers'])
                stats=routes[('/api/admin/statistics','GET')](name='',team='',db=db)
                self.assertEqual(stats['response_count'],before+new_before+1)
                self.assertTrue(any(q['topic']=='검증 항목 single' and q['answered']==1 for q in stats['questions']))
                self.assertEqual(connection.execute(text('SELECT COUNT(*) FROM survey_responses')).scalar(),before)
                for kind in ('text','single','multiple'):
                    self.assertTrue(any(q['kind']==kind and q['answered']==1 for q in stats['questions']))
            finally:
                db.close();outer.rollback()
            self.assertEqual(connection.execute(text('SELECT COUNT(*) FROM v4_responses')).scalar(),new_before)
            self.assertEqual(connection.execute(text('SELECT revision FROM v4_form_state WHERE id=1')).scalar(),initial_revision)
        engine.dispose()


if __name__=='__main__':unittest.main()
