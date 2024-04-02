import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import alpaca_trade_api as tradeapi
import time

# Alpaca API credentials (replace with your actual credentials)
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
BASE_URL = 'https://paper-api.alpaca.markets'  # For paper trading, replace with live URL for live trading

# Initialize Alpaca API with proper security measures
try:
    api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')
    account = api.get_account()
except Exception as e:
    print("Error:", e)
    exit()

# Function to fetch historical data
def fetch_data(symbol, start_date, end_date):
    try:
        data = yf.download(symbol, start=start_date, end=end_date)
        return data
    except Exception as e:
        print("Error fetching data:", e)
        return None

# Function to calculate price changes
def calculate_price_changes(data, window):
    try:
        return data['Close'].pct_change(window=window).dropna()
    except Exception as e:
        print("Error calculating price changes:", e)
        return None

# Function to identify butterfly effect signals
def butterfly_effect(data, window):
    try:
        price_changes = calculate_price_changes(data, window)
        mean_change = price_changes.mean()
        std_dev_change = price_changes.std()
        z_score = (price_changes.iloc[-1] - mean_change) / std_dev_change
        return z_score
    except Exception as e:
        print("Error identifying butterfly effect signals:", e)
        return None

# Function to execute trades based on signals
def execute_trades(symbol, z_score, available_balance):
    try:
        positions = api.list_positions()
        if z_score > 1.0:  # Buy signal
            if symbol not in [position.symbol for position in positions]:
                qty = int(available_balance / data['Close'].iloc[-1])
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                print("Buy signal for {} at {}. Quantity: {}".format(symbol, datetime.datetime.now(), qty))
        elif z_score < -1.0:  # Sell signal
            if symbol in [position.symbol for position in positions]:
                qty = int(available_balance / data['Close'].iloc[-1])
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                print("Sell signal for {} at {}. Quantity: {}".format(symbol, datetime.datetime.now(), qty))
    except Exception as e:
        print("Error executing trades:", e)

# Main function
def main():
    try:
        symbol = 'AAPL'  # Example symbol
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2024, 1, 1)
        window = 10  # Window for calculating price changes
        
        while True:
            # Fetch account information to get available balance
            try:
                account = api.get_account()
                available_balance = float(account.buying_power)
            except Exception as e:
                print("Error fetching account information:", e)
                exit()

            # Fetch historical data
            data = fetch_data(symbol, start_date, end_date)
            
            if data is not None:
                # Identify butterfly effect signals
                z_score = butterfly_effect(data, window)
                
                if z_score is not None:
                    # Execute trades
                    execute_trades(symbol, z_score, available_balance)
                
            # Sleep for some time before fetching data again
            time.sleep(60)  # Sleep for 60 seconds before fetching data again
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
