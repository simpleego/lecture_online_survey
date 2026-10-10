"""MariaDB 응답을 PostgreSQL SQL로 변환. 생성 파일은 Git에 올리지 않습니다."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pymysql
from dotenv import dotenv_values
from psycopg import sql

TABLES = ["team", "category", "practice", "study_problem", "review_frequency",
          "preffered_occupation", "learn_env", "facillities", "survey_responses"]


def export(source_env, output):
    if output.exists():
        raise ValueError("기존 파일을 덮어쓰지 않습니다. 새 출력 파일명을 지정해 주세요.")
    settings = dotenv_values(source_env)
    schema = Path(__file__).with_name("database.sql").read_text(encoding="utf-8")
    # 실제 데이터만 가져오며 초기 선택지 INSERT는 실행하지 않습니다.
    schema = re.sub(r"INSERT INTO\s+.*?;", "", schema, flags=re.S)
    schema = schema.replace("BEGIN;", "").replace("COMMIT;", "")
    statements = ["-- 기존 응답 포함: 비공개 보관. 빈 PostgreSQL DB에만 복원합니다.",
                  "BEGIN;", "SET standard_conforming_strings = on;", schema]
    counts = {}
    connection = pymysql.connect(host=settings.get("DB_HOST", "127.0.0.1"),
        port=int(settings.get("DB_PORT", "3306")), user=settings["DB_USER"],
        password=settings["DB_PASSWORD"], database=settings["DB_NAME"], charset="utf8mb4")
    try:
        with connection.cursor() as cursor:
            cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT")
            for table in TABLES:
                cursor.execute(f"SELECT * FROM `{table}` ORDER BY id")
                columns = [c[0] for c in cursor.description]
                rows = cursor.fetchall()
                counts[table] = len(rows)
                for row in rows:
                    insert = sql.SQL("INSERT INTO {} ({}) VALUES ({});").format(
                        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, columns)),
                        sql.SQL(", ").join(sql.Literal(value) for value in row))
                    statements.append(insert.as_string())
                statements.append(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1), EXISTS(SELECT 1 FROM {table}));")
            connection.rollback()
    finally:
        connection.close()
    statements.append("COMMIT;")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n\n".join(statements) + "\n", encoding="utf-8")
    manifest = {"exported_at_kst": datetime.now(timezone(timedelta(hours=9))).isoformat(),
                "table_row_counts": counts, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "file": output.name}
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-env", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.source_env, args.output), ensure_ascii=False))
