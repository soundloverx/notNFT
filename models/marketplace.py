import datetime

from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship

from db_connector import Base
from models.card import Card
from models.user import User


class Marketplace(Base):
    __tablename__ = 'marketplace'
    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey(User.id), nullable=False)
    card_id = Column(Integer, ForeignKey(Card.id), nullable=False)
    asking_price = Column('asking_price', Integer, nullable=False)
    date_added = Column('date_added', TIMESTAMP, nullable=False)
    o_user = relationship("User", back_populates="market_cards")
    o_card = relationship("Card", back_populates="market_users")

    def __init__(self, seller_id, card_id, price, date=datetime.datetime.utcnow()):
        self.seller_id, self.card_id, self.asking_price, self.date_added = seller_id, card_id, price, date

    def to_json(self):
        return {"seller_id": self.seller_id, "card_id": self.card_id, "asking_price": self.asking_price,
                "date_added": self.date_added}
