# Installation Guide

This guide will walk you through installing and setting up CyberSentinel AI on your system.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **Operating System**: Linux (Ubuntu 18.04+), macOS (10.14+), or Windows 10
- **Python**: Version 3.8 or higher
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 1GB free disk space for logs and databases
- **Network**: Stable internet connection for API access

#### Recommended Requirements
- **Operating System**: Linux (Ubuntu 20.04+) or macOS (11.0+)
- **Python**: Version 3.9 or higher
- **Memory**: 8GB RAM for optimal performance
- **Storage**: 5GB+ for extensive historical data
- **Network**: High-speed internet for rapid data collection

### Required Accounts and API Keys

Before installation, you'll need to obtain API keys from the following services:

#### 1. GitHub API Access
- **Personal Access Token** with repository read permissions
- **Multiple tokens recommended** for higher rate limits
- **Scopes needed**: `public_repo`, `read:org` (optional)

**How to obtain**:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with appropriate scopes
3. Save the token securely

#### 2. OpenAI API Access
- **API Key** for GPT model access
- **Organization ID** (if applicable)
- **Base URL** (if using custom endpoints)

**How to obtain**:
1. Visit https://platform.openai.com/
2. Create account and generate API key
3. Note your organization ID if applicable

#### 3. Google Gemini API Access (Optional)
- **API Key** for Gemini model access
- **Base URL** for API endpoint

**How to obtain**:
1. Visit Google AI Studio
2. Create project and generate API key
3. Enable Gemini API access

#### 4. Blog Platform API (Optional)
- **API Token** for automated publishing
- Platform-specific configuration

## Installation Methods

### Method 1: Direct Installation (Recommended)

#### Step 1: Clone the Repository
```bash
# Clone the main repository
git clone https://github.com/GizzZmo/CyberSentinel-AI.git

# Navigate to the project directory
cd CyberSentinel-AI

# Verify the clone was successful
ls -la
```

#### Step 2: Set Up Python Environment
```bash
# Check Python version
python3 --version

# Create virtual environment
python3 -m venv cybersentinel-env

# Activate virtual environment
# On Linux/macOS:
source cybersentinel-env/bin/activate

# On Windows:
cybersentinel-env\Scripts\activate

# Verify activation
which python  # Should show virtual environment path
```

#### Step 3: Install Dependencies
```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Common Dependencies Include**:
- `requests` - HTTP library for API calls
- `sqlalchemy` - Database ORM
- `openai` - OpenAI API client
- `google-generativeai` - Gemini API client
- `beautifulsoup4` - HTML parsing
- `schedule` - Task scheduling
- `python-dateutil` - Date/time utilities

#### Step 4: Create Directory Structure
```bash
# Create necessary directories
mkdir -p logs
mkdir -p database
mkdir -p data/articles
mkdir -p data/analysis
mkdir -p data/reports

# Verify directory structure
tree .  # or ls -la if tree is not available
```

### Method 2: Docker Installation (Alternative)

#### Prerequisites for Docker
- Docker Engine 20.0+
- Docker Compose 1.29+

#### Step 1: Create Docker Environment
```bash
# Clone repository
git clone https://github.com/GizzZmo/CyberSentinel-AI.git
cd CyberSentinel-AI

# Create Dockerfile (if not present)
cat > Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
EOF
```

#### Step 2: Create Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  cybersentinel:
    build: .
    volumes:
      - ./logs:/app/logs
      - ./database:/app/database
      - ./data:/app/data
      - ./config.py:/app/config.py
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

#### Step 3: Build and Run
```bash
# Build the container
docker-compose build

# Run the service
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Configuration Setup

### Step 1: Create Configuration File

Create the main configuration file `config.py`:

