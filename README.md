# FinFlow Data Platform
End-to-end fintech data engineering platform demonstrating batch and streaming
ingestion, data lake, Spark transformations, ClickHouse warehouse with medallion
architecture, dbt, Airflow orchestration, data quality, governance, catalog,
dashboards, and observability.
## Status
Under construction. See the Implementation Manual for build instructions.
## Quick Start
```bash
cp .env.example .env
# Edit .env with your secrets
docker compose up -d
```
## Technology Stack
| Layer | Technology |
| --- | --- |
| Sources | PostgreSQL, FastAPI, OpenSearch |
| Batch Ingestion | Apache NiFi |
| Streaming | Debezium, Apache Kafka |
| Data Lake | MinIO (S3) |
| Processing | Apache Spark, Python |
| Warehouse | ClickHouse |
| Transforms | dbt |
| Orchestration | Apache Airflow |
| Dashboards | Apache Superset |
| Catalog | OpenMetadata |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions |
## License
MIT
