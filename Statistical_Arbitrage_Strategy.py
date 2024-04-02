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
def fetch_data(symbol1, symbol2, start_date, end_date):
    try:
        data1 = yf.download(symbol1, start=start_date, end=end_date)
        data2 = yf.download(symbol2, start=start_date, end=end_date)
        return data1, data2
    except Exception as e:
        print("Error fetching data:", e)
        return None, None

# Function to calculate spread between two assets
def calculate_spread(data1, data2):
    try:
        spread = data1['Close'] - data2['Close']
        return spread
    except Exception as e:
        print("Error calculating spread:", e)
        return None

# Function to calculate historical mean and standard deviation of spread
def calculate_stats(spread):
    try:
        mean = spread.mean()
        std_dev = spread.std()
        return mean, std_dev
    except Exception as e:
        print("Error calculating stats:", e)
        return None, None

# Function to execute trades based on spread signals
def execute_trades(data1, data2, symbol1, symbol2, available_balance):
    try:
        spread = calculate_spread(data1, data2)
        mean, std_dev = calculate_stats(spread)
        
        if mean is not None and std_dev is not None:
            current_spread = spread.iloc[-1]
            z_score = (current_spread - mean) / std_dev
            
            if z_score > 1.0:
                # Buy signal
                qty1 = int(available_balance / data1['Close'].iloc[-1])
                qty2 = int(available_balance / data2['Close'].iloc[-1])
                api.submit_order(
                    symbol=symbol1,
                    qty=qty1,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                api.submit_order(
                    symbol=symbol2,
                    qty=qty2,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                print("Buy signal detected. Placed order to buy {} shares of {} and sell {} shares of {}.".format(qty1, symbol1, qty2, symbol2))
            elif z_score < -1.0:
                # Sell signal
                qty1 = int(available_balance / data1['Close'].iloc[-1])
                qty2 = int(available_balance / data2['Close'].iloc[-1])
                api.submit_order(
                    symbol=symbol1,
                    qty=qty1,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                api.submit_order(
                    symbol=symbol2,
                    qty=qty2,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                print("Sell signal detected. Placed order to sell {} shares of {} and buy {} shares of {}.".format(qty1, symbol1, qty2, symbol2))
    except Exception as e:
        print("Error executing trades:", e)

# Main function
def main():
    try:
        symbol1 = 'AAPL'  # Example symbol 1 (AAPL)
        symbol2 = 'MSFT'  # Example symbol 2 (MSFT)
        start_date = datetime.datetime.now() - datetime.timedelta(days=365)  # 1 year historical data
        end_date = datetime.datetime.now()
        risk_per_trade = 0.01  # Risk per trade as a fraction of available balance
        
        while True:
            # Fetch account information to get available balance
            try:
                account = api.get_account()
                available_balance = float(account.buying_power)
            except Exception as e:
                print("Error fetching account information:", e)
                exit()

            # Fetch historical data for both symbols
            data1, data2 = fetch_data(symbol1, symbol2, start_date, end_date)
            
            if data1 is not None and data2 is not None:
                # Execute trades based on spread signals
                execute_trades(data1, data2, symbol1, symbol2, available_balance * risk_per_trade)
                
            # Sleep for some time before fetching data again
            time.sleep(60)  # Sleep for 60 seconds before fetching data again
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
