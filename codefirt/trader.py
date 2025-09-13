# codefirt/trader.py

import time
from codefirt.utils import get_option_symbol

# To avoid placing multiple trades in a short period
last_trade_time = 0
COOLDOWN_PERIOD = 300 # 5 minutes

def _place_dry_run_trade(fyers, config, strikes_to_trade, option_type):
    """
    Constructs and prints the orders that would be placed.
    This function is for simulation only (DRY RUN).
    """
    global last_trade_time
    print(f"\n--- !!! MOCK TRADE PLACEMENT: {option_type} !!! ---")

    orders = []
    for strike in strikes_to_trade:
        symbol = get_option_symbol(config, strike, option_type)
        order_data = {
            "symbol": symbol,
            "qty": config.get('base_quantity', 75),
            "type": 2,  # Market Order
            "side": 1,  # Buy
            "productType": config.get('product_type', 'INTRADAY'),
            "limitPrice": 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": "False",
            "orderTag": f"signal_trade_{int(time.time())}"
        }
        orders.append(order_data)

    # --- TO ENABLE LIVE TRADING ---
    # 1. Make sure you have sufficient funds in your Fyers account.
    # 2. Understand the risks associated with automated trading.
    # 3. Uncomment the two lines below.
    #
    # print("Sending orders to Fyers API...")
    # response = fyers.place_basket_orders(data=orders)
    # print(f"API Response: {response}")

    print("--- DRY RUN ORDER DETAILS ---")
    for order in orders:
        print(order)
    print("-----------------------------\n")

    last_trade_time = time.time()

def check_and_execute_trades(fyers, nifty_data, call_data, put_data, config):
    """
    Checks for trading signals and executes trades if conditions are met.
    """
    global last_trade_time
    if time.time() - last_trade_time < COOLDOWN_PERIOD:
        return # In a cooldown period, don't place new trades

    # --- 1. Check if NIFTY is stable ---
    nifty_movement_threshold = config.get('nifty_movement_threshold', 15)

    _, _, nifty_abs_change_3m = nifty_data.get('change_3m', (None, 0, 0))
    _, _, nifty_abs_change_5m = nifty_data.get('change_5m', (None, 0, 0))

    if abs(nifty_abs_change_3m) > nifty_movement_threshold or abs(nifty_abs_change_5m) > nifty_movement_threshold:
        return # Nifty is moving too much, so no trade based on this signal

    # --- 2. Define strikes for signal and action ---
    if not call_data: return
    atm_strike = sorted(call_data.keys())[len(call_data) // 2]

    call_signal_strikes = [atm_strike, atm_strike - 50, atm_strike - 100]
    put_signal_strikes = [atm_strike, atm_strike + 50, atm_strike + 100]

    action_strikes = [atm_strike - 50, atm_strike, atm_strike + 100]

    # --- 3. Check for Call trade signal ---
    for strike in call_signal_strikes:
        if strike in call_data and call_data[strike]:
            _, pct_3m, _ = call_data[strike].get('change_3m', (None, 0, 0))
            _, pct_5m, _ = call_data[strike].get('change_5m', (None, 0, 0))

            if pct_3m > 30 or pct_5m > 30:
                print(f"TRADE SIGNAL: High OI jump on CALL strike {strike}. NIFTY is stable.")
                _place_dry_run_trade(fyers, config, action_strikes, "CE")
                return

    # --- 4. Check for Put trade signal ---
    for strike in put_signal_strikes:
        if strike in put_data and put_data[strike]:
            _, pct_3m, _ = put_data[strike].get('change_3m', (None, 0, 0))
            _, pct_5m, _ = put_data[strike].get('change_5m', (None, 0, 0))

            if pct_3m > 30 or pct_5m > 30:
                print(f"TRADE SIGNAL: High OI jump on PUT strike {strike}. NIFTY is stable.")
                _place_dry_run_trade(fyers, config, action_strikes, "PE")
                return
