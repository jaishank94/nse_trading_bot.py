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

# Function to implement a simple moving average crossover strategy
def moving_average_crossover(data, short_window=50, long_window=200):
    try:
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['short_mavg'] = data['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
        signals['long_mavg'] = data['Close'].rolling(window=long_window, min_periods=1, center=False).mean()
        signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] 
                                                    > signals['long_mavg'][short_window:], 1.0, 0.0)
        signals['positions'] = signals['signal'].diff()
        return signals
    except Exception as e:
        print("Error in moving average crossover strategy:", e)
        return None

# Function to execute trades based on signals
def execute_trades(signals, banknifty, nifty50, available_balance):
    try:
        banknifty_positions = 0
        nifty50_positions = 0
        banknifty_trade_size = 0
        nifty50_trade_size = 0
        banknifty_entry_price = 0
        nifty50_entry_price = 0
        banknifty_pnl = 0
        nifty50_pnl = 0
        banknifty_data = banknifty['Close']
        nifty50_data = nifty50['Close']
        
        for index, signal in signals.iterrows():
            if signal['positions'] == 1:
                # Execute buy orders for BankNIFTY and NIFTY50
                banknifty_positions += 1
                nifty50_positions += 1
                
                # Calculate trade size based on available balance and risk per trade
                banknifty_trade_size = available_balance / banknifty_data[index]
                nifty50_trade_size = available_balance / nifty50_data[index]
                
                banknifty_entry_price = banknifty_data[index]
                nifty50_entry_price = nifty50_data[index]
                
                # Place buy orders using Alpaca API
                api.submit_order(
                    symbol='BANKNIFTY',  # Example symbol for BankNIFTY
                    qty=banknifty_trade_size,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                api.submit_order(
                    symbol='NIFTY50',  # Example symbol for NIFTY50
                    qty=nifty50_trade_size,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                
                print("Buy signal for BankNIFTY and NIFTY50 at {}".format(index))
                print("BankNIFTY Trade Size: {}, Entry Price: {}".format(banknifty_trade_size, banknifty_entry_price))
                print("NIFTY50 Trade Size: {}, Entry Price: {}".format(nifty50_trade_size, nifty50_entry_price))
                
            elif signal['positions'] == -1:
                # Execute sell orders for BankNIFTY and NIFTY50
                banknifty_pnl += (banknifty_data[index] - banknifty_entry_price) * banknifty_trade_size
                nifty50_pnl += (nifty50_data[index] - nifty50_entry_price) * nifty50_trade_size
                
                banknifty_positions -= 1
                nifty50_positions -= 1
                
                # Place sell orders using Alpaca API
                api.submit_order(
                    symbol='BANKNIFTY',  # Example symbol for BankNIFTY
                    qty=banknifty_trade_size,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                api.submit_order(
                    symbol='NIFTY50',  # Example symbol for NIFTY50
                    qty=nifty50_trade_size,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                
                print("Sell signal for BankNIFTY and NIFTY50 at {}".format(index))
                print("BankNIFTY P&L: {}, NIFTY50 P&L: {}".format(banknifty_pnl, nifty50_pnl))
    except Exception as e:
        print("Error executing trades:", e)

# Main function
def main():
    try:
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2024, 1, 1)
        risk_per_trade = 0.05  # Example risk per trade as a fraction of available balance
        
        while True:
            # Fetch account information to get available balance
            try:
                account = api.get_account()
                available_balance = float(account.buying_power)
            except Exception as e:
                print("Error fetching account information:", e)
                exit()

            # Fetch historical data for BankNIFTY and NIFTY50
            banknifty_data = fetch_data('^NSEBANK', start_date, end_date)
            nifty50_data = fetch_data('^NSEI', start_date, end_date)
            
            if banknifty_data is not None and nifty50_data is not None:
                # Implement trading strategy
                banknifty_signals = moving_average_crossover(banknifty_data)
                nifty50_signals = moving_average_crossover(nifty50_data)
                
                if banknifty_signals is not None and nifty50_signals is not None:
                    # Execute trades
                    execute_trades(banknifty_signals, banknifty_data, nifty50_data, available_balance * risk_per_trade)
                
            # Sleep for some time before fetching data again
            time.sleep(60)  # Sleep for 60 seconds before fetching data again
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
