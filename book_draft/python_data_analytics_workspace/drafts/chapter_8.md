# Chapter 8: Real-World Case Studies

In the preceding chapters, we explored the mechanics of the modern Python data stack—from the blistering speed of DuckDB and Polars to the seamless memory sharing of Apache Arrow. Now, it is time to put these tools to work. In this chapter, we will build three real-world projects that solve common, yet complex, data challenges.

We will conclude with an end-to-end pipeline for an interactive sales dashboard, complete with industry-standard DevOps practices: testing, containerization using Docker, and automated CI/CD deployment workflows.

---

## Project 1: Financial Market Data Analysis

Financial data analytics often involves processing massive amounts of tick data—sometimes exceeding 10 GB per day. Loading this data into memory using traditional tools like Pandas is practically impossible on a standard laptop. Instead, we use DuckDB and Polars to query and process this data out-of-core.

### The Challenge
Process 10+ GB of raw trade data (CSV) to calculate the volume-weighted average price (VWAP) on a 5-minute rolling basis for a set of stock tickers.

### The Solution

We'll use DuckDB to handle the initial data ingestion and filtering, leveraging its ability to query CSV files directly from disk.

```python
import duckdb
import polars as pl

# 1. Use DuckDB to filter the 10GB CSV without loading it fully into RAM
query = """
    SELECT 
        ticker,
        timestamp,
        price,
        volume
    FROM read_csv_auto('market_tick_data_10GB.csv')
    WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL')
        AND date = '2026-10-14'
"""

# Execute and fetch as an Apache Arrow table, then seamlessly convert to Polars
# This is a zero-copy operation!
filtered_data = duckdb.query(query).arrow()
df = pl.from_arrow(filtered_data)

# 2. Use Polars to calculate the 5-minute rolling VWAP
# We define VWAP = sum(price * volume) / sum(volume)
vwap_df = (
    df
    .sort("timestamp")
    .group_by_dynamic("timestamp", every="5m", group_by="ticker")
    .agg([
        (pl.col("price") * pl.col("volume")).sum().alias("total_value"),
        pl.col("volume").sum().alias("total_volume")
    ])
    .with_columns(
        (pl.col("total_value") / pl.col("total_volume")).alias("vwap")
    )
    .select(["ticker", "timestamp", "vwap"])
)

print(vwap_df.head())
```

By leveraging DuckDB for the "heavy lifting" I/O filtering and Polars for the complex rolling window aggregations, a query that would crash a 16GB RAM machine completes in a matter of seconds.

---

## Project 2: E-commerce Customer Segmentation

Customer segmentation is a cornerstone of marketing analytics. One of the most common methods is RFM analysis (Recency, Frequency, Monetary value).

### The Challenge
Calculate RFM scores for millions of customer transactions and segment customers into distinct marketing cohorts using the modern stack.

### The Solution

Here, we will do the entire transformation within DuckDB, demonstrating how powerful its analytical functions are before moving the aggregated result into Polars for final output.

```python
import duckdb
import polars as pl

# Create an in-memory DuckDB connection
con = duckdb.connect()

# Query directly from a directory of Parquet files
query = """
WITH customer_aggregates AS (
    SELECT 
        customer_id,
        MAX(order_date) as last_order_date,
        COUNT(DISTINCT order_id) as frequency,
        SUM(order_total) as monetary
    FROM read_parquet('ecommerce_data/*.parquet')
    GROUP BY customer_id
),
rfm_calculations AS (
    SELECT 
        customer_id,
        DATE_DIFF('day', last_order_date, CURRENT_DATE) as recency,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY DATE_DIFF('day', last_order_date, CURRENT_DATE) DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
    FROM customer_aggregates
)
SELECT * FROM rfm_calculations;
"""

# Fetch result to Polars
rfm_df = pl.from_arrow(con.execute(query).arrow())

# Create a final segmentation label using Polars
rfm_segmented = rfm_df.with_columns(
    (pl.col("r_score").cast(pl.Utf8) + 
     pl.col("f_score").cast(pl.Utf8) + 
     pl.col("m_score").cast(pl.Utf8)).alias("rfm_cell")
)

print(rfm_segmented.head())
```

---

## Project 3: Interactive Sales Dashboard (End-to-End Pipeline)

Building a dashboard isn't just about creating visualizations—it's about engineering a reliable pipeline that automatically updates, tests itself, and deploys seamlessly. In this project, we implement a full CI/CD lifecycle using modern DevOps practices.

### 1. The Dashboard Application (`app.py`)

We'll use Streamlit for the frontend, consuming data processed by DuckDB and Polars.

```python
import streamlit as st
import duckdb
import polars as pl
import plotly.express as px

@st.cache_data
def load_data():
    # DuckDB securely reads and aggregates raw data
    query = """
        SELECT region, product_category, SUM(sales) as total_sales
        FROM read_csv_auto('raw_sales.csv')
        GROUP BY region, product_category
    """
    return pl.from_arrow(duckdb.query(query).arrow())

st.title("Interactive Sales Dashboard 2026")

df = load_data()

# Plotly Interactive Chart
fig = px.bar(
    df.to_pandas(), # Plotly still natively integrates better with Pandas DataFrame
    x="region", 
    y="total_sales", 
    color="product_category",
    title="Sales by Region and Category"
)

st.plotly_chart(fig)
```

### 2. Dependency Management and Testing

A reliable deployment starts with locking down dependencies and writing unit tests. We use `uv` for lightning-fast dependency resolution.

```bash
# requirements.txt
streamlit==1.30.0
duckdb==0.10.0
polars==0.20.0
plotly==5.18.0
pytest==8.0.0
```

**Unit Testing (`test_app.py`)**

Always validate your data queries before deployment to prevent broken dashboards.

```python
import duckdb
import polars as pl

def test_data_aggregation():
    # Setup mock data in memory
    con = duckdb.connect()
    con.execute("CREATE TABLE sales (region VARCHAR, product_category VARCHAR, sales DOUBLE)")
    con.execute("INSERT INTO sales VALUES ('North', 'Electronics', 100.0), ('North', 'Electronics', 50.0)")
    
    query = "SELECT region, SUM(sales) as total_sales FROM sales GROUP BY region"
    df = pl.from_arrow(con.execute(query).arrow())
    
    # Assert correctness
    assert df.filter(pl.col("region") == "North").select("total_sales").item() == 150.0
```

### 3. Containerizing the Application (Docker)

To ensure the dashboard runs exactly the same in production as it does on your local machine, we containerize it using Docker. Security best practices dictate running the container as a non-root user.

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN useradd -m appuser

WORKDIR /app

# Install dependencies using uv for speed
RUN pip install uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY app.py raw_sales.csv ./

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 4. CI/CD Pipeline (GitHub Actions)

We automate the testing and deployment workflow using GitHub Actions. This pipeline ensures that every code change is automatically tested and built into a Docker container.

```yaml
# .github/workflows/deploy.yml
name: Dashboard CI/CD Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install --system -r requirements.txt
          
      - name: Run Unit Tests
        run: |
          pytest test_app.py

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
          
      - name: Build and Push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/sales-dashboard:latest
```

### Summary

By blending the incredible performance of DuckDB and Polars with modern DevOps and CI/CD pipelines, you've now mastered the complete lifecycle of a 2026-era data application. Your data is not only processed at lightning speeds but is also securely deployed, rigorously tested, and automatically updated.
