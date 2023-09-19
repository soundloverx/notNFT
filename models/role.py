from sqlalchemy import Column, Integer, String, text
from db_connector import Base, db_session


class Role(Base):
    __tablename__ = 'roles'
    id = Column("id", Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    def __init__(self, name):
        self.name = name

    def validate_roles(self):
        with db_session.begin() as transaction:
            existing_roles = transaction.session.query(Role).order_by(Role.id).all()
            if len(existing_roles) != 2 or existing_roles[0].id != 1 or existing_roles[1].id != 2:
                transaction.session.execute(text("TRUNCATE TABLE " + self.__tablename__))
                transaction.session.add(Role("admin"))
                transaction.session.add(Role("user"))
