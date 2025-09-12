# FAQ - Frequently Asked Questions

This page addresses common questions about CyberSentinel AI, covering installation, configuration, operation, and troubleshooting.

## General Questions

### What is CyberSentinel AI?

**Q**: What exactly does CyberSentinel AI do?

**A**: CyberSentinel AI is an automated security monitoring and AI analysis system that:
- Continuously monitors CVE databases and GitHub repositories for security-related content
- Uses artificial intelligence (OpenAI GPT and Google Gemini) to analyze and categorize findings
- Generates daily security briefing reports with intelligent filtering and prioritization
- Automatically publishes findings to blog platforms
- Maintains a comprehensive database of security intelligence

### Who should use CyberSentinel AI?

**Q**: Is this tool suitable for my use case?

**A**: CyberSentinel AI is designed for:
- **Security professionals** who need continuous threat intelligence
- **SOC analysts** requiring automated vulnerability monitoring
- **Security researchers** tracking the latest developments
- **Organizations** needing comprehensive security awareness
- **Bug bounty hunters** looking for the latest vulnerability research
- **Anyone** interested in staying informed about cybersecurity trends

### How much does it cost to run?

**Q**: What are the operational costs?

**A**: The main costs are:
- **OpenAI API usage**: ~$10-50/month depending on analysis volume
- **GitHub API**: Free (with rate limits) or GitHub Pro for higher limits
- **Google Gemini API**: Optional backup, free tier available
- **Server hosting**: $5-20/month for a small VPS
- **Blog platform**: Varies by provider (many free options available)

Total estimated cost: **$15-100/month** depending on scale and usage.

## Installation and Setup

### System Requirements

**Q**: What are the minimum system requirements?

**A**: 
- **Operating System**: Linux (Ubuntu 18.04+), macOS (10.14+), or Windows 10
- **Python**: Version 3.8 or higher (3.9+ recommended)
- **Memory**: 2GB minimum, 4GB recommended
- **Storage**: 1GB for logs and databases (5GB+ for extensive historical data)
- **Network**: Stable internet connection for API access

### Installation Issues

**Q**: I'm getting "ModuleNotFoundError" when starting the system.

**A**: This usually indicates missing Python dependencies. Try:
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Check virtual environment
source cybersentinel-env/bin/activate
which python  # Should point to virtual environment
```

**Q**: The system fails to start with configuration errors.

**A**: Verify your configuration:
```bash
# Test configuration validity
python -c "import config; print('Configuration valid')"

# Check for required API keys
python test_config.py

