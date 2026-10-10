"""Non-destructive v4 schema migration; run once with the DB administrator."""
import json
import os
from pathlib import Path
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import main


def seeds(db):
    def values(table, column):
        return list(db.execute(text(f"SELECT {column} FROM {table} ORDER BY sort_order,id")).scalars())
    scores=['1','2','3','4','5']
    groups=[
        ('수업 이해도', [('understanding_level','전체적인 수업 이해도','single',scores,True),('understanding_good','잘 이해되는 부분','text',[],False),('understanding_difficult','어려운 부분','text',[],False),('understanding_areas','이해가 잘 되는 분야','multiple',values('category','category_value'),False)]),
        ('실습 수행 상태',[('practice_level','실습 코드를 혼자 작성할 수 있는 정도','single',scores,True),('practice_status','현재 실습 단계','single',values('practice','practice_status'),True),('practice_comment','실습 수행에 대한 추가 의견','text',[],False)]),
        ('학습 중 가장 어려운 점',[('hardest_points','학습 중 가장 어려운 점','multiple',values('study_problem','problem_name'),False),('hardest_comment','구체적으로 어떤 점이 어렵습니까?','text',[],False)]),
        ('복습 및 개인 학습 방법',[('review_frequency','수업 후 복습 빈도','single',values('review_frequency','frequency_name'),True),('ai_learning_usage','AI 도구를 학습에 어떻게 활용합니까?','text',[],False),('improvement_method','부족한 부분을 보완하는 방법','text',[],False)]),
        ('프로젝트 참여 상태',[(k,t,'text',[],False) for k,t in [('project_role','현재 팀 내 역할'),('desired_role','앞으로 맡고 싶은 역할'),('collaboration_difficulty','협업 시 어려운 점'),('project_strength','프로젝트에서 자신 있는 부분'),('project_burden','프로젝트에서 부담되는 부분')]]),
        ('AI 코딩 도구 활용 수준',[('ai_tool_level','AI 코딩 도구 활용 수준','single',scores,True),('ai_tool_usage','AI 도구 활용 목적','multiple',['코드 생성','오류 분석','코드 설명','리팩터링','테스트 생성','문서 작성'],False),('code_understanding','AI 생성 코드 이해 수준','single',['거의 이해하지 못하고 사용한다','일부만 이해한다','전체 흐름은 이해한다','수정해서 사용할 수 있다','검증하고 개선할 수 있다'],True),('ai_tool_comment','AI 도구 활용에 대한 추가 의견','text',[],False)]),
        ('취업 및 진로 방향',[('desired_job','희망 직무','text',[],False),('career_fields','관심 분야','multiple',values('preffered_occupation','occupation_value'),False),('course_career_fit','현재 과정과 진로의 적합도','single',scores,True),('career_comment','진로에 대해 고민되는 점','text',[],False)]),
        ('교육과정 및 강의 의견',[('class_speed','수업 속도','single',['많이 느리다','조금 느리다','적당하다','조금 빠르다','많이 빠르다'],True),('practice_amount','실습량','single',['매우 부족하다','조금 부족하다','적당하다','조금 많다','매우 많다'],True),('need_more_explanation','추가 설명이 필요한 부분','text',[],False),('instructor_support','강사에게 바라는 지원 사항','text',[],False)]),
    ]
    result=[]
    for section, questions in groups:
        for key,topic,kind,options,required in questions:
            result.append(dict(legacy_key=key,section=section,topic=topic,kind=kind,options_json=json.dumps(options,ensure_ascii=False),required=required,allow_comment=False,sort_order=(len(result)+1)*10))
    for table,section in [('learn_env','학습환경'),('facillities','건물 인프라 및 편의 지원')]:
        for r in db.execute(text(f'SELECT * FROM {table} ORDER BY sort_order,id')).mappings():
            result.append(dict(legacy_key=f"{table}:{r['id']}",section=section,topic=r['item_name'],kind='single',options_json=r['options_json'],required=True,allow_comment=True,sort_order=(len(result)+1)*10))
    return result


def run():
    engine=create_engine(URL.create('mysql+pymysql',username=os.getenv('DB_MIGRATION_USER','root'),password=os.getenv('DB_MIGRATION_PASSWORD',main.DB_PASSWORD),host=main.DB_HOST,port=int(main.DB_PORT),database=main.DB_NAME,query={'charset':'utf8mb4'}))
    with engine.begin() as db:
        before=db.execute(text('SELECT COUNT(*) FROM survey_responses')).scalar()
        db.execute(text('''CREATE TABLE IF NOT EXISTS v4_form_state (id INT PRIMARY KEY, revision INT NOT NULL) ENGINE=InnoDB'''))
        db.execute(text('''CREATE TABLE IF NOT EXISTS v4_questions (
            id INT AUTO_INCREMENT PRIMARY KEY, legacy_key VARCHAR(100) NULL UNIQUE,
            topic VARCHAR(200) NOT NULL, section VARCHAR(100) NOT NULL,
            kind VARCHAR(20) NOT NULL, options_json LONGTEXT NOT NULL,
            required BOOLEAN NOT NULL DEFAULT FALSE, allow_comment BOOLEAN NOT NULL DEFAULT FALSE,
            sort_order INT NOT NULL DEFAULT 1000, revision INT NOT NULL DEFAULT 1, deleted BOOLEAN NOT NULL DEFAULT FALSE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'''))
        db.execute(text('''CREATE TABLE IF NOT EXISTS v4_responses (
            id BIGINT AUTO_INCREMENT PRIMARY KEY, student_name VARCHAR(50) NOT NULL,
            team_name VARCHAR(50) NULL, form_revision INT NOT NULL, snapshot_json LONGTEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'''))
        # Only bootstrap on the first migration. Never restore deleted questions on rerun.
        if not db.execute(text('SELECT id FROM v4_form_state WHERE id=1')).first():
            for q in seeds(db):
                db.execute(text('''INSERT INTO v4_questions(legacy_key,topic,section,kind,options_json,required,allow_comment,sort_order)
                    VALUES(:legacy_key,:topic,:section,:kind,:options_json,:required,:allow_comment,:sort_order)'''),q)
            db.execute(text('INSERT INTO v4_form_state VALUES(1,1)'))
        assert db.execute(text('SELECT COUNT(*) FROM survey_responses')).scalar()==before
    # Grant access only to new tables; the original tables retain their existing permissions.
    user=main.DB_USER.replace("'","''")
    database=main.DB_NAME.replace('`','``')
    with engine.begin() as db:
        for table in ('v4_questions','v4_form_state'):
            db.execute(text(f"GRANT SELECT,INSERT,UPDATE ON `{database}`.`{table}` TO '{user}'@'localhost'"))
        db.execute(text(f"GRANT SELECT,INSERT ON `{database}`.`v4_responses` TO '{user}'@'localhost'"))
        print('Definitions:',db.execute(text('SELECT COUNT(*) FROM v4_questions WHERE deleted=0')).scalar())
        print('Legacy responses preserved:',before)
    engine.dispose()


if __name__=='__main__':
    run()
