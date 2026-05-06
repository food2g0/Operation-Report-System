"""
locustfile.py — Realistic 500-branch ORS load test using Locust.

Usage:
    pip install locust

    # Headless (CI / server terminal):
    locust --headless -u 500 -r 25 --run-time 3m --host http://222.127.90.218

    # Bypass Nginx (direct to app, no rate limiting):
    locust --headless -u 500 -r 25 --run-time 3m --host http://222.127.90.218:5000

    # Interactive web UI (open http://localhost:8089):
    locust --host http://222.127.90.218

Scenario weights (realistic daily branch workflow):
    ┌─────────────────────────────────────────┬────────┐
    │ Task                                    │ Weight │
    ├─────────────────────────────────────────┼────────┤
    │ Health check (periodic keep-alive)      │  5     │
    │ Load previous balance (SELECT)          │  20    │
    │ Check existing entry (SELECT)           │  15    │
    │ Submit daily_reports (INSERT/UPDATE)    │  10    │
    │ Submit daily_reports_brand_a            │  10    │
    │ Submit payable_tbl (Palawan)            │  8     │
    │ Submit payable_tbl_brand_a              │  8     │
    │ Submit global_other_services_tbl        │  6     │
    │ Submit other_services_tbl_brand_a       │  6     │
    │ Read report history (SELECT × 2 tables) │  10    │
    │ Admin summary SELECT (aggregation)      │  2     │
    └─────────────────────────────────────────┴────────┘
"""

import datetime
import json
import os
import random
import time
import threading

from locust import HttpUser, task, between, events
from locust.exception import StopUser
import requests as _requests

# ── Config ─────────────────────────────────────────────────────────────────────
API_KEY = os.environ.get(
    "ORS_API_KEY",
    "",
)

CORPS    = ["PALAWAN", "GLOBAL", "FT_HO", "SANLA", "MC", "OSF"]
BRANCHES = [f"BR{i:04d}" for i in range(1, 600)]
USERS    = [f"user_{i}" for i in range(1, 50)]

