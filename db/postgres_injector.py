from sqlalchemy import create_engine, text

# class Injector:
#     def __init__(self):
#         url = 'postgresql+psycopg2:///:memory:'
#         self.engine = create_engine()

# import psycopg2
from opensea_requests_sql import OpenSea

class Injector:
    def __init__(self, username: str = None, password: str = None, port: str = None, database: str = None, host: str = None):
        self.username = 'postgres'
        self.port = '5432'
        self.database = 'local'
        self.password = 'postgres'
        if not username:
            self.url = f'postgresql+psycopg2://{self.username}:{self.password}@localhost:{self.port}/{self.database}'
        else:
            self.url = f'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}'
        
        self.engine = create_engine(self.url)

    
    def connect(self):
        return self.connect(database = self.database, user = self.username, password = self.password)
    
    def create_tables(self, file_path = './create_tables.sql'):
        with open(file_path) as f:
            q = f.read()
        conn = self.engine.connect()
        # try:
        conn.execute(text(q))
        conn.commit()
        conn.close()
    
    def _add_collections_opensea(self):
        opensea = OpenSea()
        collections = opensea.save_collections()
        with open('./insert_queries/opensea/collection.sql') as f:
            q = f.read()
        
        with self.engine.connect() as conn:
            conn.execute(text(q), collections)
            conn.commit()
        print("added")

def main():
    injector = Injector()
    injector.create_tables()
    injector._add_collections_opensea()

if __name__ == "__main__":
    main()