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

# Function to execute arbitrage trades based on signals
def execute_arbitrage_trades(data1, data2, symbol1, symbol2, available_balance):
    try:
        price1 = data1['Close'].iloc[-1]
        price2 = data2['Close'].iloc[-1]
        
        # Calculate position size based on available balance
        position_size = min(price1, price2) * available_balance
        
        if price1 > price2:
            # Buy symbol2 and sell symbol1
            api.submit_order(
                symbol=symbol1,
                qty=int(position_size / price1),
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            api.submit_order(
                symbol=symbol2,
                qty=int(position_size / price2),
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            print("Arbitrage opportunity detected. Placed order to sell {} shares of {} and buy {} shares of {}.".format(
                int(position_size / price1), symbol1, int(position_size / price2), symbol2))
        elif price1 < price2:
            # Buy symbol1 and sell symbol2
            api.submit_order(
                symbol=symbol1,
                qty=int(position_size / price1),
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            api.submit_order(
                symbol=symbol2,
                qty=int(position_size / price2),
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            print("Arbitrage opportunity detected. Placed order to buy {} shares of {} and sell {} shares of {}.".format(
                int(position_size / price1), symbol1, int(position_size / price2), symbol2))
    except Exception as e:
        print("Error executing arbitrage trades:", e)

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
            data1 = fetch_data(symbol1, start_date, end_date)
            data2 = fetch_data(symbol2, start_date, end_date)
            
            if data1 is not None and data2 is not None:
                # Execute arbitrage trades
                execute_arbitrage_trades(data1, data2, symbol1, symbol2, available_balance * risk_per_trade)
                
            # Sleep for some time before fetching data again
            time.sleep(60)  # Sleep for 60 seconds before fetching data again
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
