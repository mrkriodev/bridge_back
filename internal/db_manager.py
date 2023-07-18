from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

path_to_sql_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bridge_records.db')
engine_db = create_engine(f"sqlite:///{path_to_sql_db}", echo=True)
DbSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)


# Dependency
def get_db_session():
    db_session = DbSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


get_db_session().send(None).close()
