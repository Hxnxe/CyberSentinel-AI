# Configuration Guide

This guide provides detailed information about configuring CyberSentinel AI for your specific environment and requirements.

## Configuration Overview

CyberSentinel AI uses a combination of Python configuration files and environment variables to manage system settings. The primary configuration is handled through `config.py`, with optional environment variable overrides for enhanced security.

## Configuration File Structure

### Primary Configuration (`config.py`)

The main configuration file contains all system settings organized into logical sections:

```python
# config.py - CyberSentinel AI Configuration

# Database Configuration
DATABASE_PATH = "database"
CVE_DATABASE = f"{DATABASE_PATH}/cve_record.db"
GITHUB_DATABASE = f"{DATABASE_PATH}/github_repo.db"

# API Configuration
GITHUB_TOKENS = ["token1", "token2", "token3"]
PRIMARY_AI_CONFIG = {...}
BACKUP_AI_CONFIGS = [...]
GEMINI_AI_CONFIG = {...}

# Monitoring Configuration  
MONITOR_INTERVAL = 3600
GITHUB_KEYWORDS = [...]
WATCHED_REPOSITORIES = [...]

# Filtering Configuration
BLACKLIST_USERS = [...]
BLACKLIST_REPOSITORIES = [...]

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "logs/security_monitor.log"
```

## Database Configuration

### SQLite Settings

```python
# Database paths and settings
DATABASE_PATH = "database"
"""Base directory for all database files"""

CVE_DATABASE = f"{DATABASE_PATH}/cve_record.db"
"""SQLite database for CVE vulnerability records"""

GITHUB_DATABASE = f"{DATABASE_PATH}/github_repo.db"
"""SQLite database for GitHub repository data"""

# Database connection settings
DATABASE_TIMEOUT = 30
"""Database operation timeout in seconds"""

DATABASE_PRAGMA = {
    "journal_mode": "WAL",     # Write-Ahead Logging for better concurrency
    "synchronous": "NORMAL",   # Balance between safety and performance
    "cache_size": -64000,      # 64MB cache size
    "temp_store": "MEMORY"     # Store temporary data in memory
}
"""SQLite PRAGMA settings for optimization"""
```

### Database Migration and Backup

```python
# Backup configuration
DATABASE_BACKUP_INTERVAL = 86400  # Daily backups (24 hours)
DATABASE_BACKUP_PATH = "backups"
DATABASE_BACKUP_RETENTION = 30    # Keep 30 days of backups

# Migration settings
DATABASE_VERSION = "1.0"
AUTO_MIGRATE = True               # Automatically apply schema migrations
```

## API Configuration

### GitHub API Settings

```python
# GitHub API configuration
GITHUB_TOKENS = [
    "ghp_token1_example123",
    "ghp_token2_example456", 
    "ghp_token3_example789"
]
"""
List of GitHub Personal Access Tokens.
Multiple tokens are used for rate limit distribution.
Required scopes: public_repo, read:org (optional)
"""

# GitHub API settings
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_RATE_LIMIT_THRESHOLD = 100  # Switch tokens when below this limit
GITHUB_REQUEST_TIMEOUT = 30        # API request timeout in seconds
GITHUB_MAX_RETRIES = 3             # Maximum retry attempts
GITHUB_BACKOFF_FACTOR = 2          # Exponential backoff multiplier

# GitHub search parameters
GITHUB_SEARCH_SORT = "updated"     # Sort by: updated, stars, forks
GITHUB_SEARCH_ORDER = "desc"       # Order: asc, desc
GITHUB_SEARCH_PER_PAGE = 100       # Results per page (max 100)
GITHUB_MAX_SEARCH_RESULTS = 1000   # Maximum total results to process
```

### OpenAI API Configuration

```python
# Primary OpenAI configuration
PRIMARY_AI_CONFIG = {
    "api_key": "sk-your-openai-key-here",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini-2024-07-18",
    "max_tokens": 2000,
    "temperature": 0.1,
    "timeout": 60,
    "max_retries": 3
}

# Backup OpenAI configurations
BACKUP_AI_CONFIGS = [
    {
        "api_key": "sk-backup-key-1",
        "base_url": "https://api.openai.com/v1", 
        "model": "gpt-3.5-turbo",
        "max_tokens": 1500,
        "temperature": 0.1
    },
    {
        "api_key": "sk-backup-key-2",
        "base_url": "https://custom-endpoint.com/v1",
        "model": "gpt-4o-mini-2024-07-18",
        "max_tokens": 2000,
        "temperature": 0.1
    }
]

# AI analysis settings
AI_ANALYSIS_BATCH_SIZE = 10        # Process items in batches
AI_RATE_LIMIT_RPM = 100           # Requests per minute limit
AI_CONCURRENT_REQUESTS = 3         # Concurrent API requests
AI_FALLBACK_DELAY = 60            # Delay before trying fallback model
```

