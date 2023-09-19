import datetime
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from db_connector import Base
from models.card import Card
from models.user import User


class Ledger(Base):
    __tablename__ = 'ledger'
    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey(User.id), nullable=False)
    card_id = Column(Integer, ForeignKey(Card.id), nullable=False)
    asking_price = Column('asking_price', Integer, nullable=False)
    date_added = Column('date_added', TIMESTAMP, nullable=False)
    buyer_id = Column(Integer, ForeignKey(User.id), nullable=False)
    purchase_date = Column('purchase_date', TIMESTAMP, nullable=False)

    def __init__(self, seller_id, card_id, asking_price, date_added, buyer_id, purchase_date):
        self.seller_id, self.card_id, self.asking_price = seller_id, card_id, asking_price
        self.date_added, self.buyer_id, self.purchase_date = date_added, buyer_id, purchase_date
