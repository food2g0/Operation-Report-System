"""
server_monitor.py — Real-time server metrics dashboard during load tests.

Monitors:
  System  : CPU %, RAM %, Disk I/O (MB/s read/write, IOPS)
  API     : RPS, error rate, P50/P95/P99 latency, cache hit rate
  Database: Connections, running threads, slow queries, InnoDB buffer hit rate

Two modes (auto-detected):
  LOCAL  — run ON the Ubuntu server (full psutil + MySQL + API metrics)
  REMOTE — run from Windows (API metrics only via /api/stats polling)

Usage:
    # On the server:
    python server_monitor.py

    # From Windows against the remote server:
    python server_monitor.py --host http://222.127.90.218:5000

    # Custom interval / log to CSV:
    python server_monitor.py --interval 2 --log monitor_log.csv

    # Stop after N seconds:
    python server_monitor.py --duration 300

Requires (server): pip install psutil pymysql rich requests
Requires (Windows): pip install rich requests
"""

import argparse
import collections
import csv
import datetime
import os
import socket
import statistics
import sys
import time
import threading
from typing import Optional

# ── Optional imports ───────────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    sys.exit("Install requests:  pip install requests")

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    from rich import box
    RICH = True
except ImportError:
    RICH = False
    Console = Live = Table = Panel = Columns = Text = box = None
    print("[WARN] Install rich for a nicer display:  pip install rich")

try:
    import psutil
    PSUTIL = True
except ImportError:
    PSUTIL = False

try:
    import pymysql
    PYMYSQL = True
except ImportError:
    PYMYSQL = False

# ── Config ─────────────────────────────────────────────────────────────────────
DEFAULT_HOST     = "http://127.0.0.1:5000"
DEFAULT_INTERVAL = 2          # seconds between polls
API_KEY = os.environ.get(
    "ORS_API_KEY",
    "",
)

# May be overridden by --key CLI argument (set in main() below)
_cli_api_key: str = ""

# Alert thresholds
ALERT_CPU_PCT      = 80.0
ALERT_RAM_PCT      = 85.0
ALERT_ERROR_RATE   = 1.0      # %
ALERT_P95_MS       = 500      # ms
ALERT_SLOW_QUERIES = 5        # count delta per interval
ALERT_DB_CONNS     = 90       # % of max_connections

# MySQL connection (server-side only) — reads env vars or falls back to defaults
MYSQL_HOST = os.environ.get("MYSQL_HOST",     "222.127.90.218")
MYSQL_USER = os.environ.get("MYSQL_USER",     "ors_user")
MYSQL_PASS = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB   = os.environ.get("MYSQL_DB",       "operation_db")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "33306"))



def _is_local(host: str) -> bool:
    return "127.0.0.1" in host or "localhost" in host


def _fmt_bytes(n: float) -> str:
    if n >= 1_048_576:
        return f"{n/1_048_576:.1f} MB/s"
    if n >= 1024:
        return f"{n/1024:.1f} KB/s"
    return f"{n:.0f} B/s"


def _color_val(val: float, warn: float, danger: float, fmt: str = ".1f") -> str:
    """Return a rich-markup colored string based on thresholds."""
    s = f"{val:{fmt}}"
    if val >= danger:
        return f"[bold red]{s}[/bold red]"
    if val >= warn:
        return f"[yellow]{s}[/yellow]"
    return f"[green]{s}[/green]"


def _alert_text(msg: str) -> str:
    return f"[bold red]⚠ {msg}[/bold red]"


