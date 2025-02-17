# 🔥 CyberSentinel AI - Automated Security Monitoring and AI Analysis System

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

CyberSentinel AI is an **automated security monitoring and AI analysis system** designed to **track the latest security vulnerabilities (CVEs)** and **security-related repositories on GitHub** in real-time. It leverages **Artificial Intelligence (AI) technology** for in-depth analysis and **automatically publishes valuable security intelligence to a blog platform**.

## 🚀 Key Features

*   **Multi-Source Data Monitoring**:
    *   **CVE Monitoring**: Real-time scraping of the latest CVE-related information from GitHub, enabling rapid discovery and tracking of the latest vulnerability trends.
    *   **GitHub Repository Monitoring**: Comprehensive monitoring of security-related open-source projects on GitHub through keyword searches and predefined watch lists.
*   **Intelligent AI Analysis**:
    *   **OpenAI & Gemini Dual Engine**: Integrated with OpenAI and Gemini AI models, providing powerful natural language processing capabilities for in-depth security data analysis.
    *   **Multi-Dimensional Security Assessment**: Evaluation of CVEs and repositories from multiple dimensions, including **vulnerability principles**, **exploitation methods**, **risk levels**, and **impact scope**, ensuring depth and breadth of analysis.
    *   **Value Judgment and Filtering**: Intelligent AI-driven judgment of security information value, automatically filtering out low-value information and focusing on truly noteworthy security threats and technologies.
*   **Automated Workflow**:
    *   **Fully Automated Monitoring**: The system runs **24/7** unattended, automating security information collection, analysis, and report generation.
    *   **Daily Security Briefing**: Generates daily security briefing reports on a schedule, summarizing the latest CVE vulnerabilities and GitHub security repository dynamics, and pushing them to a blog platform.
    *   **Dynamic Blacklisting**: Automatically updates blacklists based on AI analysis results, reducing interference from invalid information and improving monitoring efficiency.
*   **Flexible Configuration and Management**:
    *   **Multi-GitHub Token Support**: Supports configuration of multiple GitHub Tokens, intelligently rotating usage to effectively avoid API rate limits.
    *   **Configurable Monitoring Parameters**: Keywords, watch repository lists, blacklists, etc., can be flexibly adjusted through configuration files to meet different monitoring needs.
    *   **Detailed Logging**: Detailed logs are recorded for all critical steps of system operation, facilitating troubleshooting and system monitoring.
*   **Automated Blog Publishing**:
    *   **Integrated Blog Platform**: Integrated with a blog platform API to automatically publish daily security briefing reports, quickly sharing security intelligence.
    *   **Markdown Reports**: Analysis results and security briefings are generated in **Markdown format**, making them easy to read and edit.

## 🛠️ Technical Implementation

### 1. Monitoring Modules (Monitors)

*   **`cve_monitor.py`**: **CVE Monitor**
    *   **GitHub API Interaction**: Uses the GitHub API to search for CVE-related repositories, keyword `CVE-202+`, and sorts by `updated` time.
    *   **CVE Information Extraction**: Extracts CVE numbers from repository names and descriptions using regular expressions.
    *   **Repository Information Crawling**: Retrieves repository descriptions, star counts, update times, recent commits, and other information.
    *   **Blacklist Filtering**: Supports **user blacklists** and **repository blacklists** to filter out invalid information sources.
    *   **File Content Analysis**: Clones repositories locally and **intelligently analyzes** **README.md** and other **high-priority files**, calculates file **relevance scores**, and initially filters high-value repositories.
    *   **Intelligent Token Management**: Implements automatic rotation and status checking of GitHub Tokens, dynamically switching available tokens to ensure the continuity of monitoring tasks.
    *   **Database Storage**: Uses the **SQLite** database **`database/cve_record.db`** to store CVE records, including CVE numbers, descriptions, publication dates, last modified dates, repository URLs, and other information.

