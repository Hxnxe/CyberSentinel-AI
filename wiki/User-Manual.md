# User Manual

This comprehensive user manual provides guidance for daily operations, monitoring, and management of CyberSentinel AI.

## Getting Started

### First Time Setup

After completing the [Installation Guide](Installation-Guide.md), follow these steps to get started:

1. **Verify Configuration**:
   ```bash
   python -c "import config; print('✅ Configuration loaded successfully')"
   ```

2. **Test API Connectivity**:
   ```bash
   python test_config.py
   ```

3. **Initialize Databases**:
   ```bash
   python init_database.py
   ```

4. **Start Monitoring**:
   ```bash
   python main.py
   ```

### Daily Operations Overview

CyberSentinel AI operates in continuous monitoring cycles, typically requiring minimal daily intervention. The system:

- **Monitors** CVE databases and GitHub repositories automatically
- **Analyzes** findings using AI models
- **Generates** daily security briefing reports
- **Publishes** reports to configured blog platforms
- **Maintains** databases and logs automatically

## System Operation

### Starting the System

#### Standard Startup
```bash
# Navigate to project directory
cd /path/to/CyberSentinel-AI

# Activate virtual environment
source cybersentinel-env/bin/activate

# Start monitoring system
python main.py
```

#### Startup with Options
```bash
# Start with verbose logging
python main.py --verbose

# Start in dry-run mode (no database writes)
python main.py --dry-run

# Start with custom config file
python main.py --config custom_config.py

# Start in daemon mode (background)
python main.py --daemon
```

#### Using systemd (Linux)

Create a systemd service file for automatic startup:

```ini
# /etc/systemd/system/cybersentinel.service
[Unit]
Description=CyberSentinel AI Security Monitor
After=network.target

[Service]
Type=simple
User=cybersentinel
WorkingDirectory=/opt/cybersentinel-ai
Environment=PATH=/opt/cybersentinel-ai/cybersentinel-env/bin
ExecStart=/opt/cybersentinel-ai/cybersentinel-env/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable cybersentinel
sudo systemctl start cybersentinel
sudo systemctl status cybersentinel
```

### Monitoring System Health

#### Real-time Log Monitoring
```bash
# Follow main log file
tail -f logs/security_monitor.log

# Monitor error messages only
tail -f logs/security_monitor.log | grep ERROR

# Monitor specific component
tail -f logs/security_monitor.log | grep "cve_monitor"
```

#### System Status Check
```bash
# Check if process is running
ps aux | grep python | grep main.py

# Check system resource usage
top -p $(pgrep -f "python main.py")

# Check database sizes
du -sh database/*.db

# Check log file sizes
du -sh logs/*.log
```

#### Health Check Script
```python
# health_check.py
import requests
import sqlite3
import os
from datetime import datetime, timedelta

def check_system_health():
    """Comprehensive system health check."""
    health_status = {}
    
    # Check database accessibility
    try:
        conn = sqlite3.connect("database/cve_record.db")
        cursor = conn.execute("SELECT COUNT(*) FROM cve_records")
        cve_count = cursor.fetchone()[0]
        conn.close()
        health_status["database"] = {"status": "healthy", "cve_records": cve_count}
    except Exception as e:
        health_status["database"] = {"status": "error", "error": str(e)}
    
    # Check log file freshness
    try:
        log_file = "logs/security_monitor.log"
        if os.path.exists(log_file):
            mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            age_hours = (datetime.now() - mod_time).total_seconds() / 3600
            if age_hours < 2:  # Log should be updated within 2 hours
                health_status["logging"] = {"status": "healthy", "last_update": mod_time}
            else:
                health_status["logging"] = {"status": "stale", "last_update": mod_time}
    except Exception as e:
        health_status["logging"] = {"status": "error", "error": str(e)}
    
    # Check API connectivity
    health_status["apis"] = test_api_connectivity()
    
    return health_status

if __name__ == "__main__":
    status = check_system_health()
    print(json.dumps(status, indent=2, default=str))
```

### Managing the System

#### Graceful Shutdown
```bash
# Send SIGTERM to allow graceful shutdown
pkill -TERM -f "python main.py"

# Or use systemctl if running as service
sudo systemctl stop cybersentinel
```

