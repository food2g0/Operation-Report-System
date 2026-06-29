"""
admin — all admin-side dashboards, pages, and management utilities.

Structure
─────────
admin/
├── dashboard.py       AdminDashboard  (was admin_dashboard.py)
├── super_dashboard.py SuperAdminDashboard (was super_admin_dashboard.py)
├── accounting.py      AccountingDashboard (was accounting_dashboard.py)
├── manage.py          admin utility functions (was admin_manage.py)
├── user_management.py UserManagementPage (was user_management_page.py)
├── machine_management.py MachinePage (was machine_management_page.py)
└── pages/             tab pages loaded inside AdminDashboard
    ├── palawan.py
    ├── mc.py
    ├── fund_transfer.py
    ├── payable.py
    ├── global_payable.py
    ├── report.py
    ├── variance_review.py
    ├── daily_transaction.py
    ├── new_sanla.py
    ├── new_renew.py
    ├── global_other_services.py
    ├── ft_ho.py
    ├── depo_br.py
    ├── review_summary.py
    └── bir_book.py

Root-level shims (admin_dashboard.py, super_admin_dashboard.py, etc.) are kept
for any callers that haven't been migrated yet.
"""
from admin.dashboard import AdminDashboard
from admin.super_dashboard import SuperAdminDashboard
from admin.accounting import AccountingDashboard

__all__ = ["AdminDashboard", "SuperAdminDashboard", "AccountingDashboard"]
