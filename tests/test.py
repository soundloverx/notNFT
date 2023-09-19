import json
import unittest
from unittest.mock import patch, Mock, call

from flask import Flask

import backend
from backend import register_user
from exceptions.InvalidBodyException import InvalidBodyException
from models.inventory import Inventory


class EmployeeTests(unittest.TestCase):

    def setUp(self):
        self.mock_user = Mock()
        self.mock_market_entry1 = Mock()
        self.mock_market_entry1.o_card.id = 1
        self.mock_market_entry2 = Mock()
        self.mock_market_entry2.o_card.id = 2
        self.mock_user.market_cards = [self.mock_market_entry1, self.mock_market_entry2]
        self.mock_new_card1 = {"name": "Daniel1", "age": 12, "skill": 1}
        self.mock_new_card2 = {"name": "Daniel2", "age": 22, "skill": 2}
        self.mock_new_card3 = {"name": "Daniel3", "age": 32, "skill": 3}
        self.mock_new_card_set = [self.mock_new_card1, self.mock_new_card2, self.mock_new_card3]
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.mock_transaction = Mock()
        self.mock_transaction.session = Mock()

    def test_employee_data(self):
        with patch("requests.get") as mocked_get:
            random_data = {"country": "ro"}
            mocked_get.return_value.text = json.dumps(random_data)

            self.assertEqual({'country': 'ro'}, backend.json_validation(mocked_get.return_value.text, "country"))

    def test_json_no_country_exceptions(self):
        with patch("requests.get") as mocked_get:
            random_data = {"country": ""}
            mocked_get.return_value.text = json.dumps(random_data)
            with self.assertRaises(InvalidBodyException):
                backend.json_validation(mocked_get.return_value.text, "country")

    def test_json_empty_body_exceptions(self):
        with patch("requests.get") as mocked_get:
            random_data = ""
            with self.assertRaises(InvalidBodyException):
                backend.json_validation(random_data, "country")

    def give_card_to_user(card, user):
        pass

    @patch('backend.load_json_body')
    @patch('backend.new_user_validation')
    @patch('backend.db_session')
    @patch('backend.receive_api_cards')
    @patch('backend.add_new_cards')
    @patch('backend.give_cards_to_new_user')
    def test_successful_registration(self, *params):
        user_details = {
            "username": "test2testtest",
            "email": "test2testtest@yahoo.com",
            "password": "te2st",
            "country": "te2st",
        }
        request_data = json.dumps(user_details)
        with self.app.test_request_context(method='POST', data=request_data, content_type='application/json'):
            response = register_user()
            self.assertEqual(response, user_details)

    @patch('backend.give_card_to_user')
    def test_delete_market_entries(self, mock_give_card):
        backend.delete_market_transaction(self.mock_user, self.mock_transaction)

        mock_give_card.assert_any_call(self.mock_market_entry1.o_card, self.mock_user)
        mock_give_card.assert_any_call(self.mock_market_entry2.o_card, self.mock_user)

        expected_calls = [
            call(self.mock_market_entry1),
            call(self.mock_market_entry2)
        ]
        self.mock_transaction.session.delete.assert_has_calls(expected_calls)

    def test_existing_inventory(self):
        class MockUser:
            def __init__(self, user_id, inventory_cards):
                self.id = user_id
                self.inventory_cards = inventory_cards

        mock_existing_inventory = Inventory(user_id=1, card_id=1)
        mock_user = MockUser(1, [mock_existing_inventory])

        class MockCard:
            def __init__(self, card_id):
                self.id = card_id

        mock_card = MockCard(1)
        backend.give_card_to_user(mock_card, mock_user)
        self.assertEqual(mock_existing_inventory.amount, 2)

    def test_new_inventory(self):
        class MockUser:
            def __init__(self, user_id, inventory_cards):
                self.id = user_id
                self.inventory_cards = inventory_cards

        mock_user = MockUser(1, [])

        class MockCard:
            def __init__(self, card_id):
                self.id = card_id

        mock_card = MockCard(1)

        backend.give_card_to_user(mock_card, mock_user)

        self.assertEqual(len(mock_user.inventory_cards), 1)
        self.assertEqual(mock_user.inventory_cards[0].card_id, 1)
        self.assertEqual(mock_user.inventory_cards[0].amount, 1)


if __name__ == "__main__":
    unittest.main()
