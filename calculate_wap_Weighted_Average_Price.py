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

# Function to calculate Weighted Average Price (WAP)
def calculate_wap(data):
    try:
        wap = (data['Close'] * data['Volume']).sum() / data['Volume'].sum()
        return wap
    except Exception as e:
        print("Error calculating WAP:", e)
        return None

# Function to execute trades based on WAP signals
def execute_trades(data, symbol, available_balance):
    try:
        current_price = data['Close'].iloc[-1]
        wap = calculate_wap(data)
        
        if wap is not None:
            if current_price > wap:
                # Buy signal
                qty = int(available_balance / current_price)
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                print("Buy signal detected. Placed order to buy {} shares of {}.".format(qty, symbol))
            elif current_price < wap:
                # Sell signal
                qty = int(available_balance / current_price)
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                print("Sell signal detected. Placed order to sell {} shares of {}.".format(qty, symbol))
    except Exception as e:
        print("Error executing trades:", e)

# Main function
def main():
    try:
        symbol = 'AAPL'  # Example symbol (AAPL)
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

            # Fetch historical data
            data = fetch_data(symbol, start_date, end_date)
            
            if data is not None:
                # Execute trades based on WAP signals
                execute_trades(data, symbol, available_balance * risk_per_trade)
                
            # Sleep for some time before fetching data again
            time.sleep(60)  # Sleep for 60 seconds before fetching data again
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
