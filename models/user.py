from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from db_connector import Base
from models.role import Role


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey(Role.id), nullable=False)
    budget = Column(Integer, nullable=False)
    country = Column(String(255), nullable=False)
    active = Column(Integer, nullable=False)
    inventory_cards = relationship("Inventory", back_populates="o_user")
    market_cards = relationship("Marketplace", back_populates="o_user")

    def __init__(self, username, email, password, country, role_id=2, budget=500, active=1):
        self.username, self.email, self.password = username, email, password
        self.country, self.role_id, self.budget, self.active = country, role_id, budget, active

    def to_json(self):
        return {"id": self.id, "username": self.username, "email": self.email, "budget": self.budget,
                "country": self.country}

    def set_country(self, country):
        self.country = country

    def set_active(self, active_status_code):
        self.active = active_status_code

    def set_budget(self, budget):
        self.budget = budget

    def set_role(self, role_id):
        self.role_id = role_id
