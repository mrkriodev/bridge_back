from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

print(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')):
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

#path_to_sql_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bridge_records.db')
#engine_db = create_engine(f"sqlite:///{path_to_sql_db}", echo=True)
print(os.getenv('DB_USER'))
engine_db = create_engine(f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:5432/bridge")
DbSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)


# Dependency
def get_db_session():
    db_session = DbSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


get_db_session().send(None).close()