# ── Token fetch ────────────────────────────────────────────────────────────────
def _get_token(host: str, timeout: int = 5) -> Optional[str]:
    key = _cli_api_key or API_KEY
    try:
        r = requests.post(
            f"{host}/api/token",
            json={"api_key": key},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json().get("token")
        # Print status code to help diagnose wrong key vs connection issue
        print(f"\n  [token] HTTP {r.status_code}: {r.text[:120]}")
    except requests.exceptions.ConnectionError as e:
        print(f"\n  [token] Connection refused — is api_server.py running on {host}?")
        print(f"          Check with:  ss -tlnp | grep python")
    except requests.exceptions.Timeout:
        print(f"\n  [token] Timed out connecting to {host}")
    except Exception as e:
        print(f"\n  [token] Error: {e}")
    return None


# ── API stats polling ─────────────────────────────────────────────────────────
def _poll_api_stats(host: str, token: str, timeout: int = 5) -> dict:
    try:
        r = requests.get(
            f"{host}/api/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


# ── System metrics (local only) ───────────────────────────────────────────────
_prev_disk_io = None
_prev_disk_ts = None

def _poll_system() -> dict:
    global _prev_disk_io, _prev_disk_ts
    if not PSUTIL:
        return {}

    cpu   = psutil.cpu_percent(interval=None)
    ram   = psutil.virtual_memory()
    swap  = psutil.swap_memory()

    # Disk I/O delta
    disk_read_bps  = 0.0
    disk_write_bps = 0.0
    disk_read_iops = 0.0
    disk_write_iops= 0.0
    try:
        curr_io = psutil.disk_io_counters()
        now     = time.monotonic()
        if _prev_disk_io is not None and _prev_disk_ts is not None:
            dt = now - _prev_disk_ts
            if dt > 0:
                disk_read_bps   = (curr_io.read_bytes  - _prev_disk_io.read_bytes)  / dt
                disk_write_bps  = (curr_io.write_bytes - _prev_disk_io.write_bytes) / dt
                disk_read_iops  = (curr_io.read_count  - _prev_disk_io.read_count)  / dt
                disk_write_iops = (curr_io.write_count - _prev_disk_io.write_count) / dt
        _prev_disk_io = curr_io
        _prev_disk_ts = now
    except Exception:
        pass

    # Per-CPU usage
    try:
        per_cpu = psutil.cpu_percent(percpu=True)
    except Exception:
        per_cpu = []

    return {
        "cpu_pct":        cpu,
        "per_cpu":        per_cpu,
        "ram_pct":        ram.percent,
        "ram_used_gb":    ram.used / (1024**3),
        "ram_total_gb":   ram.total / (1024**3),
        "swap_pct":       swap.percent,
        "disk_read_bps":  disk_read_bps,
        "disk_write_bps": disk_write_bps,
        "disk_read_iops": disk_read_iops,
        "disk_write_iops":disk_write_iops,
    }


# ── MySQL metrics (local only) ─────────────────────────────────────────────────
_prev_slow_queries = None
_prev_questions    = None
_prev_db_ts        = None

def _poll_mysql() -> dict:
    global _prev_slow_queries, _prev_questions, _prev_db_ts
    if not PYMYSQL:
        return {}
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST, user=MYSQL_USER,
            password=MYSQL_PASS, database=MYSQL_DB,
            port=MYSQL_PORT, connect_timeout=3,
        )
        cur = conn.cursor()

        # Global status vars we care about
        cur.execute("""
            SHOW GLOBAL STATUS WHERE Variable_name IN (
                'Threads_connected', 'Threads_running', 'Threads_cached',
                'Slow_queries', 'Questions',
                'Com_select', 'Com_insert', 'Com_update', 'Com_delete',
                'Innodb_buffer_pool_reads',
                'Innodb_buffer_pool_read_requests',
                'Innodb_row_lock_waits',
                'Innodb_row_lock_time_avg',
                'Aborted_connects', 'Connection_errors_max_connections'
            )
        """)
        status = {row[0]: row[1] for row in cur.fetchall()}

        # Max connections variable
        cur.execute("SHOW VARIABLES LIKE 'max_connections'")
        row = cur.fetchone()
        max_conns = int(row[1]) if row else 151

        # Active non-sleep queries
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.processlist
            WHERE command != 'Sleep'
        """)
        active_queries = cur.fetchone()[0]

        # Slow queries right now (running > 1s)
        cur.execute("""
            SELECT id, user, host, db, time, state, LEFT(info, 80) AS query
            FROM information_schema.processlist
            WHERE time > 1 AND command != 'Sleep'
            ORDER BY time DESC
            LIMIT 5
        """)
        slow_now = cur.fetchall()

        cur.close()
        conn.close()

        # Derived metrics
        threads_connected = int(status.get("Threads_connected", 0))
        threads_running   = int(status.get("Threads_running",   0))
        slow_queries_total= int(status.get("Slow_queries",      0))
        questions         = int(status.get("Questions",         0))
        bp_reads          = int(status.get("Innodb_buffer_pool_reads",         0))
        bp_req            = int(status.get("Innodb_buffer_pool_read_requests", 0))
        row_lock_waits    = int(status.get("Innodb_row_lock_waits",            0))
        row_lock_avg_ms   = int(status.get("Innodb_row_lock_time_avg",         0))

        conn_pct = threads_connected / max_conns * 100 if max_conns else 0
        bp_hit_rate = (
            (1 - bp_reads / bp_req) * 100
            if bp_req > 0 else 100.0
        )

        # Deltas per interval
        now = time.monotonic()
        slow_delta = 0
        qps = 0.0
        if _prev_slow_queries is not None and _prev_questions is not None and _prev_db_ts is not None:
            dt = now - _prev_db_ts
            slow_delta = slow_queries_total - _prev_slow_queries
            qps = (questions - _prev_questions) / dt if dt > 0 else 0.0
        _prev_slow_queries = slow_queries_total
        _prev_questions    = questions
        _prev_db_ts        = now

        return {
            "threads_connected": threads_connected,
            "threads_running":   threads_running,
            "threads_cached":    int(status.get("Threads_cached", 0)),
            "max_connections":   max_conns,
            "conn_pct":          conn_pct,
            "active_queries":    active_queries,
            "slow_queries_total":slow_queries_total,
            "slow_delta":        slow_delta,
            "qps":               qps,
            "bp_hit_rate":       bp_hit_rate,
            "row_lock_waits":    row_lock_waits,
            "row_lock_avg_ms":   row_lock_avg_ms,
            "slow_now":          slow_now,
            "com_select":        int(status.get("Com_select", 0)),
            "com_insert":        int(status.get("Com_insert", 0)),
            "com_update":        int(status.get("Com_update", 0)),
        }
    except Exception as e:
        return {"error": str(e)}


# ── API latency calculator from /api/stats recent list ────────────────────────
def _calc_latency(recent: list) -> dict:
    lats = [r["ms"] for r in recent if isinstance(r.get("ms"), (int, float))]
    if not lats:
        return {"p50": 0, "p95": 0, "p99": 0, "mean": 0, "max": 0}
    sl = sorted(lats)
    n  = len(sl)
    return {
        "p50":  sl[n // 2],
        "p95":  sl[int(n * 0.95)],
        "p99":  sl[int(n * 0.99)],
        "mean": int(statistics.mean(sl)),
        "max":  max(sl),
    }


def _calc_rps_and_errors(recent: list, interval: float) -> tuple:
    """Estimate RPS and error rate from the recent request window."""
    if not recent:
        return 0.0, 0.0
    total  = len(recent)
    errors = sum(1 for r in recent if r.get("status", 200) >= 400)
    # /api/stats recent buffer is 200 entries; use actual count for rate estimation
    err_rate = errors / total * 100 if total else 0.0
    # RPS estimate: total requests in window / window_age
    timestamps = [r.get("time") for r in recent if r.get("time")]
    rps = 0.0
    if len(timestamps) >= 2:
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            t_newest = datetime.datetime.strptime(timestamps[0],  fmt)
            t_oldest = datetime.datetime.strptime(timestamps[-1], fmt)
            window_s = max((t_newest - t_oldest).total_seconds(), 1.0)
            rps = total / window_s
        except Exception:
            pass
    return rps, err_rate


# ── Alerts accumulator ─────────────────────────────────────────────────────────
_alerts: collections.deque = collections.deque(maxlen=6)

def _check_alerts(sys_m: dict, db_m: dict, api_m: dict, lat: dict, err_rate: float):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    if sys_m.get("cpu_pct", 0) >= ALERT_CPU_PCT:
        _alerts.appendleft(f"[{ts}] CPU {sys_m['cpu_pct']:.0f}% >= {ALERT_CPU_PCT}%")
    if sys_m.get("ram_pct", 0) >= ALERT_RAM_PCT:
        _alerts.appendleft(f"[{ts}] RAM {sys_m['ram_pct']:.0f}% >= {ALERT_RAM_PCT}%")
    if err_rate >= ALERT_ERROR_RATE:
        _alerts.appendleft(f"[{ts}] Error rate {err_rate:.1f}% >= {ALERT_ERROR_RATE}%")
    if lat.get("p95", 0) >= ALERT_P95_MS:
        _alerts.appendleft(f"[{ts}] P95 latency {lat['p95']}ms >= {ALERT_P95_MS}ms")
    if db_m.get("slow_delta", 0) >= ALERT_SLOW_QUERIES:
        _alerts.appendleft(f"[{ts}] {db_m['slow_delta']} new slow queries this interval")
    if db_m.get("conn_pct", 0) >= ALERT_DB_CONNS:
        _alerts.appendleft(f"[{ts}] DB connections at {db_m['conn_pct']:.0f}% of max")


# ── Rich dashboard builder ─────────────────────────────────────────────────────
def _build_dashboard(sys_m: dict, db_m: dict, api_stats: dict,
                     lat: dict, rps: float, err_rate: float,
                     local_mode: bool, tick: int) -> Panel:
    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uptime = api_stats.get("uptime", "—")

    # ── System table ──────────────────────────────────────────────────────────
    sys_tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
    sys_tbl.add_column(style="bold cyan", no_wrap=True, width=22)
    sys_tbl.add_column(style="white", justify="right")

    if local_mode and sys_m:
        sys_tbl.add_row("CPU Usage",
            _color_val(sys_m["cpu_pct"], 60, ALERT_CPU_PCT, ".1f") + "%")
        if sys_m.get("per_cpu"):
            bars = " ".join(
                ("█" if c >= 80 else "▓" if c >= 50 else "░")
                for c in sys_m["per_cpu"]
            )
            sys_tbl.add_row("  per core", f"[dim]{bars}[/dim]")
        sys_tbl.add_row("RAM Usage",
            _color_val(sys_m["ram_pct"], 70, ALERT_RAM_PCT, ".1f") + "%" +
            f"  ({sys_m['ram_used_gb']:.1f}/{sys_m['ram_total_gb']:.1f} GB)")
        if sys_m.get("swap_pct", 0) > 0:
            sys_tbl.add_row("Swap Usage",
                _color_val(sys_m["swap_pct"], 20, 50, ".1f") + "%")
        sys_tbl.add_row("Disk Read",
            f"[cyan]{_fmt_bytes(sys_m['disk_read_bps'])}[/cyan]"
            f"  {sys_m['disk_read_iops']:.0f} IOPS")
        sys_tbl.add_row("Disk Write",
            f"[magenta]{_fmt_bytes(sys_m['disk_write_bps'])}[/magenta]"
            f"  {sys_m['disk_write_iops']:.0f} IOPS")
    else:
        sys_tbl.add_row("[dim]System metrics[/dim]", "[dim]server-side only[/dim]")

    # ── API table ─────────────────────────────────────────────────────────────
    api_tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
    api_tbl.add_column(style="bold cyan", no_wrap=True, width=22)
    api_tbl.add_column(style="white", justify="right")

    api_tbl.add_row("Uptime",      f"[white]{uptime}[/white]")
    api_tbl.add_row("RPS",         f"[bold white]{rps:.1f}[/bold white] req/s")
    api_tbl.add_row("Error Rate",
        _color_val(err_rate, 0.5, ALERT_ERROR_RATE, ".2f") + "%")
    api_tbl.add_row("Latency P50",  f"{lat.get('p50', '—')} ms")
    api_tbl.add_row("Latency P95",
        _color_val(lat.get("p95", 0), 300, ALERT_P95_MS, "d") + " ms")
    api_tbl.add_row("Latency P99",
        _color_val(lat.get("p99", 0), 500, 800, "d") + " ms")
    api_tbl.add_row("Latency Max",
        _color_val(lat.get("max", 0), 600, 1000, "d") + " ms")

    cache = api_stats.get("cache", {})
    hit_rate = cache.get("hit_rate_pct", 0)
    api_tbl.add_row("Cache Backend", f"[dim]{cache.get('backend', '—')}[/dim]")
    api_tbl.add_row("Cache Hit Rate",
        _color_val(hit_rate, 20, 5, ".1f") + "%" +
        f"  ({cache.get('hits', 0)}H / {cache.get('misses', 0)}M)")

    pool = api_stats.get("db_pool", {})
    api_tbl.add_row("DB Pool",
        f"[green]{pool.get('available', '?')}[/green] avail  "
        f"[yellow]{pool.get('checked_out', '?')}[/yellow] out  "
        f"overflow=[dim]{pool.get('overflow', '?')}[/dim]")

    # ── DB table ──────────────────────────────────────────────────────────────
    db_tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
    db_tbl.add_column(style="bold cyan", no_wrap=True, width=22)
    db_tbl.add_column(style="white", justify="right")

    if local_mode and db_m and "error" not in db_m:
        conn_pct = db_m.get("conn_pct", 0)
        db_tbl.add_row("Connections",
            _color_val(db_m["threads_connected"], 50, 100, "d") +
            f" / {db_m['max_connections']}"
            f"  ({_color_val(conn_pct, 50, ALERT_DB_CONNS, '.0f')}%)")
        db_tbl.add_row("Active Queries",
            _color_val(db_m["active_queries"], 5, 20, "d"))
        db_tbl.add_row("Threads Running",
            _color_val(db_m["threads_running"], 4, 8, "d"))
        db_tbl.add_row("QPS (delta)",     f"[white]{db_m.get('qps', 0):.0f}[/white] q/s")
        db_tbl.add_row("Slow Queries",
            _color_val(db_m["slow_delta"], 1, ALERT_SLOW_QUERIES, "d") +
            f"  (total: {db_m['slow_queries_total']})")
        bp = db_m.get("bp_hit_rate", 100)
        db_tbl.add_row("InnoDB Buffer Hit",
            _color_val(bp, 95, 90, ".1f") + "%")
        if db_m.get("row_lock_waits", 0) > 0:
            db_tbl.add_row("Row Lock Waits",
                f"[yellow]{db_m['row_lock_waits']}[/yellow]"
                f"  avg {db_m['row_lock_avg_ms']}ms")
        db_tbl.add_row("SEL/INS/UPD",
            f"[dim]{db_m.get('com_select',0)}/"
            f"{db_m.get('com_insert',0)}/"
            f"{db_m.get('com_update',0)}[/dim]")
    elif "error" in db_m:
        db_tbl.add_row("[red]MySQL error[/red]", f"[dim]{db_m['error'][:40]}[/dim]")
    else:
        db_tbl.add_row("[dim]MySQL metrics[/dim]", "[dim]server-side only[/dim]")

    # ── Slow queries panel ────────────────────────────────────────────────────
    slow_rows = db_m.get("slow_now", []) if local_mode else []
    slow_panel_content = ""
    if slow_rows:
        sq_tbl = Table(box=box.SIMPLE, padding=(0, 1), expand=True)
        sq_tbl.add_column("Time(s)", style="red",  justify="right", width=8)
        sq_tbl.add_column("State",   style="yellow", width=16)
        sq_tbl.add_column("Query",   style="dim",    no_wrap=True)
        for row in slow_rows:
            _, _, _, _, t, state, q = row
            sq_tbl.add_row(str(t), str(state or ""), str(q or ""))
    else:
        sq_tbl = Text("No slow queries detected", style="dim green")

    # ── Alerts ────────────────────────────────────────────────────────────────
    if _alerts:
        alert_lines = "\n".join(f"[bold red]{a}[/bold red]" for a in _alerts)
    else:
        alert_lines = "[green]✓ All metrics within normal range[/green]"

    # ── Endpoint breakdown ────────────────────────────────────────────────────
    hits   = api_stats.get("total_hits",   {})
    errors = api_stats.get("total_errors", {})
    ep_tbl = Table(box=box.SIMPLE, padding=(0, 1), expand=True)
    ep_tbl.add_column("Endpoint",   style="bold white", no_wrap=True)
    ep_tbl.add_column("Hits",       justify="right", style="cyan")
    ep_tbl.add_column("Errors",     justify="right")
    ep_tbl.add_column("Err%",       justify="right")
    for ep in sorted(hits.keys()):
        h = hits[ep]
        e = errors.get(ep, 0)
        ep_pct = e / h * 100 if h else 0.0
        ep_tbl.add_row(
            ep,
            str(h),
            f"[red]{e}[/red]" if e else "[green]0[/green]",
            _color_val(ep_pct, 0.5, 1.0, ".1f") + "%" if h else "[dim]—[/dim]",
        )

    # ── Layout ────────────────────────────────────────────────────────────────
    mode_tag = "[green]LOCAL[/green]" if local_mode else "[yellow]REMOTE[/yellow]"
    title = f"[bold cyan]ORS Server Monitor[/bold cyan]  {mode_tag}  [dim]{ts}[/dim]  tick={tick}"

    from rich.layout import Layout
    layout = Layout()
    layout.split_column(
        Layout(name="top",    size=12),
        Layout(name="ep",     size=len(hits) + 4 if hits else 5),
        Layout(name="slow",   size=len(slow_rows) + 4 if slow_rows else 3),
        Layout(name="alerts", size=4),
    )
    layout["top"].split_row(
        Layout(Panel(sys_tbl,  title="[bold]System",   border_style="blue"),  name="sys"),
        Layout(Panel(api_tbl,  title="[bold]API",      border_style="cyan"),  name="api"),
        Layout(Panel(db_tbl,   title="[bold]Database", border_style="green"), name="db"),
    )
    layout["ep"].update(Panel(ep_tbl,    title="[bold]Endpoint Breakdown",  border_style="dim"))
    layout["slow"].update(Panel(sq_tbl,  title="[bold]Active Slow Queries", border_style="red" if slow_rows else "dim"))
    layout["alerts"].update(Panel(alert_lines, title="[bold]Alerts",         border_style="red" if _alerts else "dim green"))

    return Panel(layout, title=title, border_style="bold cyan")


# ── Plain-text fallback ────────────────────────────────────────────────────────
def _print_plain(sys_m, db_m, api_stats, lat, rps, err_rate, tick):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*60}  {ts}  tick={tick}")
    print(f"  API  | RPS={rps:.1f}  Err={err_rate:.2f}%  P50={lat.get('p50')}ms  P95={lat.get('p95')}ms  P99={lat.get('p99')}ms")
    cache = api_stats.get("cache", {})
    print(f"  Cache| {cache.get('backend','?')}  hit={cache.get('hit_rate_pct',0):.1f}%  hits={cache.get('hits',0)}  misses={cache.get('misses',0)}")
    pool  = api_stats.get("db_pool", {})
    print(f"  Pool | avail={pool.get('available','?')}  out={pool.get('checked_out','?')}  overflow={pool.get('overflow','?')}")
    if sys_m:
        print(f"  SYS  | CPU={sys_m.get('cpu_pct',0):.1f}%  RAM={sys_m.get('ram_pct',0):.1f}%  "
              f"DiskR={_fmt_bytes(sys_m.get('disk_read_bps',0))}  DiskW={_fmt_bytes(sys_m.get('disk_write_bps',0))}")
    if db_m and "error" not in db_m:
        print(f"  DB   | conns={db_m.get('threads_connected',0)}/{db_m.get('max_connections',0)}"
              f"  running={db_m.get('threads_running',0)}  slow_delta={db_m.get('slow_delta',0)}"
              f"  buf_hit={db_m.get('bp_hit_rate',0):.1f}%  QPS={db_m.get('qps',0):.0f}")
    if _alerts:
        for a in list(_alerts)[:3]:
            print(f"  ⚠    | {a}")


# ── CSV logger ─────────────────────────────────────────────────────────────────
_csv_file   = None
_csv_writer = None

def _init_csv(path: str):
    global _csv_file, _csv_writer
    _csv_file = open(path, "w", newline="", encoding="utf-8")
    _csv_writer = csv.writer(_csv_file)
    _csv_writer.writerow([
        "timestamp", "tick",
        "cpu_pct", "ram_pct", "disk_read_bps", "disk_write_bps",
        "disk_read_iops", "disk_write_iops",
        "rps", "error_rate_pct", "p50_ms", "p95_ms", "p99_ms", "max_ms",
        "cache_hit_pct", "cache_hits", "cache_misses",
        "db_pool_available", "db_pool_out",
        "db_connections", "db_running", "db_slow_delta", "db_qps", "db_bp_hit",
    ])

def _log_csv(tick, sys_m, db_m, api_stats, lat, rps, err_rate):
    if _csv_writer is None:
        return
    cache = api_stats.get("cache", {})
    pool  = api_stats.get("db_pool", {})
    _csv_writer.writerow([
        datetime.datetime.now().isoformat(), tick,
        sys_m.get("cpu_pct",        ""),
        sys_m.get("ram_pct",        ""),
        sys_m.get("disk_read_bps",  ""),
        sys_m.get("disk_write_bps", ""),
        sys_m.get("disk_read_iops", ""),
        sys_m.get("disk_write_iops",""),
        f"{rps:.1f}", f"{err_rate:.2f}",
        lat.get("p50", ""), lat.get("p95", ""), lat.get("p99", ""), lat.get("max", ""),
        cache.get("hit_rate_pct", ""),
        cache.get("hits",   ""),
        cache.get("misses", ""),
        pool.get("available",    ""),
        pool.get("checked_out",  ""),
        db_m.get("threads_connected", ""),
        db_m.get("threads_running",   ""),
        db_m.get("slow_delta",        ""),
        f"{db_m.get('qps', 0):.0f}" if db_m.get("qps") is not None else "",
        f"{db_m.get('bp_hit_rate', 0):.1f}" if db_m.get("bp_hit_rate") is not None else "",
    ])
    _csv_file.flush()


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ORS Server Monitor")
    parser.add_argument("--host",     default=DEFAULT_HOST, help="API base URL")
    parser.add_argument("--interval", default=DEFAULT_INTERVAL, type=float, help="Poll interval (seconds)")
    parser.add_argument("--log",      default="",  help="Save metrics to CSV file")
    parser.add_argument("--duration", default=0,   type=int, help="Stop after N seconds (0=forever)")
    parser.add_argument("--key",      default="",  help="Override ORS_API_KEY for this session")
    args = parser.parse_args()

    global _cli_api_key
    _cli_api_key = args.key

    host       = args.host.rstrip("/")
    local_mode = _is_local(host) and PSUTIL

    print(f"ORS Server Monitor")
    print(f"  Host       : {host}")
    print(f"  Mode       : {'LOCAL (full metrics)' if local_mode else 'REMOTE (API metrics only)'}")
    print(f"  Interval   : {args.interval}s")
    print(f"  psutil     : {'yes' if PSUTIL else 'no — pip install psutil'}")
    print(f"  pymysql    : {'yes' if PYMYSQL else 'no — pip install pymysql'}")
    if args.log:
        print(f"  CSV log    : {args.log}")
        _init_csv(args.log)
    print()

    # Get initial token
    print("Fetching token...", end=" ", flush=True)
    token = _get_token(host)
    if not token:
        print("FAILED — check host and API_KEY")
        sys.exit(1)
    print("OK")
    print("Starting monitor (Ctrl+C to stop)...\n")

    # Prime psutil CPU (first call returns 0.0)
    if PSUTIL:
        psutil.cpu_percent(interval=None)
        time.sleep(0.2)

    tick      = 0
    start_ts  = time.monotonic()
    console   = Console() if RICH else None

    # Token refresh — re-fetch every 11 hours
    token_ts = time.monotonic()

    def _maybe_refresh_token():
        nonlocal token, token_ts
        if time.monotonic() - token_ts > 11 * 3600:
            new = _get_token(host)
            if new:
                token    = new
                token_ts = time.monotonic()

    try:
        if RICH:
            with Live(console=console, refresh_per_second=1, screen=False) as live:
                while True:
                    _maybe_refresh_token()
                    tick += 1

                    sys_m    = _poll_system()
                    db_m     = _poll_mysql() if local_mode else {}
                    api_stats= _poll_api_stats(host, token)

                    recent   = api_stats.get("recent", [])
                    lat      = _calc_latency(recent)
                    rps, err = _calc_rps_and_errors(recent, args.interval)

                    _check_alerts(sys_m, db_m, api_stats, lat, err)

                    if args.log:
                        _log_csv(tick, sys_m, db_m, api_stats, lat, rps, err)

                    panel = _build_dashboard(sys_m, db_m, api_stats, lat, rps, err, local_mode, tick)
                    live.update(panel)

                    if args.duration and (time.monotonic() - start_ts) >= args.duration:
                        break
                    time.sleep(args.interval)
        else:
            while True:
                _maybe_refresh_token()
                tick += 1

                sys_m    = _poll_system()
                db_m     = _poll_mysql() if local_mode else {}
                api_stats= _poll_api_stats(host, token)

                recent   = api_stats.get("recent", [])
                lat      = _calc_latency(recent)
                rps, err = _calc_rps_and_errors(recent, args.interval)

                _check_alerts(sys_m, db_m, api_stats, lat, err)

                if args.log:
                    _log_csv(tick, sys_m, db_m, api_stats, lat, rps, err)

                _print_plain(sys_m, db_m, api_stats, lat, rps, err, tick)

                if args.duration and (time.monotonic() - start_ts) >= args.duration:
                    break
                time.sleep(args.interval)

    except KeyboardInterrupt:
        pass
    finally:
        if _csv_file:
            _csv_file.close()
            print(f"\nMetrics saved to: {args.log}")
        print("\nMonitor stopped.")

        # Print final summary
        print("\n── Final Alerts ─────────────────────────────")
        if _alerts:
            for a in _alerts:
                print(f"  ⚠  {a}")
        else:
            print("  ✓  No threshold breaches detected")


if __name__ == "__main__":
    main()