#### Restart System
```bash
# For systemd service
sudo systemctl restart cybersentinel

# For manual process
pkill -TERM -f "python main.py"
sleep 5
python main.py &
```

#### Update Configuration
```bash
# Edit configuration file
nano config.py

# Validate new configuration
python -c "import config; print('Configuration valid')"

# Restart system to apply changes
sudo systemctl restart cybersentinel
```

## Daily Workflows

### Morning Routine (5 minutes)

1. **Check System Status**:
   ```bash
   # Quick status check
   systemctl status cybersentinel
   python health_check.py
   ```

2. **Review Overnight Activity**:
   ```bash
   # Check for errors in last 24 hours
   tail -1000 logs/security_monitor.log | grep -E "(ERROR|CRITICAL)" | tail -20
   
   # Check analysis progress
   sqlite3 database/cve_record.db "SELECT COUNT(*) FROM cve_records WHERE date(discovery_date) = date('now');"
   ```

3. **Review Daily Report**:
   ```bash
   # Open latest daily report
   ls -t data/reports/ | head -1 | xargs -I {} cat "data/reports/{}"
   ```

### Weekly Maintenance (15 minutes)

1. **Database Maintenance**:
   ```bash
   # Vacuum databases to reclaim space
   sqlite3 database/cve_record.db "VACUUM;"
   sqlite3 database/github_repo.db "VACUUM;"
   
   # Check database integrity
   sqlite3 database/cve_record.db "PRAGMA integrity_check;"
   ```

2. **Log Cleanup**:
   ```bash
   # Archive old logs
   find logs/ -name "*.log.*" -mtime +30 -delete
   
   # Check log disk usage
   du -sh logs/
   ```

3. **API Usage Review**:
   ```bash
   # Check GitHub API rate limits
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
   
   # Review API costs (OpenAI dashboard)
   echo "Check OpenAI usage at https://platform.openai.com/usage"
   ```

4. **System Performance Review**:
   ```bash
   # Check memory usage trends
   grep "Memory usage" logs/security_monitor.log | tail -10
   
   # Review analysis success rates
   grep "Analysis completed" logs/security_monitor.log | wc -l
   grep "Analysis failed" logs/security_monitor.log | wc -l
   ```

### Monthly Tasks (30 minutes)

1. **Database Backup**:
   ```bash
   # Create monthly backup
   mkdir -p backups/$(date +%Y-%m)
   cp database/*.db backups/$(date +%Y-%m)/
   
   # Compress old backups
   find backups/ -name "*.db" -mtime +7 -exec gzip {} \;
   ```

2. **Configuration Review**:
   ```bash
   # Review blacklists for false positives
   sqlite3 database/github_repo.db "SELECT name, url FROM repositories WHERE relevance_score < 0.3 LIMIT 20;"
   
   # Check for deprecated API endpoints
   grep -i "deprecated" logs/security_monitor.log
   ```

3. **Performance Optimization**:
   ```bash
   # Analyze database query performance
   sqlite3 database/cve_record.db ".timer on" "SELECT * FROM cve_records ORDER BY discovery_date DESC LIMIT 100;"
   
   # Review system resource usage
   sar -u 1 10  # CPU usage
   sar -r 1 10  # Memory usage
   ```

## Working with Data

### Database Operations

#### Querying CVE Records
```sql
-- Connect to CVE database
sqlite3 database/cve_record.db

-- Recent CVE discoveries
SELECT cve_number, description, discovery_date 
FROM cve_records 
WHERE discovery_date >= date('now', '-7 days')
ORDER BY discovery_date DESC;

-- High-risk CVEs
SELECT cve_number, description, severity_score
FROM cve_records 
WHERE JSON_EXTRACT(analysis_result, '$.risk_level') = 'Critical'
ORDER BY discovery_date DESC;

-- CVE analysis status
SELECT 
  COUNT(*) as total,
  SUM(is_analyzed) as analyzed,
  COUNT(*) - SUM(is_analyzed) as pending
FROM cve_records;
```

