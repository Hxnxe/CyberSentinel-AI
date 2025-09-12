# Troubleshooting Guide

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with CyberSentinel AI.

## Quick Diagnosis

### System Health Check

Start with this quick health check script to identify common issues:

```bash
#!/bin/bash
# health_check.sh - Quick system diagnosis

echo "🔍 CyberSentinel AI Health Check"
echo "================================="

# Check if main process is running
if pgrep -f "python main.py" > /dev/null; then
    echo "✅ Main process is running"
    PID=$(pgrep -f "python main.py")
    echo "   Process ID: $PID"
else
    echo "❌ Main process is NOT running"
fi

# Check database files
if [ -f "database/cve_record.db" ]; then
    echo "✅ CVE database exists"
    SIZE=$(du -h database/cve_record.db | cut -f1)
    echo "   Size: $SIZE"
else
    echo "❌ CVE database missing"
fi

# Check log file
if [ -f "logs/security_monitor.log" ]; then
    echo "✅ Log file exists"
    AGE=$(stat -c %Y logs/security_monitor.log)
    NOW=$(date +%s)
    DIFF=$((NOW - AGE))
    if [ $DIFF -lt 3600 ]; then
        echo "   Status: Recently updated (${DIFF}s ago)"
    else
        echo "   ⚠️ Status: Last updated $((DIFF/3600)) hours ago"
    fi
else
    echo "❌ Log file missing"
fi

# Check recent errors
if [ -f "logs/security_monitor.log" ]; then
    ERROR_COUNT=$(tail -1000 logs/security_monitor.log | grep -c "ERROR\|CRITICAL")
    if [ $ERROR_COUNT -eq 0 ]; then
        echo "✅ No recent errors in logs"
    else
        echo "⚠️ Found $ERROR_COUNT recent errors"
    fi
fi

# Check disk space
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 90 ]; then
    echo "✅ Disk space OK ($DISK_USAGE% used)"
else
    echo "⚠️ Low disk space ($DISK_USAGE% used)"
fi

echo "================================="
echo "Health check complete"
```

## Installation and Startup Issues

### System Won't Start

#### Problem: Process exits immediately

**Symptoms**:
- Command `python main.py` exits without output
- No process visible in `ps aux | grep python`
- No recent entries in log files

**Diagnosis**:
```bash
# Check for immediate errors
python main.py 2>&1 | head -20

# Check configuration syntax
python -c "import config" 2>&1

# Check dependencies
pip check

# Check file permissions
ls -la *.py database/ logs/
```

**Solutions**:
1. **Fix configuration errors**:
   ```bash
   # Common configuration issues
   python -c "
   import config
   required = ['GITHUB_TOKENS', 'PRIMARY_AI_CONFIG']
   for item in required:
       if not hasattr(config, item) or not getattr(config, item):
           print(f'Missing: {item}')
   "
   ```

2. **Fix file permissions**:
   ```bash
   chmod 755 .
   chmod 644 *.py
   chmod 755 database/ logs/
   chmod 644 database/*.db logs/*.log
   ```

3. **Reinstall dependencies**:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

#### Problem: Import errors

**Symptoms**:
- `ModuleNotFoundError` messages
- `ImportError` messages
- Missing package errors

**Diagnosis**:
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check virtual environment
which python
which pip

# List installed packages
pip list | grep -E "(requests|openai|sqlite|schedule)"
```

**Solutions**:
```bash
# Activate virtual environment
source cybersentinel-env/bin/activate

# Update pip and reinstall
pip install --upgrade pip
pip install -r requirements.txt

# If virtual environment is corrupted, recreate it
deactivate
rm -rf cybersentinel-env
python3 -m venv cybersentinel-env
source cybersentinel-env/bin/activate
pip install -r requirements.txt
```

#### Problem: Permission denied errors

**Symptoms**:
- "Permission denied" when accessing files
- Database lock errors
- Cannot write to log files

**Diagnosis**:
```bash
# Check file ownership
ls -la database/ logs/

# Check directory permissions
stat database/ logs/

# Check disk space
df -h .

