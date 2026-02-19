import argparse
import datetime
from db_connect_pooled import db_manager
from security import hash_password


def init_schema():
    """Create tables: corporations, branches, clients"""
    queries = [
        """
        CREATE TABLE IF NOT EXISTS corporations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
        """
        CREATE TABLE IF NOT EXISTS daily_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            username VARCHAR(64),
            branch VARCHAR(255),
            cash_result DECIMAL(15,2) DEFAULT 0.00,

            /* Debit fields */
            rescate_jewelry DECIMAL(15,2) DEFAULT 0.00,
            rescate_jewelry_lotes INT DEFAULT 0,
            interest DECIMAL(15,2) DEFAULT 0.00,
            interest_lotes INT DEFAULT 0,
            penalty DECIMAL(15,2) DEFAULT 0.00,
            penalty_lotes INT DEFAULT 0,
            stamp DECIMAL(15,2) DEFAULT 0.00,
            stamp_lotes INT DEFAULT 0,
            resguardo_affidavit DECIMAL(15,2) DEFAULT 0.00,
            resguardo_affidavit_lotes INT DEFAULT 0,
            habol_renew_tubos DECIMAL(15,2) DEFAULT 0.00,
            habol_renew_tubos_lotes INT DEFAULT 0,
            habol_rt_interest_stamp DECIMAL(15,2) DEFAULT 0.00,
            habol_rt_interest_stamp_lotes INT DEFAULT 0,
            jew_ai DECIMAL(15,2) DEFAULT 0.00,
            jew_ai_lotes INT DEFAULT 0,
            sc DECIMAL(15,2) DEFAULT 0.00,
            sc_lotes INT DEFAULT 0,
            fund_transfer_from_branch DECIMAL(15,2) DEFAULT 0.00,
            fund_transfer_from_branch_lotes INT DEFAULT 0,
            sendah_load_sc DECIMAL(15,2) DEFAULT 0.00,
            sendah_load_sc_lotes INT DEFAULT 0,
            ppay_co_sc DECIMAL(15,2) DEFAULT 0.00,
            ppay_co_sc_lotes INT DEFAULT 0,
            palawan_send_out DECIMAL(15,2) DEFAULT 0.00,
            palawan_send_out_lotes INT DEFAULT 0,
            palawan_sc DECIMAL(15,2) DEFAULT 0.00,
            palawan_sc_lotes INT DEFAULT 0,
            palawan_suki_card DECIMAL(15,2) DEFAULT 0.00,
            palawan_suki_card_lotes INT DEFAULT 0,
            palawan_pay_cash_in_sc DECIMAL(15,2) DEFAULT 0.00,
            palawan_pay_cash_in_sc_lotes INT DEFAULT 0,
            palawan_pay_bills_sc DECIMAL(15,2) DEFAULT 0.00,
            palawan_pay_bills_sc_lotes INT DEFAULT 0,
            palawan_load DECIMAL(15,2) DEFAULT 0.00,
            palawan_load_lotes INT DEFAULT 0,
            palawan_change_receiver DECIMAL(15,2) DEFAULT 0.00,
            palawan_change_receiver_lotes INT DEFAULT 0,
            mc_in DECIMAL(15,2) DEFAULT 0.00,
            mc_in_lotes INT DEFAULT 0,
            handling_fee DECIMAL(15,2) DEFAULT 0.00,
            handling_fee_lotes INT DEFAULT 0,
            other_penalty DECIMAL(15,2) DEFAULT 0.00,
            other_penalty_lotes INT DEFAULT 0,
            cash_shortage_overage DECIMAL(15,2) DEFAULT 0.00,
            cash_shortage_overage_lotes INT DEFAULT 0,

            /* Credit fields */
            empeno_jew_new DECIMAL(15,2) DEFAULT 0.00,
            empeno_jew_new_lotes INT DEFAULT 0,
            empeno_jew_renew DECIMAL(15,2) DEFAULT 0.00,
            empeno_jew_renew_lotes INT DEFAULT 0,
            fund_transfer_to_head_office DECIMAL(15,2) DEFAULT 0.00,
            fund_transfer_to_head_office_lotes INT DEFAULT 0,
            fund_transfer_to_branch DECIMAL(15,2) DEFAULT 0.00,
            fund_transfer_to_branch_lotes INT DEFAULT 0,
            palawan_pay_out DECIMAL(15,2) DEFAULT 0.00,
            palawan_pay_out_lotes INT DEFAULT 0,
            palawan_pay_out_incentives DECIMAL(15,2) DEFAULT 0.00,
            palawan_pay_out_incentives_lotes INT DEFAULT 0,
            palawan_pay_cash_out DECIMAL(15,2) DEFAULT 0.00,
            palawan_pay_cash_out_lotes INT DEFAULT 0,
            mc_out DECIMAL(15,2) DEFAULT 0.00,
            mc_out_lotes INT DEFAULT 0,
            pc_salary DECIMAL(15,2) DEFAULT 0.00,
            pc_salary_lotes INT DEFAULT 0,
            pc_rental DECIMAL(15,2) DEFAULT 0.00,
            pc_rental_lotes INT DEFAULT 0,
            pc_electric DECIMAL(15,2) DEFAULT 0.00,
            pc_electric_lotes INT DEFAULT 0,
            pc_water DECIMAL(15,2) DEFAULT 0.00,
            pc_water_lotes INT DEFAULT 0,
            pc_internet DECIMAL(15,2) DEFAULT 0.00,
            pc_internet_lotes INT DEFAULT 0,
            pc_lbc_jrs_jnt DECIMAL(15,2) DEFAULT 0.00,
            pc_lbc_jrs_jnt_lotes INT DEFAULT 0,
            pc_permits_bir_payments DECIMAL(15,2) DEFAULT 0.00,
            pc_permits_bir_payments_lotes INT DEFAULT 0,
            pc_supplies_xerox_maintenance DECIMAL(15,2) DEFAULT 0.00,
            pc_supplies_xerox_maintenance_lotes INT DEFAULT 0,
            pc_transpo DECIMAL(15,2) DEFAULT 0.00,
            pc_transpo_lotes INT DEFAULT 0,
            palawan_cancel DECIMAL(15,2) DEFAULT 0.00,
            palawan_cancel_lotes INT DEFAULT 0,
            palawan_suki_discounts DECIMAL(15,2) DEFAULT 0.00,
            palawan_suki_discounts_lotes INT DEFAULT 0,
            palawan_suki_rebates DECIMAL(15,2) DEFAULT 0.00,
            palawan_suki_rebates_lotes INT DEFAULT 0,
            others DECIMAL(15,2) DEFAULT 0.00,
            others_lotes INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,

        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) NOT NULL UNIQUE,
            password VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            corporation VARCHAR(255),
            branch VARCHAR(255),
            role VARCHAR(32) DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """,
    ]

    for q in queries:
        res = db_manager.execute_query(q)

    print("Schema initialized (corporations, branches, users)")


def create_corporation(name: str):
    q = "INSERT INTO corporations (name) VALUES (%s)"
    res = db_manager.execute_query(q, (name,))
    if res is None:
        print("Failed to create corporation")
        return None

    row = db_manager.execute_query("SELECT id FROM corporations WHERE name=%s", (name,))
    if row:
        print(f"Corporation created: {name} (id={row[0]['id']})")
        return row[0]['id']


def create_branch(name: str, corporation_id: int):
    q = "INSERT INTO branches (corporation_id, name) VALUES (%s, %s)"
    res = db_manager.execute_query(q, (corporation_id, name))
    if res is None:
        print("Failed to create branch")
        return None

    row = db_manager.execute_query("SELECT id FROM branches WHERE corporation_id=%s AND name=%s", (corporation_id, name))
    if row:
        print(f"Branch created: {name} (id={row[0]['id']})")
        return row[0]['id']


def _next_username():
    """Generate next username in format CL-0000, CL-0001, ..."""
    row = db_manager.execute_query("SELECT MAX(CAST(SUBSTRING(username,4) AS UNSIGNED)) AS maxnum FROM users WHERE username LIKE 'CL-%'")
    maxnum = 0
    if row and row[0] and row[0].get('maxnum') is not None:
        try:
            maxnum = int(row[0]['maxnum'])
        except Exception:
            maxnum = 0

    next_num = maxnum + 1
    username = f"CL-{str(next_num).zfill(4)}"
    return username


def create_client(first_name: str, last_name: str, corporation_id: int, branch_id: int, password: str = None):
    username = _next_username()
    
    # Hash password if provided
    hashed_password = hash_password(password) if password else None
    
    # Resolve corporation and branch names
    corp_name = None
    branch_name = None
    cres = db_manager.execute_query("SELECT name FROM corporations WHERE id=%s", (corporation_id,))
    if cres:
        corp_name = cres[0].get('name')
    bres = db_manager.execute_query("SELECT name FROM branches WHERE id=%s", (branch_id,))
    if bres:
        branch_name = bres[0].get('name')

    # Insert directly into users table with hashed password with hashed password
    q = "INSERT INTO users (username, password, first_name, last_name, corporation, branch, role) VALUES (%s, %s, %s, %s, %s, %s, 'user')"
    res = db_manager.execute_query(q, (username, hashed_password, first_name, last_name, corp_name, branch_name))
    if res is None:
        print("Failed to create client")
        return None

    row = db_manager.execute_query("SELECT id, username FROM users WHERE username=%s", (username,))
    if row:
        print(f"Client created: {first_name} {last_name} -> username {row[0]['username']} (id={row[0]['id']})")
        return row[0]
    
    return None


def list_clients():
    rows = db_manager.execute_query("SELECT id, username, first_name, last_name, corporation, branch, created_at FROM users WHERE role='user' ORDER BY id DESC LIMIT 100")
    if not rows:
        print("No clients found")
        return
    for r in rows:
        print(r)


def list_corporations():
    rows = db_manager.execute_query("SELECT id, name FROM corporations")
    if not rows:
        print("No corporations found")
        return
    for r in rows:
        print(r)


def list_branches():
    rows = db_manager.execute_query("SELECT id, name, corporation_id FROM branches")
    if not rows:
        print("No branches found")
        return
    for r in rows:
        print(r)


def main():
    parser = argparse.ArgumentParser(description="Admin management: corporations, branches, clients")
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('init', help='Initialize DB schema')

    p1 = sub.add_parser('addcorp', help='Add corporation')
    p1.add_argument('name')

    p2 = sub.add_parser('addbranch', help='Add branch')
    p2.add_argument('corp_id', type=int)
    p2.add_argument('name')

    p3 = sub.add_parser('addclient', help='Add client')
    p3.add_argument('first_name')
    p3.add_argument('last_name')
    p3.add_argument('corp_id', type=int)
    p3.add_argument('branch_id', type=int)
    p3.add_argument('--password', default=None)

    sub.add_parser('list_clients', help='List clients')
    sub.add_parser('list_corporations', help='List corporations')
    sub.add_parser('list_branches', help='List branches')

    args = parser.parse_args()
    if args.cmd == 'init':
        init_schema()
    elif args.cmd == 'addcorp':
        create_corporation(args.name)
    elif args.cmd == 'addbranch':
        create_branch(args.name, args.corp_id)
    elif args.cmd == 'addclient':
        create_client(args.first_name, args.last_name, args.corp_id, args.branch_id, args.password)
    elif args.cmd == 'list_clients':
        list_clients()
    elif args.cmd == 'list_corporations':
        list_corporations()
    elif args.cmd == 'list_branches':
        list_branches()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()