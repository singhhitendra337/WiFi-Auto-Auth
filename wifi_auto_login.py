import sqlite3
import requests
import datetime
import re
import argparse
import json
import os


# --- CONFIGURATION ---
CONFIG_PATH = "config.json"

def load_config():
    """Load configuration file and return config dict"""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            "Missing config.json. Please copy config.example.json to config.json and fill in your details."
        )
    
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    
    return config

# Global variables - will be loaded when needed
URL = None
USERNAME = None
PASSWORD = None
PRODUCT_TYPE = None

# --- DATABASE SETUP ---
DB_NAME = "wifi_log.db"

# Initialize logging
from config.logging_config import setup_logging_from_env, get_logger
setup_logging_from_env()
logger = get_logger(__name__)

def setup_database():
    """Create the database and table if they do not exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            password TEXT,
            a TEXT,
            response_status TEXT,
            response_message TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_attempt(username, password, a, response_status, response_message):
    """Log each login attempt in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO login_attempts (timestamp, username, password, a, response_status, response_message)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.datetime.now(), username, "******", a, response_status, response_message))
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---
def extract_message(response_text):
    """Extracts the meaningful message from the XML response."""
    match = re.search(r"<message><!\[CDATA\[(.*?)\]\]></message>", response_text)
    return match.group(1) if match else "Unknown response"

# --- MAIN WIFI LOGIN FUNCTION ---
def wifi_login():
    """Perform the WiFi login request and log the result."""
    # Load config when needed
    config = load_config()
    global URL, USERNAME, PASSWORD, PRODUCT_TYPE
    URL = config["wifi_url"]
    USERNAME = config["username"]
    PASSWORD = config["password"]
    PRODUCT_TYPE = config.get("product_type", "0")
    
    a_value = str(int(datetime.datetime.now().timestamp()))  # Generate dynamic 'a' value

    payload = {
        "mode": "191",
        "username": USERNAME,
        "password": PASSWORD,
        "a": a_value,
        "producttype": PRODUCT_TYPE
    }

    try:
        response = requests.post(URL, data=payload)
        response_status = response.status_code
        response_message = extract_message(response.text)

        print(f"\n📌 Login Attempt")
        print(f"Time: {datetime.datetime.now()}")
        print(f"Username: {USERNAME}")
        print(f"Session ID (a): {a_value}")
        print(f"Status: {response_status}")
        print(f"Message: {response_message}")
        print("-" * 80)

        # Log the attempt in SQLite
        log_attempt(USERNAME, PASSWORD, a_value, response_status, response_message)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        log_attempt(USERNAME, PASSWORD, a_value, "FAILED", str(e))

# --- VIEW LOGIN LOGS ---
def view_logs(limit=5):
    """Display login logs in a readable format."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, username, a, response_status, response_message 
        FROM login_attempts 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))

    logs = cursor.fetchall()
    conn.close()

    if not logs:
        logger.info("No login attempts found in database")
        return

    logger.info("Recent login attempts retrieved from database")
    logger.info("=" * 80)

    for log in logs:
        timestamp, username, a, status, message = log
        logger.info(f"Time: {timestamp}")
        logger.info(f"Username: {username}")
        logger.info(f"Session ID (a): {a}")
        logger.info(f"Status: {status}")
        logger.info(f"Message: {message}")
        logger.info("-" * 80)

def parse_arguments():
    """Parse command line arguments for logging configuration."""
    parser = argparse.ArgumentParser(description='WiFi Auto Login with Professional Logging')

    # Logging configuration arguments
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file',
        action='store_true',
        default=True,
        help='Enable file logging (default: enabled)'
    )
    parser.add_argument(
        '--no-log-file',
        action='store_false',
        dest='log_file',
        help='Disable file logging'
    )
    parser.add_argument(
        '--log-dir',
        default='./logs',
        help='Directory for log files (default: ./logs)'
    )
    parser.add_argument(
        '--console-logging',
        action='store_true',
        default=True,
        help='Enable console logging (default: enabled)'
    )
    parser.add_argument(
        '--no-console-logging',
        action='store_false',
        dest='console_logging',
        help='Disable console logging'
    )

    # Application arguments
    parser.add_argument(
        '--view-logs',
        type=int,
        metavar='N',
        help='View last N login attempts instead of performing login'
    )
    parser.add_argument(
        '--max-attempts',
        type=int,
        default=5,
        help='Maximum number of login attempts to show when viewing logs (default: 5)'
    )

    return parser.parse_args()


def clear_logs():
    """Deletes all logs from the login_attempts table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM login_attempts")
    conn.commit()
    conn.close()
    print("✅ All logs have been cleared.")

