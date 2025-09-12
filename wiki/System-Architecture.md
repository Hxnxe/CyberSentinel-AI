# System Architecture

## Overview

CyberSentinel AI follows a modular, microservices-inspired architecture designed for scalability, reliability, and maintainability. The system is built using Python and follows modern software engineering practices.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CyberSentinel AI System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
│  │  CVE Monitor  │  │ GitHub Monitor│  │  Article Fetcher    │   │
│  │               │  │               │  │                     │   │
│  │ • GitHub API  │  │ • Repository  │  │ • WeChat Articles   │   │
│  │ • CVE Search  │  │   Search      │  │ • Security Feeds    │   │
│  │ • Blacklist   │  │ • Watch Lists │  │ • URL Extraction    │   │
│  │   Filter      │  │ • Commit      │  │                     │   │
│  │               │  │   Analysis    │  │                     │   │
│  └───────┬───────┘  └───────┬───────┘  └──────────┬──────────┘   │
│          │                  │                     │              │
│          └──────────────────┼─────────────────────┘              │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │   AI Analyzer   │                          │
│                    │                 │                          │
│                    │ • OpenAI API    │                          │
│                    │ • Gemini API    │                          │
│                    │ • Prompt Engine │                          │
│                    │ • JSON Parser   │                          │
│                    │ • Risk Assess   │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│     ┌───────────────────────┼───────────────────────┐            │
│     │                       │                       │            │
│ ┌───▼────┐         ┌────────▼────────┐       ┌─────▼──────┐     │
│ │Database│         │ Article Manager │       │Blog Manager│     │
│ │        │         │                 │       │            │     │
│ │• SQLite│         │• Report Gen     │       │• API Client│     │
│ │• CVE DB│         │• Deduplication  │       │• Publishing│     │
│ │• Repo  │         │• Classification │       │• Scheduling│     │
│ │  DB    │         │• Markdown Gen   │       │            │     │
│ └────────┘         └─────────────────┘       └────────────┘     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                     Infrastructure Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   Logger    │  │ Config Mgmt  │  │     CSV Writer          │  │
│  │ • Log Levels│  │ • Settings   │  │ • Data Export           │  │
│  │ • File Out  │  │ • API Keys   │  │ • Format Conversion     │  │
│  │ • Rotation  │  │ • Parameters │  │                         │  │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Monitoring Layer

#### CVE Monitor (`cve_monitor.py`)
**Purpose**: Discovers and tracks CVE-related repositories and vulnerabilities

**Key Responsibilities**:
- Search GitHub for CVE-related repositories
- Extract CVE numbers from repository metadata
- Analyze repository content for security relevance
- Filter results using blacklists and relevance scoring
- Store findings in SQLite database

**Technical Details**:
- **API Integration**: GitHub REST API v3/v4
- **Search Strategy**: Keyword-based searches (`CVE-202+`)
- **Content Analysis**: README parsing, commit analysis
- **Storage**: SQLite database (`database/cve_record.db`)
- **Token Management**: Rotating GitHub API tokens

**Data Flow**:
```
GitHub API → Repository Discovery → Content Analysis → Filtering → Database Storage
```

#### GitHub Monitor (`github_monitor.py`)
**Purpose**: Monitors security-related repositories and projects

**Key Responsibilities**:
- Keyword-based repository searching
- Watch list monitoring for specific repositories
- Commit analysis for security-related changes
- Repository metadata collection and analysis
- Blacklist filtering and relevance scoring

**Technical Details**:
- **Search Keywords**: Configurable security-related terms
- **Watch Lists**: Predefined high-value repositories
- **Commit Analysis**: Recent activity monitoring
- **Storage**: SQLite database (`database/github_repo.db`)

**Monitoring Strategies**:
- **Active Search**: Regular keyword-based searches
- **Passive Monitoring**: Watch list repository tracking
- **Trend Analysis**: Star count and activity monitoring

#### Article Fetcher (`article_fetcher.py`)
**Purpose**: Collects security articles from various sources

**Key Responsibilities**:
- Fetch articles from WeChat public accounts
- Extract article titles and URLs
- Clean and standardize article metadata
- Implement retry mechanisms for reliability

**Supported Sources**:
- **BruceFeIix** WeChat account
- **D洞见 (doonsec)** WeChat account
- **Extensible**: Framework for additional sources

### 2. Analysis Layer

#### AI Analyzer (`analyzer.py`)
**Purpose**: AI-powered analysis and intelligence extraction

**Key Responsibilities**:
- Analyze collected data using AI models
- Generate structured intelligence reports
- Assess risk levels and security implications
- Filter and prioritize findings
- Update blacklists based on analysis results

**AI Models**:
- **Primary**: OpenAI GPT models (`gpt-4o-mini-2024-07-18`)
- **Backup**: Additional OpenAI endpoints
- **Fallback**: Google Gemini API

**Analysis Types**:
- **CVE Analysis**: Vulnerability assessment and impact analysis
- **Repository Analysis**: Security tool and research evaluation
- **Article Classification**: Content categorization and relevance scoring
- **Trend Analysis**: Pattern recognition in security developments

**Output Format**:
```json
{
  "brief_description": "string",
  "detailed_summary": "string",
  "risk_level": "Critical|High|Medium|Low",
  "key_points": ["string"],
  "technical_details": "string",
  "affected_components": ["string"],
  "value_assessment": "High|Medium|Low",
  "security_type": "string",
  "exploitation_status": "string"
}
```

### 3. Data Management Layer

#### Database Models (`database/models.py`)
**Purpose**: Data persistence and management

