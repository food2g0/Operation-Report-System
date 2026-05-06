"""
load_test.py — Simulate 400+ branches uploading reports simultaneously.

Usage:
    python load_test.py                        # 400 branches, all scenarios
    python load_test.py --branches 100         # quick run with 100 branches
    python load_test.py --url http://222.127.90.218  # target server
    python load_test.py --ramp 10              # ramp-up 10 new branches per second

Requires: pip install requests rich
"""

import argparse
import datetime
import random
import statistics
import sys
import time
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    sys.exit("Install requests first:  pip install requests")

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich import box
    RICH = True
except ImportError:
    RICH = False
    print("[INFO] Install 'rich' for a nicer display:  pip install rich")

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_URL      = "http://222.127.90.218"
DEFAULT_BRANCHES = 400
API_KEY          = os.environ.get("ORS_API_KEY", "")
JWT_HOURS        = 12   # matches ORS_JWT_HOURS on the server
TOKEN_WORKERS    = 40   # parallel threads for the token-fetch phase
REPORT_WORKERS   = 80   # parallel threads for the report-upload phase

# Realistic corporation/branch names
CORPS = ["PALAWAN", "GLOBAL", "FT_HO", "SANLA", "MC", "OSF"]
BRANCHES = [f"BR{i:04d}" for i in range(1, 600)]
USERS    = [f"user_{i}" for i in range(1, 50)]

# ── Result container ──────────────────────────────────────────────────────────
@dataclass
class Result:
    branch:     str
    scenario:   str
    status:     int          # HTTP status code, 0 = connection error
    latency_ms: float
    cached:     bool  = False
    error:      str   = ""