def test_connection():
    """Tests if the login URL is reachable."""
    config = load_config()
    url = config["wifi_url"]
    print(f"🔗 Testing connection to {url}...")
    try:
        response = requests.head(url, timeout=5) # Use HEAD to be efficient
        if response.status_code == 200:
            print(f"✅ Connection successful! The server responded with status {response.status_code}.")
        else:
            print(f"⚠️ Connection successful, but the server responded with status {response.status_code}.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")

def run_setup_wizard():
    """Guides the user through an interactive setup process."""
    print("--- WiFi-Auto-Auth Interactive Setup ---")
    print("This wizard will help you configure the script.")
    
    url = input("1. Enter the POST request URL from your network's login page: ")
    username = input("2. Enter your login username: ")
    password = input("3. Enter your login password: ")

    print("\nSetup Complete!")

def start_dashboard():
    """Start the web dashboard server."""
    try:
        import subprocess
        import sys
        print("🚀 Starting WiFi Auto Auth Dashboard...")
        print("📊 Dashboard will be available at: http://127.0.0.1:8000")
        print("🔑 Default credentials: admin / admin123")
        print("🛑 Press Ctrl+C to stop the server")
        
        # Start the dashboard server
        subprocess.run([sys.executable, "dashboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting dashboard: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped.")
    except ImportError:
        print("❌ Dashboard dependencies not installed. Please run: pip install -r requirements.txt")
    except FileNotFoundError:
        print("❌ Dashboard server not found. Please ensure dashboard.py exists.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to automatically log into captive portal WiFi networks."
    )
    
    parser.add_argument(
        '--login', 
        action='store_true', 
        help="Perform a login attempt."
    )
    parser.add_argument(
        '--view-logs', 
        nargs='?', 
        const=5, 
        type=int, 
        metavar='N', 
        help="View the last N login attempts. Defaults to 5 if no number is provided."
    )
    parser.add_argument(
        '--setup', 
        action='store_true', 
        help="Run the interactive setup wizard to configure credentials."
    )
    parser.add_argument(
        '--test', 
        action='store_true', 
        help="Test the connection to the login URL without logging in."
    )
    parser.add_argument(
        '--clear-logs', 
        action='store_true', 
        help="Clear all login logs from the database."
    )
    parser.add_argument(
        '--dashboard', 
        action='store_true', 
        help="Start the web dashboard server for monitoring login attempts."
    )

    args = parser.parse_args()
    
    # For operations that don't need config, handle them first
    if args.setup:
        run_setup_wizard()
    elif args.dashboard:
        start_dashboard()
    else:
        # For operations that need database/config
        try:
            setup_database()  # Ensure the database is always set up
            
            if args.login:
                wifi_login()
            elif args.view_logs is not None:
                view_logs(args.view_logs)
            elif args.test:
                test_connection()
            elif args.clear_logs:
                clear_logs()
            else:
                print("No arguments provided. Performing default login action.")
                wifi_login()
                view_logs(1)
                
        except FileNotFoundError as e:
            print(f"❌ Configuration Error: {e}")
            print("💡 Run 'python wifi_auto_login.py --setup' to configure the application.")
            print("📖 Or copy config.example.json to config.json and edit it manually.")
