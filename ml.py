import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

import db_connector
from models import card


def recalculate_card_values_linear_regression():
    ledger_data = pd.read_sql('SELECT card_id, asking_price FROM ledger', db_connector.engine)

    card_mean_prices = ledger_data.groupby('card_id')['asking_price'].mean()
    ledger_data = ledger_data.merge(card_mean_prices, on='card_id', suffixes=('', '_mean'))

    x = ledger_data[['card_id']]
    y = ledger_data['asking_price_mean']

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.15, random_state=50)

    model = LinearRegression()
    model.fit(x_train, y_train)

    with db_connector.db_session.begin_nested() as transaction:
        for c in transaction.session.query(card.Card).all():
            c.market_value = round(model.predict(pd.DataFrame({'card_id': [c.id]}))[0])


def recalculate_card_values_simple():
    ledger_data = pd.read_sql('SELECT card_id, asking_price FROM ledger', db_connector.engine)
    card_statistics = ledger_data.groupby('card_id')['asking_price'].agg(['mean', 'median']).reset_index()

    with db_connector.db_session.begin_nested() as transaction:
        for c in transaction.session.query(card.Card).all():
            card_info = card_statistics.loc[card_statistics['card_id'] == c.id]
            if not card_info.empty:
                c.market_value = round(card_info['mean'].values[0])
