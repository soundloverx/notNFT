import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# Load your historical sales data into a DataFrame
data = pd.read_csv('d:/Downloads/ledger.csv')  # Replace with your data source

# Perform data preprocessing and feature engineering here

# Split the data into training and testing sets
X = data[['card_id', 'asking_price']]
y = data['asking_price']  # Target variable
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train a Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = model.predict(X_test)

cards_features = []
for i in range(1, 3):
    cards_features.append({'card_id': i})

cards_data = pd.DataFrame(cards_features)

print("Predicted prices for all cards : ", model.predict(cards_data))

# Evaluate the model's performance
# mse = mean_squared_error(y_test, y_pred)
# print(f'Mean Squared Error: {mse}')

# Now you can use the trained model to make predictions on future data
