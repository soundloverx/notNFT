import sqlalchemy
from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from db_connector import Base


class Inventory(Base):
    __tablename__ = 'inventory'
    user_id = Column("user_id", Integer, sqlalchemy.ForeignKey("users.id"), primary_key=True)
    card_id = Column("card_id", Integer, sqlalchemy.ForeignKey("cards.id"), primary_key=True)
    amount = Column(Integer, nullable=False)
    o_user = relationship("User", back_populates="inventory_cards")
    o_card = relationship("Card", back_populates="inventory_users")

    def __init__(self, user_id, card_id, amount=1):
        self.user_id, self.card_id, self.amount = user_id, card_id, amount

    def increment_amount(self):
        self.amount = self.amount + 1

    def decrement_amount(self):
        self.amount = self.amount - 1

    def to_json(self):
        my_json = {"amount": self.amount}
        my_json.update(self.o_card.to_json())
        return my_json