# Check for file locks
lsof database/*.db logs/*.log
```

**Solutions**:
```bash
# Fix ownership (replace 'username' with your username)
sudo chown -R username:username database/ logs/ data/

# Fix permissions
chmod 755 database/ logs/ data/
chmod 644 database/*.db logs/*.log

# Create missing directories
mkdir -p database logs data/reports data/analysis
```

## Configuration Issues

### API Authentication Problems

#### Problem: GitHub API authentication failures

**Symptoms**:
- "401 Unauthorized" errors in logs
- "Bad credentials" messages
- No repository data being collected

**Diagnosis**:
```bash
# Test GitHub token manually
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Check token in configuration
python -c "
import config
for i, token in enumerate(config.GITHUB_TOKENS):
    if token:
        print(f'Token {i+1}: {token[:8]}...')
    else:
        print(f'Token {i+1}: Empty')
"

# Check rate limits
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

**Solutions**:
1. **Verify token validity**:
   ```bash
   # Test each token
   for token in YOUR_TOKEN_1 YOUR_TOKEN_2; do
       echo "Testing token: ${token:0:8}..."
       curl -s -H "Authorization: token $token" https://api.github.com/user | jq .login
   done
   ```

2. **Regenerate tokens**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Delete old tokens and create new ones
   - Update configuration with new tokens

3. **Check token scopes**:
   ```bash
   # Check token scopes
   curl -I -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   # Look for X-OAuth-Scopes header
   ```

#### Problem: OpenAI API failures

**Symptoms**:
- "Invalid API key" errors
- "Rate limit exceeded" for OpenAI
- AI analysis not working

**Diagnosis**:
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer YOUR_OPENAI_KEY" \
     -H "Content-Type: application/json" \
     https://api.openai.com/v1/models

# Check configuration
python -c "
import config
ai_config = config.PRIMARY_AI_CONFIG
print(f'API Key: {ai_config.get(\"api_key\", \"Missing\")[:8]}...')
print(f'Base URL: {ai_config.get(\"base_url\", \"Missing\")}')
print(f'Model: {ai_config.get(\"model\", \"Missing\")}')
"
```

**Solutions**:
1. **Verify API key**:
   ```python
   # test_openai.py
   import openai
   import config
   
   try:
       client = openai.OpenAI(
           api_key=config.PRIMARY_AI_CONFIG["api_key"],
           base_url=config.PRIMARY_AI_CONFIG["base_url"]
       )
       models = client.models.list()
       print("✅ OpenAI API working")
       print(f"Available models: {[m.id for m in models.data[:3]]}")
   except Exception as e:
       print(f"❌ OpenAI API error: {e}")
   ```

2. **Check API usage and limits**:
   - Visit https://platform.openai.com/usage
   - Check current usage and rate limits
   - Ensure billing information is up to date

### Database Problems

#### Problem: Database corruption

**Symptoms**:
- "Database disk image is malformed" errors
- Inconsistent query results
- System crashes when accessing database

**Diagnosis**:
```bash
# Check database integrity
sqlite3 database/cve_record.db "PRAGMA integrity_check;"
sqlite3 database/github_repo.db "PRAGMA integrity_check;"

# Check database file
file database/*.db

# Check for locks
lsof database/*.db
```

**Solutions**:
1. **Repair database**:
   ```bash
   # Create backup first
   cp database/cve_record.db database/cve_record.db.backup
   
   # Try to repair
   sqlite3 database/cve_record.db ".recover" > cve_recovered.sql
   mv database/cve_record.db database/cve_record.db.corrupted
   sqlite3 database/cve_record.db < cve_recovered.sql
   
   # Verify repair
   sqlite3 database/cve_record.db "PRAGMA integrity_check;"
   ```

2. **Restore from backup**:
   ```bash
   # If you have backups
   cp backups/latest/cve_record.db database/
   
   # Or reinitialize (will lose data)
   rm database/*.db
   python init_database.py
   ```

#### Problem: Database locks

**Symptoms**:
- "Database is locked" errors
- Long delays when accessing database
- System hangs on database operations

**Diagnosis**:
```bash
# Check for processes using database
lsof database/*.db

# Check database mode
sqlite3 database/cve_record.db "PRAGMA journal_mode;"

# Check for WAL files
ls -la database/*.wal database/*.shm
```

**Solutions**:
```bash
# Stop all processes using database
pkill -f "python main.py"

# Remove lock files if present
rm -f database/*.wal database/*.shm

# Set WAL mode for better concurrency
sqlite3 database/cve_record.db "PRAGMA journal_mode=WAL;"
sqlite3 database/github_repo.db "PRAGMA journal_mode=WAL;"

# Restart system
python main.py
```

## Performance Issues

### High Memory Usage

#### Problem: Memory consumption keeps growing

**Symptoms**:
- Memory usage >2GB and growing
- System becomes sluggish
- Out of memory errors

**Diagnosis**:
```bash
# Monitor memory usage
ps -p $(pgrep -f "python main.py") -o pid,ppid,cmd,%mem,rss

# Check for memory leaks
python -c "
import psutil
import os
process = psutil.Process($(pgrep -f 'python main.py'))
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
print(f'Open files: {len(process.open_files())}')
"

# Check system memory
free -h
```

**Solutions**:
1. **Optimize configuration**:
   ```python
   # Add to config.py
   BATCH_SIZE = 10              # Smaller batches
   MAX_WORKERS = 2             # Fewer threads
   CACHE_MAX_SIZE = 100        # Smaller cache
   ANALYSIS_BATCH_SIZE = 5     # Smaller AI batches
   ```

2. **Implement memory monitoring**:
   ```python
   # memory_monitor.py
   import psutil
   import time
   import os
   
   def monitor_memory():
       process = psutil.Process(os.getpid())
       while True:
           mem_mb = process.memory_info().rss / 1024 / 1024
           if mem_mb > 1000:  # Alert if >1GB
               print(f"High memory usage: {mem_mb:.1f} MB")
           time.sleep(60)
   ```

3. **Restart periodically**:
   ```bash
   # Add to crontab for daily restart
   0 3 * * * /usr/bin/systemctl restart cybersentinel
   ```

### Slow Performance

#### Problem: System runs slowly

**Symptoms**:
- Long delays between monitoring cycles
- Slow database queries
- AI analysis takes too long

**Diagnosis**:
```bash
# Check CPU usage
top -p $(pgrep -f "python main.py")

# Check database performance
time sqlite3 database/cve_record.db "SELECT COUNT(*) FROM cve_records;"

# Check network latency
curl -w "%{time_total}" -s -o /dev/null https://api.github.com/
curl -w "%{time_total}" -s -o /dev/null https://api.openai.com/
```

**Solutions**:
1. **Database optimization**:
   ```sql
   -- Connect to database
   sqlite3 database/cve_record.db
   
   -- Add indexes
   CREATE INDEX IF NOT EXISTS idx_cve_discovery_date ON cve_records(discovery_date);
   CREATE INDEX IF NOT EXISTS idx_cve_analyzed ON cve_records(is_analyzed);
   CREATE INDEX IF NOT EXISTS idx_repo_last_update ON repositories(last_update);
   
   -- Optimize database
   VACUUM;
   ANALYZE;
   ```

2. **Increase intervals**:
   ```python
   # In config.py
   MONITOR_INTERVAL = 7200      # 2 hours instead of 1
   CVE_MONITOR_INTERVAL = 3600  # 1 hour instead of 30 minutes
   ```

3. **Use faster AI models**:
   ```python
   # In config.py
   PRIMARY_AI_CONFIG = {
       "model": "gpt-3.5-turbo",  # Faster than gpt-4
       "max_tokens": 1000,        # Shorter responses
       "temperature": 0.1
   }
   ```

## API and Network Issues

### Rate Limiting Problems

#### Problem: API rate limits exceeded

**Symptoms**:
- "Rate limit exceeded" errors
- 429 HTTP status codes
- Slow data collection

**Diagnosis**:
```bash
# Check current rate limits
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit

# Check OpenAI usage
curl -H "Authorization: Bearer YOUR_OPENAI_KEY" \
     https://api.openai.com/v1/usage

# Count API calls in logs
grep -c "API call" logs/security_monitor.log
```

**Solutions**:
1. **Add more GitHub tokens**:
   ```python
   # In config.py - add more tokens
   GITHUB_TOKENS = [
       "ghp_token1",
       "ghp_token2", 
       "ghp_token3",
       "ghp_token4",  # Add more tokens
       "ghp_token5"
   ]
   ```

2. **Implement better rate limiting**:
   ```python
   # In config.py
   GITHUB_RATE_LIMIT_THRESHOLD = 200  # Switch tokens earlier
   API_REQUEST_DELAY = 1              # Add delays between requests
   BATCH_DELAY = 5                    # Delay between batches
   ```

3. **Optimize API usage**:
   ```python
   # In config.py
   GITHUB_SEARCH_PER_PAGE = 100       # Get more results per request
   ENABLE_CACHING = True              # Cache API responses
   CACHE_TTL_SECONDS = 1800           # 30-minute cache
   ```

### Network Connectivity Issues

#### Problem: Network timeouts and connection errors

**Symptoms**:
- Connection timeout errors
- DNS resolution failures
- Intermittent API failures

**Diagnosis**:
```bash
# Test basic connectivity
ping -c 4 api.github.com
ping -c 4 api.openai.com

# Test DNS resolution
nslookup api.github.com
nslookup api.openai.com

# Test HTTP connectivity
curl -I https://api.github.com/
curl -I https://api.openai.com/v1/models
```

**Solutions**:
1. **Increase timeouts**:
   ```python
   # In config.py
   GITHUB_REQUEST_TIMEOUT = 60        # Increase from 30
   PRIMARY_AI_CONFIG = {
       "timeout": 120,                # Increase AI timeout
       "max_retries": 5              # More retries
   }
   ```

2. **Implement retry logic**:
   ```python
   # Add to utils/
   import time
   import random
   
   def retry_with_backoff(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except Exception as e:
               if attempt < max_retries - 1:
                   delay = (2 ** attempt) + random.uniform(0, 1)
                   time.sleep(delay)
               else:
                   raise e
   ```

## Data and Analysis Issues

### No Data Collection

#### Problem: System runs but no data is collected

**Symptoms**:
- Empty databases
- No new records being created
- Logs show monitoring activity but no results

**Diagnosis**:
```bash
# Check database content
sqlite3 database/cve_record.db "SELECT COUNT(*) FROM cve_records;"
sqlite3 database/github_repo.db "SELECT COUNT(*) FROM repositories;"

# Check recent activity
sqlite3 database/cve_record.db "SELECT COUNT(*) FROM cve_records WHERE date(discovery_date) >= date('now', '-1 day');"

# Check API responses in logs
grep "API response" logs/security_monitor.log | tail -10
```

**Solutions**:
1. **Check filtering criteria**:
   ```python
   # Review config.py filtering settings
   MIN_REPOSITORY_STARS = 5          # Lower threshold
   MIN_RELEVANCE_SCORE = 0.1         # Lower threshold
   BLACKLIST_USERS = []              # Temporarily empty
   BLACKLIST_REPOSITORIES = []       # Temporarily empty
   ```

2. **Test API calls manually**:
   ```bash
   # Test GitHub search
   curl -H "Authorization: token YOUR_TOKEN" \
        "https://api.github.com/search/repositories?q=CVE-2024+in:name,description&sort=updated"
   
   # Check if results are returned
   ```

3. **Enable debug logging**:
   ```python
   # In config.py
   LOG_LEVEL = "DEBUG"
   COMPONENT_LOG_LEVELS = {
       "cve_monitor": "DEBUG",
       "github_monitor": "DEBUG"
   }
   ```

### AI Analysis Failures

#### Problem: AI analysis not working

**Symptoms**:
- Records in database but no analysis results
- AI analysis timeout errors
- Invalid JSON responses from AI

**Diagnosis**:
```bash
# Check analysis status
sqlite3 database/cve_record.db "SELECT COUNT(*), SUM(is_analyzed) FROM cve_records;"

# Check AI errors in logs
grep "AI analysis" logs/security_monitor.log | grep "ERROR"

# Test AI manually
python -c "
import config
from ai.analyzer import AIAnalyzer
analyzer = AIAnalyzer(config.PRIMARY_AI_CONFIG)
result = analyzer.analyze_text('Test CVE-2024-12345 vulnerability')
print(result)
"
```

**Solutions**:
1. **Fix AI configuration**:
   ```python
   # Verify config.py
   PRIMARY_AI_CONFIG = {
       "api_key": "sk-...",           # Valid key
       "base_url": "https://api.openai.com/v1",
       "model": "gpt-4o-mini-2024-07-18",
       "max_tokens": 2000,
       "temperature": 0.1,
       "timeout": 60
   }
   ```

2. **Simplify AI prompts**:
   ```python
   # Use simpler prompts for testing
   TEST_PROMPT = """
   Analyze this security item and respond with JSON:
   {"risk_level": "Medium", "summary": "Brief description"}
   
   Item: {input_text}
   """
   ```

3. **Implement fallback models**:
   ```python
   # In config.py
   BACKUP_AI_CONFIGS = [
       {"model": "gpt-3.5-turbo", ...},  # Faster fallback
       {"model": "gpt-4", ...}           # High-quality fallback
   ]
   ```

## Log Analysis and Debugging

### Understanding Log Messages

#### Common log patterns and their meanings:

```bash
# Normal operation
INFO - cve_monitor - Starting CVE monitoring cycle
INFO - github_monitor - Found 25 repositories to analyze
INFO - ai_analyzer - Analysis completed for CVE-2024-12345

# Rate limiting
WARNING - github_monitor - Rate limit approaching: 150 remaining
INFO - github_monitor - Switching to token 2

# Errors to investigate
ERROR - database - Database connection failed
CRITICAL - ai_analyzer - All AI models failed
ERROR - config - Missing required configuration: GITHUB_TOKENS
```

#### Log analysis commands:

```bash
# Count errors by type
grep "ERROR" logs/security_monitor.log | cut -d' ' -f4 | sort | uniq -c

# Find performance bottlenecks
grep "took [0-9]*s" logs/security_monitor.log | sort -k3 -nr | head -10

# Check API success rates
grep "API call" logs/security_monitor.log | tail -100 | \
  awk '{if(/success/) s++; else f++} END {print "Success:", s, "Failed:", f}'

# Monitor memory usage over time
grep "Memory usage" logs/security_monitor.log | tail -20
```

### Advanced Debugging

#### Enable verbose logging:

```python
# debug_config.py
import logging

# Override log configuration for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Enable SQL logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Performance profiling:

```python
# profile_performance.py
import cProfile
import pstats
from main import CyberSentinelAI

def profile_system():
    """Profile system performance."""
    system = CyberSentinelAI()
    
    # Profile monitoring cycle
    profiler = cProfile.Profile()
    profiler.enable()
    
    system.run_monitoring_cycle()
    
    profiler.disable()
    
    # Save results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    stats.dump_stats('performance_profile.stats')

if __name__ == "__main__":
    profile_system()
```

## Emergency Procedures

### System Recovery

#### Complete system failure:

```bash
# 1. Stop all processes
pkill -f "python main.py"

# 2. Check system resources
df -h
free -h
ps aux | head -20

# 3. Backup current state
mkdir emergency_backup_$(date +%Y%m%d_%H%M)
cp -r database/ logs/ config.py emergency_backup_$(date +%Y%m%d_%H%M)/

# 4. Restore from known good backup
cp backups/latest/*.db database/
cp backups/latest/config.py .

# 5. Restart with minimal configuration
python main.py --safe-mode --verbose
```

#### Data corruption recovery:

```bash
# 1. Stop system
systemctl stop cybersentinel

# 2. Backup corrupted data
mv database/ database_corrupted_$(date +%Y%m%d)

# 3. Restore from backup
cp -r backups/latest/ database/

# 4. Verify integrity
sqlite3 database/cve_record.db "PRAGMA integrity_check;"

# 5. Restart system
systemctl start cybersentinel
```

### Getting Additional Help

If troubleshooting steps don't resolve your issue:

1. **Collect diagnostic information**:
   ```bash
   # Create support bundle
   tar -czf cybersentinel_diagnostics_$(date +%Y%m%d).tar.gz \
       logs/ config.py.example database/*.db.stats system_info.txt
   ```

2. **System information script**:
   ```bash
   # system_info.sh
   echo "System Information" > system_info.txt
   echo "==================" >> system_info.txt
   uname -a >> system_info.txt
   python3 --version >> system_info.txt
   pip list >> system_info.txt
   df -h >> system_info.txt
   free -h >> system_info.txt
   ```

3. **Submit issue with**:
   - Complete error messages and stack traces
   - Relevant log excerpts
   - System information
   - Steps to reproduce the problem
   - What troubleshooting steps you've already tried

---

*This troubleshooting guide covers the most common issues with CyberSentinel AI. For additional support, please refer to the [FAQ](FAQ.md) or submit an issue on GitHub.*