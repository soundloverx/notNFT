from flask import Flask, request

import backend
import db_connector
from models.ledger import Ledger
from models.marketplace import Marketplace
from models.role import Role

Marketplace(0, 0, 0)
Ledger(0, 0, 0, None, 0, None)
db_connector.create_tables()
Role("temp").validate_roles()
app = Flask(__name__)


@app.route('/app/user/register', methods=['POST'])
def register_user():
    return backend.register_user()


def web_auth(function):
    def wrapper(*args, **kwargs):
        if not backend.identify_user(request.headers):
            return {"message": "Failed to authorize"}, 401
        return function(*args, **kwargs)

    return wrapper


@app.route('/app/user/inventory', methods=['GET'], endpoint='get_inventory')
@web_auth
def get_inventory():
    return backend.get_inventory()


@app.route('/app/user/edit', methods=['PATCH'], endpoint='edit_user')
@web_auth
def edit_user():
    return backend.edit_user()


@app.route("/app/admin/toggle_active", methods=['DELETE'], endpoint="toggle_user")
@web_auth
def toggle_user():
    return backend.toggle_user()


@app.route("/app/admin/upgrade_user", methods=['POST'], endpoint="upgrade_user")
@web_auth
def upgrade_user():
    return backend.upgrade_user()


@app.route("/app/marketplace", methods=['POST'], endpoint="add_to_marketplace")
@web_auth
def add_to_marketplace():
    return backend.add_to_marketplace()


@app.route('/app/marketplace', methods=['GET'], endpoint='get_marketplace')
@web_auth
def get_marketplace():
    return backend.get_marketplace()


@app.route("/app/marketplace", methods=['PATCH'], endpoint="buy_from_marketplace")
@web_auth
def buy_from_marketplace():
    return backend.buy_from_marketplace()


@app.route("/app/marketplace", methods=['DELETE'], endpoint="cancel_from_marketplace")
@web_auth
def cancel_from_marketplace():
    return backend.cancel_from_marketplace()


if __name__ == '__main__':
    app.run()
