import hashlib
import json
import datetime

import requests
from flask import request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import ml
from db_connector import db_session
from exceptions.IncorrectJsonFormatException import IncorrectJsonFormatException
from exceptions.InvalidBodyException import InvalidBodyException
from exceptions.MissingCardException import MissingCardException
from exceptions.NoPermissionException import NoPermissionException
from exceptions.UnavailableEmailException import UnavailableEmailException
from exceptions.UnavailableNameException import UnavailableNameException
from exceptions.MarketTransactionException import MarketTransactionException
from exceptions.UserNotFoundException import UserNotFoundException
from models import user
from models.card import Card
from models.inventory import Inventory
from models.ledger import Ledger
from models.marketplace import Marketplace
from models.role import Role
from third_party_api import receive_api_cards


def after(func_to_run_after):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            func_to_run_after()
            return result
        return wrapper
    return decorator


def new_user_validation(user_details):
    if user_details.get("username") is None or user_details.get("email") is None \
            or user_details.get("password") is None or user_details.get("country") is None:
        raise IncorrectJsonFormatException
    with db_session.begin_nested() as transaction:
        check_by_name = transaction.session.query(user.User).filter(
            user.User.username == user_details.get("username")).first()
        check_by_email = transaction.session.query(user.User).filter(
            user.User.email == user_details.get("email")).first()
    if check_by_name:
        raise UnavailableNameException("Unavailable username")
    if check_by_email:
        raise UnavailableEmailException("Unavailable email")


def add_new_cards(transaction, cards):
    for card in cards:
        existing_card = transaction.session.query(Card).filter(Card.player_name == card.get("name")).first()
        if not existing_card:
            transaction.session.add(Card(card.get("name"), card.get("age"), card.get("skill")))


def give_card_to_user(card, user):
    existing_inventory = next(
        (inventory_card for inventory_card in user.inventory_cards if inventory_card.card_id == card.id), None)
    if existing_inventory:
        existing_inventory.increment_amount()
    else:
        user.inventory_cards.append(Inventory(user.id, card.id))


def give_cards_to_new_user(transaction, cards, new_user):
    for card in cards:
        existing_card = transaction.session.query(Card).filter(Card.player_name == card.get("name")).first()
        give_card_to_user(existing_card, new_user)


def register_user():
    user_details = load_json_body()
    try:
        new_user_validation(user_details)
    except (UnavailableNameException, UnavailableEmailException) as ex:
        return '{"message": "' + str(ex) + '"}', 403
    except IncorrectJsonFormatException:
        return '{"message": "Incorrect json format"}', 400
    except Exception as unexpected:
        return '{"message": "' + str(unexpected) + '"}', 500

    with db_session.begin_nested() as transaction:
        try:
            new_user = user.User(user_details.get("username"), user_details.get("email"),
                                 hashlib.md5(user_details.get("password").encode('utf-8')).hexdigest(),
                                 user_details.get("country"))
            transaction.session.add(new_user)
            cards = receive_api_cards()
            add_new_cards(transaction, cards)
            give_cards_to_new_user(transaction, cards, new_user)
        except (IntegrityError, requests.exceptions.ConnectionError) as ex:
            transaction.rollback()
            return '{"message": "' + str(ex) + '"}', 400
    return request.data


def identify_user(headers):
    return db_session.query(user.User).filter(user.User.username == headers.get("username", "")) \
        .filter(user.User.password == hashlib.md5(headers.get("password", "").encode('utf-8')).hexdigest()) \
        .filter(user.User.active == 1).first()


def get_inventory():
    me = identify_user(request.headers)
    inventory = db_session.query(Inventory).filter(Inventory.user_id == me.id).all()
    collection_value = sum([inv.o_card.market_value * inv.amount for inv in inventory])
    return {"user": me.to_json(), "inventory": [inv.to_json() for inv in inventory],
            "collection_value": collection_value}, 200


def edit_user():
    data = request.data.decode('utf-8')
    country_info = json_validation(data, "country")
    me = identify_user(request.headers)
    with db_session.begin_nested():
        me.set_country(country_info.get("country"))
    return {"user": me.to_json()}, 200


def json_validation(data, json_field):
    if len(data) == 0:
        raise InvalidBodyException("the Json body is empty")
    if len(json.loads(data).get(json_field)) == 0:
        raise InvalidBodyException("There is no country in edit field")
    country_info = json.loads(data)
    print(country_info)
    return country_info


def toggle_user():
    user_id = request.args.get("id")
    me = identify_user(request.headers)
    if me.role_id == 2:
        raise NoPermissionException("You don't have the right")
    with db_session.begin_nested() as transaction:
        try:
            existing_user = transaction.session.query(user.User).filter(user.User.id == user_id).first()
            if existing_user and existing_user.id != me.id:
                active = update_active_status(existing_user, transaction)
            else:
                raise UserNotFoundException("User not available")
        except (SQLAlchemyError, UserNotFoundException) as error:
            transaction.rollback()
            return {"message": str(error)}, 500
    return {"user": existing_user.to_json().get("username"), "active": active}, 200