*   **`github_monitor.py`**: **GitHub Repository Monitor**
    *   **Keyword Search**: Periodically searches GitHub repositories based on the `GITHUB_KEYWORDS` list defined in the configuration file **`config.py`**.
    *   **Watch List**: Supports the `WATCHED_REPOSITORIES` list in the configuration file **`config.py`** to **focus monitoring** on predefined security repositories.
    *   **Repository Information Crawling**: Retrieves detailed repository information, including descriptions, star counts, last update times, recent commit records, and more.
    *   **Commit Record Analysis**: Crawls the **recent commit records** of repositories, **intelligently analyzes** commit information and file changes, and initially judges the **security relevance** of repositories.
    *   **Blacklist Filtering**: Supports **user blacklists** and **repository blacklists** to filter out invalid information sources.
    *   **Intelligent Token Management**: Shares the Token management mechanism with the CVE monitor.
    *   **Database Storage**: Uses the **SQLite** database **`database/github_repo.db`** to store GitHub repository records, including repository names, URLs, descriptions, last update times, star counts, whether they are high-value repositories, and other information.

### 2. AI Analysis Module (AI)

*   **`analyzer.py`**: **AI Analyzer**
    *   **OpenAI & Gemini API**: Integrates **OpenAI API** (primary) and **Gemini API** (backup), supports **multi-model** switching, such as `gpt-4o-mini-2024-07-18` (fallback model).
    *   **Prompt Engineering**: Designed **different Prompt templates** for **different analysis scenarios** (CVE analysis, new repository analysis, repository update analysis, specific watch repository analysis) to optimize AI analysis results.
    *   **JSON Format Output**: Requires AI to **strictly output analysis results in JSON format** for easy program parsing and data processing.
    *   **Multi-Dimensional Security Analysis**: AI analysis results include rich information such as **brief descriptions of vulnerabilities/repositories**, **detailed summaries**, **risk levels**, **key points**, **technical details**, **affected components**, **value assessments**, **security types**, **update types**, and **vulnerability exploitation status**.
    *   **Result Validation and Standardization**: Performs **strict format validation** and **content standardization** on the JSON results returned by AI to ensure the accuracy and usability of the data.
    *   **Dynamic Blacklist Update**: Based on AI analysis results, **automatically judges** whether repositories or users should be added to the blacklist and **dynamically updates the blacklist file**.
    *   **Analysis Result Persistence**: **Saves** AI analysis results as **JSON files** and **updates** corresponding records in the **database**.
    *   **Article Title Classification**: Supports **AI classification** of security article titles for generating security briefing reports.
    *   **API Failover**: When OpenAI API calls fail, **automatically switches** to **backup OpenAI API** or **Gemini API** to improve system **stability and availability**.

### 3. Data Processing and Management (Utils)

*   **`logger.py`**: **Logger**
    *   Uses the `logging` module to provide **complete logging** functionality, covering **DEBUG**, **INFO**, **WARNING**, **ERROR**, and other levels.
    *   Log information is **detailed** and **structured**, making it easy to troubleshoot and monitor the system.
    *   Logs are output to the file **`logs/security_monitor.log`** and rolled over daily.

*   **`csv_writer.py`**: **CSV Result Writer** (currently not used, can be extended)
    *   Provides the function of **exporting analysis results to CSV files** for easy data analysis and sharing.

*   **`article_fetcher.py`**: **Article Fetcher**
    *   **Multi-Source Fetching**: Currently supports fetching security articles from **BruceFeIix** and **D洞见 (doonsec)** WeChat official accounts.
    *   **Article Title and URL Extraction**: Uses regular expressions to extract article titles and URLs from web page content.
    *   **Retry Mechanism**: Uses a **backoff strategy** retry mechanism to improve the **stability and success rate** of article fetching.
    *   **Article Title Cleaning**: **Standardizes** and **cleans** article titles, removing redundant markers and formats.

*   **`article_manager.py`**: **Article Manager**
    *   **Article De-duplication**: **Automatically filters** processed article URLs to avoid duplicate analysis and pushing.
    *   **AI Classification Result Processing**: Processes AI article title classification results and **organizes article lists by category**.
    *   **Daily Security Briefing Report Generation**: **Regularly** generates **Markdown format** daily security briefing reports, summarizing the latest security articles and AI analysis results.
    *   **Automated Blog Publishing**: Calls the `blog_manager.py` module to **automatically publish daily security briefing reports to a blog platform**.
    *   **Article Data Persistence**: **Saves** processed URLs and classified articles as **JSON files** for easy subsequent use and management.