### Gemini API Configuration

```python
# Gemini AI configuration (fallback)
GEMINI_AI_CONFIG = {
    "api_key": "your-gemini-api-key",
    "model": "gemini-pro",
    "base_url": "https://generativelanguage.googleapis.com",
    "timeout": 60,
    "max_retries": 3,
    "temperature": 0.1,
    "max_output_tokens": 2000
}

# Gemini-specific settings
GEMINI_SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]
```

## Monitoring Configuration

### Search and Discovery Settings

```python
# Monitoring intervals
MONITOR_INTERVAL = 3600           # Main monitoring cycle (1 hour)
CVE_MONITOR_INTERVAL = 1800       # CVE-specific monitoring (30 minutes)
GITHUB_MONITOR_INTERVAL = 2400    # GitHub monitoring (40 minutes)
ARTICLE_FETCH_INTERVAL = 7200     # Article fetching (2 hours)

# Search keywords for GitHub repositories
GITHUB_KEYWORDS = [
    # Core security terms
    "security", "vulnerability", "exploit", "CVE", "0day", "zero-day",
    
    # Security tools and frameworks
    "penetration testing", "pentest", "red team", "blue team", 
    "security scanner", "vulnerability scanner", "security tool",
    
    # Threat categories
    "malware", "ransomware", "trojan", "backdoor", "rootkit",
    "phishing", "social engineering", "apt", "advanced persistent threat",
    
    # Security operations
    "incident response", "threat hunting", "forensics", "SIEM", "SOC",
    "security monitoring", "threat intelligence", "IOC", "indicators of compromise",
    
    # Compliance and standards
    "OWASP", "NIST", "ISO 27001", "compliance", "audit",
    
    # Cryptography and privacy
    "cryptography", "encryption", "privacy", "data protection",
    
    # Web security
    "XSS", "SQL injection", "CSRF", "web security", "application security"
]

# Repository watch lists
WATCHED_REPOSITORIES = [
    # Official security repositories
    "MITRE/cve",
    "CVEProject/cvelistV5", 
    "OWASP/Top10",
    
    # Security tools
    "rapid7/metasploit-framework",
    "nmap/nmap",
    "sqlmapproject/sqlmap", 
    "SecureAuthCorp/impacket",
    "danielmiessler/SecLists",
    
    # Vulnerability research
    "projectdiscovery/nuclei-templates",
    "swisskyrepo/PayloadsAllTheThings",
    "carlospolop/hacktricks",
    
    # Security frameworks
    "OWASP/CheatSheetSeries",
    "MITRE/attack-data",
    "center-for-threat-informed-defense/adversary_emulation_library"
]
```

### Content Filtering

```python
# User blacklists (exclude these users from monitoring)
BLACKLIST_USERS = [
    "spam-user-example",
    "irrelevant-bot",
    "commercial-advertiser",
    "fake-security-account"
]

# Repository blacklists (exclude these repositories)
BLACKLIST_REPOSITORIES = [
    "awesome-lists",           # Generic awesome lists
    "tutorial-basic",          # Basic tutorials
    "homework-assignment",     # Academic assignments
    "test-repository",         # Test repos
    "fork-collection"          # Pure fork collections
]

# Content filtering rules
MIN_REPOSITORY_STARS = 5          # Minimum stars for consideration
MIN_REPOSITORY_AGE_DAYS = 7       # Minimum age in days
MAX_REPOSITORY_FORKS_RATIO = 10   # Max forks:stars ratio
EXCLUDE_ARCHIVED = True           # Exclude archived repositories
EXCLUDE_FORKS = True             # Exclude fork repositories
REQUIRE_RECENT_ACTIVITY_DAYS = 90 # Require activity within 90 days

# Relevance scoring thresholds
MIN_RELEVANCE_SCORE = 0.3         # Minimum relevance score (0.0-1.0)
HIGH_VALUE_THRESHOLD = 0.8        # Threshold for high-value classification
AUTO_ANALYZE_THRESHOLD = 0.5      # Auto-trigger AI analysis above this score
```