# ── HTTP session factory (with retry) ────────────────────────────────────────
def _make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=2, backoff_factor=0.2, status_forcelist=[502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s.mount("http://",  adapter)
    s.mount("https://", adapter)
    return s


# ── Token fetch ───────────────────────────────────────────────────────────────
def fetch_token(base_url: str, session: requests.Session, timeout: int = 10) -> Optional[str]:
    try:
        r = session.post(
            f"{base_url}/api/token",
            json={"api_key": API_KEY},
            timeout=timeout,
        )
        if r.status_code == 200:
            return r.json().get("token")
    except Exception:
        pass
    return None


# ── SQL scenarios simulating real branch report uploads ───────────────────────
def _rand_date() -> str:
    base = datetime.date(2026, 4, 24)
    delta = datetime.timedelta(days=random.randint(0, 30))
    return str(base - delta)

def _rand_amount() -> float:
    return round(random.uniform(100, 99999), 2)

def _rand_lotes() -> int:
    return random.randint(0, 50)

def build_scenarios(branch: str) -> List[dict]:
    corp  = random.choice(CORPS)
    user  = random.choice(USERS)
    date  = _rand_date()
    amt   = _rand_amount()

    beginning = _rand_amount()
    deb       = _rand_amount()
    cre       = round(random.uniform(0, deb), 2)
    debit_total   = round(beginning + deb, 2)
    credit_total  = cre
    ending        = round(debit_total - credit_total, 2)
    cash_count    = round(ending + random.uniform(-500, 500), 2)
    cash_result   = round(cash_count - ending, 2)
    variance_status = "balanced" if abs(cash_result) < 0.01 else ("over" if cash_result > 0 else "short")

    sc   = round(random.uniform(10, 500), 2)
    comm = round(sc * 0.05, 2)
    tot  = round(amt + sc + comm, 2)

    return [
        # ── daily_reports (Brand B) ────────────────────────────────────────
        {
            "name": "INSERT daily_reports",
            "sql": (
                "INSERT INTO daily_reports "
                "(date, username, branch, corporation, beginning_balance, debit_total, "
                " credit_total, ending_balance, cash_count, cash_result, variance_status, is_locked) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "  beginning_balance=VALUES(beginning_balance), debit_total=VALUES(debit_total), "
                "  credit_total=VALUES(credit_total), ending_balance=VALUES(ending_balance), "
                "  cash_count=VALUES(cash_count), cash_result=VALUES(cash_result), "
                "  variance_status=VALUES(variance_status)"
            ),
            "params": [date, user, branch, corp, beginning, debit_total, credit_total,
                       ending, cash_count, cash_result, variance_status, 0],
            "endpoint": "exec",
        },
        {
            "name": "SELECT daily_reports",
            "sql": (
                "SELECT id, date, beginning_balance, debit_total, credit_total, "
                "ending_balance, cash_result, variance_status "
                "FROM daily_reports WHERE branch=%s ORDER BY date DESC LIMIT 10"
            ),
            "params": [branch],
            "endpoint": "exec",
        },
        # ── daily_reports_brand_a (Brand A) ───────────────────────────────
        {
            "name": "INSERT daily_reports_brand_a",
            "sql": (
                "INSERT INTO daily_reports_brand_a "
                "(date, username, branch, corporation, beginning_balance, debit_total, "
                " credit_total, ending_balance, cash_count, cash_result, variance_status, is_locked) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "  beginning_balance=VALUES(beginning_balance), debit_total=VALUES(debit_total), "
                "  credit_total=VALUES(credit_total), ending_balance=VALUES(ending_balance), "
                "  cash_count=VALUES(cash_count), cash_result=VALUES(cash_result), "
                "  variance_status=VALUES(variance_status)"
            ),
            "params": [date, user, branch, corp, beginning, debit_total, credit_total,
                       ending, cash_count, cash_result, variance_status, 0],
            "endpoint": "exec",
        },
        {
            "name": "SELECT daily_reports_brand_a",
            "sql": (
                "SELECT id, date, beginning_balance, debit_total, credit_total, "
                "ending_balance, cash_result, variance_status "
                "FROM daily_reports_brand_a WHERE branch=%s ORDER BY date DESC LIMIT 10"
            ),
            "params": [branch],
            "endpoint": "exec",
        },
        # ── global_other_services_tbl ─────────────────────────────────────
        {
            "name": "INSERT global_other_services_tbl",
            "sql": (
                "INSERT INTO global_other_services_tbl "
                "(date, branch, corporation, username, "
                " gcash_out, gcash_out_lotes, moneygram, moneygram_lotes, "
                " transfast, transfast_lotes, ria, ria_lotes, "
                " remitly, remitly_lotes, mc_out, mc_out_lotes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE "
                "  gcash_out=VALUES(gcash_out), moneygram=VALUES(moneygram), "
                "  transfast=VALUES(transfast), ria=VALUES(ria), "
                "  remitly=VALUES(remitly), mc_out=VALUES(mc_out)"
            ),
            "params": [
                date, branch, corp, user,
                _rand_amount(), _rand_lotes(), _rand_amount(), _rand_lotes(),
                _rand_amount(), _rand_lotes(), _rand_amount(), _rand_lotes(),
                _rand_amount(), _rand_lotes(), _rand_amount(), _rand_lotes(),
            ],
            "endpoint": "exec",
        },
        {
            "name": "SELECT global_other_services_tbl",
            "sql": (
                "SELECT date, branch, gcash_out, moneygram, transfast, ria, remitly, mc_out "
                "FROM global_other_services_tbl WHERE branch=%s ORDER BY date DESC LIMIT 10"
            ),
            "params": [branch],
            "endpoint": "exec",
        },
        # ── other_services_brand_a (alias: other_services_tbl_brand_a) ────
        {
            "name": "INSERT other_services_tbl_brand_a",
            "sql": (
                "INSERT INTO other_services_tbl_brand_a "
                "(date, branch, corporation, username, "
                " palawan_send_out, palawan_send_out_lotes, palawan_sc, palawan_sc_lotes, "
                " gcash_in, gcash_in_lotes, gcash_out, gcash_out_lotes, "
                " remitly, remitly_lotes, moneygram, moneygram_lotes) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE "
                "  palawan_send_out=VALUES(palawan_send_out), palawan_sc=VALUES(palawan_sc), "
                "  gcash_in=VALUES(gcash_in), gcash_out=VALUES(gcash_out), "
                "  remitly=VALUES(remitly), moneygram=VALUES(moneygram)"
            ),
            "params": [
                date, branch, corp, user,
                _rand_amount(), _rand_lotes(), _rand_amount(), _rand_lotes(),
                _rand_amount(), _rand_lotes(), _rand_amount(), _rand_lotes(),
                _rand_amount(), _rand_lotes(), _rand_amount(), _rand_lotes(),
            ],
            "endpoint": "exec",
        },
        {
            "name": "SELECT other_services_tbl_brand_a",
            "sql": (
                "SELECT date, branch, palawan_send_out, palawan_sc, gcash_in, gcash_out "
                "FROM other_services_tbl_brand_a WHERE branch=%s ORDER BY date DESC LIMIT 10"
            ),
            "params": [branch],
            "endpoint": "exec",
        },
        # ── payable_tbl (Brand B) ─────────────────────────────────────────
        {
            "name": "INSERT payable_tbl",
            "sql": (
                "INSERT INTO payable_tbl "
                "(corporation, branch, date, "
                " sendout_capital, sendout_sc, sendout_commission, sendout_total, "
                " payout_capital, payout_sc, payout_commission, payout_total, "
                " skid, skir, cancellation, inc) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE "
                "  sendout_capital=VALUES(sendout_capital), sendout_total=VALUES(sendout_total), "
                "  payout_capital=VALUES(payout_capital), payout_total=VALUES(payout_total)"
            ),
            "params": [
                corp, branch, date,
                amt, sc, comm, tot,
                _rand_amount(), sc, comm, tot,
                round(random.uniform(0, 500), 2), round(random.uniform(0, 500), 2),
                round(random.uniform(0, 200), 2), round(random.uniform(0, 1000), 2),
            ],
            "endpoint": "exec",
        },
        {
            "name": "SELECT payable_tbl",
            "sql": (
                "SELECT date, branch, sendout_total, payout_total "
                "FROM payable_tbl WHERE branch=%s ORDER BY date DESC LIMIT 10"
            ),
            "params": [branch],
            "endpoint": "exec",
        },
        # ── payable_tbl_brand_a (Brand A) ─────────────────────────────────
        {
            "name": "INSERT payable_tbl_brand_a",
            "sql": (
                "INSERT INTO payable_tbl_brand_a "
                "(corporation, branch, date, "
                " sendout_capital, sendout_sc, sendout_commission, sendout_total, "
                " payout_capital, payout_sc, payout_commission, payout_total, "
                " skid, skir, cancellation, inc) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON DUPLICATE KEY UPDATE "
                "  sendout_capital=VALUES(sendout_capital), sendout_total=VALUES(sendout_total), "
                "  payout_capital=VALUES(payout_capital), payout_total=VALUES(payout_total)"
            ),
            "params": [
                corp, branch, date,
                amt, sc, comm, tot,
                _rand_amount(), sc, comm, tot,
                round(random.uniform(0, 500), 2), round(random.uniform(0, 500), 2),
                round(random.uniform(0, 200), 2), round(random.uniform(0, 1000), 2),
            ],
            "endpoint": "exec",
        },
        {
            "name": "SELECT payable_tbl_brand_a",
            "sql": (
                "SELECT date, branch, sendout_total, payout_total "
                "FROM payable_tbl_brand_a WHERE branch=%s ORDER BY date DESC LIMIT 10"
            ),
            "params": [branch],
            "endpoint": "exec",
        },
        # ── API stress-test endpoints ─────────────────────────────────────
        {
            "name": "GET /health",
            "sql":  None,
            "params": None,
            "endpoint": "health",
        },
        {
            "name": "GET /api/stats",
            "sql":  None,
            "params": None,
            "endpoint": "stats",
        },
        {
            "name": "POST /api/token",
            "sql":  None,
            "params": None,
            "endpoint": "token",
        },
        {
            "name": "SELECT exec_safe",
            "sql": (
                "SELECT COUNT(*) AS cnt FROM daily_reports WHERE branch=%s"
            ),
            "params": [branch],
            "endpoint": "exec_safe",
        },
    ]


# ── Single branch simulation ───────────────────────────────────────────────────
def simulate_branch(
    branch: str,
    base_url: str,
    token: str,
    timeout: int = 15,
) -> List[Result]:
    session = _make_session()
    headers = {"Authorization": f"Bearer {token}"}
    results: List[Result] = []

    for scenario in build_scenarios(branch):
        t0       = time.perf_counter()
        endpoint = scenario.get("endpoint", "exec")

        # ── Health check (no auth) ──────────────────────────────────────────
        if endpoint == "health":
            try:
                r = session.get(f"{base_url}/api/health", timeout=timeout)
                ms = (time.perf_counter() - t0) * 1000
                results.append(Result(
                    branch=branch, scenario=scenario["name"],
                    status=r.status_code, latency_ms=round(ms, 1),
                ))
            except Exception as e:
                ms = (time.perf_counter() - t0) * 1000
                results.append(Result(
                    branch=branch, scenario=scenario["name"],
                    status=0, latency_ms=round(ms, 1), error=str(e)[:80],
                ))
            continue

        # ── Stats endpoint ──────────────────────────────────────────────────
        if endpoint == "stats":
            try:
                r = session.get(
                    f"{base_url}/api/stats", headers=headers, timeout=timeout)
                ms = (time.perf_counter() - t0) * 1000
                results.append(Result(
                    branch=branch, scenario=scenario["name"],
                    status=r.status_code, latency_ms=round(ms, 1),
                ))
            except Exception as e:
                ms = (time.perf_counter() - t0) * 1000
                results.append(Result(
                    branch=branch, scenario=scenario["name"],
                    status=0, latency_ms=round(ms, 1), error=str(e)[:80],
                ))
            continue

        # ── Token endpoint (stress auth) ────────────────────────────────────
        if endpoint == "token":
            try:
                r = session.post(
                    f"{base_url}/api/token",
                    json={"api_key": API_KEY},
                    timeout=timeout,
                )
                ms = (time.perf_counter() - t0) * 1000
                results.append(Result(
                    branch=branch, scenario=scenario["name"],
                    status=r.status_code, latency_ms=round(ms, 1),
                ))
            except Exception as e:
                ms = (time.perf_counter() - t0) * 1000
                results.append(Result(
                    branch=branch, scenario=scenario["name"],
                    status=0, latency_ms=round(ms, 1), error=str(e)[:80],
                ))
            continue

        # ── /api/exec or /api/exec_safe (SQL workload) ──────────────────────
        api_path = "/api/exec_safe" if endpoint == "exec_safe" else "/api/exec"
        payload = {"sql": scenario["sql"], "params": scenario["params"]}
        try:
            r = session.post(
                f"{base_url}{api_path}",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            ms = (time.perf_counter() - t0) * 1000
            cached = False
            if r.status_code == 200:
                try:
                    cached = r.json().get("cached", False)
                except Exception:
                    pass
            results.append(Result(
                branch=branch, scenario=scenario["name"],
                status=r.status_code, latency_ms=round(ms, 1),
                cached=cached,
            ))
        except requests.exceptions.ConnectionError as e:
            ms = (time.perf_counter() - t0) * 1000
            results.append(Result(
                branch=branch, scenario=scenario["name"],
                status=0, latency_ms=round(ms, 1), error="ConnectionError",
            ))
        except requests.exceptions.Timeout:
            ms = (time.perf_counter() - t0) * 1000
            results.append(Result(
                branch=branch, scenario=scenario["name"],
                status=0, latency_ms=round(ms, 1), error="Timeout",
            ))
        except Exception as e:
            ms = (time.perf_counter() - t0) * 1000
            results.append(Result(
                branch=branch, scenario=scenario["name"],
                status=0, latency_ms=round(ms, 1), error=str(e)[:80],
            ))

    return results


# ── Progress counter (thread-safe) ────────────────────────────────────────────
_lock        = threading.Lock()
_done_count  = 0
_total_count = 0

def _inc():
    global _done_count
    with _lock:
        _done_count += 1


# ── Print summary table ────────────────────────────────────────────────────────
def print_summary(all_results: List[Result], elapsed: float, branch_count: int):
    total   = len(all_results)
    ok      = [r for r in all_results if r.status == 200]
    errors  = [r for r in all_results if r.status != 200]
    cached  = [r for r in ok if r.cached]
    lats    = [r.latency_ms for r in all_results]
    ok_lats = [r.latency_ms for r in ok]

    status_counts = Counter(r.status for r in all_results)
    error_by_type = Counter(r.error for r in errors if r.error)
    by_scenario: dict = defaultdict(lambda: {"ok": 0, "err": 0, "lats": []})
    for r in all_results:
        s = by_scenario[r.scenario]
        if r.status == 200:
            s["ok"] += 1
        else:
            s["err"] += 1
        s["lats"].append(r.latency_ms)

    rps = total / elapsed if elapsed else 0

    if RICH:
        console = Console()
        console.rule("[bold cyan]LOAD TEST RESULTS")

        # ── Overview ──────────────────────────────────────────────────────────
        overview = Table(box=box.SIMPLE_HEAVY, show_header=False, padding=(0, 2))
        overview.add_column(style="bold cyan", no_wrap=True)
        overview.add_column(style="white")
        overview.add_row("Branches simulated",    str(branch_count))
        overview.add_row("Total requests",        str(total))
        overview.add_row("Success (200)",          f"[green]{len(ok)}[/green]  ({len(ok)/total*100:.1f}%)")
        overview.add_row("Errors",                 f"[red]{len(errors)}[/red]  ({len(errors)/total*100:.1f}%)" if errors else "[green]0[/green]")
        overview.add_row("Cache hits",             f"{len(cached)} / {len(ok)}  ({len(cached)/len(ok)*100:.1f}%)" if ok else "0")
        overview.add_row("Elapsed",                f"{elapsed:.2f}s")
        overview.add_row("Throughput",             f"{rps:.1f} req/s")
        console.print(overview)

        # ── Latency ───────────────────────────────────────────────────────────
        if lats:
            slats = sorted(lats)
            n     = len(slats)
            lat_t = Table(title="Latency (all requests)", box=box.SIMPLE, padding=(0, 2))
            for col in ["Min", "Median", "P90", "P95", "P99", "Max", "Mean"]:
                lat_t.add_column(col, style="cyan", justify="right")
            lat_t.add_row(
                f"{min(slats):.0f}ms",
                f"{slats[n//2]:.0f}ms",
                f"{slats[int(n*.90)]:.0f}ms",
                f"{slats[int(n*.95)]:.0f}ms",
                f"{slats[int(n*.99)]:.0f}ms",
                f"{max(slats):.0f}ms",
                f"{statistics.mean(slats):.0f}ms",
            )
            console.print(lat_t)

        # ── Per-scenario breakdown ─────────────────────────────────────────────
        sc_t = Table(title="Per-Scenario Breakdown", box=box.SIMPLE, padding=(0, 2))
        sc_t.add_column("Scenario",    style="bold white", no_wrap=True)
        sc_t.add_column("OK",          style="green",  justify="right")
        sc_t.add_column("Err",         style="red",    justify="right")
        sc_t.add_column("Median ms",   justify="right")
        sc_t.add_column("P95 ms",      justify="right")
        sc_t.add_column("Max ms",      justify="right")
        for sc_name, sc_data in sorted(by_scenario.items()):
            sl = sorted(sc_data["lats"])
            n  = len(sl)
            sc_t.add_row(
                sc_name,
                str(sc_data["ok"]),
                str(sc_data["err"]) if sc_data["err"] else "[green]0[/green]",
                f"{sl[n//2]:.0f}" if n else "-",
                f"{sl[int(n*.95)]:.0f}" if n else "-",
                f"{max(sl):.0f}" if n else "-",
            )
        console.print(sc_t)

        # ── HTTP status breakdown ──────────────────────────────────────────────
        if len(status_counts) > 1 or (status_counts and 200 not in status_counts):
            st_t = Table(title="HTTP Status Codes", box=box.SIMPLE, padding=(0, 2))
            st_t.add_column("Status", style="cyan")
            st_t.add_column("Count",  justify="right")
            for code, cnt in sorted(status_counts.items()):
                color = "green" if code == 200 else ("yellow" if code == 429 else "red")
                st_t.add_row(f"[{color}]{code}[/{color}]", str(cnt))
            console.print(st_t)

        # ── Top errors ────────────────────────────────────────────────────────
        if error_by_type:
            console.print("\n[bold red]Top errors:[/bold red]")
            for msg, cnt in error_by_type.most_common(5):
                console.print(f"  {cnt:>4}x  {msg}")

        # ── Verdict ───────────────────────────────────────────────────────────
        success_rate = len(ok) / total * 100 if total else 0
        if success_rate >= 99:
            console.rule("[bold green]PASS — server handled the load cleanly")
        elif success_rate >= 95:
            console.rule("[bold yellow]WARN — minor errors (check rate limiting or DB pool)")
        else:
            console.rule("[bold red]FAIL — significant errors detected")

    else:
        # Plain-text fallback
        print("=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Branches simulated : {branch_count}")
        print(f"Total requests     : {total}")
        print(f"Success (200)      : {len(ok)} ({len(ok)/total*100:.1f}%)")
        print(f"Errors             : {len(errors)} ({len(errors)/total*100:.1f}%)")
        print(f"Cache hits         : {len(cached)}")
        print(f"Elapsed            : {elapsed:.2f}s")
        print(f"Throughput         : {rps:.1f} req/s")
        if lats:
            slats = sorted(lats)
            n     = len(slats)
            print(f"\nLatency (ms):  min={min(slats):.0f}  median={slats[n//2]:.0f}  "
                  f"p90={slats[int(n*.9)]:.0f}  p99={slats[int(n*.99)]:.0f}  max={max(slats):.0f}")
        # Always show HTTP status breakdown
        print("\nHTTP status codes:")
        for code, cnt in sorted(status_counts.items()):
            label = " <-- RATE LIMITED by Nginx" if code == 429 else ""
            label = " <-- CONNECTION REFUSED"    if code == 0   else label
            print(f"  {code:>3}  {cnt:>5}x{label}")
        # Per-scenario breakdown
        print("\nPer-scenario breakdown:")
        print(f"  {'Scenario':<22} {'OK':>6} {'Err':>6} {'Median':>8} {'P95':>8} {'Max':>8}")
        for sc_name, sc_data in sorted(by_scenario.items()):
            sl = sorted(sc_data["lats"])
            n  = len(sl)
            med = f"{sl[n//2]:.0f}ms" if n else "-"
            p95 = f"{sl[int(n*.95)]:.0f}ms" if n else "-"
            mx  = f"{max(sl):.0f}ms" if n else "-"
            print(f"  {sc_name:<22} {sc_data['ok']:>6} {sc_data['err']:>6} {med:>8} {p95:>8} {mx:>8}")
        if error_by_type:
            print("\nTop connection errors:")
            for msg, cnt in error_by_type.most_common(5):
                print(f"  {cnt}x  {msg}")
        success_rate = len(ok) / total * 100 if total else 0
        print()
        if success_rate >= 99:
            print("VERDICT: PASS — server handled the load cleanly")
        elif success_rate >= 95:
            print("VERDICT: WARN — minor errors (check rate limiting or DB pool)")
        else:
            print("VERDICT: FAIL — significant errors detected")
            if status_counts.get(429, 0) > 10:
                print("  TIP: Most failures are 429 (rate limited). This is normal when")
                print("  load-testing from a SINGLE IP — Nginx limits per IP.")
                print("  Use --direct to bypass Nginx and test the app server directly:")
                print("    python load_test.py --direct")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global _total_count

    parser = argparse.ArgumentParser(description="ORS load test — simulates 400+ concurrent branch uploads")
    parser.add_argument("--url",      default=DEFAULT_URL,      help="Base API URL")
    parser.add_argument("--branches", default=DEFAULT_BRANCHES, type=int, help="Number of branches to simulate")
    parser.add_argument("--ramp",     default=0,               type=int, help="New branches per second (0=instant burst)")
    parser.add_argument("--timeout",  default=15,              type=int, help="Per-request timeout in seconds")
    parser.add_argument("--direct",   action="store_true",
                        help="Bypass Nginx — connect directly to port 5000 (use for single-IP load testing)")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    if args.direct:
        # Strip port if present, then force port 5000
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(base_url)
        base_url = urlunparse(parsed._replace(netloc=f"{parsed.hostname}:5000"))
        print("  [--direct] Bypassing Nginx — using", base_url)
    branch_count = args.branches
    _total_count = branch_count

    console = Console() if RICH else None

    print(f"\nTarget : {base_url}")
    print(f"Branches: {branch_count}")
    print(f"Ramp-up : {'instant burst' if args.ramp == 0 else f'{args.ramp} branches/sec'}")

    # ── Phase 1: Verify server is up ──────────────────────────────────────────
    print("\n[Phase 1] Checking server health...")
    try:
        r = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"  /api/health → {r.status_code}  {r.json()}")
        if r.status_code != 200:
            print("  WARNING: server returned non-200 health check")
    except Exception as e:
        print(f"  ERROR: Cannot reach {base_url} — {e}")
        sys.exit(1)

    # ── Phase 2: Fetch tokens (one per branch to be realistic) ───────────────
    print(f"\n[Phase 2] Fetching tokens ({min(TOKEN_WORKERS, branch_count)} parallel)...")
    session0 = _make_session()

    token_ok = 0
    master_token = fetch_token(base_url, session0)
    if not master_token:
        print("  ERROR: Could not obtain a token — check API_KEY and server.")
        sys.exit(1)

    # In production, clients share a token per machine.  Here we reuse one
    # master token for all simulated branches (same as production flow).
    print(f"  Token OK (expires {JWT_HOURS}h)")

    # ── Phase 3: Simulate all branches ───────────────────────────────────────
    branch_names = random.sample(BRANCHES, min(branch_count, len(BRANCHES)))
    # If more branches than pre-defined names, wrap around
    while len(branch_names) < branch_count:
        branch_names += random.sample(BRANCHES, min(branch_count - len(branch_names), len(BRANCHES)))

    all_results: List[Result] = []
    lock = threading.Lock()

    print(f"\n[Phase 3] Launching {branch_count} branches "
          f"({'burst' if args.ramp == 0 else f'ramp {args.ramp}/s'})...")

    if RICH:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
        )
        task_id = progress.add_task("Branches uploading...", total=branch_count)
    else:
        progress = None

    def run_branch(branch_name):
        results = simulate_branch(branch_name, base_url, master_token, args.timeout)
        with lock:
            all_results.extend(results)
            if RICH and progress:
                progress.advance(task_id)
        return len(results)

    t_start = time.perf_counter()

    if RICH:
        with Live(progress, refresh_per_second=10):
            if args.ramp == 0:
                # Instant burst
                with ThreadPoolExecutor(max_workers=REPORT_WORKERS) as pool:
                    futures = [pool.submit(run_branch, b) for b in branch_names]
                    for f in as_completed(futures):
                        _ = f.result()  # surface exceptions
            else:
                # Ramp-up
                batch_delay = 1.0 / args.ramp
                futures = []
                with ThreadPoolExecutor(max_workers=REPORT_WORKERS) as pool:
                    for b in branch_names:
                        futures.append(pool.submit(run_branch, b))
                        time.sleep(batch_delay)
                    for f in as_completed(futures):
                        _ = f.result()
    else:
        with ThreadPoolExecutor(max_workers=REPORT_WORKERS) as pool:
            futures = [pool.submit(run_branch, b) for b in branch_names]
            done = 0
            for f in as_completed(futures):
                _ = f.result()
                done += 1
                if done % 50 == 0 or done == branch_count:
                    print(f"  {done}/{branch_count} branches done  "
                          f"({time.perf_counter()-t_start:.1f}s elapsed)")

    elapsed = time.perf_counter() - t_start

    # ── Phase 4: Pull final server stats ─────────────────────────────────────
    print(f"\n[Phase 4] Fetching final server stats...")
    # Wait briefly so rate-limit bucket can refill before the stats call
    time.sleep(1)
    try:
        r = session0.get(
            f"{base_url}/api/stats",
            headers={"Authorization": f"Bearer {master_token}"},
            timeout=10,
        )
        if r.status_code == 429:
            print("  Stats request rate-limited (429) — retrying in 3s...")
            time.sleep(3)
            r = session0.get(
                f"{base_url}/api/stats",
                headers={"Authorization": f"Bearer {master_token}"},
                timeout=10,
            )
        if r.status_code == 200:
            s = r.json()
            cache = s.get("cache", {})
            pool  = s.get("db_pool", {})
            print(f"  Server uptime  : {s.get('uptime')}")
            print(f"  Cache backend  : {cache.get('backend')}  "
                  f"hit_rate={cache.get('hit_rate_pct')}%  "
                  f"hits={cache.get('hits')}  misses={cache.get('misses')}")
            print(f"  DB pool        : size={pool.get('pool_size')}  "
                  f"checked_out={pool.get('checked_out')}  "
                  f"overflow={pool.get('overflow')}  "
                  f"available={pool.get('available')}")
    except Exception as e:
        print(f"  Could not fetch stats: {e}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print_summary(all_results, elapsed, branch_count)


if __name__ == "__main__":
    main()