*   **`blog_manager.py`**: **Blog Manager**
    *   **Blog Platform API Interaction**: Encapsulates **common functions** for interacting with blog platform APIs, such as **creating articles** and **updating articles**.
    *   **Article ID Mapping Management**: **Records** the **article IDs** of daily security briefing reports on the blog platform for easy subsequent updates and management.
    *   **Automated Blog Publishing**: Implements the function of **automatically publishing daily security briefing reports to a blog platform**.

### 4. Database (Database)

*   **`database/models.py`**: **Database Model Definition**
    *   Uses **SQLAlchemy** to define two data models, **`CVERecord`** (CVE record) and **`Repository`** (GitHub repository record), to facilitate data storage and querying.
    *   The database uses **SQLite**, and the file paths are **`database/cve_record.db`** and **`database/github_repo.db`**.

### 5. Configuration File (Config)

*   **`config.py`**: **System Configuration File**
    *   Centrally manages the system's **configuration parameters**, such as database paths, API keys, monitoring intervals, keyword lists, blacklists, etc.
    *   Facilitates users to **customize** and **adjust** system behavior.
    *   Includes the following main configuration items:
        *   `DATABASE_PATH`: Database file path
        *   `MONITOR_INTERVAL`: Monitoring cycle interval (seconds)
        *   `GITHUB_TOKEN`: GitHub API Token (supports list `GITHUB_TOKENS`)
        *   `GITHUB_KEYWORDS`: List of GitHub repository search keywords
        *   `WATCHED_REPOSITORIES`: List of GitHub repositories to focus on monitoring
        *   `BLACKLIST_USERS`: User blacklist
        *   `BLACKLIST_REPOSITORIES`: Repository blacklist
        *   `PRIMARY_AI_CONFIG`: Primary AI service (OpenAI) configuration
        *   `BACKUP_AI_CONFIGS`: List of backup AI service (OpenAI) configurations
        *   `GEMINI_AI_CONFIG`: Gemini AI service configuration
        *   `BLOG_TOKEN`: Blog platform API Token

### 6. Main Program (Main)

*   **`main.py`**: **System Main Program**
    *   **Initializes** each module (monitors, AI analyzer, article manager, etc.).
    *   **Starts** the monitoring cycle, **regularly** executing CVE monitoring, GitHub repository monitoring, AI analysis, article crawling, and blog publishing tasks.
    *   Uses **multi-threading** to achieve **concurrent monitoring** and **AI analysis**, improving system efficiency.
    *   **Exception handling** and **retry mechanisms** ensure stable system operation.
    *   **Status Monitoring Thread**: **Regularly checks** system operating status and records logs.
    *   **Daily Blog Publishing**: **Regularly** automatically publishes daily security briefing reports to a blog platform.
    *   **Command-Line Startup**: Users can start and stop the monitoring system via the command line.

## ⚙️ Running Environment

*   Python 3.8+
*   Dependencies (see `requirements.txt`)

## 📦 Installation Steps

1.  **Clone the code repository**

    ```bash
    git clone [Project Repository Address]
    cd [Project Directory]
    ```

2.  **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the `config.py` file**

    *   Configure GitHub API Token (`GITHUB_TOKEN` or `GITHUB_TOKENS`)
    *   Configure OpenAI API key and Base URL (`PRIMARY_AI_CONFIG`, `BACKUP_AI_CONFIGS`)
    *   Configure Gemini API key and Base URL (`GEMINI_AI_CONFIG`)
    *   Configure Blog platform API Token (`BLOG_TOKEN`) (if you need to automatically publish to a blog)
    *   Modify other configuration items as needed, such as monitoring interval, keyword list, blacklist, etc.

4.  **Run the system**

    ```bash
    python main.py
    ```

## 📝 Future Plans

*   **More Data Source Support**: Expand support for more security information sources, such as security communities, vulnerability platforms, etc.
*   **More Refined AI Analysis**: Continuously optimize Prompt engineering to improve the accuracy and depth of AI analysis.
*   **Richer Features**: Such as vulnerability early warning, threat intelligence visualization, custom reports, etc.
*   **Web UI Management Interface**: Develop a Web UI management interface to facilitate users to configure and manage the monitoring system.

## 🤝 Contribution

Contributions are welcome! If you have any suggestions or bug reports, please submit an Issue or Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Thank you for your attention!** ⭐ **Star** this project to support our work!
