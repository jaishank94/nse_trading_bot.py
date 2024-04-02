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

# Function to implement Mean Reversion strategy
def mean_reversion_strategy(data, window=20, deviation=2):
    try:
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['rolling_mean'] = data['Close'].rolling(window=window).mean()
        signals['upper_band'] = signals['rolling_mean'] + deviation * data['Close'].rolling(window=window).std()
        signals['lower_band'] = signals['rolling_mean'] - deviation * data['Close'].rolling(window=window).std()
        signals['signal'][window:] = np.where(data['Close'][window:] > signals['upper_band'][window:], -1.0, 0.0)
        signals['signal'][window:] = np.where(data['Close'][window:] < signals['lower_band'][window:], 1.0, signals['signal'][window:])
        signals['positions'] = signals['signal'].diff()
        return signals
    except Exception as e:
        print("Error in Mean Reversion strategy:", e)
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
            elif signals['positions'].iloc[-1] == -1:
                # Sell signal
                qty = int(available_balance / signals['Close'].iloc[-1])
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                print("Sell signal detected. Placed order to sell {} shares of {}.".format(qty, symbol))
        elif current_position.side == 'long' and signals['positions'].iloc[-1] == -1:
            # Close long position if sell signal detected
            api.submit_order(
                symbol=symbol,
                qty=int(current_position.qty),
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            print("Sell signal detected. Closing long position.")
        elif current_position.side == 'short' and signals['positions'].iloc[-1] == 1:
            # Close short position if buy signal detected
            api.submit_order(
                symbol=symbol,
                qty=int(current_position.qty),
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            print("Buy signal detected. Closing short position.")
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
                # Implement Mean Reversion strategy
                signals = mean_reversion_strategy(data)
                
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