```python
# config.py - CyberSentinel AI Configuration

import os

# Database Configuration
DATABASE_PATH = "database"
CVE_DATABASE = f"{DATABASE_PATH}/cve_record.db"
GITHUB_DATABASE = f"{DATABASE_PATH}/github_repo.db"

# GitHub API Configuration
GITHUB_TOKENS = [
    "ghp_your_token_1_here",
    "ghp_your_token_2_here",
    "ghp_your_token_3_here"  # Add multiple tokens for better rate limits
]

# Primary GitHub token (will use first available)
GITHUB_TOKEN = GITHUB_TOKENS[0] if GITHUB_TOKENS else None

# Monitoring Configuration
MONITOR_INTERVAL = 3600  # Check every hour (3600 seconds)
GITHUB_KEYWORDS = [
    "security", "vulnerability", "exploit", "CVE", "0day",
    "penetration testing", "red team", "blue team", "malware",
    "incident response", "threat hunting", "SIEM", "SOC"
]

# Repository Watch Lists
WATCHED_REPOSITORIES = [
    "MITRE/cve",
    "rapid7/metasploit-framework", 
    "nmap/nmap",
    "sqlmapproject/sqlmap",
    "SecureAuthCorp/impacket"
]

# Blacklist Configuration
BLACKLIST_USERS = [
    "spam-user-example",
    "irrelevant-bot"
]

BLACKLIST_REPOSITORIES = [
    "spam-repo-example",
    "duplicate-content"
]

# AI Configuration - OpenAI Primary
PRIMARY_AI_CONFIG = {
    "api_key": "sk-your-openai-api-key-here",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini-2024-07-18",
    "max_tokens": 2000,
    "temperature": 0.1
}

# AI Configuration - OpenAI Backup
BACKUP_AI_CONFIGS = [
    {
        "api_key": "sk-backup-openai-key-here", 
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
        "max_tokens": 1500,
        "temperature": 0.1
    }
]

# AI Configuration - Gemini Fallback
GEMINI_AI_CONFIG = {
    "api_key": "your-gemini-api-key-here",
    "model": "gemini-pro",
    "base_url": "https://generativelanguage.googleapis.com"
}

# Blog Platform Configuration (Optional)
BLOG_TOKEN = "your-blog-api-token-here"
BLOG_BASE_URL = "https://your-blog-platform.com/api"

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "logs/security_monitor.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Report Configuration
DAILY_REPORT_TIME = "23:00"  # Generate daily reports at 11:00 PM
REPORT_OUTPUT_DIR = "data/reports"
```

### Step 2: Environment Variables (Alternative)

For enhanced security, you can use environment variables instead of hardcoding sensitive information:

```bash
# Create .env file
cat > .env << EOF
# GitHub Configuration
GITHUB_TOKEN_1=ghp_your_token_1_here
GITHUB_TOKEN_2=ghp_your_token_2_here
GITHUB_TOKEN_3=ghp_your_token_3_here

# OpenAI Configuration  
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BACKUP_KEY=sk-backup-openai-key-here

# Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Blog Configuration
BLOG_TOKEN=your-blog-api-token-here
EOF

# Load environment variables
source .env
```

Then modify `config.py` to use environment variables:

```python
import os

# Use environment variables with fallbacks
GITHUB_TOKENS = [
    os.getenv('GITHUB_TOKEN_1'),
    os.getenv('GITHUB_TOKEN_2'), 
    os.getenv('GITHUB_TOKEN_3')
]
GITHUB_TOKENS = [token for token in GITHUB_TOKENS if token]  # Remove None values

PRIMARY_AI_CONFIG = {
    "api_key": os.getenv('OPENAI_API_KEY'),
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini-2024-07-18",
    "max_tokens": 2000,
    "temperature": 0.1
}
```

### Step 3: Verify Configuration

Create a simple test script to verify your configuration:

```python
# test_config.py
import config
import requests

def test_github_token():
    """Test GitHub API access"""
    for i, token in enumerate(config.GITHUB_TOKENS):
        if not token:
            continue
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            print(f"✅ GitHub Token {i+1}: Valid")
        else:
            print(f"❌ GitHub Token {i+1}: Invalid ({response.status_code})")

def test_openai_key():
    """Test OpenAI API access"""
    import openai
    try:
        client = openai.OpenAI(
            api_key=config.PRIMARY_AI_CONFIG["api_key"],
            base_url=config.PRIMARY_AI_CONFIG["base_url"]
        )
        response = client.models.list()
        print("✅ OpenAI API: Valid")
    except Exception as e:
        print(f"❌ OpenAI API: Invalid ({e})")

if __name__ == "__main__":
    print("Testing Configuration...")
    test_github_token()
    test_openai_key()
    print("Configuration test complete.")
```

