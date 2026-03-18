# Chapter 3: Data Transformation and Wrangling with Polars

Data wrangling is the process of transforming raw, messy data into clean, structured formats suitable for analysis or machine learning models. For over a decade, Python developers relied on Pandas for these tasks. However, as datasets have grown into the gigabyte and terabyte range, Pandas' single-threaded architecture and high memory footprint have become significant bottlenecks.

**Polars** represents a paradigm shift. Written in Rust, it is a blazingly fast DataFrame library designed from the ground up for multi-threading, vectorized operations, and query optimization. In this chapter, we will explore the core concepts of Polars and learn how to perform complex data wrangling tasks efficiently.

---

## Core Polars Concepts

Before diving into transformations, it is essential to understand how Polars structures data and processes operations.

### Series and DataFrames

Like Pandas, Polars organizes data into two primary structures:
1.  **Series:** A 1-dimensional column of data. Every element in a Series must have the same data type (e.g., all integers or all strings).
2.  **DataFrame:** A 2-dimensional tabular structure composed of one or more Series.

```python
import polars as pl

# Creating a Series
ages = pl.Series("Age", [25, 30, 35, 40])

# Creating a DataFrame from a dictionary
df = pl.DataFrame({
    "Employee": ["Alice", "Bob", "Charlie", "Diana"],
    "Age": ages,
    "Department": ["HR", "Engineering", "Sales", "Engineering"]
})

print(df)
```

Unlike Pandas, Polars relies heavily on Apache Arrow's memory format under the hood, ensuring memory is contiguous and highly cache-efficient for modern CPUs.

### Eager vs. Lazy Execution

As introduced in Chapter 2, Polars supports both eager and lazy execution. While eager execution (using `pl.DataFrame`) runs commands immediately, lazy execution (using `pl.LazyFrame` via `.lazy()` or `.scan_*()`) builds a query plan.

Whenever possible, **always default to lazy execution** for complex transformations. The Polars query optimizer will reorder your operations to minimize memory usage and maximize speed.

```python
# Converting an eager DataFrame to a LazyFrame
lazy_df = df.lazy()

# Building a plan (No computation happens yet)
plan = (
    lazy_df
    .filter(pl.col("Age") > 28)
    .select(["Employee", "Department"])
)

# Executing the optimized plan
result = plan.collect()
print(result)
```

---

## Data Filtering and Selection

Selecting specific rows and columns is the foundation of data wrangling. Polars uses a powerful concept called **Expressions** to define these operations.

### Expressions in Polars

In Pandas, you often filter data using bracket notation (`df[df['Age'] > 30]`). In Polars, you use expressions, typically starting with `pl.col()`. This syntax is highly readable and allows the engine to optimize the underlying execution.

```python
import polars as pl

df = pl.read_csv("employees.csv")

# Selecting columns and creating a new derived column
transformed_df = df.select([
    pl.col("first_name"),
    pl.col("last_name"),
    (pl.col("salary") * 1.10).alias("new_salary") # 10% raise
])
```

The `alias()` method renames the output of the expression. Expressions can be chained infinitely, and Polars evaluates them in parallel wherever possible.

### Complex Filtering Using Multi-Threading

Polars evaluates multiple expressions in the `.filter()` or `.with_columns()` context concurrently. 

```python
# Filtering for Engineers earning over 80k OR Sales staff over 30 years old
filtered_df = df.filter(
    (pl.col("Department") == "Engineering") & (pl.col("Salary") > 80000) |
    (pl.col("Department") == "Sales") & (pl.col("Age") > 30)
)
```

Because Polars is written in Rust, it utilizes all available CPU cores to evaluate these logical conditions across millions of rows simultaneously.

---

## Aggregations and Grouping

Aggregating data is where Polars truly shines compared to legacy tools. The syntax is declarative, making it easy to perform multiple aggregations in a single pass.

### GroupBy Operations

The `.group_by()` (or `.groupby()` in older versions) method allows you to split your data into groups and apply expressions to each group.

```python
# Calculating multiple metrics per department
department_stats = df.group_by("Department").agg([
    pl.len().alias("employee_count"),
    pl.col("Salary").mean().alias("avg_salary"),
    pl.col("Age").max().alias("oldest_employee")
])

print(department_stats)
```

### Window Functions

Window functions allow you to perform aggregations over a specific "window" of rows without collapsing the DataFrame. In Polars, window functions are triggered using the `.over()` expression.

```python
# Calculating the average salary per department and appending it to the original rows
df_with_avg = df.with_columns([
    pl.col("Salary").mean().over("Department").alias("dept_avg_salary")
])

# Now we can calculate how much each employee earns compared to their department average
df_compared = df_with_avg.with_columns([
    (pl.col("Salary") - pl.col("dept_avg_salary")).alias("salary_diff_from_avg")
])
```

Window functions are incredibly powerful for feature engineering in machine learning, such as calculating rolling averages or ranking items within categories.

---

## Handling Missing Data and Anomalies

Real-world datasets are rarely perfect. They contain null values, outliers, and formatting errors. Polars provides a robust suite of tools to handle these anomalies safely.

### Filling Nulls, Dropping Rows, and Interpolation Strategies

Polars explicitly distinguishes between `null` (missing data) and `NaN` (Not a Number, usually from float operations). 

```python
import polars as pl

# Assume df has missing values in 'Age' and 'Salary' columns
messy_df = pl.DataFrame({
    "Name": ["Alice", "Bob", None, "Diana"],
    "Age": [25, None, 35, 40],
    "Salary": [50000, 60000, 55000, None]
})

# 1. Drop rows where specific columns are null
clean_df = messy_df.drop_nulls(subset=["Name"])

# 2. Fill missing Ages with the median age
clean_df = clean_df.with_columns(
    pl.col("Age").fill_null(strategy="median") # Alternatively, use a static value or 'forward'/'backward' fill
)

# 3. Interpolate missing Salary linearly
clean_df = clean_df.with_columns(
    pl.col("Salary").interpolate()
)

print(clean_df)
```

By leveraging `fill_null` and `interpolate` within `.with_columns()`, Polars can execute these cleaning steps across massive datasets with minimal memory overhead.

### Conclusion

Polars provides a modern, expressive API for data wrangling that naturally guides developers toward writing efficient, scalable code. By understanding the importance of lazy execution, mastering Polars expressions, and utilizing powerful aggregations and window functions, you can prepare datasets for analysis in a fraction of the time required by traditional tools.

In the next chapter, we will look at how to bridge the gap between this high-performance Python engine and SQL by integrating Polars directly with DuckDB.