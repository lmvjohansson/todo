"""
collect_metrics.py - Deployment experiment metrics collector

Combines ECS service event timing with k6 load test results into a single
CSV row per experiment run.

Usage:
    python collect_metrics.py \
        --experiment rolling_success_1 \
        --strategy rolling \
        --condition success \
        --k6-file results.json \
        --pipeline-start 14:05:23 \
        [--failure-mode none] \
        [--profile knightec] \
        [--output experiment_results.csv]

Arguments:
    --experiment      Unique experiment run ID (e.g. rolling_success_1)
    --strategy        Deployment strategy: rolling, blue-green, canary
    --condition       Test condition: success, failure
    --k6-file         Path to k6 JSON output file
    --pipeline-start  Time pipeline was triggered, HH:MM:SS (Stockholm time)
    --failure-mode    Failure mode: none, crash, health_fail, health_slow, application_error (default: none)
    --profile         AWS CLI profile (default: knightec)
    --output          Output CSV file (default: experiment_results.csv)
    --baseline-error  Error rate threshold for MTTR calculation in % (default: 1.0)
    --stable-window   Seconds of stable error rate required for MTTR end (default: 60)

MTTR definition:
    MTTR ends when BOTH conditions are satisfied:
        1. ECS reports steady state (rollback_end)
        2. k6 error rate has been below baseline_error threshold for stable_window seconds
    MTTR = pipeline_start -> max(rollback_end, k6_stable_time)
    If blast radius is 0%, condition 2 is met immediately and MTTR == pipeline_start -> rollback_end.
"""

import argparse
import boto3
import csv
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict


# ── Timezone helpers ──────────────────────────────────────────────────────────

STOCKHOLM = timezone(timedelta(hours=2))  # UTC+2 (CEST)


def parse_local_time(time_str):
    """Parse HH:MM:SS in Stockholm time and return UTC datetime."""
    today = datetime.now(tz=STOCKHOLM).strftime('%Y-%m-%d')
    dt = datetime.fromisoformat(f"{today}T{time_str}+02:00")
    return dt.astimezone(timezone.utc)


def fmt(dt):
    """Format datetime as HH:MM:SS UTC+2 for display."""
    return dt.astimezone(STOCKHOLM).strftime('%H:%M:%S')


def seconds_between(a, b):
    """Return seconds between two datetimes (b - a)."""
    return round((b - a).total_seconds(), 1)


# ── ECS metrics ───────────────────────────────────────────────────────────────

def fetch_ecs_events(profile, cluster='todo-cluster', service='todo-backend-service'):
    """Query ECS service events via boto3."""
    session = boto3.Session(profile_name=profile)
    ecs = session.client('ecs', region_name='eu-north-1')

    response = ecs.describe_services(cluster=cluster, services=[service])
    if not response['services']:
        print(f"ERROR: Service '{service}' not found in cluster '{cluster}'")
        sys.exit(1)

    return response['services'][0]['events']


def parse_ecs_timing_from_events(events, pipeline_start, condition, failure_mode='none'):
    """
    Derive all deployment timing from the ECS events log.

    Locates the deployment window by finding the first 'has started' event
    after the pipeline trigger (within a 15 minute build window), then extracts:

    Success:
        ecs_start       first task started after pipeline trigger
        ecs_end         'deployment completed' after ecs_start
        rollback_end    'reached a steady state' after ecs_start

    Failure:
        ecs_start       first task started after pipeline trigger
        detection_time  for application_error: 'alarm detected' or 'rolling back'
                        for other failure modes: 'rolling back' or first 'deregistered'
        rollback_end    'reached a steady state' after detection_time
    """
    pipeline_epoch = pipeline_start.timestamp()
    sorted_events = sorted(events, key=lambda e: e['createdAt'])

    ecs_start = None
    ecs_end = None
    detection_time = None
    rollback_end = None

    for event in sorted_events:
        ts = event['createdAt'].astimezone(timezone.utc)
        msg = event['message']
        epoch = ts.timestamp()

        if 'has started' in msg and pipeline_epoch <= epoch <= pipeline_epoch + 900:
            ecs_start = ts
            break

    if ecs_start is None:
        print("WARNING: Could not find deployment start in events log.")
        print("         The events may have been pushed out of the 100-event window.")
        return {
            'ecs_start': None,
            'ecs_end': None,
            'detection_time': None,
            'rollback_end': None,
        }

    for event in sorted_events:
        ts = event['createdAt'].astimezone(timezone.utc)
        msg = event['message']

        if ts <= ecs_start:
            continue

        if 'deployment completed' in msg and ecs_end is None:
            ecs_end = ts

        if 'reached a steady state' in msg:
            rollback_end = ts

        if condition == 'failure':
            if detection_time is None and 'alarm detected' in msg:
                detection_time = ts
            if detection_time is None and 'rolling back' in msg:
                detection_time = ts
            # For application_error, 'deregistered' fires during normal rolling replacement
            # before the alarm fires — only use it for health check failure modes
            if detection_time is None and failure_mode != 'application_error' and 'deregistered' in msg:
                detection_time = ts

    return {
        'ecs_start': ecs_start,
        'ecs_end': ecs_end if condition == 'success' else None,
        'detection_time': detection_time,
        'rollback_end': rollback_end,
    }


