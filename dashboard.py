"""
WiFi Auto Auth Dashboard - Web-based monitoring interface for WiFi login attempts
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import uvicorn
import secrets
from pathlib import Path

# Import existing logging configuration
try:
    from config.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
CONFIG_PATH = "config.json"
DB_NAME = "wifi_log.db"

# Load configuration
def load_dashboard_config():
    """Load dashboard configuration from config.json"""
    if not os.path.exists(CONFIG_PATH):
        # Use default configuration if config.json doesn't exist
        return {
            "host": "127.0.0.1",
            "port": 8000,
            "username": "admin",
            "password": "admin123",
            "secret_key": secrets.token_urlsafe(32)
        }
    
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        return config.get("dashboard", {
            "host": "127.0.0.1",
            "port": 8000,
            "username": "admin",
            "password": "admin123",
            "secret_key": secrets.token_urlsafe(32)
        })
    except (json.JSONDecodeError, KeyError):
        logger.warning("Invalid config.json, using default dashboard configuration")
        return {
            "host": "127.0.0.1",
            "port": 8000,
            "username": "admin",
            "password": "admin123",
            "secret_key": secrets.token_urlsafe(32)
        }

# Dashboard configuration
DASHBOARD_CONFIG = load_dashboard_config()

# --- PYDANTIC MODELS ---
class LoginAttempt(BaseModel):
    id: int
    timestamp: str
    username: str
    a: str
    response_status: str
    response_message: str

class DashboardStats(BaseModel):
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    success_rate: float
    last_attempt: Optional[str]

class FilterParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status_filter: Optional[str] = None
    limit: int = 50

# --- FASTAPI APP SETUP ---
app = FastAPI(title="WiFi Auto Auth Dashboard", version="1.0.0")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")

# Create static directory if it doesn't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Simple authentication
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Simple HTTP Basic Authentication"""
    correct_username = secrets.compare_digest(credentials.username, DASHBOARD_CONFIG["username"])
    correct_password = secrets.compare_digest(credentials.password, DASHBOARD_CONFIG["password"])
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- DATABASE FUNCTIONS ---
def get_db_connection():
    """Get database connection"""
    if not os.path.exists(DB_NAME):
        logger.warning(f"Database {DB_NAME} not found. Creating empty database.")
        # Create an empty database with the required table structure
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
        return conn
    
    return sqlite3.connect(DB_NAME)

def get_login_attempts(filters: FilterParams) -> List[Dict]:
    """Get login attempts with filters"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT id, timestamp, username, a, response_status, response_message 
        FROM login_attempts 
        WHERE 1=1
    """
    params = []
    
    if filters.start_date:
        query += " AND timestamp >= ?"
        params.append(filters.start_date)
    
    if filters.end_date:
        query += " AND timestamp <= ?"
        params.append(filters.end_date)
    
    if filters.status_filter:
        if filters.status_filter == "success":
            query += " AND response_status = '200'"
        elif filters.status_filter == "failed":
            query += " AND response_status != '200'"
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(filters.limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "username": row[2],
            "a": row[3],
            "response_status": row[4],
            "response_message": row[5]
        }
        for row in rows
    ]

def get_dashboard_stats() -> DashboardStats:
    """Get dashboard statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total attempts
    cursor.execute("SELECT COUNT(*) FROM login_attempts")
    total_attempts = cursor.fetchone()[0]
    
    # Successful attempts (assuming 200 is success)
    cursor.execute("SELECT COUNT(*) FROM login_attempts WHERE response_status = '200'")
    successful_attempts = cursor.fetchone()[0]
    
    # Failed attempts
    failed_attempts = total_attempts - successful_attempts
    
    # Success rate
    success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0
    
    # Last attempt
    cursor.execute("SELECT timestamp FROM login_attempts ORDER BY timestamp DESC LIMIT 1")
    last_attempt_row = cursor.fetchone()
    last_attempt = last_attempt_row[0] if last_attempt_row else None
    
    conn.close()
    
    return DashboardStats(
        total_attempts=total_attempts,
        successful_attempts=successful_attempts,
        failed_attempts=failed_attempts,
        success_rate=round(success_rate, 2),
        last_attempt=last_attempt
    )

def get_hourly_stats(days: int = 7) -> List[Dict]:
    """Get hourly login attempt statistics for the last N days"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    start_date = datetime.now() - timedelta(days=days)
    
    query = """
        SELECT 
            strftime('%Y-%m-%d %H', timestamp) as hour,
            COUNT(*) as total_attempts,
            SUM(CASE WHEN response_status = '200' THEN 1 ELSE 0 END) as successful_attempts
        FROM login_attempts 
        WHERE timestamp >= ?
        GROUP BY strftime('%Y-%m-%d %H', timestamp)
        ORDER BY hour
    """
    
    cursor.execute(query, (start_date.isoformat(),))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "hour": row[0],
            "total_attempts": row[1],
            "successful_attempts": row[2],
            "failed_attempts": row[1] - row[2]
        }
        for row in rows
    ]

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(authenticate)):
    """Main dashboard page"""
    logger.info(f"Dashboard accessed by user: {username}")
    
    # Get recent login attempts
    filters = FilterParams(limit=10)
    recent_attempts = get_login_attempts(filters)
    
    # Get statistics
    stats = get_dashboard_stats()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recent_attempts": recent_attempts,
        "stats": stats,
        "username": username
    })

@app.get("/api/attempts")
async def get_attempts_api(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    username: str = Depends(authenticate)
):
    """API endpoint to get login attempts with filters"""
    filters = FilterParams(
        start_date=start_date,
        end_date=end_date,
        status_filter=status_filter,
        limit=limit
    )
    
    attempts = get_login_attempts(filters)
    logger.info(f"API call: Retrieved {len(attempts)} login attempts")
    
    return {"attempts": attempts}

@app.get("/api/stats")
async def get_stats_api(username: str = Depends(authenticate)):
    """API endpoint to get dashboard statistics"""
    stats = get_dashboard_stats()
    logger.info("API call: Retrieved dashboard statistics")
    return stats

@app.get("/api/hourly-stats")
async def get_hourly_stats_api(days: int = 7, username: str = Depends(authenticate)):
    """API endpoint to get hourly statistics"""
    stats = get_hourly_stats(days)
    logger.info(f"API call: Retrieved hourly statistics for last {days} days")
    return {"hourly_stats": stats}

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page (for custom authentication if needed)"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# --- SERVER MANAGEMENT ---
def start_dashboard_server(host: str = None, port: int = None, debug: bool = False):
    """Start the dashboard server"""
    host = host or DASHBOARD_CONFIG["host"]
    port = port or DASHBOARD_CONFIG["port"]
    
    logger.info(f"Starting WiFi Auto Auth Dashboard on http://{host}:{port}")
    logger.info(f"Username: {DASHBOARD_CONFIG['username']}")
    logger.info(f"Password: {DASHBOARD_CONFIG['password']}")
    
    uvicorn.run(
        "dashboard:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WiFi Auto Auth Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    start_dashboard_server(args.host, args.port, args.debug)