## Analysis Configuration

### AI Analysis Settings

```python
# Analysis prompts and templates
CVE_ANALYSIS_PROMPT = """
Analyze the following CVE vulnerability information and provide a comprehensive assessment:

CVE: {cve_number}
Description: {description}
Repository: {repository_url}

Please provide analysis in the following JSON format:
{{
  "brief_description": "Brief summary of the vulnerability",
  "detailed_summary": "Detailed technical analysis",
  "risk_level": "Critical|High|Medium|Low",
  "key_points": ["key point 1", "key point 2"],
  "technical_details": "Technical exploitation details",
  "affected_components": ["component1", "component2"],
  "value_assessment": "High|Medium|Low",
  "security_type": "Type of security issue",
  "exploitation_status": "Proof-of-concept available|Exploited in wild|Theoretical"
}}
"""

REPOSITORY_ANALYSIS_PROMPT = """
Analyze the following GitHub repository for security relevance:

Repository: {repository_name}
Description: {description}  
Stars: {stars}
Language: {language}
Recent Activity: {recent_commits}

Provide analysis in JSON format with security assessment and value evaluation.
"""

# Analysis quality controls
ANALYSIS_MIN_RESPONSE_LENGTH = 100    # Minimum AI response length
ANALYSIS_MAX_RESPONSE_LENGTH = 5000   # Maximum AI response length
ANALYSIS_REQUIRED_FIELDS = [          # Required fields in AI response
    "brief_description", "risk_level", "value_assessment"
]
ANALYSIS_RETRY_ON_INCOMPLETE = True   # Retry if response incomplete
```

### Blacklist Management

```python
# Dynamic blacklist settings
ENABLE_DYNAMIC_BLACKLIST = True       # Enable AI-driven blacklist updates
BLACKLIST_UPDATE_THRESHOLD = 0.2     # Score below which to blacklist
BLACKLIST_REVIEW_INTERVAL = 7        # Days between blacklist reviews
MAX_DYNAMIC_BLACKLIST_SIZE = 1000    # Maximum dynamic blacklist entries

# Blacklist categories
BLACKLIST_CATEGORIES = {
    "spam": {"weight": 1.0, "auto_add": True},
    "irrelevant": {"weight": 0.8, "auto_add": True}, 
    "duplicate": {"weight": 0.6, "auto_add": False},
    "low_quality": {"weight": 0.4, "auto_add": False}
}
```

## Reporting Configuration

### Report Generation

```python
# Daily report settings
DAILY_REPORT_ENABLED = True
DAILY_REPORT_TIME = "23:00"          # UTC time for daily report generation
DAILY_REPORT_TIMEZONE = "UTC"        # Timezone for scheduling

# Report content settings
REPORT_MAX_ITEMS_PER_CATEGORY = 20   # Maximum items per category
REPORT_MIN_RELEVANCE_SCORE = 0.4     # Minimum score for inclusion
REPORT_INCLUDE_ANALYSIS = True       # Include AI analysis in reports
REPORT_INCLUDE_METADATA = True       # Include technical metadata

# Report output settings
REPORT_OUTPUT_DIR = "data/reports"    # Directory for generated reports
REPORT_FILENAME_FORMAT = "security-briefing-{date}.md"
REPORT_ARCHIVE_AFTER_DAYS = 90       # Archive reports after 90 days

# Report sections configuration
REPORT_SECTIONS = {
    "cve_analysis": {
        "title": "🔍 Vulnerability Analysis",
        "enabled": True,
        "max_items": 15
    },
    "new_repositories": {
        "title": "🛠️ New Security Tools",
        "enabled": True, 
        "max_items": 10
    },
    "repository_updates": {
        "title": "📈 Repository Updates",
        "enabled": True,
        "max_items": 10
    },
    "security_articles": {
        "title": "📚 Security Articles",
        "enabled": True,
        "max_items": 20
    }
}
```

### Blog Publishing