# ── k6 metrics ────────────────────────────────────────────────────────────────

def parse_k6_results(filepath):
    """
    Parse k6 JSON output into 10-second buckets.
    Returns dict: bucket_epoch -> {durations, errors, total}
    """
    buckets = defaultdict(lambda: {'durations': [], 'errors': 0, 'total': 0})

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get('type') != 'Point':
                continue

            metric = obj.get('metric')
            data = obj.get('data', {})
            value = data.get('value', 0)
            time_str = data.get('time', '')

            try:
                ts = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                epoch = ts.timestamp()
            except Exception:
                continue

            bucket = int(epoch // 10) * 10

            if metric == 'http_req_duration':
                buckets[bucket]['durations'].append(value)
                buckets[bucket]['total'] += 1
            elif metric == 'http_req_failed':
                if value == 1:
                    buckets[bucket]['errors'] += 1

    return buckets


def percentile(data, p):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (p / 100) * (len(sorted_data) - 1)
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[lower] + (index - lower) * (sorted_data[upper] - sorted_data[lower])


def error_rate(bucket):
    if bucket['total'] == 0:
        return 0.0
    return bucket['errors'] / bucket['total'] * 100


def compute_window_metrics(buckets, window_start, window_end):
    """Calculate p50/p95/p99 and error rate for requests within a time window."""
    start_epoch = window_start.timestamp()
    end_epoch = window_end.timestamp()

    durations = []
    errors = 0
    total = 0

    for bucket_epoch, data in buckets.items():
        if start_epoch <= bucket_epoch <= end_epoch:
            durations.extend(data['durations'])
            errors += data['errors']
            total += data['total']

    return {
        'p50': round(percentile(durations, 50), 2),
        'p95': round(percentile(durations, 95), 2),
        'p99': round(percentile(durations, 99), 2),
        'error_rate_pct': round(errors / total * 100, 2) if total > 0 else 0.0,
        'total_requests': total,
        'error_requests': errors,
    }


def find_k6_stable_time(buckets, search_start, baseline_error_pct=1.0, stable_window_seconds=60):
    """
    Find when k6 error rate dropped below threshold and stayed there.
    Searches from search_start onwards.
    Returns UTC datetime or None if not found.
    """
    start_epoch = search_start.timestamp()
    sorted_buckets = sorted(b for b in buckets.keys() if b >= start_epoch)

    stable_since = None
    for bucket_epoch in sorted_buckets:
        er = error_rate(buckets[bucket_epoch])
        if er <= baseline_error_pct:
            if stable_since is None:
                stable_since = bucket_epoch
            elif bucket_epoch - stable_since >= stable_window_seconds:
                return datetime.fromtimestamp(stable_since, tz=timezone.utc)
        else:
            stable_since = None

    return None


def compute_mttr(pipeline_start, rollback_end, k6_stable_time):
    """
    MTTR = pipeline_start -> max(rollback_end, k6_stable_time).
    Both conditions must be satisfied: ECS steady state AND k6 error rate stable.
    If k6_stable_time is None (no errors observed), MTTR = pipeline_start -> rollback_end.
    """
    if rollback_end is None:
        return None, None

    if k6_stable_time is None:
        mttr_end = rollback_end
        mttr_limited_by = 'ecs'
    else:
        mttr_end = max(rollback_end, k6_stable_time)
        mttr_limited_by = 'ecs' if rollback_end >= k6_stable_time else 'k6'

    return seconds_between(pipeline_start, mttr_end), mttr_limited_by


def compute_baseline_metrics(buckets, baseline_end, baseline_duration_seconds=120):
    """
    Calculate baseline metrics from the period before the deployment.
    Uses baseline_duration_seconds before baseline_end.
    """
    end_epoch = baseline_end.timestamp()
    start_epoch = end_epoch - baseline_duration_seconds

    durations = []
    for bucket_epoch, data in buckets.items():
        if start_epoch <= bucket_epoch <= end_epoch:
            durations.extend(data['durations'])

    return {
        'baseline_p50_ms': round(percentile(durations, 50), 2),
        'baseline_p95_ms': round(percentile(durations, 95), 2),
        'baseline_p99_ms': round(percentile(durations, 99), 2),
    }


# ── Cost metrics ──────────────────────────────────────────────────────────────

def fetch_last_log_event(logs_client, log_group, stream_name):
    """
    Fetch the last log event from a stream.
    Returns (message, timestamp_ms) tuple, or (None, None) if no events found.
    """
    response = logs_client.get_log_events(
        logGroupName=log_group,
        logStreamName=stream_name,
        limit=1,
        startFromHead=False,
    )
    events = response.get('events', [])
    if not events:
        return None, None
    return events[0]['message'], events[0]['timestamp']


def fetch_log_streams_in_window(profile, window_start, window_end, log_group='/ecs/todo-backend'):
    """
    Fetch all CloudWatch log streams in log_group that were active during
    [window_start, window_end]. Returns list of dicts with first and last
    as UTC datetimes representing actual task start and stop times.

    For streams without a 'Shutting down: Master' final log line, last is
    set to window_end — the task was still running when the window closed.
    """
    session = boto3.Session(profile_name=profile)
    logs = session.client('logs', region_name='eu-north-1')

    window_start_ms = int(window_start.timestamp() * 1000)
    window_end_ms   = int(window_end.timestamp() * 1000)

    streams = []
    kwargs = {'logGroupName': log_group, 'orderBy': 'LastEventTime', 'descending': True}

    while True:
        page = logs.describe_log_streams(**kwargs)
        for stream in page['logStreams']:
            first = stream.get('firstEventTimestamp', 0)
            last  = stream.get('lastEventTimestamp', 0)

            if first == 0 and last == 0:
                continue

            if first >= window_end_ms:
                continue

            if first < window_start_ms - (24 * 3600 * 1000):
                continue

            first_dt = datetime.fromtimestamp(first / 1000, tz=timezone.utc)

            last_msg, last_ts_ms = fetch_last_log_event(logs, log_group, stream['logStreamName'])
            if last_msg is None:
                continue
            elif 'Shutting down: Master' in last_msg:
                last_dt = datetime.fromtimestamp(last_ts_ms / 1000, tz=timezone.utc)
            else:
                last_dt = window_end

            if last_dt <= window_start:
                continue

            streams.append({
                'name':  stream['logStreamName'],
                'first': first_dt,
                'last':  last_dt,
            })

        if 'nextToken' not in page:
            break
        kwargs['nextToken'] = page['nextToken']

    return streams


def compute_cost_metrics(streams, window_start, window_end, baseline_tasks=5):
    """
    Compute extra task-seconds and estimated cost for a deployment window.

    For each log stream active during [window_start, window_end], computes the
    overlap with the window. Subtracts the baseline (steady-state tasks x window
    duration) to isolate overhead attributable to the deployment.

    Returns dict with:
        extra_task_seconds   -- task-seconds above baseline
        estimated_cost_usd   -- extra_task_seconds x Fargate per-second rate
    """
    VCPU_COST_PER_SECOND   = 0.0445 / 3600 * 0.5
    MEMORY_COST_PER_SECOND = 0.0049 / 3600 * 1.0
    TASK_COST_PER_SECOND   = VCPU_COST_PER_SECOND + MEMORY_COST_PER_SECOND

    window_duration = (window_end - window_start).total_seconds()

    actual_task_seconds = 0.0
    for stream in streams:
        task_start = max(stream['first'], window_start)
        task_end   = min(stream['last'],  window_end)

        if task_end <= task_start:
            continue

        overlap = (task_end - task_start).total_seconds()
        actual_task_seconds += overlap

    baseline_task_seconds = baseline_tasks * window_duration
    extra_task_seconds    = max(0.0, actual_task_seconds - baseline_task_seconds)
    estimated_cost_usd    = extra_task_seconds * TASK_COST_PER_SECOND

    return {
        'extra_task_seconds':  round(extra_task_seconds, 1),
        'estimated_cost_usd':  round(estimated_cost_usd, 6),
    }


# ── CSV output ────────────────────────────────────────────────────────────────

CSV_COLUMNS = [
    'experiment_id',
    'strategy',
    'condition',
    'failure_mode',
    'date',
    'pipeline_start',
    'ecs_deployment_start',
    'ecs_deployment_end',
    'total_deployment_duration_s',
    'ecs_deployment_duration_s',
    'baseline_p50_ms',
    'baseline_p95_ms',
    'baseline_p99_ms',
    'deployment_window_p50_ms',
    'deployment_window_p95_ms',
    'deployment_window_p99_ms',
    'deployment_window_error_rate_pct',
    'detection_time_s',
    'rollback_duration_s',
    'blast_radius_pct',
    'blast_radius_total_requests',
    'blast_radius_error_requests',
    'mttr_s',
    'mttr_limited_by',
    'k6_file',
    'extra_task_seconds',
    'estimated_cost_usd',
    'notes',
]


def write_csv_row(output_file, row):
    file_exists = os.path.exists(output_file)
    with open(output_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"\nResults written to: {output_file}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Collect deployment experiment metrics')
    parser.add_argument('--experiment',      required=True, help='Unique experiment ID')
    parser.add_argument('--strategy',        required=True, choices=['rolling', 'blue-green', 'canary'])
    parser.add_argument('--condition',       required=True, choices=['success', 'failure'])
    parser.add_argument('--k6-file',         required=True, help='Path to k6 JSON output file')
    parser.add_argument('--pipeline-start',  required=True, help='Pipeline trigger time HH:MM:SS (Stockholm time)')
    parser.add_argument('--failure-mode',    default='none', choices=['none', 'crash', 'health_fail', 'health_slow', 'application_error'])
    parser.add_argument('--profile',         default='knightec', help='AWS CLI profile')
    parser.add_argument('--output',          default='experiment_results.csv')
    parser.add_argument('--baseline-error',  type=float, default=1.0, help='Error rate threshold for MTTR (%%)')
    parser.add_argument('--stable-window',   type=int, default=60, help='Seconds of stable error rate for MTTR end')
    parser.add_argument('--notes',           default='', help='Optional notes for this run')
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Collecting metrics for: {args.experiment}")
    print(f"{'='*60}")

    pipeline_start = parse_local_time(args.pipeline_start)
    print(f"Pipeline start:     {fmt(pipeline_start)} (Stockholm)")

    print("\nQuerying ECS service events...")
    events = fetch_ecs_events(args.profile)
    timing = parse_ecs_timing_from_events(events, pipeline_start, args.condition, args.failure_mode)

    ecs_start = timing['ecs_start']
    ecs_end = timing['ecs_end']
    detection_time = timing['detection_time']
    rollback_end = timing['rollback_end']

    if ecs_start is None:
        print("ERROR: Cannot proceed without deployment start time.")
        sys.exit(1)

    print(f"ECS deployment start: {fmt(ecs_start)}")
    print(f"ECS deployment end:   {fmt(ecs_end) if ecs_end else 'N/A (failure scenario)'}")
    if rollback_end:
        print(f"ECS steady state:     {fmt(rollback_end)}")

    print(f"\nParsing k6 results from: {args.k6_file}")
    buckets = parse_k6_results(args.k6_file)
    print(f"Loaded {len(buckets)} time windows")

    baseline = compute_baseline_metrics(buckets, ecs_start)
    print(f"\nBaseline (pre-deployment):")
    print(f"  p50: {baseline['baseline_p50_ms']}ms  p95: {baseline['baseline_p95_ms']}ms  p99: {baseline['baseline_p99_ms']}ms")

    window_end = ecs_end or rollback_end or ecs_start
    deployment_window = compute_window_metrics(buckets, ecs_start, window_end)
    print(f"\nDeployment window metrics:")
    print(f"  p50: {deployment_window['p50']}ms  p95: {deployment_window['p95']}ms  p99: {deployment_window['p99']}ms")
    print(f"  Error rate: {deployment_window['error_rate_pct']}%  Requests: {deployment_window['total_requests']}")

    incident_end = ecs_end or rollback_end
    total_duration = seconds_between(pipeline_start, incident_end) if incident_end else None
    ecs_duration = seconds_between(ecs_start, ecs_end) if ecs_end else None

    print(f"\nTiming:")
    print(f"  Total deployment duration: {total_duration}s")
    print(f"  ECS deployment duration:   {ecs_duration}s")

    detection_time_s = None
    rollback_duration_s = None
    blast_radius_pct = None
    blast_radius_total = None
    blast_radius_errors = None
    mttr_s = None
    mttr_limited_by = None

    if args.condition == 'failure':
        if detection_time:
            detection_time_s = seconds_between(ecs_start, detection_time)
            print(f"  Detection time:            {detection_time_s}s")
        else:
            print("  Detection time:            NOT FOUND in events")

        if detection_time and rollback_end:
            rollback_duration_s = seconds_between(detection_time, rollback_end)
            print(f"  Rollback duration:         {rollback_duration_s}s")

        failure_end = rollback_end or window_end
        br = compute_window_metrics(buckets, ecs_start, failure_end)
        blast_radius_pct = br['error_rate_pct']
        blast_radius_total = br['total_requests']
        blast_radius_errors = br['error_requests']
        print(f"  Blast radius:              {blast_radius_pct}% ({blast_radius_errors}/{blast_radius_total} requests)")

        k6_stable_time = find_k6_stable_time(buckets, ecs_start, args.baseline_error, args.stable_window)
        mttr_s, mttr_limited_by = compute_mttr(pipeline_start, rollback_end, k6_stable_time)

        if mttr_s is not None:
            print(f"  MTTR:                      {mttr_s}s (limited by: {mttr_limited_by})")
            if k6_stable_time:
                print(f"  k6 stable at:              {fmt(k6_stable_time)}")
            print(f"  ECS steady state at:       {fmt(rollback_end) if rollback_end else 'NOT FOUND'}")
        else:
            print(f"  MTTR:                      NOT FOUND")

    print(f"\nCollecting cost metrics...")
    extra_task_seconds = ''
    estimated_cost_usd = ''
    if rollback_end is not None:
        cost_window_end = rollback_end + timedelta(minutes=10)
        streams = fetch_log_streams_in_window(args.profile, ecs_start, cost_window_end)
        print(f"  Found {len(streams)} log streams active during deployment window")
        cost = compute_cost_metrics(streams, ecs_start, cost_window_end)
        extra_task_seconds = cost['extra_task_seconds']
        estimated_cost_usd = cost['estimated_cost_usd']
        print(f"  Extra task-seconds:  {extra_task_seconds}s")
        print(f"  Estimated cost:      ${estimated_cost_usd}")
    else:
        print("  WARNING: rollback_end not found, skipping cost collection")

    today = datetime.now(tz=STOCKHOLM).strftime('%Y-%m-%d')
    row = {
        'experiment_id':                    args.experiment,
        'strategy':                         args.strategy,
        'condition':                        args.condition,
        'failure_mode':                     args.failure_mode,
        'date':                             today,
        'pipeline_start':                   fmt(pipeline_start),
        'ecs_deployment_start':             fmt(ecs_start),
        'ecs_deployment_end':               fmt(ecs_end) if ecs_end else '',
        'total_deployment_duration_s':      total_duration or '',
        'ecs_deployment_duration_s':        ecs_duration or '',
        'baseline_p50_ms':                  baseline['baseline_p50_ms'],
        'baseline_p95_ms':                  baseline['baseline_p95_ms'],
        'baseline_p99_ms':                  baseline['baseline_p99_ms'],
        'deployment_window_p50_ms':         deployment_window['p50'],
        'deployment_window_p95_ms':         deployment_window['p95'],
        'deployment_window_p99_ms':         deployment_window['p99'],
        'deployment_window_error_rate_pct': deployment_window['error_rate_pct'],
        'detection_time_s':                 detection_time_s or '',
        'rollback_duration_s':              rollback_duration_s or '',
        'blast_radius_pct':                 blast_radius_pct or '',
        'blast_radius_total_requests':      blast_radius_total or '',
        'blast_radius_error_requests':      blast_radius_errors or '',
        'mttr_s':                           mttr_s or '',
        'mttr_limited_by':                  mttr_limited_by or '',
        'extra_task_seconds':               extra_task_seconds,
        'estimated_cost_usd':               estimated_cost_usd,
        'k6_file':                          args.k6_file,
        'notes':                            args.notes,
    }

    write_csv_row(args.output, row)
    print(f"\nDone! Row added to {args.output}")


if __name__ == '__main__':
    main()