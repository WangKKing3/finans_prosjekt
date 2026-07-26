# Financial News Scraper & Monitoring Tool

This repository contains a full-stack web application for automated financial news scraping, keyword filtering, and structured data storage. The tool allows users to target news sources, process multiple URLs in parallel, and store deduplicated records for downstream analysis.

---

## Technical Focus
The project is centered around the following core areas:

*   **Web Scraping & Extraction:** Automated HTML fetching via custom HTTP headers and DOM parsing using BeautifulSoup to extract canonical article URLs and titles.
*   **Parallel Execution:** Utilization of multi-threading via Python's `ThreadPoolExecutor` to handle concurrent scraping requests across multiple source URLs.
*   **Data Modeling & Deduplication:** Persistence layer built with SQLAlchemy and SQLite, utilizing unique URL constraints to prevent duplicate entries across runs.
*   **Web Architecture:** Modular Flask application enforcing separation of concerns between web routes, core scraping engines, and relational database models.

---

## Key Challenges
The project required problem-solving in the following areas:

*   **Concurrency Control:** Managing parallel scraping jobs cleanly to optimize execution speed without exceeding resource limits or triggering aggressive rate limiting on target domains.
*   **Data Integrity & State Handling:** Reusing historical data (e.g., pre-computed summaries or metrics) when existing articles are re-scraped, ensuring data consistency while adding new records.
*   **Robust Parsing:** Handling varied HTML structures, short or malformed titles, and non-standard link targets across different web sources.

---

*Developed as a financial news monitoring and data processing engine.*
