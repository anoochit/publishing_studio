# Chapter 2: High-Speed Data Ingestion and Export

Data analytics begins with ingestion—getting raw data into your analytical engine. In the legacy Python data stack, loading a 10 GB CSV file into Pandas would often result in a crashed Python kernel and a frustrating Out-Of-Memory (OOM) error. Today's modern stack solves this at the root by rethinking both *how* data is stored and *how* it is read into memory.

In this chapter, we will explore modern file formats, how to query them directly from disk using DuckDB, and how to utilize Polars' lazy execution engine to process datasets significantly larger than your machine's RAM.

---

## Working with File Formats

For decades, the Comma-Separated Values (CSV) format has been the default standard for data exchange. However, CSV is inherently flawed for large-scale analytics: it is row-based, uncompressed, lacks strict data typing, and is slow to parse.

### Moving Beyond CSV: Introduction to Parquet and Arrow IPC

To achieve high performance, modern workflows rely heavily on two columnar formats: **Apache Parquet** and **Arrow IPC (Inter-Process Communication)**.

1. **Apache Parquet:** 
   Parquet is an open-source, columnar storage file format optimized for fast retrieval and efficient compression. Unlike CSV, where data is stored row-by-row, Parquet stores data column-by-column. This means if you have a dataset with 100 columns but only need to query two of them, the engine only reads the data for those two columns from the disk (known as *column projection* or *predicate pushdown*). This drastically reduces I/O wait times and memory usage.
   
2. **Arrow IPC (Feather):** 
   While Parquet is optimized for disk storage and compression, Arrow IPC (formerly known as Feather) is optimized for RAM and rapid data exchange between processes. It stores data in the exact memory layout used by Apache Arrow, meaning there is zero deserialization cost when loading it into DuckDB or Polars.

*Rule of thumb for 2026:* Store your raw and archival data in Parquet. Use Arrow IPC for temporary files passed between Python scripts or local microservices.

---

## Reading and Writing Data with DuckDB

DuckDB is designed to operate directly on flat files without requiring you to "load" them into a database first. It achieves this by creating optimized execution plans that read only the necessary chunks of data.

### Querying CSV and Parquet Directly from Disk

With DuckDB, the file *is* the table. You can pass the file path directly into the `FROM` clause of your SQL query.

```python
import duckdb

# Querying a Parquet file natively
result = duckdb.query("""
    SELECT 
        user_id, 
        SUM(purchase_amount) as total_spent
    FROM 'ecommerce_data.parquet'
    WHERE purchase_date >= '2026-01-01'
    GROUP BY user_id
    ORDER BY total_spent DESC
    LIMIT 10
""").df()

print(result)
```

Notice how seamless this is. DuckDB's engine analyzes the query, identifies that only `user_id`, `purchase_amount`, and `purchase_date` are needed, and reads *only* those columns from the Parquet file.

### Handling Datasets Larger than RAM

One of DuckDB's most powerful features is its ability to perform "out-of-core" processing. If your dataset exceeds your available RAM (e.g., trying to aggregate a 50 GB dataset on a laptop with 16 GB of RAM), DuckDB will automatically spool intermediate results to disk.

To enable this efficiently, you can set a memory limit and configure a temporary directory:

```python
import duckdb

# Connect to a persistent database or configure in-memory limits
con = duckdb.connect('my_local_warehouse.duckdb')

# Configure memory limits and temp directory for out-of-core processing
con.execute("PRAGMA memory_limit='10GB'")
con.execute("PRAGMA temp_directory='/tmp/duckdb_spool'")

# Execute a massive join that exceeds 10GB of RAM
con.execute("""
    CREATE TABLE aggregated_results AS
    SELECT a.id, b.transaction_value
    FROM 'massive_table_A.parquet' a
    JOIN 'massive_table_B.parquet' b ON a.id = b.id
""")
```

By explicitly setting the memory limit, DuckDB ensures that your OS won't kill the Python process. It gracefully pages chunks of data to the specified temporary directory.

---

## Reading and Writing Data with Polars

While DuckDB relies on SQL, Polars provides a powerful, multi-threaded DataFrame API. Polars is written in Rust, giving it incredible speed and memory safety when parsing files.

### Lazy Reading vs. Eager Reading

Polars introduces a paradigm shift for Python developers: the distinction between **Eager** and **Lazy** execution.

*   **Eager Execution (`pl.read_csv`, `pl.read_parquet`):** The engine reads the entire file into memory immediately and executes operations step-by-step. This is similar to how Pandas operates.
*   **Lazy Execution (`pl.scan_csv`, `pl.scan_parquet`):** The engine does *not* read the data immediately. Instead, it builds a query plan (a Directed Acyclic Graph, or DAG) of the operations you want to perform. Data is only processed when you explicitly call `.collect()`.

Lazy execution is crucial for large files because Polars' query optimizer can apply predicate pushdowns and column projections before a single byte is read.

```python
import polars as pl

# EAGER: Reads the whole 10GB file into memory (High risk of OOM)
# df_eager = pl.read_parquet('sales_data.parquet') 

# LAZY: Builds a query plan (Takes milliseconds, uses almost no RAM)
lazy_plan = (
    pl.scan_parquet('sales_data.parquet')
    .filter(pl.col('region') == 'North America')
    .select(['store_id', 'revenue'])
    .group_by('store_id')
    .agg(pl.col('revenue').sum().alias('total_revenue'))
)

# Execution happens ONLY when collect() is called.
# Polars will only read the 'region', 'store_id', and 'revenue' columns.
final_df = lazy_plan.collect()

print(final_df)
```

### Schema Inference and Data Types

When reading CSVs, Polars must guess the data types of each column—a process called schema inference. Because Polars is strictly typed (unlike Pandas, which falls back to generic `Object` types), incorrect inferences can cause errors.

By default, Polars scans the first 100 rows to infer the schema. For messy datasets, you can override this behavior or provide explicit schemas:

```python
import polars as pl

# Providing explicit schemas prevents inference errors and speeds up parsing
schema = {
    "user_id": pl.Int64,
    "signup_date": pl.Date,
    "is_active": pl.Boolean,
    "lifetime_value": pl.Float64
}

# Reading a messy CSV with strict typing
df = pl.read_csv(
    "messy_users.csv",
    schema=schema,
    ignore_errors=True, # Skips rows that don't match the strict schema
    null_values=["NA", "N/A", "missing"] # Standardizes null representations
)

# Writing the cleaned data to Parquet for future fast access
df.write_parquet("clean_users.parquet")
```

### Conclusion

Mastering modern data ingestion means abandoning the "load everything into memory" mindset. By transitioning to columnar formats like Parquet, leveraging DuckDB’s out-of-core SQL engine, and utilizing Polars' lazy execution plans, you can process enterprise-scale datasets on consumer-grade hardware. 

In the next chapter, we will take these ingested DataFrames and dive deep into data wrangling and complex transformations using Polars.