# Shared token — fetched ONCE before the test starts, reused by all users.
_shared_token = None
_token_lock   = threading.Lock()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Fetch a single JWT before any users start — avoids 500 simultaneous token requests."""
    global _shared_token
    host = environment.host.rstrip("/")
    print(f"\n[setup] Fetching token from {host}/api/token ...")
    try:
        resp = _requests.post(
            f"{host}/api/token",
            json={"api_key": API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            _shared_token = resp.json().get("token")
            print(f"[setup] Token OK — test starting\n")
        else:
            print(f"[setup] ERROR: token endpoint returned {resp.status_code}: {resp.text[:200]}")
            environment.runner.quit()
    except Exception as e:
        print(f"[setup] ERROR: could not reach server — {e}")
        environment.runner.quit()


# ── Helpers ────────────────────────────────────────────────────────────────────
def _rand_date(days_back: int = 30) -> str:
    base  = datetime.date(2026, 4, 24)
    delta = datetime.timedelta(days=random.randint(0, days_back))
    return str(base - delta)


def _amt() -> float:
    return round(random.uniform(100, 99_999), 2)


def _lotes() -> int:
    return random.randint(0, 50)


def _build_daily_report_params(branch: str, corp: str, user: str, date: str):
    """Return (beginning, debit_total, credit_total, ending, cash_count, cash_result, variance_status)."""
    beginning     = _amt()
    deb_sum       = _amt()
    cre_sum       = round(random.uniform(0, deb_sum), 2)
    debit_total   = round(beginning + deb_sum, 2)
    credit_total  = cre_sum
    ending        = round(debit_total - credit_total, 2)
    cash_count    = round(ending + random.uniform(-500, 500), 2)
    cash_result   = round(cash_count - ending, 2)
    variance      = (
        "balanced" if abs(cash_result) < 0.01
        else "over" if cash_result > 0
        else "short"
    )
    return beginning, debit_total, credit_total, ending, cash_count, cash_result, variance


# ── Locust User ────────────────────────────────────────────────────────────────
class BranchUser(HttpUser):
    """
    Simulates a single branch operator:
      - Authenticates once on start
      - Continuously performs the realistic mix of reads and writes
    """

    # Realistic think-time: operators pause 1–5s between actions
    wait_time = between(1, 5)

    def on_start(self):
        """Called once per simulated user. Pick an identity and grab the shared token."""
        if not _shared_token:
            raise StopUser()
        self.branch  = random.choice(BRANCHES)
        self.corp    = random.choice(CORPS)
        self.user    = random.choice(USERS)
        self.token   = _shared_token
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # ── Utility: execute a SQL statement via /api/exec ──────────────────────
    def _exec(self, sql: str, params: list, name: str):
        for attempt in range(2):
            try:
                return self.client.post(
                    "/api/exec",
                    json={"sql": sql, "params": params},
                    headers=self.headers,
                    name=name,
                )
            except Exception:
                if attempt == 1:
                    raise
                time.sleep(0.5)

    def _exec_safe(self, sql: str, params: list, name: str):
        for attempt in range(2):
            try:
                return self.client.post(
                    "/api/exec_safe",
                    json={"sql": sql, "params": params},
                    headers=self.headers,
                    name=name,
                )
            except Exception:
                if attempt == 1:
                    raise
                time.sleep(0.5)

    # ══════════════════════════════════════════════════════════════════════════
    # TASKS — weights mirror a real branch operator's daily workflow
    # ══════════════════════════════════════════════════════════════════════════

    @task(5)
    def health_check(self):
        """Periodic keep-alive / connectivity check (no auth)."""
        self.client.get("/api/health", name="/api/health")

    @task(20)
    def load_previous_balance(self):
        """
        Most-frequent read: client fetches previous-day ending balance
        before the operator can enter today's opening balance.
        """
        date = _rand_date(10)
        for brand_table in ("daily_reports_brand_a", "daily_reports"):
            self._exec(
                f"SELECT ending_balance FROM {brand_table} "
                f"WHERE date=%s AND branch=%s AND corporation=%s "
                f"ORDER BY id DESC LIMIT 1",
                [date, self.branch, self.corp],
                name=f"SELECT {brand_table} [prev_balance]",
            )

    @task(15)
    def check_existing_entry(self):
        """
        Client checks whether today's entry already exists (locked/unlocked)
        before showing the form to the operator.
        """
        date = _rand_date(5)
        for brand_table in ("daily_reports_brand_a", "daily_reports"):
            self._exec(
                f"SELECT is_locked FROM {brand_table} "
                f"WHERE date=%s AND branch=%s AND corporation=%s LIMIT 1",
                [date, self.branch, self.corp],
                name=f"SELECT {brand_table} [check_locked]",
            )

    @task(10)
    def submit_daily_report_brand_b(self):
        """INSERT/UPDATE daily_reports (Brand B) — the primary cash-flow record."""
        date = _rand_date(3)
        bb, dt, ct, ending, cc, cr, vs = _build_daily_report_params(
            self.branch, self.corp, self.user, date
        )
        self._exec(
            "INSERT INTO daily_reports "
            "(date, username, branch, corporation, beginning_balance, debit_total, "
            " credit_total, ending_balance, cash_count, cash_result, variance_status, is_locked) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "  beginning_balance=VALUES(beginning_balance), debit_total=VALUES(debit_total), "
            "  credit_total=VALUES(credit_total), ending_balance=VALUES(ending_balance), "
            "  cash_count=VALUES(cash_count), cash_result=VALUES(cash_result), "
            "  variance_status=VALUES(variance_status)",
            [date, self.user, self.branch, self.corp,
             bb, dt, ct, ending, cc, cr, vs, 0],
            name="INSERT daily_reports",
        )

    @task(10)
    def submit_daily_report_brand_a(self):
        """INSERT/UPDATE daily_reports_brand_a — pawnshop brand."""
        date = _rand_date(3)
        bb, dt, ct, ending, cc, cr, vs = _build_daily_report_params(
            self.branch, self.corp, self.user, date
        )
        self._exec(
            "INSERT INTO daily_reports_brand_a "
            "(date, username, branch, corporation, beginning_balance, debit_total, "
            " credit_total, ending_balance, cash_count, cash_result, variance_status, is_locked) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "  beginning_balance=VALUES(beginning_balance), debit_total=VALUES(debit_total), "
            "  credit_total=VALUES(credit_total), ending_balance=VALUES(ending_balance), "
            "  cash_count=VALUES(cash_count), cash_result=VALUES(cash_result), "
            "  variance_status=VALUES(variance_status)",
            [date, self.user, self.branch, self.corp,
             bb, dt, ct, ending, cc, cr, vs, 0],
            name="INSERT daily_reports_brand_a",
        )

    @task(8)
    def submit_payable_brand_b(self):
        """INSERT/UPDATE payable_tbl — Palawan Express send/payout totals (Brand B)."""
        date    = _rand_date(3)
        capital = _amt()
        sc      = round(random.uniform(10, 500), 2)
        comm    = round(sc * 0.05, 2)
        total   = round(capital + sc + comm, 2)
        self._exec_safe(
            "INSERT INTO payable_tbl "
            "(corporation, branch, date, "
            " sendout_capital, sendout_sc, sendout_commission, sendout_total, "
            " payout_capital, payout_sc, payout_commission, payout_total, "
            " skid, skir, cancellation, inc) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "  sendout_capital=VALUES(sendout_capital), sendout_total=VALUES(sendout_total), "
            "  payout_capital=VALUES(payout_capital), payout_total=VALUES(payout_total), "
            "  updated_at=CURRENT_TIMESTAMP",
            [self.corp, self.branch, date,
             capital, sc, comm, total,
             _amt(), sc, comm, total,
             round(random.uniform(0, 500), 2), round(random.uniform(0, 500), 2),
             round(random.uniform(0, 200), 2), round(random.uniform(0, 1000), 2)],
            name="INSERT payable_tbl",
        )

    @task(8)
    def submit_payable_brand_a(self):
        """INSERT/UPDATE payable_tbl_brand_a — Palawan Express (Brand A)."""
        date    = _rand_date(3)
        capital = _amt()
        sc      = round(random.uniform(10, 500), 2)
        comm    = round(sc * 0.05, 2)
        total   = round(capital + sc + comm, 2)
        self._exec_safe(
            "INSERT INTO payable_tbl_brand_a "
            "(corporation, branch, date, "
            " sendout_capital, sendout_sc, sendout_commission, sendout_total, "
            " payout_capital, payout_sc, payout_commission, payout_total, "
            " skid, skir, cancellation, inc) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "  sendout_capital=VALUES(sendout_capital), sendout_total=VALUES(sendout_total), "
            "  payout_capital=VALUES(payout_capital), payout_total=VALUES(payout_total), "
            "  updated_at=CURRENT_TIMESTAMP",
            [self.corp, self.branch, date,
             capital, sc, comm, total,
             _amt(), sc, comm, total,
             round(random.uniform(0, 500), 2), round(random.uniform(0, 500), 2),
             round(random.uniform(0, 200), 2), round(random.uniform(0, 1000), 2)],
            name="INSERT payable_tbl_brand_a",
        )

    @task(6)
    def submit_global_other_services(self):
        """INSERT/UPDATE global_other_services_tbl — e-wallet & remittance capital."""
        date = _rand_date(3)
        self._exec(
            "INSERT INTO global_other_services_tbl "
            "(date, branch, corporation, username, "
            " gcash_out, gcash_out_lotes, moneygram, moneygram_lotes, "
            " transfast, transfast_lotes, ria, ria_lotes, "
            " remitly, remitly_lotes, mc_out, mc_out_lotes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "  gcash_out=VALUES(gcash_out), moneygram=VALUES(moneygram), "
            "  transfast=VALUES(transfast), ria=VALUES(ria), "
            "  remitly=VALUES(remitly), mc_out=VALUES(mc_out)",
            [date, self.branch, self.corp, self.user,
             _amt(), _lotes(), _amt(), _lotes(),
             _amt(), _lotes(), _amt(), _lotes(),
             _amt(), _lotes(), _amt(), _lotes()],
            name="INSERT global_other_services_tbl",
        )

    @task(6)
    def submit_other_services_brand_a(self):
        """INSERT/UPDATE other_services_tbl_brand_a — Palawan + e-wallet services."""
        date = _rand_date(3)
        self._exec(
            "INSERT INTO other_services_tbl_brand_a "
            "(date, branch, corporation, username, "
            " palawan_send_out, palawan_send_out_lotes, palawan_sc, palawan_sc_lotes, "
            " gcash_in, gcash_in_lotes, gcash_out, gcash_out_lotes, "
            " remitly, remitly_lotes, moneygram, moneygram_lotes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE "
            "  palawan_send_out=VALUES(palawan_send_out), palawan_sc=VALUES(palawan_sc), "
            "  gcash_in=VALUES(gcash_in), gcash_out=VALUES(gcash_out), "
            "  remitly=VALUES(remitly), moneygram=VALUES(moneygram)",
            [date, self.branch, self.corp, self.user,
             _amt(), _lotes(), _amt(), _lotes(),
             _amt(), _lotes(), _amt(), _lotes(),
             _amt(), _lotes(), _amt(), _lotes()],
            name="INSERT other_services_tbl_brand_a",
        )

    @task(10)
    def read_report_history(self):
        """
        Operator reviews the last 10 days of their own branch data.
        These SELECTs should hit Redis cache after the first branch request.
        """
        for brand_table in ("daily_reports", "daily_reports_brand_a"):
            self._exec(
                f"SELECT id, date, beginning_balance, debit_total, credit_total, "
                f"ending_balance, cash_result, variance_status "
                f"FROM {brand_table} "
                f"WHERE branch=%s AND corporation=%s "
                f"ORDER BY date DESC LIMIT 10",
                [self.branch, self.corp],
                name=f"SELECT {brand_table} [history]",
            )

    @task(2)
    def admin_summary_aggregation(self):
        """
        Admin-level aggregation query — heavier SELECT, low frequency.
        Simulates the review page loading branch totals for a date range.
        """
        end_date   = datetime.date(2026, 4, 24)
        start_date = end_date - datetime.timedelta(days=7)
        for brand_table in ("daily_reports", "daily_reports_brand_a"):
            self._exec(
                f"SELECT branch, corporation, "
                f"  SUM(debit_total) AS total_debit, "
                f"  SUM(credit_total) AS total_credit, "
                f"  SUM(cash_result) AS total_variance, "
                f"  COUNT(*) AS report_count "
                f"FROM {brand_table} "
                f"WHERE date BETWEEN %s AND %s "
                f"  AND corporation=%s "
                f"GROUP BY branch, corporation "
                f"ORDER BY branch",
                [str(start_date), str(end_date), self.corp],
                name=f"SELECT {brand_table} [admin_summary]",
            )