**Database Design**:
- **Technology**: SQLite (lightweight, file-based)
- **Models**: SQLAlchemy ORM
- **Databases**: Separate databases for CVE and repository data

**CVE Record Model**:
```python
class CVERecord:
    id: Primary Key
    cve_number: String (CVE identifier)
    description: Text (vulnerability description)
    publication_date: DateTime
    last_modified_date: DateTime
    repository_url: String
    analysis_result: JSON (AI analysis)
```

**Repository Model**:
```python
class Repository:
    id: Primary Key
    name: String (repository name)
    url: String (repository URL)
    description: Text
    last_update: DateTime
    star_count: Integer
    is_high_value: Boolean
    analysis_result: JSON (AI analysis)
```

#### Article Manager (`article_manager.py`)
**Purpose**: Content management and report generation

**Key Responsibilities**:
- Deduplicate articles and prevent reprocessing
- Organize content by categories and classifications
- Generate daily security briefing reports
- Manage blog publishing workflows
- Maintain historical records

**Report Generation Process**:
1. **Collection**: Gather analyzed content from all sources
2. **Classification**: Categorize content by type and relevance
3. **Deduplication**: Remove duplicate or similar items
4. **Formatting**: Generate Markdown reports
5. **Publishing**: Trigger blog publication workflow

#### Blog Manager (`blog_manager.py`)
**Purpose**: Automated content publishing

**Key Responsibilities**:
- Interface with blog platform APIs
- Manage article creation and updates
- Track published content IDs
- Handle publishing failures and retries

**Publishing Workflow**:
```
Report Generation → Content Formatting → API Upload → Status Tracking → Error Handling
```

### 4. Infrastructure Layer

#### Configuration Management (`config.py`)
**Purpose**: Centralized system configuration

**Configuration Categories**:
- **Database**: File paths and connection settings
- **APIs**: Authentication tokens and endpoints
- **Monitoring**: Intervals, keywords, watch lists
- **Filtering**: Blacklists and relevance thresholds
- **AI**: Model selection and prompts

**Key Configuration Items**:
```python
# Database Configuration
DATABASE_PATH = "path/to/databases"

# API Configuration
GITHUB_TOKENS = ["token1", "token2", "token3"]
PRIMARY_AI_CONFIG = {
    "api_key": "openai_key",
    "base_url": "api_endpoint",
    "model": "gpt-4o-mini-2024-07-18"
}

# Monitoring Configuration
GITHUB_KEYWORDS = ["security", "vulnerability", "exploit"]
WATCHED_REPOSITORIES = ["org/security-repo"]
BLACKLIST_USERS = ["spam-user"]
```

#### Logging System (`logger.py`)
**Purpose**: Comprehensive system monitoring and debugging

**Logging Features**:
- **Multiple Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **File Output**: Rotating log files with daily rotation
- **Structured Format**: Consistent formatting for analysis
- **Component Tagging**: Source identification for log entries

**Log File Structure**:
```
logs/
├── security_monitor.log          # Current log
├── security_monitor.log.2025-09-11  # Previous day
└── security_monitor.log.2025-09-10  # Older logs
```

### 5. Main Orchestration

#### Main Program (`main.py`)
**Purpose**: System orchestration and workflow management

**Key Responsibilities**:
- Initialize all system components
- Coordinate monitoring and analysis workflows
- Manage system scheduling and timing
- Handle exceptions and system recovery
- Provide system status monitoring

**Execution Flow**:
1. **Initialization**: Load configuration and initialize components
2. **Monitoring Loop**: Execute monitoring tasks on schedule
3. **Analysis Processing**: Trigger AI analysis for new findings
4. **Report Generation**: Create and publish daily reports
5. **Status Monitoring**: Track system health and performance

**Threading Model**:
- **Main Thread**: Orchestration and coordination
- **Monitor Threads**: Parallel monitoring of different sources
- **Analysis Thread**: AI processing queue
- **Status Thread**: System health monitoring

## Data Flow Architecture

### 1. Collection Phase
```
External Sources → Monitors → Raw Data → Database Storage
```

### 2. Analysis Phase
```
Database → AI Analyzer → Structured Intelligence → Updated Records
```

### 3. Reporting Phase
```
Analyzed Data → Article Manager → Report Generation → Blog Publishing
```

### 4. Feedback Phase
```
Analysis Results → Blacklist Updates → Improved Filtering → Better Signal-to-Noise
```

## Scalability Considerations

### Current Design Strengths
- **Modular Architecture**: Easy to extend and modify
- **Database Independence**: SQLite for simplicity, easily upgradeable
- **API Abstraction**: Multiple AI providers for redundancy
- **Configuration-Driven**: Behavior modification without code changes

### Future Scalability Options
- **Database Migration**: PostgreSQL or MongoDB for larger datasets
- **Distributed Processing**: Celery task queues for heavy workloads
- **Caching Layer**: Redis for frequently accessed data
- **Load Balancing**: Multiple instances for high availability

## Security Architecture

### Authentication & Authorization
- **API Key Management**: Secure storage and rotation of API credentials
- **Token Validation**: GitHub API token health monitoring
- **Access Control**: Read-only operations for data collection

### Data Security
- **Local Storage**: All data stored locally for privacy
- **Encryption**: API communications over HTTPS
- **Audit Logging**: Complete audit trail of system operations

### Operational Security
- **Rate Limiting**: Respect API rate limits to prevent blocking
- **Error Handling**: Graceful degradation on failures
- **Monitoring**: System health and anomaly detection

---

*This architecture documentation provides the technical foundation for understanding how CyberSentinel AI operates. For implementation details, see the [Code Documentation](Code-Documentation.md).*