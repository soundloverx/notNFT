import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

engine = sqlalchemy.create_engine("mysql+mysqlconnector://root:nopass@localhost/python_project", echo=False)
Base = declarative_base()
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def create_tables():
    Base.metadata.create_all(bind=engine)

