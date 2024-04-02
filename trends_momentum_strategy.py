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

# Function to implement Trends and Momentum Following strategy
def trends_momentum_strategy(data, short_window=50, long_window=200):
    try:
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['short_mavg'] = data['Close'].rolling(window=short_window, min_periods=1).mean()
        signals['long_mavg'] = data['Close'].rolling(window=long_window, min_periods=1).mean()
        signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)
        signals['positions'] = signals['signal'].diff()
        return signals
    except Exception as e:
        print("Error in Trends and Momentum Following strategy:", e)
        return None

# Function to execute trades based on signals
def execute_trades(signals, symbol, available_balance):
    try:
        positions = api.list_positions()
        current_position = next((position for position in positions if position.symbol == symbol), None)
        
        if current_position is None:
            # No current position, place a new trade based on the signal
            if signals['positions'].iloc[-1] == 1:
                # Buy signal
                qty = int(available_balance / signals['Close'].iloc[-1])
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                print("Buy signal detected. Placed order to buy {} shares of {}.".format(qty, symbol))
        elif current_position.side == 'long' and signals['positions'].iloc[-1] == 0:
            # Close long position if no buy signal detected
            api.submit_order(
                symbol=symbol,
                qty=int(current_position.qty),
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            print("No buy signal detected. Closing long position.")
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
                # Implement Trends and Momentum Following strategy
                signals = trends_momentum_strategy(data)
                
                if signals is not None:
                    # Execute trades
                    execute_trades(signals, symbol, available_balance * risk_per_trade)
                
            # Sleep for some time before fetching data again
            time.sleep(60)  # Sleep for 60 seconds before fetching data again
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
