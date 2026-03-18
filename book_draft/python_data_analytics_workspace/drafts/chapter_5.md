# Chapter 5: Advanced Data Processing

After mastering the core aggregations and filtering techniques discussed in earlier chapters, data professionals inevitably encounter specialized data formats that require advanced handling. Real-world analytics often revolves around three notoriously complex areas: temporal data, unstructured text, and nested structures. 

In this chapter, we will delve into how Polars handles time-series analysis with unprecedented speed, processes large-scale text strings using parallelized regular expressions, and seamlessly unrolls nested JSON arrays and structs—all while maintaining the performance benefits of a Rust-backed engine.

---

## Time-Series Analysis

Time-series data is ubiquitous, from financial market ticks to IoT sensor logs. Because time-series records depend on temporal order, calculating moving averages, resampling to different frequencies, and shifting data points are essential operations. Polars natively supports robust temporal data types (`Date`, `Datetime`, `Duration`, `Time`) and offers dedicated time-series expressions.

### Resampling Data

Resampling involves changing the frequency of your time-series observations—for example, converting minutely tick data into daily summaries. In Polars, this is accomplished using the `.group_by_dynamic()` method, which performs window-based groupings over a temporal column.

```python
import polars as pl
from datetime import datetime

# Sample time-series DataFrame
df = pl.DataFrame({
    "timestamp": [
        datetime(2026, 1, 1, 10, 0), datetime(2026, 1, 1, 10, 30),
        datetime(2026, 1, 1, 11, 0), datetime(2026, 1, 1, 11, 15)
    ],
    "price": [100.5, 101.2, 102.0, 101.8],
    "volume": [10, 15, 8, 12]
})

# Resampling to 1-hour intervals (OHLCV - Open, High, Low, Close, Volume)
resampled_df = (
    df.sort("timestamp")
    .group_by_dynamic("timestamp", every="1h")
    .agg([
        pl.col("price").first().alias("open"),
        pl.col("price").max().alias("high"),
        pl.col("price").min().alias("low"),
        pl.col("price").last().alias("close"),
        pl.col("volume").sum().alias("total_volume")
    ])
)

print(resampled_df)
```

The `every` parameter accepts simple string aliases like `"1h"` (1 hour), `"1d"` (1 day), or `"15m"` (15 minutes), making temporal bucketing highly intuitive.

### Rolling Windows and Shifting

Rolling windows allow you to apply a calculation over a sliding subset of data. This is frequently used for smoothing out volatility in datasets, like calculating a 3-day moving average. Shifting, on the other hand, moves data backwards or forwards in time, which is critical for calculating day-over-day percentage changes.

```python
# Calculating a 2-period rolling average and a 1-period shift (lag)
df_analytics = df.sort("timestamp").with_columns([
    # Rolling Mean
    pl.col("price")
      .rolling_mean(window_size=2)
      .alias("rolling_mean_price"),
      
    # Previous Row's Price (Lag of 1)
    pl.col("price")
      .shift(1)
      .alias("prev_price")
]).with_columns([
    # Calculate percentage return based on the shifted price
    ((pl.col("price") - pl.col("prev_price")) / pl.col("prev_price"))
    .alias("period_return")
])

print(df_analytics)
```

By heavily optimizing these rolling operations in Rust, Polars drastically reduces the execution time for large temporal calculations compared to Python-native loops or Pandas.

---

## Text and String Manipulation

While numerical data is the bread and butter of analytics, text processing is critical for cleaning categoricals, extracting information from logs, and preparing data for Natural Language Processing (NLP). Polars namespaces all string operations under the `.str` accessor.

### Regex Operations and Text Extraction

Polars natively supports Regular Expressions (Regex) across its `.str` methods. Because these operations map directly to underlying Rust string methods, they bypass Python's Global Interpreter Lock (GIL) and run in parallel across CPU cores.

```python
# Sample text DataFrame
logs_df = pl.DataFrame({
    "log_id": [1, 2, 3],
    "message": [
        "ERROR 2026-03-01: Connection timeout from IP 192.168.1.10",
        "INFO 2026-03-01: User admin logged in",
        "ERROR 2026-03-02: Disk full on drive C:"
    ]
})

# Extracting patterns and cleaning strings
processed_logs = logs_df.with_columns([
    # Check if the log is an ERROR
    pl.col("message").str.contains("ERROR").alias("is_error"),
    
    # Extract the IP address using a Regex capture group
    pl.col("message")
      .str.extract(r"IP (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", 1)
      .alias("ip_address"),
      
    # Convert string to lowercase for standardized searching
    pl.col("message").str.to_lowercase().alias("msg_lower")
])

print(processed_logs)
```

With `str.extract()`, `str.replace()`, and `str.contains()`, you have a full suite of highly concurrent tools to parse log files, scrape messy web data, or standardize messy CRM inputs.

---

## Working with Nested Data

Modern APIs and NoSQL databases often output data in JSON format, which contains deeply nested structures like arrays (lists) and structs (dictionaries). Flattening these into a tabular format is typically a grueling process in traditional pipelines. Polars handles this elegantly with dedicated `List` and `Struct` data types.

### Handling JSON Arrays and Structs

When you read a JSON file into Polars, nested arrays become `List` columns, and nested JSON objects become `Struct` columns. The `.list` and `.struct` namespaces provide the necessary tools to unroll and extract this data.

```python
import polars as pl

# Imagine this data was read from an API via pl.read_json()
api_data = pl.DataFrame({
    "user_id": [101, 102],
    "metadata": [
        {"browser": "Chrome", "version": 120},
        {"browser": "Firefox", "version": 122}
    ],
    "purchase_history": [
        [15.99, 20.50, 9.99],
        [100.00]
    ]
})

# 1. Unnesting Structs (Expanding a dictionary into multiple columns)
unnested_df = api_data.unnest("metadata")

# 2. Exploding Lists (Turning a list of N elements into N separate rows)
exploded_df = unnested_df.explode("purchase_history")

# 3. Aggregating List Elements (Calculating sum without exploding)
summed_df = unnested_df.with_columns([
    pl.col("purchase_history").list.sum().alias("lifetime_value"),
    pl.col("purchase_history").list.len().alias("purchase_count")
])

print(summed_df)
```

The combination of `.unnest()` for structs and `.explode()` for lists empowers you to flatten complex JSON payloads in just a few lines of code. More importantly, doing this inside the Polars engine ensures strict typing and avoids the massive memory bloat associated with Python's standard `json` library.

### Conclusion

Advanced data processing requires an engine that can intelligently handle complex temporal bucketing, parallelize regex across millions of strings, and safely unroll nested architectures. By utilizing Polars' specialized namespaces (`.str`, `.list`, `.struct`) and its temporal aggregations, you can keep your data transformations entirely within the high-performance Rust core.

With data now thoroughly cleaned, transformed, and processed, we can turn our attention to the visual and predictive stages of the pipeline. In the upcoming chapters, we will explore interactive visualization techniques and how to prepare this pristine data for machine learning models.