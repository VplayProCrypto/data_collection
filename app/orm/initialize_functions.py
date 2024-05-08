import os
from sqlmodel import create_engine, Session

engine = create_engine(os.environ.get('TIMESCALE_URL'))


initial_sql = [
    "../db/raw_sql/drop_tables.sql",
    "../db/raw_sql/tables.sql",
    "../db/raw_sql/hypertables.sql",
    "../db/raw_sql/indexes.sql",
]
def initialize_db(sql_files):
    with Session(engine) as session:
        for sql_file in sql_files:
            with open(sql_file, "r") as file:
                sql = file.read()
                session.execute(sql)
        session.commit()