#### Querying Repository Records
```sql
-- Connect to repository database
sqlite3 database/github_repo.db

-- High-value repositories
SELECT name, url, star_count, relevance_score
FROM repositories 
WHERE is_high_value = 1
ORDER BY star_count DESC;

-- Recent repository updates
SELECT name, url, last_update
FROM repositories 
WHERE last_update >= datetime('now', '-24 hours')
ORDER BY last_update DESC;

-- Repository analysis summary
SELECT 
  COUNT(*) as total_repos,
  AVG(relevance_score) as avg_relevance,
  COUNT(CASE WHEN is_high_value = 1 THEN 1 END) as high_value_count
FROM repositories;
```

#### Data Export
```bash
# Export CVE data to CSV
sqlite3 -header -csv database/cve_record.db "SELECT * FROM cve_records;" > cve_export.csv

# Export repository data to JSON
python -c "
import sqlite3, json
conn = sqlite3.connect('database/github_repo.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute('SELECT * FROM repositories LIMIT 100')
data = [dict(row) for row in cursor]
print(json.dumps(data, indent=2, default=str))
" > repo_export.json
```

### Report Management

#### Viewing Daily Reports
```bash
# List recent reports
ls -lt data/reports/ | head -10

# View latest report
cat data/reports/$(ls -t data/reports/ | head -1)

# Search reports for specific CVE
grep -r "CVE-2024-" data/reports/

# Count items in today's report
grep -c "^*" data/reports/security-briefing-$(date +%Y-%m-%d).md
```

#### Manual Report Generation
```python
# generate_report.py
from utils.article_manager import ArticleManager
from datetime import datetime

def generate_manual_report():
    """Generate a manual security briefing report."""
    manager = ArticleManager()
    
    # Generate report for specific date
    report_date = datetime.now()
    report_content = manager.generate_daily_briefing(report_date)
    
    # Save report
    filename = f"manual-report-{report_date.strftime('%Y-%m-%d-%H%M')}.md"
    with open(f"data/reports/{filename}", "w") as f:
        f.write(report_content)
    
    print(f"Manual report generated: {filename}")

if __name__ == "__main__":
    generate_manual_report()
```

#### Report Analytics
```python
# report_analytics.py
import os, re
from collections import Counter
from datetime import datetime, timedelta

def analyze_reports(days_back=30):
    """Analyze recent reports for trends."""
    report_dir = "data/reports"
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    cve_counts = []
    repo_counts = []
    
    for filename in os.listdir(report_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(report_dir, filename)
            file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_date >= cutoff_date:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Count CVEs mentioned
                cve_matches = re.findall(r'CVE-\d{4}-\d+', content)
                cve_counts.append(len(set(cve_matches)))
                
                # Count repository links
                repo_matches = re.findall(r'github\.com/[^/\s)]+/[^/\s)]+', content)
                repo_counts.append(len(set(repo_matches)))
    
    print(f"Report Analysis (Last {days_back} days):")
    print(f"Average CVEs per report: {sum(cve_counts)/len(cve_counts):.1f}")
    print(f"Average repositories per report: {sum(repo_counts)/len(repo_counts):.1f}")
    print(f"Total reports analyzed: {len(cve_counts)}")

if __name__ == "__main__":
    analyze_reports()
```

## Troubleshooting Common Issues

### System Not Starting

**Symptoms**: Process exits immediately or fails to start

**Diagnosis**:
```bash
# Check configuration validity
python -c "import config"

# Check for permission issues
ls -la database/
ls -la logs/

# Check for port conflicts
netstat -tulpn | grep :8080  # if using web interface
```

**Solutions**:
- Fix configuration errors in `config.py`
- Ensure proper file permissions (755 for directories, 644 for files)
- Check available disk space
- Verify Python environment and dependencies

### High Memory Usage

**Symptoms**: System consuming excessive memory

**Diagnosis**:
```bash
# Monitor memory usage
top -p $(pgrep -f "python main.py")

# Check for memory leaks
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

**Solutions**:
- Reduce batch sizes in configuration
- Increase monitoring intervals
- Clear old analysis results from memory
- Restart system periodically

### API Rate Limiting

**Symptoms**: API errors or delays in data collection

**Diagnosis**:
```bash
# Check GitHub rate limits
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit

# Review API usage in logs
grep "rate limit" logs/security_monitor.log | tail -10
```

**Solutions**:
- Add more GitHub tokens to configuration
- Increase monitoring intervals
- Implement more aggressive caching
- Use backup API endpoints

### Database Issues

**Symptoms**: Database errors or corruption

**Diagnosis**:
```bash
# Check database integrity
sqlite3 database/cve_record.db "PRAGMA integrity_check;"

