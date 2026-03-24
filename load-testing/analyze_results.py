import json
import sys
from datetime import datetime, timezone
from collections import defaultdict
import statistics

def parse_results(filepath, window_seconds=10):
    windows = defaultdict(lambda: {"durations": [], "errors": 0, "total": 0})

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") != "Point":
                continue

            metric = obj.get("metric")
            data = obj.get("data", {})
            time_str = data.get("time", "")
            value = data.get("value", 0)

            try:
                ts = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                epoch = ts.timestamp()
            except Exception:
                continue

            bucket = int(epoch // window_seconds) * window_seconds

            if metric == "http_req_duration":
                windows[bucket]["durations"].append(value)
                windows[bucket]["total"] += 1
            elif metric == "http_req_failed":
                if value == 1:
                    windows[bucket]["errors"] += 1

    return windows


def percentile(data, p):
    if not data:
        return 0
    sorted_data = sorted(data)
    index = (p / 100) * (len(sorted_data) - 1)
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    fraction = index - lower
    return sorted_data[lower] + fraction * (sorted_data[upper] - sorted_data[lower])


def print_results(windows, window_seconds=10, deployment_time=None):
    print(f"\n{'Time':<25} {'Requests':>10} {'Errors':>8} {'Error%':>8} {'p50 (ms)':>10} {'p95 (ms)':>10} {'p99 (ms)':>10}")
    print("-" * 90)

    for bucket in sorted(windows.keys()):
        w = windows[bucket]
        durations = w["durations"]
        total = w["total"]
        errors = w["errors"]

        if total == 0:
            continue

        p50 = percentile(durations, 50)
        p95 = percentile(durations, 95)
        p99 = percentile(durations, 99)
        error_pct = (errors / total * 100) if total > 0 else 0

        ts = datetime.fromtimestamp(bucket, tz=timezone.utc).strftime('%H:%M:%S')

        # Mark the deployment window
        marker = ""
        if deployment_time:
            if abs(bucket - deployment_time) < window_seconds * 3:
                marker = " <-- deployment"

        print(f"{ts:<25} {total:>10} {errors:>8} {error_pct:>7.1f}% {p50:>10.1f} {p95:>10.1f} {p99:>10.1f}{marker}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <results.json> [deployment_timestamp]")
        print("Example: python analyze_results.py results.json 14:23:00")
        sys.exit(1)

    filepath = sys.argv[1]

    deployment_time = None
    if len(sys.argv) >= 3:
        try:
            today = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')
            dt = datetime.fromisoformat(f"{today}T{sys.argv[2]}+00:00")
            deployment_time = dt.timestamp()
            print(f"Marking deployment at: {sys.argv[2]} UTC")
        except Exception:
            print(f"Could not parse deployment time '{sys.argv[2]}', ignoring.")

    windows = parse_results(filepath)
    print_results(windows, deployment_time=deployment_time)
    print(f"\nTotal time windows: {len(windows)}")
