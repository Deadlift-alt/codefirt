# codefirt/utils.py

def get_option_symbol(config, strike, option_type):
    """
    Constructs the option symbol for Fyers API.

    *** IMPORTANT ***
    This function uses a hardcoded prefix (e.g., "NIFTY25807") from the
    Survivor.yml config file. This prefix contains the expiry date.
    This means the application will STOP WORKING when the options for that
    specific date expire.

    For a production-ready application, this logic must be replaced with a
    dynamic mechanism to fetch the current list of tradable symbols from the
    Fyers API and determine the correct expiry prefix for the current week/month.
    """
    symbol_initials = config.get('symbol_initials', 'NIFTY')
    return f"NSE:{symbol_initials}{strike}{option_type}"