def update_active_status(existing_user, transaction):
    if existing_user.active == 1:
        delete_market_transaction(existing_user, transaction)
    existing_user.set_active(1 - existing_user.active)
    active = existing_user.active
    return active


def delete_market_transaction(existing_user, transaction):
    for market_entry in existing_user.market_cards:
        give_card_to_user(market_entry.o_card, existing_user)
        transaction.session.delete(market_entry)


def upgrade_user():
    user_id = request.args.get("id")
    me = identify_user(request.headers)
    if me.role_id == 2:
        raise NoPermissionException("You don't have the right")
    with db_session.begin_nested() as transaction:
        try:
            existing_user = db_session.query(user.User).filter(user.User.id == user_id).first()
            if existing_user and existing_user.id != me.id and existing_user.active != 0:
                upgrade_role_budget(existing_user)
            else:
                raise UserNotFoundException("User not available")

        except (SQLAlchemyError, InvalidBodyException, UserNotFoundException) as error:
            transaction.rollback()
            return {"message": str(error)}, 500
        return {"Updated user:": existing_user.to_json().get("username")}, 200
    return {"message": "User not available"}, 400


def upgrade_role_budget(existing_user):
    details = load_json_body()
    existing_role = db_session.query(Role).filter(Role.id == details.get("role_id", -1)).first()
    if existing_role:
        existing_user.set_role(existing_role.id)
    if details.get("budget"):
        existing_user.set_budget(details.get("budget"))
    return existing_user


def add_to_marketplace():
    me = identify_user(request.headers)
    with db_session.begin_nested() as transaction:
        try:
            details = load_json_body()
            card_id = details.get("card_id")
            if not card_id or not details.get("asking_price"):
                raise IncorrectJsonFormatException("Incomplete JSON: must contain both role_id and asking_price.")
            existing_card = next((card for card in me.inventory_cards if card.card_id == card_id), None)
            if not existing_card:
                raise MissingCardException("You do not own card_id " + str(card_id))
            market_entry = Marketplace(me.id, card_id, details.get("asking_price"))
            transaction.session.add(market_entry)
            existing_card.decrement_amount()
            if existing_card.amount == 0:
                transaction.session.delete(existing_card)
            return market_entry.to_json(), 200
        except (SQLAlchemyError, InvalidBodyException, IncorrectJsonFormatException, MissingCardException) as error:
            transaction.rollback()
            return {"message": str(error)}, 500


def load_json_body():
    data = request.data.decode('utf-8')
    if len(data) == 0:
        raise InvalidBodyException("The Json body is empty")
    details = json.loads(data)
    return details


def get_marketplace():
    output = []
    with db_session.begin_nested() as transaction:
        market = transaction.session.query(Marketplace).all()
        for entry in market:
            output.append(
                {"seller": entry.o_user.username, "card": entry.o_card.to_json(), "asking_price": entry.asking_price,
                 "date_added": entry.date_added, "id": entry.id})
    return output, 200


@after(ml.recalculate_card_values_linear_regression)
def buy_from_marketplace():
    market_id = request.args.get("id")
    me = identify_user(request.headers)
    with db_session.begin_nested() as transaction:
        try:
            market_record = transaction.session.query(Marketplace).filter(Marketplace.id == market_id).first()
            buy_from_market_validation(market_record, me)
            update_budget(market_record, me)
            give_card_to_user(market_record.o_card, me)
            transaction.session.add(Ledger(market_record.seller_id, market_record.card_id, market_record.asking_price,
                                           market_record.date_added, me.id, datetime.datetime.utcnow()))
            transaction.session.delete(market_record)
            return {"message": "Purchase successful", "seller": market_record.o_user.username,
                    "card": market_record.o_card.to_json(), "asking_price": market_record.asking_price,
                    "date_added": market_record.date_added, "id": market_record.id}, 200
        except (SQLAlchemyError, MarketTransactionException) as error:
            transaction.rollback()
            return {"message": str(error)}, 500


def buy_from_market_validation(market_record, me):
    if not market_record:
        raise MarketTransactionException("Market entry doesn't exist")
    if me.budget < market_record.asking_price:
        raise MarketTransactionException("Stop being poor")
    if me.id == market_record.seller_id:
        raise MarketTransactionException("You are not allowed to buy your own card. You can cancel the sell.")


def update_budget(market_record, me):
    market_record.o_user.budget += market_record.asking_price
    me.budget -= market_record.asking_price


def cancel_from_marketplace():
    market_id = request.args.get("id")
    me = identify_user(request.headers)
    with db_session.begin_nested() as transaction:
        try:
            market_record = transaction.session.query(Marketplace).filter(Marketplace.id == market_id).first()
            cancel_from_market_validation(market_record, me)
            give_card_to_user(market_record.o_card, me)
            transaction.session.delete(market_record)
            return {"message": "Market entry cancelled"}, 200
        except (SQLAlchemyError, MarketTransactionException) as error:
            transaction.rollback()
            return {"message": str(error)}, 500


def cancel_from_market_validation(market_record, user):
    if not market_record:
        raise MarketTransactionException("Market entry doesn't exist anymore")
    if user.id != market_record.seller_id:
        raise MarketTransactionException("Not your entry to cancel")