Run the test:
```bash
python test_config.py
```

## Initial Database Setup

### Automatic Database Creation

The system will automatically create SQLite databases on first run, but you can initialize them manually:

```python
# init_database.py
from database.models import create_tables

def initialize_databases():
    """Initialize SQLite databases"""
    print("Creating database tables...")
    create_tables()
    print("✅ Database initialization complete")

if __name__ == "__main__":
    initialize_databases()
```

### Manual Database Verification

```bash
# Check if databases were created
ls -la database/

# Should show:
# cve_record.db
# github_repo.db
```

## First Run

### Step 1: Test Installation
```bash
# Activate virtual environment (if not already active)
source cybersentinel-env/bin/activate

# Test basic import functionality
python -c "import config; print('Configuration loaded successfully')"
```

### Step 2: Dry Run
```bash
# Run with verbose logging to verify everything works
python main.py --dry-run --verbose
```

### Step 3: Full System Start
```bash
# Start the monitoring system
python main.py

# Monitor logs in separate terminal
tail -f logs/security_monitor.log
```

## Verification Steps

### 1. Check System Health
```bash
# Verify processes are running
ps aux | grep python

# Check log files for errors
tail -50 logs/security_monitor.log | grep ERROR
```

### 2. Verify Data Collection
```bash
# Check database content
sqlite3 database/cve_record.db "SELECT COUNT(*) FROM cve_records;"
sqlite3 database/github_repo.db "SELECT COUNT(*) FROM repositories;"
```

### 3. Test AI Analysis
```bash
# Check for analysis results
ls -la data/analysis/
cat data/analysis/latest_analysis.json
```

## Troubleshooting Common Issues

### Issue 1: Python Version Compatibility
```bash
# Error: "Python 3.8+ required"
python3 --version
# Solution: Upgrade Python or use pyenv

pyenv install 3.9.16
pyenv local 3.9.16
```

### Issue 2: Missing Dependencies
```bash
# Error: "ModuleNotFoundError"
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Issue 3: API Authentication Errors
```bash
# Error: "401 Unauthorized"
# Check API keys in config.py
python test_config.py
```

### Issue 4: Database Connection Issues
```bash
# Error: "Database locked" or "Permission denied"
chmod 755 database/
chmod 644 database/*.db
```

### Issue 5: Network Connectivity
```bash
# Test API connectivity
curl -H "Authorization: token YOUR_GITHUB_TOKEN" https://api.github.com/user
```

## Performance Optimization

### Memory Usage
```python
# Add to config.py for memory optimization
BATCH_SIZE = 50  # Process items in smaller batches
MAX_WORKERS = 2  # Limit concurrent threads
```

### Rate Limiting
```python
# Configure API rate limits
GITHUB_RATE_LIMIT = 5000  # Requests per hour
OPENAI_RATE_LIMIT = 100   # Requests per minute
```

## Next Steps

After successful installation:

1. **Read the [Configuration Guide](Configuration-Guide.md)** for advanced settings
2. **Review the [User Manual](User-Manual.md)** for daily operations
3. **Check the [Monitoring Guide](Monitoring-Guide.md)** for system health monitoring
4. **Explore the [API Reference](API-Reference.md)** for integration options

## Support

If you encounter issues during installation:

1. **Check the [Troubleshooting Guide](Troubleshooting.md)**
2. **Review the [FAQ](FAQ.md)** for common questions
3. **Search existing [GitHub Issues](https://github.com/GizzZmo/CyberSentinel-AI/issues)**
4. **Create a new issue** with detailed error information

---

*Installation complete! Your CyberSentinel AI system is ready to monitor and analyze cybersecurity threats.*