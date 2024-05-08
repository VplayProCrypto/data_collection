import os
from sqlmodel import create_engine, Session

engine = create_engine(os.environ.get('TIMESCALE_URL'))


def initialize_db(sql_files):
    with Session(engine) as session:
        for sql_file in sql_files:
            with open(sql_file, "r") as file:
                sql = file.read()
                session.execute(sql)
        session.commit()


