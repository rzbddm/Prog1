import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from tkinter import Tk, filedialog

def get_tickers_from_file():
    Tk().withdraw()  # We don't want a full GUI, so keep the root window from appearing
    file_path = filedialog.askopenfilename(title="Select the file with ticker symbols")
    with open(file_path, 'r') as file:
        # Skip the first line (cell A1) and read the rest
        tickers = file.read().splitlines()[1:]
    return tickers

def calculate_ichimoku(data):
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    data['Conversion_Line'] = ((high_9 + low_9) / 2).round(2)
    
    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    data['Base_Line'] = ((high_26 + low_26) / 2).round(2)
    
    data['Span_A'] = ((data['Conversion_Line'] + data['Base_Line']) / 2).shift(26).round(2)
    
    high_52 = data['High'].rolling(window=52).max()
    low_52 = data['Low'].rolling(window=52).min()
    data['Span_B'] = ((high_52 + low_52) / 2).shift(26).round(2)
    
    data['Lagging_Line'] = data['Close'].shift(-26).round(2)
    
    return data

def calculate_macd(data):
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = (ema_12 - ema_26).round(2)
    
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean().round(2)
    
    return data

def calculate_rsi(data, period=13):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data['RSI'] = (100 - (100 / (1 + rs))).round(2)
    return data

def calculate_stochastic(data, period=13):
    low_min = data['Low'].rolling(window=period).min()
    high_max = data['High'].rolling(window=period).max()
    data['Stochastic'] = ((data['Close'] - low_min) / (high_max - low_min) * 100).round(2)
    return data

def download_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    
    try:
        data = stock.history(start=start_date, end=end_date)
        if not data.empty:
            data = data.round(2)
            data['daily_return'] = data['Close'].pct_change().round(2)
            data['cum_return'] = (1 + data['daily_return']).cumprod().round(2)
            data = calculate_ichimoku(data)
            data = calculate_macd(data)
            data = calculate_rsi(data)
            data = calculate_stochastic(data)
        else:
            print(f"No data found for {ticker}.")
            data = pd.DataFrame()
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        data = pd.DataFrame()
    
    return data

def save_data(ticker, data):
    directory = 'tickers'
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, f"{ticker}.csv")

    header = ['Date', 'High', 'Low', 'Open', 'Close', 'Adj Close', 'Volume', 
              'daily_return', 'cum_return', 'Span_A', 'Span_B', 'Lagging_Line', 
              'Conversion_Line', 'Base_Line', 'MACD', 'MACD_Signal', 'RSI', 'Stochastic']

    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        existing_data.index = pd.to_datetime(existing_data.index, utc=True).tz_convert('America/New_York')
        latest_date = existing_data.index.max()
        new_data = data[data.index > latest_date]
        if not new_data.empty:
            combined_data = pd.concat([existing_data, new_data]).drop_duplicates().sort_index()
            combined_data.index = combined_data.index.strftime('%m-%d-%Y')
            combined_data.to_csv(file_path, mode='w', index=True, header=True)
            print(f"Data for {ticker} updated successfully.")
        else:
            print(f"No new data available for {ticker}.")
    else:
        data.index = pd.to_datetime(data.index, utc=True).tz_convert('America/New_York')
        data.index = data.index.strftime('%m-%d-%Y')
        data.to_csv(file_path, mode='w', index=True, header=True)
        print(f"Data for {ticker} saved successfully.")

def main():
    tickers = get_tickers_from_file()
    
    # Ask the user how many days to go back in time
    days_back = int(input("Enter the number of days to go back in time: "))
    
    # Calculate the date
    past_date = datetime.now() - timedelta(days=days_back)
    
    # Display the date
    print(f"The date {days_back} days ago was: {past_date.strftime('%Y-%m-%d')}")
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        data = download_data(ticker, start_date, end_date)
        if not data.empty:
            save_data(ticker, data)
        else:
            print(f"No data downloaded for {ticker}. Check if the ticker symbol is valid or try again later.")

if __name__ == "__main__":
    main()
