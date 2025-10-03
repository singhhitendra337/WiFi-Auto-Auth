# WiFi Auto Auth Dashboard

A beautiful web-based monitoring interface for WiFi Auto Auth that provides real-time visualization of login attempts, statistics, and historical data.

## 🚀 Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Copy config**: `cp config.example.json config.json` (edit with your WiFi details)
3. **Generate data**: `python wifi_auto_login.py --login` (run a few times)
4. **Start dashboard**: `python wifi_auto_login.py --dashboard`
5. **Access**: Open http://127.0.0.1:8000 (username: admin, password: admin123)

## Features

### 🎯 Core Features
- **Real-time Dashboard**: Live monitoring of WiFi login attempts
- **Interactive Charts**: Time-based visualizations using Chart.js
- **Advanced Filtering**: Filter by date range, status, and more
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Secure Access**: HTTP Basic Authentication protection
- **RESTful API**: Complete API for data access and integration

### 📊 Dashboard Components
- **Statistics Cards**: Total attempts, success rate, failure count
- **Login Attempts Table**: Detailed view of recent attempts
- **Time-based Charts**: Visual representation of login patterns
- **Success Rate Pie Chart**: Quick overview of success vs failure rates
- **Real-time Updates**: Auto-refresh every 30 seconds

### 🔒 Security Features
- HTTP Basic Authentication
- Configurable credentials
- Session management
- Secure API endpoints

## Installation

### Prerequisites
- Python 3.7 or higher
- All dependencies from `requirements.txt`

### Install Dependencies

```bash
pip install -r requirements.txt
```

The dashboard requires these additional packages:
- `fastapi>=0.104.0` - Modern web framework
- `uvicorn>=0.24.0` - ASGI server
- `jinja2>=3.1.0` - Template engine
- `python-multipart>=0.0.6` - Form data handling
- `aiofiles>=23.2.0` - Async file operations

## Configuration

### Dashboard Settings

Add dashboard configuration to your `config.json`:

```json
{
  "wifi_url": "http://192.168.1.1/login",
  "username": "your_username",
  "password": "your_password",
  "product_type": "router",
  "dashboard": {
    "host": "127.0.0.1",
    "port": 8000,
    "username": "admin",
    "password": "admin123"
  }
}
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `host` | Dashboard server host | `127.0.0.1` |
| `port` | Dashboard server port | `8000` |
| `username` | Dashboard login username | `admin` |
| `password` | Dashboard login password | `admin123` |

## Usage

### Starting the Dashboard

#### Method 1: Using CLI Command
```bash
python wifi_auto_login.py --dashboard
```

#### Method 2: Direct Server Start
```bash
python dashboard.py
```

#### Method 3: Custom Host/Port
```bash
python dashboard.py --host 0.0.0.0 --port 8080
```

### Accessing the Dashboard

1. **Open your browser** and navigate to: `http://127.0.0.1:8000`
2. **Enter credentials** when prompted:
   - Username: `admin` (or your configured username)
   - Password: `admin123` (or your configured password)
3. **Explore the dashboard** - you'll see all your WiFi login statistics and history

### Dashboard Sections

#### 📈 Statistics Overview
- **Total Attempts**: All login attempts recorded
- **Successful**: Number of successful logins
- **Failed**: Number of failed attempts
- **Success Rate**: Percentage of successful logins

#### 🔍 Filtering Options
- **Date Range**: Filter attempts by start and end date
- **Status Filter**: Show only successful or failed attempts
- **Result Limit**: Control number of results displayed (25, 50, 100, 200)

#### 📊 Visualizations
- **Login Attempts Over Time**: Line chart showing hourly login patterns
- **Success Rate Distribution**: Pie chart showing success vs failure ratio
- **Real-time Updates**: Charts refresh automatically every 30 seconds

#### 📋 Login Attempts Table
- **Timestamp**: When the login attempt occurred
- **Username**: User account used for login
- **Session ID**: Unique session identifier
- **Status**: Success (200) or failure status codes
- **Message**: Response message from the WiFi system

## API Endpoints

The dashboard provides a RESTful API for integration:

### Authentication
All API endpoints require HTTP Basic Authentication using the same credentials as the dashboard.

### Available Endpoints

#### `GET /`
Main dashboard page (HTML)

#### `GET /api/attempts`
Get login attempts with optional filters

**Query Parameters:**
- `start_date`: Filter attempts after this date (ISO format)
- `end_date`: Filter attempts before this date (ISO format)
- `status_filter`: `success` or `failed`
- `limit`: Maximum number of results (default: 50)

