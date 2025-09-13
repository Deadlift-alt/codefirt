# codefirt/main.py

import yaml
import fyers_client
import time
from datetime import datetime, timedelta
import os
from collections import deque
import display
import trader
import codefirt.utils as utils
from playsound import playsound

# --- Constants ---
MAX_DATA_POINTS = 180
TIME_INTERVALS = {
    "3m": 3, "5m": 5, "10m": 10, "15m": 15, "30m": 30, "3hr": 180
}
COLOR_RULES = {
    "3m": 10, "5m": 12, "10m": 15, "30m": 30, "3hr": 100
}
ALERT_THRESHOLD = 0.30

# --- Data Store ---
data_store = {}

def load_config(filepath="codefirt/Survivor.yml"):
    with open(filepath, 'r') as file:
        return yaml.safe_load(file)['default']

def update_data_store(symbol, value):
    if symbol not in data_store:
        data_store[symbol] = deque(maxlen=MAX_DATA_POINTS)
    data_store[symbol].append((datetime.now(), value))

def get_historical_value(symbol, minutes_ago):
    if symbol not in data_store or not data_store[symbol]:
        return None
    target_time = datetime.now() - timedelta(minutes=minutes_ago)
    closest_point = min(data_store[symbol], key=lambda x: abs(x[0] - target_time))
    if abs((closest_point[0] - target_time).total_seconds()) < 70:
        return closest_point[1]
    return None

def calculate_change(current_value, historical_value):
    if current_value is None or historical_value is None or historical_value == 0:
        return "N/A", 0.0, 0.0
    absolute_change = current_value - historical_value
    percentage_change = (absolute_change / historical_value) * 100
    formatted_string = f"{percentage_change:+.2f}% ({absolute_change:,.0f})"
    return formatted_string, percentage_change, absolute_change

def get_nifty_price(fyers, symbol):
    data = {"symbols": symbol}
    try:
        response = fyers.quotes(data=data)
        if response.get('s') == 'ok':
            return response['d'][0]['v']['lp']
        else:
            print(f"API Error fetching NIFTY price: {response.get('message')}")
            return None
    except Exception as e:
        print(f"Exception fetching NIFTY price for {symbol}: {e}")
        return None

def get_oi_data(fyers, symbol):
    # The 'depth' endpoint provides OI data. Alternatively, the 'quotes' endpoint
    # can also be used and may be more performant for multiple symbols.
    data = {"symbol": symbol, "ohlcv_flag": "1"}
    try:
        response = fyers.depth(data=data)
        if response.get('s') == 'ok' and symbol in response.get('d', {}):
            return response['d'][symbol].get('open_interest', 0)
        else:
            # This can happen if the option symbol is incorrect or not trading.
            # print(f"API Error fetching OI for {symbol}: {response.get('message')}")
            return None
    except Exception as e:
        print(f"Exception fetching OI for {symbol}: {e}")
        return None

def get_atm_strike(nifty_price):
    return round(nifty_price / 50) * 50

def process_data_for_display(fyers, config):
    nifty_symbol = config.get('index_symbol', 'NSE:NIFTY50-INDEX')
    nifty_price = get_nifty_price(fyers, nifty_symbol)

    if not nifty_price:
        return None, None, None

    update_data_store(nifty_symbol, nifty_price)

    atm_strike = get_atm_strike(nifty_price)
    strikes = [atm_strike + i * 50 for i in range(-2, 3)]

    nifty_display_data = {"price": f"{nifty_price:,.2f}"}
    call_display_data = {s: {} for s in strikes}
    put_display_data = {s: {} for s in strikes}

    for key, minutes in TIME_INTERVALS.items():
        hist_price = get_historical_value(nifty_symbol, minutes)
        nifty_display_data[f"change_{key}"] = calculate_change(nifty_price, hist_price)

    for strike in strikes:
        for opt_type in ["CE", "PE"]:
            symbol = utils.get_option_symbol(config, strike, opt_type)
            oi = get_oi_data(fyers, symbol)

            if oi is not None:
                update_data_store(symbol, oi)
                display_data = call_display_data if opt_type == "CE" else put_display_data
                display_data[strike]["oi"] = f"{oi:,}"

                for key, minutes in TIME_INTERVALS.items():
                    hist_oi = get_historical_value(symbol, minutes)
                    display_data[strike][f"change_{key}"] = calculate_change(oi, hist_oi)

    return nifty_display_data, call_display_data, put_display_data

def main():
    print("Starting the live OI data fetcher...")
    try:
        config = load_config()
    except FileNotFoundError:
        print("ERROR: codefirt/Survivor.yml not found.")
        return
    except Exception as e:
        print(f"ERROR: Could not load or parse Survivor.yml: {e}")
        return

    try:
        access_token = fyers_client.get_access_token()
        if not access_token: return
        fyers = fyers_client.initialize_fyers_model(access_token)
        profile = fyers.get_profile()
        if profile.get('s') == 'error':
            print(f"Login failed. Please check credentials and token generation. Error: {profile.get('message')}")
            return
        print("Fyers client initialized successfully.")
    except Exception as e:
        print(f"ERROR: Fyers client initialization failed: {e}")
        return

    while True:
        try:
            nifty_data, call_data, put_data = process_data_for_display(fyers, config)

            if nifty_data:
                call_red_cells, put_red_cells = display.render_tables(nifty_data, call_data, put_data, COLOR_RULES)

                total_cells = len(call_data) * len(TIME_INTERVALS)
                if total_cells > 0 and ((call_red_cells / total_cells > ALERT_THRESHOLD) or (put_red_cells / total_cells > ALERT_THRESHOLD)):
                    print("ALERT: Significant OI change detected!")
                    try:
                        playsound('codefirt/alert.wav')
                    except Exception as e:
                        print(f"Could not play sound alert: {e}")

                trader.check_and_execute_trades(fyers, nifty_data, call_data, put_data, config)

            time.sleep(60)
        except KeyboardInterrupt:
            print("\nApplication stopped by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    if fyers_client.CLIENT_ID:
        main()
    else:
        print("Please fill in your Fyers API credentials in 'codefirt/fyers_client.py' and run the script.")
