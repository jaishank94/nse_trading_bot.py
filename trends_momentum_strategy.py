import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import alpaca_trade_api as tradeapi
import time

# Alpaca API credentials (replace with your actual credentials)
API_KEY = 'PK3MF7TXZKJHVAD097IP'
API_SECRET = 'OWuQ2FSZc39IK2VnNstNq3uDkFHof4nTXXXnuS0D'
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
        if 'Close' not in data.columns:
            raise ValueError("Close column not found in the fetched data.")
        return data
    except Exception as e:
        print("Error fetching data:", e)
        return None

# Function to implement Enhanced Trends and Momentum Following strategy
def enhanced_trends_momentum_strategy(data, short_window_range=(20, 60), long_window_range=(100, 300), threshold=0.05):
    try:
        best_short_window = None
        best_long_window = None
        best_performance = -float('inf')

        # Parameter Optimization
        for short_window in range(short_window_range[0], short_window_range[1] + 1, 5):
            for long_window in range(long_window_range[0], long_window_range[1] + 1, 10):
                signals = pd.DataFrame(index=data.index)
                signals['signal'] = 0.0
                signals['Close'] = data['Close']
                signals['short_mavg'] = data['Close'].rolling(window=short_window, min_periods=1).mean()
                signals['long_mavg'] = data['Close'].rolling(window=long_window, min_periods=1).mean()
                signals['signal'].iloc[short_window:] = np.where(
                    signals['short_mavg'].iloc[short_window:] > signals['long_mavg'].iloc[short_window:] * (1 + threshold), 1.0,
                    np.where(signals['short_mavg'].iloc[short_window:] < signals['long_mavg'].iloc[short_window:] * (1 - threshold), -1.0, 0.0)
                )
                signals['positions'] = np.where(signals['signal'] > 0, 1, np.where(signals['signal'] < 0, -1, 0))
                
                # Backtesting
                if signals['positions'].sum() > best_performance:
                    best_performance = signals['positions'].sum()
                    best_short_window = short_window
                    best_long_window = long_window
        
        # Generate signals using best parameters
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0.0
        signals['Close'] = data['Close']
        signals['short_mavg'] = data['Close'].rolling(window=best_short_window, min_periods=1).mean()
        signals['long_mavg'] = data['Close'].rolling(window=best_long_window, min_periods=1).mean()
        signals['signal'].iloc[best_short_window:] = np.where(
            signals['short_mavg'].iloc[best_short_window:] > signals['long_mavg'].iloc[best_short_window:] * (1 + threshold), 1.0,
            np.where(signals['short_mavg'].iloc[best_short_window:] < signals['long_mavg'].iloc[best_short_window:] * (1 - threshold), -1.0, 0.0)
        )
        signals['positions'] = np.where(signals['signal'] > 0, 1, np.where(signals['signal'] < 0, -1, 0))
        
        return signals, best_short_window, best_long_window
    except Exception as e:
        print("Error in Enhanced Trends and Momentum Following strategy:", e)
        return None, None, None


# Function to execute trades based on signals
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
                # Short signal
                qty = int(available_balance / signals['Close'].iloc[-1])
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                print("Short signal detected. Placed order to sell {} shares of {}.".format(qty, symbol))
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
        elif current_position.side == 'short' and signals['positions'].iloc[-1] == 0:
            # Close short position if no short signal detected
            api.submit_order(
                symbol=symbol,
                qty=int(abs(float(current_position.qty))),
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            print("No short signal detected. Closing short position.")
    except Exception as e:
        print("Error executing trades:", e)



# Main function
def main():
    try:
        symbol = 'AAPL'  # Example symbol (AAPL)
        start_date = datetime.datetime.now() - datetime.timedelta(days=365)  # 1 year historical data
        end_date = datetime.datetime.now()
        risk_per_trade = 0.01  # Risk per trade as a fraction of available balance
        threshold = 0.00005  # Change this threshold as needed
        
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
                # Implement Enhanced Trends and Momentum Following strategy
                signals, best_short_window, best_long_window = enhanced_trends_momentum_strategy(data, threshold=threshold)
                print("Best short window:", best_short_window)
                print("Best long window:", best_long_window, symbol, available_balance, risk_per_trade)
              
                
                if signals is not None:
                    # Execute trades
                    execute_trades(signals, symbol, available_balance * risk_per_trade)
                
            # Sleep for some time before fetching data again
            time.sleep(20)  # Sleep for 60 seconds before fetching data again
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