# Verify file permissions
ls -la config.py database/ logs/
```

**Q**: How do I get GitHub API tokens?

**A**: To obtain GitHub Personal Access Tokens:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token"
3. Select scopes: `public_repo`, `read:org` (optional)
4. Copy the token and add it to your configuration
5. For multiple tokens, repeat this process with different GitHub accounts

### Configuration Problems

**Q**: How many GitHub tokens do I need?

**A**: 
- **Minimum**: 1 token (5,000 requests/hour)
- **Recommended**: 3-5 tokens (15,000-25,000 requests/hour)
- **High volume**: 10+ tokens for enterprise use

Each token provides 5,000 requests per hour. The system automatically rotates between available tokens.

**Q**: Which OpenAI model should I use?

**A**: Model recommendations:
- **Primary**: `gpt-4o-mini-2024-07-18` (cost-effective, good quality)
- **Backup**: `gpt-3.5-turbo` (faster, lower cost)
- **High quality**: `gpt-4` (best analysis, higher cost)

For most users, `gpt-4o-mini` provides the best balance of cost and quality.

## Operation and Usage

### Daily Operations

**Q**: How much daily maintenance does the system require?

**A**: Very minimal:
- **Daily**: 5-minute health check (optional but recommended)
- **Weekly**: 15-minute maintenance (log cleanup, database optimization)
- **Monthly**: 30-minute review (performance optimization, configuration updates)

The system is designed to run autonomously with minimal intervention.

**Q**: How do I know if the system is working correctly?

**A**: Check these indicators:
- **Process running**: `ps aux | grep "python main.py"`
- **Recent logs**: `tail -f logs/security_monitor.log`
- **Database updates**: New records in CVE and repository databases
- **Daily reports**: Generated reports in `data/reports/` directory
- **No critical errors**: Check logs for ERROR or CRITICAL messages

**Q**: The system seems slow. How can I improve performance?

**A**: Performance optimization steps:
1. **Increase monitoring intervals** in configuration
2. **Add more GitHub tokens** for better rate limits
3. **Reduce batch sizes** if memory usage is high
4. **Enable caching** for frequently accessed data
5. **Use faster AI models** (e.g., gpt-3.5-turbo)
6. **Archive old data** from databases

### Data and Reports

**Q**: Where are the generated reports stored?

**A**: Reports are stored in:
- **Directory**: `data/reports/`
- **Format**: Markdown files named `security-briefing-YYYY-MM-DD.md`
- **Content**: Daily security briefings with CVE analysis, repository updates, and security articles

**Q**: How can I access historical data?

**A**: Historical data is available in:
- **CVE Database**: `database/cve_record.db` (SQLite)
- **Repository Database**: `database/github_repo.db` (SQLite)
- **Daily Reports**: `data/reports/` directory
- **Analysis Results**: JSON files in `data/analysis/`

Use SQL queries or the provided scripts to extract specific data.

**Q**: Can I customize the report format?

**A**: Yes, reports are highly customizable:
- **Template editing**: Modify report templates in `utils/article_manager.py`
- **Section control**: Configure `REPORT_SECTIONS` in `config.py`
- **Content filtering**: Adjust `REPORT_MIN_RELEVANCE_SCORE`
- **Custom sections**: Add new sections through configuration

### AI Analysis

**Q**: How accurate is the AI analysis?

**A**: AI analysis accuracy depends on several factors:
- **CVE Analysis**: ~85-95% accuracy for risk assessment and technical details
- **Repository Analysis**: ~80-90% accuracy for relevance and value assessment
- **False Positives**: ~5-10% rate (continuously improving through feedback)
- **Coverage**: Analyzes 100% of collected data automatically

The system uses multiple AI models and validation checks to ensure quality.

**Q**: Can I train the AI on my specific needs?

**A**: While you can't directly train the models, you can customize analysis:
- **Prompt engineering**: Modify analysis prompts in configuration
- **Custom filters**: Add domain-specific filtering rules
- **Scoring adjustments**: Customize relevance scoring algorithms
- **Feedback loops**: The system learns from blacklist updates

**Q**: What happens if AI analysis fails?

**A**: The system has multiple fallback mechanisms:
- **Backup models**: Automatically switches to backup OpenAI or Gemini
- **Retry logic**: Attempts analysis multiple times with backoff
- **Graceful degradation**: Continues monitoring without analysis if all AI fails
- **Manual queuing**: Failed items can be reprocessed later

## Troubleshooting

### Common Error Messages

**Q**: "API rate limit exceeded" errors

**A**: Solutions:
- **Add more tokens**: Configure additional GitHub tokens
- **Increase intervals**: Extend `MONITOR_INTERVAL` in configuration
- **Check token health**: Verify tokens are valid and not expired
- **Implement delays**: Add delays between API calls

**Q**: "Database is locked" errors

**A**: This indicates database access conflicts:
```bash
# Check for process locks
lsof database/*.db

# Stop the system gracefully
pkill -TERM -f "python main.py"

# Wait and restart
sleep 10
python main.py
```

**Q**: "AI analysis timeout" errors

**A**: Try these solutions:
- **Reduce batch size**: Process fewer items at once
- **Increase timeout**: Extend `timeout` in AI configuration
- **Switch models**: Use faster AI models like `gpt-3.5-turbo`
- **Check API status**: Verify OpenAI/Gemini service status

### Performance Issues

**Q**: High memory usage (>2GB)

**A**: Memory optimization steps:
```python
# Add to config.py
BATCH_SIZE = 10              # Smaller batches
MAX_WORKERS = 2             # Fewer threads
CACHE_MAX_SIZE = 500        # Smaller cache
MEMORY_CHECK_INTERVAL = 300 # Monitor memory more frequently
```

Also consider:
- **Restart periodically**: Add automatic restart schedule
- **Archive old data**: Remove old records from databases
- **Monitor trends**: Track memory usage over time

**Q**: Slow database queries

**A**: Database optimization:
```sql
-- Connect to database
sqlite3 database/cve_record.db

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_cve_discovery_date ON cve_records(discovery_date);
CREATE INDEX IF NOT EXISTS idx_cve_analyzed ON cve_records(is_analyzed);

-- Vacuum database to reclaim space
VACUUM;

-- Update statistics
ANALYZE;
```

### Integration Issues

**Q**: Blog publishing not working

**A**: Check blog integration:
- **API credentials**: Verify `BLOG_TOKEN` is correct
- **Endpoint URLs**: Confirm `BLOG_BASE_URL` is accurate
- **Permissions**: Ensure API token has publishing rights
- **Network access**: Test connectivity to blog platform
- **Rate limits**: Check if blog platform has rate limiting

**Q**: Reports not generating

**A**: Debug report generation:
```bash
# Check report directory permissions
ls -la data/reports/

# Test manual report generation
python -c "
from utils.article_manager import ArticleManager
manager = ArticleManager()
report = manager.generate_daily_briefing()
print('Report generated successfully')
"

# Check for data availability
sqlite3 database/cve_record.db "SELECT COUNT(*) FROM cve_records WHERE date(discovery_date) = date('now');"
```

## Advanced Usage

### Customization

**Q**: Can I add custom data sources?

**A**: Yes, the system is designed for extensibility:
- **Article sources**: Add new sources in `utils/article_fetcher.py`
- **Monitoring targets**: Extend monitors in `monitors/` directory
- **Analysis types**: Add custom analysis in `ai/analyzer.py`
- **Output formats**: Create custom formatters in `utils/`

**Q**: How do I integrate with my existing security tools?

**A**: Integration options:
- **SIEM integration**: Export data to SIEM platforms via APIs
- **Webhook notifications**: Send alerts to external systems
- **Database exports**: Regular exports to external databases
- **API endpoints**: Expose data through REST APIs
- **Custom scripts**: Build scripts using the database directly

**Q**: Can I run multiple instances?

**A**: Yes, but with considerations:
- **Database locking**: Use separate database files for each instance
- **API rate limits**: Distribute tokens across instances
- **File conflicts**: Use separate log and output directories
- **Coordination**: Implement coordination to avoid duplicate work

### Scaling and Performance

**Q**: How do I scale for enterprise use?

**A**: Enterprise scaling strategies:
- **Distributed deployment**: Run multiple instances across servers
- **Database migration**: Move to PostgreSQL or MongoDB
- **Caching layer**: Add Redis for distributed caching
- **Load balancing**: Distribute API calls across multiple endpoints
- **Container deployment**: Use Docker/Kubernetes for orchestration

**Q**: What's the maximum throughput?

**A**: Throughput depends on several factors:
- **GitHub API**: 5,000 requests/hour per token
- **AI analysis**: 60-100 items/minute (depends on model and complexity)
- **Database writes**: 1,000+ records/minute (SQLite limitation)
- **Network bandwidth**: Varies by deployment

Typical enterprise deployment: **10,000-50,000 items analyzed per day**

### Maintenance and Updates

**Q**: How do I update the system?

**A**: Update process:
```bash
# Backup current data
cp -r database/ backups/$(date +%Y%m%d)/
cp config.py backups/$(date +%Y%m%d)/

# Pull updates
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Check configuration compatibility
python -c "import config; print('Configuration compatible')"

# Restart system
sudo systemctl restart cybersentinel
```

**Q**: How often should I backup data?

**A**: Backup schedule recommendations:
- **Database**: Daily automated backups
- **Configuration**: Before any changes
- **Logs**: Weekly archives (keep 30 days)
- **Reports**: Monthly archives (keep 1 year)

**Q**: What should I monitor for system health?

**A**: Key health metrics:
- **Process uptime**: System should run continuously
- **Memory usage**: Should remain stable over time
- **API success rates**: >95% success rate for API calls
- **Analysis completion**: >90% of items should be analyzed
- **Database growth**: Steady growth without excessive size
- **Error rates**: <1% error rate in logs

## Getting Help

### Support Resources

**Q**: Where can I get help?

**A**: Support options:
- **Documentation**: Comprehensive wiki and guides
- **GitHub Issues**: Bug reports and feature requests
- **Community**: Discussions and user experiences
- **Logs**: Detailed system logs for debugging

### Reporting Issues

**Q**: How do I report a bug?

**A**: When reporting issues, include:
- **System information**: OS, Python version, hardware specs
- **Error messages**: Complete error messages and stack traces
- **Log excerpts**: Relevant log entries with timestamps
- **Configuration**: Sanitized configuration (remove API keys)
- **Steps to reproduce**: Detailed steps to recreate the issue

**Q**: How do I request new features?

**A**: Feature request process:
1. **Check existing requests**: Search GitHub issues first
2. **Describe use case**: Explain why the feature is needed
3. **Provide details**: Specific requirements and expected behavior
4. **Consider alternatives**: Mention any workarounds you've tried

### Contributing

**Q**: Can I contribute to the project?

**A**: Absolutely! Contributions are welcome:
- **Bug fixes**: Submit pull requests for bug fixes
- **New features**: Propose and implement new functionality
- **Documentation**: Improve or expand documentation
- **Testing**: Add test cases and improve coverage
- **Feedback**: Share your experiences and suggestions

See the [Developer Guide](Developer-Guide.md) for contribution guidelines.

---

*This FAQ covers the most common questions about CyberSentinel AI. For additional help, please check the other documentation pages or submit a question through the GitHub issues.*