```python
# Blog platform configuration
BLOG_ENABLED = True
BLOG_PLATFORM = "custom"             # Platform type: wordpress, medium, custom
BLOG_API_BASE_URL = "https://your-blog.com/api"
BLOG_API_TOKEN = "your-api-token"

# Publishing settings
BLOG_AUTO_PUBLISH = True             # Automatically publish reports
BLOG_PUBLISH_DELAY = 300             # Delay after report generation (seconds)
BLOG_DRAFT_MODE = False              # Publish as draft instead of live
BLOG_TAGS = ["cybersecurity", "threat-intelligence", "vulnerability-research"]

# Blog post formatting
BLOG_TITLE_FORMAT = "Daily Security Intelligence - {date}"
BLOG_EXCERPT_LENGTH = 200            # Length of post excerpt
BLOG_INCLUDE_TOC = True              # Include table of contents
BLOG_INCLUDE_METADATA = False        # Include technical metadata in post
```

## Logging Configuration

### Log Settings

```python
# Logging configuration
LOG_LEVEL = "INFO"                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "logs/security_monitor.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log rotation settings
LOG_MAX_BYTES = 10485760             # 10MB per log file
LOG_BACKUP_COUNT = 10                # Keep 10 backup files
LOG_ROTATE_WHEN = "midnight"         # Rotate at midnight
LOG_ROTATE_INTERVAL = 1              # Rotate every 1 day

# Component-specific logging
COMPONENT_LOG_LEVELS = {
    "cve_monitor": "INFO",
    "github_monitor": "INFO", 
    "ai_analyzer": "DEBUG",           # More verbose for AI debugging
    "article_manager": "INFO",
    "blog_manager": "WARNING"         # Less verbose for blog operations
}

# Log filtering
LOG_FILTERS = {
    "exclude_patterns": [
        "rate limit remaining",       # Exclude rate limit messages
        "cache hit",                 # Exclude cache status messages
    ],
    "include_only_errors": False,    # Only log errors (overrides LOG_LEVEL)
    "sanitize_api_keys": True       # Remove API keys from log messages
}
```

### Audit and Security Logging

```python
# Security event logging
SECURITY_LOG_ENABLED = True
SECURITY_LOG_FILE = "logs/security_events.log"
SECURITY_LOG_EVENTS = [
    "api_authentication",            # API key usage and failures
    "configuration_changes",         # Changes to configuration
    "data_access",                  # Database access events
    "external_requests",            # Outbound API requests
    "analysis_results"              # AI analysis outcomes
]

# Audit trail settings
AUDIT_LOG_ENABLED = True
AUDIT_LOG_FILE = "logs/audit_trail.log"
AUDIT_LOG_RETENTION_DAYS = 365      # Keep audit logs for 1 year
```

## Performance Configuration

### System Performance

```python
# Threading and concurrency
MAX_WORKER_THREADS = 4               # Maximum worker threads
MONITORING_THREAD_POOL_SIZE = 3      # Threads for monitoring tasks
ANALYSIS_THREAD_POOL_SIZE = 2        # Threads for AI analysis
BACKGROUND_TASK_INTERVAL = 300       # Background task check interval

# Memory management
MAX_MEMORY_USAGE_MB = 1024          # Maximum memory usage (1GB)
MEMORY_CHECK_INTERVAL = 600         # Check memory usage every 10 minutes
ENABLE_MEMORY_PROFILING = False     # Enable memory usage profiling

# Rate limiting
GLOBAL_RATE_LIMIT_ENABLED = True
API_RATE_LIMITS = {
    "github": {"requests_per_minute": 100, "burst": 10},
    "openai": {"requests_per_minute": 60, "burst": 5},
    "gemini": {"requests_per_minute": 30, "burst": 3}
}

# Caching settings
ENABLE_CACHING = True
CACHE_TYPE = "memory"               # memory, redis, file
CACHE_TTL_SECONDS = 3600           # Cache time-to-live (1 hour)
CACHE_MAX_SIZE = 1000              # Maximum cache entries
```

## Environment Variables

### Secure Configuration with Environment Variables

```bash
# GitHub API configuration
export GITHUB_TOKEN_1="ghp_your_token_1"
export GITHUB_TOKEN_2="ghp_your_token_2"
export GITHUB_TOKEN_3="ghp_your_token_3"

# OpenAI API configuration
export OPENAI_API_KEY="sk-your-openai-key"
export OPENAI_BACKUP_KEY="sk-backup-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"

# Gemini API configuration
export GEMINI_API_KEY="your-gemini-key"

# Blog API configuration
export BLOG_API_TOKEN="your-blog-token"
export BLOG_BASE_URL="https://your-blog.com/api"

# Database configuration
export DATABASE_PATH="/secure/path/to/databases"

# Logging configuration
export LOG_LEVEL="INFO"
export LOG_FILE="/var/log/cybersentinel/security_monitor.log"
```