**Example:**
```bash
curl -u admin:admin123 "http://localhost:8000/api/attempts?limit=10&status_filter=success"
```

#### `GET /api/stats`
Get dashboard statistics

**Response:**
```json
{
  "total_attempts": 150,
  "successful_attempts": 145,
  "failed_attempts": 5,
  "success_rate": 96.67,
  "last_attempt": "2025-10-03T10:30:45"
}
```

#### `GET /api/hourly-stats`
Get hourly statistics for charts

**Query Parameters:**
- `days`: Number of days to include (default: 7)

**Example:**
```bash
curl -u admin:admin123 "http://localhost:8000/api/hourly-stats?days=3"
```

#### `GET /health`
Health check endpoint (no authentication required)

## Development

### Running in Development Mode

```bash
python dashboard.py --debug
```

This enables:
- Auto-reload on code changes
- Detailed error messages
- Debug logging

### Custom Styling

The dashboard uses Bootstrap 5 and custom CSS. You can modify:
- `static/dashboard.css` - Custom styles
- `templates/dashboard.html` - Main dashboard template
- `templates/login.html` - Login page template

### Adding New Features

The dashboard is built with FastAPI, making it easy to extend:

1. **Add new API endpoints** in `dashboard.py`
2. **Modify database queries** in the database functions
3. **Update templates** for new UI components
4. **Add JavaScript** for new interactive features

## Troubleshooting

### Common Issues

#### "Database not found" Error
- **Cause**: The database hasn't been created yet
- **Solution**: Run the main script first: `python wifi_auto_login.py --login`

#### "Port already in use" Error
- **Cause**: Another process is using port 8000
- **Solution**: Use a different port: `python dashboard.py --port 8080`

#### Authentication Issues
- **Cause**: Incorrect credentials
- **Solution**: Check your `config.json` dashboard settings

#### Charts Not Loading
- **Cause**: No login data available
- **Solution**: Run some login attempts first to populate the database

#### Permission Denied
- **Cause**: Insufficient permissions to bind to the specified host/port
- **Solution**: Use `127.0.0.1` instead of `0.0.0.0`, or run with appropriate permissions

### Debug Mode

Enable debug mode for detailed error information:

```bash
python dashboard.py --debug
```

### Logs

The dashboard uses the same logging configuration as the main application. Check:
- Console output for real-time logs
- Log files in the `logs/` directory (if configured)

## Security Considerations

### Production Deployment

⚠️ **Important**: The default credentials are for development only!

For production deployment:

1. **Change default credentials** in `config.json`
2. **Use HTTPS** with a reverse proxy (nginx, Apache)
3. **Restrict access** by IP address if needed
4. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
5. **Consider additional authentication** methods if required

### Network Security

- The dashboard binds to `127.0.0.1` by default (localhost only)
- To allow network access, bind to `0.0.0.0` but ensure proper firewall rules
- Consider using a VPN for remote access

## Performance

### Optimization Tips

- **Limit results** using the limit parameter for better performance
- **Use date filters** to reduce database query time
- **Regular maintenance** - consider archiving old login attempts
- **Monitor database size** - SQLite performance degrades with very large databases

### Resource Usage

- **Memory**: ~50MB for typical usage
- **CPU**: Minimal when idle, moderate during chart updates
- **Database**: Grows ~1KB per login attempt
- **Network**: ~100KB per dashboard page load

## Integration Examples

### Monitoring Scripts

```python
import requests
from requests.auth import HTTPBasicAuth

# Get current statistics
response = requests.get(
    'http://localhost:8000/api/stats',
    auth=HTTPBasicAuth('admin', 'admin123')
)
stats = response.json()
print(f"Success rate: {stats['success_rate']}%")
```

### Automated Reporting

```python
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta

# Get yesterday's login attempts
yesterday = datetime.now() - timedelta(days=1)
start_date = yesterday.strftime('%Y-%m-%dT00:00:00')
end_date = yesterday.strftime('%Y-%m-%dT23:59:59')

response = requests.get(
    f'http://localhost:8000/api/attempts?start_date={start_date}&end_date={end_date}',
    auth=HTTPBasicAuth('admin', 'admin123')
)
attempts = response.json()['attempts']
print(f"Yesterday's login attempts: {len(attempts)}")
```

## Support

For issues, questions, or contributions:

1. Check the troubleshooting section above
2. Review the application logs
3. Create an issue on the project repository
4. Include detailed error messages and system information

## License

This dashboard is part of the WiFi Auto Auth project and follows the same license terms.