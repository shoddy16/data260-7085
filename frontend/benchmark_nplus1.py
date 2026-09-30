import csv
import os
import time
import statistics
import requests

BASE_URL = "http://127.0.0.1:8785/n-plus-one"
PAGE_SIZES = [10, 50, 200]
VERSIONS = ["naive", "fixed"]
REQUESTS_PER_COMBINATION = 30

os.makedirs("reports/hw04/raw", exist_ok=True)

raw_file = "reports/hw04/raw/nplus1_raw.csv"

def percentile(values, p):
    values = sorted(values)
    index = (len(values) - 1) * p / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    weight = index - lower
    return values[lower] + (values[upper] - values[lower]) * weight

raw_rows = []
summary_rows = []

for page_size in PAGE_SIZES:
    for version in VERSIONS:
        url = f"{BASE_URL}/{version}"
        latencies = []
        sql_counts = []

        for request_number in range(1, REQUESTS_PER_COMBINATION + 1):
            start = time.perf_counter()

            response = requests.get(
                url,
                params={"page_size": page_size},
                timeout=30
            )

            elapsed_ms = (time.perf_counter() - start) * 1000

            response.raise_for_status()
            data = response.json()

            sql_count = data["queries"]

            latencies.append(elapsed_ms)
            sql_counts.append(sql_count)

            raw_rows.append({
                "page_size": page_size,
                "version": version,
                "request_number": request_number,
                "sql_statements": sql_count,
                "latency_ms": round(elapsed_ms, 4)
            })

        summary_rows.append({
            "page_size": page_size,
            "version": version,
            "sql_stmts_req": statistics.mean(sql_counts),
            "p50_ms": percentile(latencies, 50),
            "p95_ms": percentile(latencies, 95),
            "p99_ms": percentile(latencies, 99)
        })

with open(raw_file, "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "page_size",
            "version",
            "request_number",
            "sql_statements",
            "latency_ms"
        ]
    )
    writer.writeheader()
    writer.writerows(raw_rows)

print("RAW DATA SAVED:", raw_file)
print("TOTAL RAW REQUESTS:", len(raw_rows))

print("\n3.4 RESULTS")
print("-" * 80)

for row in summary_rows:
    print(
        f"{row['page_size']:>8} | "
        f"{row['version']:<6} | "
        f"{row['sql_stmts_req']:>10.1f} | "
        f"{row['p50_ms']:>10.2f} | "
        f"{row['p95_ms']:>10.2f} | "
        f"{row['p99_ms']:>10.2f}"
    )