### Loading Environment Variables in Config

```python
import os
from typing import List, Optional

def get_env_list(env_var: str, separator: str = ",") -> List[str]:
    """Get list from environment variable."""
    value = os.getenv(env_var, "")
    return [item.strip() for item in value.split(separator) if item.strip()]

def get_env_bool(env_var: str, default: bool = False) -> bool:
    """Get boolean from environment variable."""
    value = os.getenv(env_var, "").lower()
    return value in ("true", "1", "yes", "on")

# Override config with environment variables
GITHUB_TOKENS = get_env_list("GITHUB_TOKENS") or GITHUB_TOKENS
PRIMARY_AI_CONFIG["api_key"] = os.getenv("OPENAI_API_KEY") or PRIMARY_AI_CONFIG["api_key"]
GEMINI_AI_CONFIG["api_key"] = os.getenv("GEMINI_API_KEY") or GEMINI_AI_CONFIG["api_key"]
BLOG_TOKEN = os.getenv("BLOG_API_TOKEN") or BLOG_TOKEN
LOG_LEVEL = os.getenv("LOG_LEVEL") or LOG_LEVEL
```

## Configuration Validation

### Validation Functions

```python
def validate_configuration() -> List[str]:
    """
    Validate system configuration and return list of errors.
    
    Returns:
        List[str]: List of validation errors, empty if valid
    """
    errors = []
    
    # Validate required API keys
    if not GITHUB_TOKENS or not any(GITHUB_TOKENS):
        errors.append("At least one GitHub token is required")
    
    if not PRIMARY_AI_CONFIG.get("api_key"):
        errors.append("OpenAI API key is required")
    
    # Validate database paths
    if not os.path.exists(DATABASE_PATH):
        try:
            os.makedirs(DATABASE_PATH)
        except Exception as e:
            errors.append(f"Cannot create database directory: {e}")
    
    # Validate log paths
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            errors.append(f"Cannot create log directory: {e}")
    
    # Validate monitoring settings
    if MONITOR_INTERVAL < 300:  # 5 minutes minimum
        errors.append("Monitor interval must be at least 300 seconds")
    
    return errors

def test_api_connectivity() -> dict:
    """
    Test connectivity to all configured APIs.
    
    Returns:
        dict: API connectivity status
    """
    results = {}
    
    # Test GitHub API
    for i, token in enumerate(GITHUB_TOKENS):
        if token:
            try:
                response = requests.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"},
                    timeout=10
                )
                results[f"github_token_{i+1}"] = response.status_code == 200
            except Exception:
                results[f"github_token_{i+1}"] = False
    
    # Test OpenAI API
    try:
        import openai
        client = openai.OpenAI(
            api_key=PRIMARY_AI_CONFIG["api_key"],
            base_url=PRIMARY_AI_CONFIG["base_url"]
        )
        models = client.models.list()
        results["openai_primary"] = True
    except Exception:
        results["openai_primary"] = False
    
    return results
```

## Best Practices

### Security Best Practices

1. **API Key Management**:
   - Use environment variables for sensitive data
   - Rotate API keys regularly
   - Monitor API key usage and rate limits
   - Use separate keys for different environments

2. **Database Security**:
   - Set appropriate file permissions (600 for database files)
   - Regular database backups
   - Monitor database size and performance
   - Use WAL mode for better concurrency

3. **Logging Security**:
   - Sanitize sensitive data in logs
   - Secure log file permissions
   - Regular log rotation and archival
   - Monitor for suspicious activities

### Performance Best Practices

1. **Resource Management**:
   - Monitor memory usage and limits
   - Use appropriate thread pool sizes
   - Implement proper rate limiting
   - Cache frequently accessed data

2. **API Usage**:
   - Respect rate limits and quotas
   - Implement exponential backoff
   - Use multiple tokens for better throughput
   - Monitor API costs and usage

3. **Database Optimization**:
   - Regular database maintenance
   - Proper indexing on frequently queried fields
   - Periodic cleanup of old records
   - Monitor database performance metrics

---

*This configuration guide provides comprehensive details for customizing CyberSentinel AI. For installation instructions, see the [Installation Guide](Installation-Guide.md). For daily operations, see the [User Manual](User-Manual.md).*