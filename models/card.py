from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db_connector import Base
from models import inventory


class Card(Base):
    __tablename__ = 'cards'

    id = Column("id", Integer, primary_key=True)
    player_name = Column("name", String(255), nullable=False)
    age = Column("age", Integer, nullable=False)
    skill_level = Column("skill_level", Integer, nullable=False)
    market_value = Column("market_value", Integer, nullable=False)
    inventory_users = relationship("Inventory", back_populates="o_card")
    market_users = relationship("Marketplace", back_populates="o_card")

    def __init__(self, player_name, age, skill_level, market_value=100):
        self.player_name, self.age, self.skill_level, self.market_value = player_name, age, skill_level, market_value

    def to_json(self):
        return {"id": self.id, "player_name": self.player_name, "age": self.age, "skill_level": self.skill_level,
                "market_value": self.market_value}