# Check database locks
lsof database/*.db

# Check disk space
df -h
```

**Solutions**:
- Stop system and check for file locks
- Run database integrity check and repair
- Ensure adequate disk space
- Restore from backup if necessary

## Advanced Usage

### Custom Analysis Rules

Create custom analysis rules for specific use cases:

```python
# custom_rules.py
def custom_cve_filter(cve_data):
    """Custom filter for CVE records."""
    # Only analyze CVEs with CVSS score > 7.0
    if cve_data.get('cvss_score', 0) > 7.0:
        return True
    
    # Always analyze CVEs with specific keywords
    keywords = ['remote code execution', 'privilege escalation', 'authentication bypass']
    description = cve_data.get('description', '').lower()
    
    return any(keyword in description for keyword in keywords)

def custom_repository_scoring(repo_data):
    """Custom scoring algorithm for repositories."""
    score = 0.0
    
    # Base score from stars (normalized)
    stars = repo_data.get('star_count', 0)
    score += min(stars / 1000, 0.3)  # Max 0.3 from stars
    
    # Bonus for recent activity
    last_update = repo_data.get('last_update')
    if last_update and is_recent(last_update, days=30):
        score += 0.2
    
    # Bonus for security-related topics
    topics = repo_data.get('topics', [])
    security_topics = ['security', 'vulnerability', 'penetration-testing']
    if any(topic in security_topics for topic in topics):
        score += 0.3
    
    return min(score, 1.0)  # Cap at 1.0
```

### Integration with External Tools

#### SIEM Integration
```python
# siem_integration.py
import json
import requests
from datetime import datetime

def send_to_siem(event_data):
    """Send security events to SIEM system."""
    siem_endpoint = "https://your-siem.com/api/events"
    
    # Format event for SIEM
    siem_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": "CyberSentinel-AI",
        "event_type": event_data.get("type"),
        "severity": event_data.get("risk_level"),
        "description": event_data.get("description"),
        "raw_data": event_data
    }
    
    # Send to SIEM
    response = requests.post(
        siem_endpoint,
        json=siem_event,
        headers={"Authorization": "Bearer YOUR_SIEM_TOKEN"}
    )
    
    return response.status_code == 200
```

#### Slack Notifications
```python
# slack_notifications.py
import requests
import json

def send_critical_alert(cve_data):
    """Send critical CVE alerts to Slack."""
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    
    # Format Slack message
    message = {
        "text": f"🚨 Critical CVE Alert: {cve_data['cve_number']}",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {"title": "CVE", "value": cve_data['cve_number'], "short": True},
                    {"title": "Risk Level", "value": cve_data['risk_level'], "short": True},
                    {"title": "Description", "value": cve_data['description'][:500]}
                ]
            }
        ]
    }
    
    # Send notification
    response = requests.post(webhook_url, json=message)
    return response.status_code == 200
```

## Tips and Best Practices

### Optimization Tips

1. **Resource Management**:
   - Monitor memory usage regularly
   - Use appropriate batch sizes for processing
   - Implement cleanup routines for old data
   - Consider using external caching for large datasets

2. **API Efficiency**:
   - Use multiple API tokens for better rate limits
   - Implement intelligent caching strategies
   - Batch API requests when possible
   - Monitor API costs and usage patterns

3. **Data Quality**:
   - Regularly review and update blacklists
   - Implement data validation and sanitization
   - Monitor false positive rates
   - Continuously refine analysis prompts

### Security Best Practices

1. **Access Control**:
   - Use dedicated service accounts
   - Implement least privilege access
   - Regularly rotate API keys
   - Monitor access logs for anomalies

2. **Data Protection**:
   - Encrypt sensitive configuration data
   - Secure database files with proper permissions
   - Implement secure log storage
   - Regular backup and disaster recovery testing

3. **Monitoring**:
   - Set up alerts for system failures
   - Monitor resource usage and performance
   - Track API usage and costs
   - Implement security event logging

---

*This user manual provides comprehensive guidance for daily operations of CyberSentinel AI. For technical details, see the [Code Documentation](Code-Documentation.md). For configuration options, see the [Configuration Guide](Configuration-Guide.md).*