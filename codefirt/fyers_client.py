# codefirt/fyers_client.py

import webbrowser
from fyers_apiv3 import fyersModel

# --- User Configuration ---
# Please fill in your Fyers API credentials here.
# You can create an app on the Fyers API dashboard: https://myapi.fyers.in/dashboard/
CLIENT_ID = ""
SECRET_KEY = ""
REDIRECT_URI = "" # e.g., "http://localhost:3000/auth"

# This file will store the access token once it's generated.
TOKEN_FILE = "codefirt/access_token.txt"

def get_access_token():
    """
    Guides the user through the Fyers API authentication process to get an access token.
    It stores the token in a file to avoid repeated logins.
    """
    # Check if the access token is already stored in the file
    try:
        with open(TOKEN_FILE, 'r') as f:
            access_token = f.read().strip()
            if access_token:
                print("Access token found in file.")
                return access_token
    except FileNotFoundError:
        pass

    if not CLIENT_ID or not SECRET_KEY or not REDIRECT_URI:
        print("Please fill in your Fyers API credentials in codefirt/fyers_client.py")
        return None

    # If not found, generate a new one
    session = fyersModel.SessionModel(
        client_id=CLIENT_ID,
        secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )

    auth_url = session.generate_authcode()
    print(f"Please open the following URL in your browser to authorize the app:")
    print(auth_url)
    webbrowser.open(auth_url, new=1)

    print("\nAfter successful login, you will be redirected to your redirect_uri with an auth_code in the query parameters.")

    # In a real application, you would have a web server to handle the redirect and get the auth_code.
    # For this script, we will ask the user to manually paste the auth_code.
    auth_code = input("Please copy the auth_code and paste it here: ")

    session.set_token(auth_code)
    response = session.generate_token()

    if response.get("access_token"):
        access_token = response["access_token"]
        # Save the access token to a file for future use
        with open(TOKEN_FILE, 'w') as f:
            f.write(access_token)
        print("Access token generated and saved successfully.")
        return access_token
    else:
        print(f"Failed to generate access token: {response}")
        return None

def initialize_fyers_model(access_token):
    """Initializes the Fyers API client."""
    if not CLIENT_ID:
        raise ValueError("CLIENT_ID is not set in fyers_client.py")

    fyers = fyersModel.FyersModel(client_id=CLIENT_ID, token=access_token, log_path="fyers_log.log")
    return fyers
