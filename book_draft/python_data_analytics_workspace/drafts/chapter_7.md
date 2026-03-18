# Chapter 7: AI-Assisted Analytics and Machine Learning Prep

As the data landscape has evolved into 2026, the roles of data analysts and data scientists have become deeply intertwined with Artificial Intelligence. AI is no longer just the end goal of a data pipeline; it is an active participant in building the pipeline itself. 

In this chapter, we will explore how to integrate modern Large Language Models (LLMs) like ChatGPT and GitHub Copilot into your analytics workflow to accelerate code generation. Furthermore, we will walk through the critical steps of preparing high-performance Polars DataFrames for machine learning models, concluding with the necessary hand-off to Pandas for legacy library compatibility.

---

## Integrating AI into the Workflow

The transition from a Pandas-first mindset to a DuckDB and Polars ecosystem requires learning new syntaxes and paradigms—specifically, thinking in terms of "Expressions" and "Lazy Execution." LLMs are incredibly adept at easing this transition, provided you know how to prompt them effectively.

### Using LLMs to Generate Polars and DuckDB Code

Tools like ChatGPT, Claude, and GitHub Copilot have ingested vast amounts of documentation and code. To get the best results when generating modern data stack code, you must be explicit in your prompts to prevent the AI from defaulting back to legacy Pandas code.

**Effective Prompting Strategies:**

1.  **Specify the Library and Version:** Always explicitly state that you want Polars or DuckDB code. (e.g., *"Write a Python script using Polars..."*)
2.  **Enforce Best Practices:** Instruct the LLM to use lazy execution or the expression API. (e.g., *"Use Polars lazy execution and the `.group_by_dynamic()` method..."*)
3.  **Provide Schema Context:** Give the LLM a sample of your schema to ensure the generated expressions reference the correct columns.

**Example Prompt:**
> "I have a Parquet file named `sales.parquet` with columns `timestamp` (Datetime), `store_id` (Int64), and `revenue` (Float64). Write a Polars script using lazy execution to calculate the 7-day rolling average of revenue per `store_id`."

**AI Generated Output:**
```python
import polars as pl

# The LLM correctly utilizes LazyFrames and the modern Expression API
lazy_plan = (
    pl.scan_parquet("sales.parquet")
    .sort("timestamp")
    .with_columns([
        pl.col("revenue")
        .rolling_mean(window_size="7d", by="timestamp")
        .over("store_id")
        .alias("7d_rolling_avg_revenue")
    ])
)

df = lazy_plan.collect()
```

By leveraging AI assistants, you can rapidly prototype complex window functions, regular expressions, and SQL CTEs for DuckDB, significantly boosting your daily productivity.

---

## Preparing Data for Machine Learning

Once your data is ingested, cleaned, and explored, the next step is often predictive modeling. Machine learning algorithms require data to be strictly numerical, void of null values, and appropriately scaled. Polars is exceptional at performing this Feature Engineering efficiently.

### Feature Engineering with Polars

Feature engineering involves creating new predictive signals from existing raw data. Because Polars evaluates expressions in parallel, it can generate hundreds of features across millions of rows in a fraction of a second.

**1. One-Hot Encoding:**
Converting categorical string variables into binary (1/0) numerical columns is essential for algorithms like XGBoost or Random Forest.

```python
import polars as pl

df = pl.DataFrame({"user_id": [1, 2, 3], "subscription": ["Basic", "Premium", "Basic"]})

# Using Polars native to_dummies (similar to Pandas get_dummies)
encoded_df = df.to_dummies("subscription")
print(encoded_df)
```

**2. Scaling and Normalization:**
Standardizing numerical data (mean = 0, variance = 1) prevents algorithms from heavily weighting features simply because their absolute numbers are larger.

```python
# Z-Score Normalization using Expressions
# Z = (X - Mean) / Standard Deviation
df_features = df.with_columns([
    ((pl.col("age") - pl.col("age").mean()) / pl.col("age").std()).alias("age_scaled"),
    ((pl.col("income") - pl.col("income").mean()) / pl.col("income").std()).alias("income_scaled")
])
```

By keeping feature engineering inside Polars, you ensure that transformations utilize the high-speed Rust engine before ever touching the slower, GIL-locked machine learning libraries.

---

## The Pandas Hand-off

Despite the massive performance advantages of Polars and DuckDB, the broader Python machine learning ecosystem (including Scikit-learn, Statsmodels, and some older deep learning wrappers) was built around NumPy arrays and Pandas DataFrames.

As of 2026, many of these libraries are adding native support for Apache Arrow, but in cases where a strict Pandas DataFrame is required, you must execute a "Hand-off."

### Safely Converting to Pandas for Scikit-learn Compatibility

Because Polars uses Apache Arrow memory under the hood, converting a Polars DataFrame to a Pandas DataFrame is often a Zero-Copy operation, provided you are using Pandas version 2.0 or newer (which supports the PyArrow backend).

```python
import polars as pl
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# 1. Load and engineer features with high-speed Polars
polars_df = (
    pl.scan_parquet("customer_data.parquet")
    .drop_nulls()
    # ... extensive feature engineering here ...
    .collect()
)

# 2. The Hand-off: Convert to PyArrow-backed Pandas DataFrame
# The use_pyarrow_extension=True ensures no memory is duplicated
pandas_df = polars_df.to_pandas(use_pyarrow_extension=True)

# 3. Standard Scikit-Learn Workflow
X = pandas_df.drop(columns=["churn_label"])
y = pandas_df["churn_label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)
```

### Conclusion

The modern data professional does not work in isolation. By integrating AI assistants to write optimized Polars and DuckDB syntax, you minimize the learning curve of the modern stack. Furthermore, by utilizing Polars for heavy-duty feature engineering and executing a safe, zero-copy hand-off to Pandas only at the final predictive step, you achieve the perfect balance: the processing speed of Rust and C++ combined with the maturity of Python's machine learning ecosystem.

In the final chapter, we will tie all of these concepts together by walking through end-to-end, real-world case studies demonstrating this architecture in production.