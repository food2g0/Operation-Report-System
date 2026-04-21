"""
create_service_tables.py
────────────────────────
Creates the three supplementary Brand-A report tables:

  daily_transaction_tbl_brand_a   – pawnshop operations (empeno/rescate fields)
  other_services_tbl_brand_a      – remittance / e-wallet / Palawan services
  PL_tbl_brand_a                  – income & expense (P&L) fields

All three also receive every insert that goes into daily_reports_brand_a.
Run once: python create_service_tables.py
"""

from db_connect_pooled import db_manager

TABLES = {

    # ── 1. Pawnshop / daily-transaction data ─────────────────────────────
    "daily_transaction_tbl_brand_a": """
        CREATE TABLE IF NOT EXISTS daily_transaction_tbl_brand_a (
            id                          INT AUTO_INCREMENT PRIMARY KEY,
            date                        DATE NOT NULL,
            branch                      VARCHAR(120),
            corporation                 VARCHAR(120),
            username                    VARCHAR(120),

            -- JEWELRY
            empeno_jew_new              DECIMAL(15,2) DEFAULT 0,
            empeno_jew_new_lotes        SMALLINT      DEFAULT 0,
            empeno_jew_renew            DECIMAL(15,2) DEFAULT 0,
            empeno_jew_renew_lotes      SMALLINT      DEFAULT 0,

            -- STORAGE
            empeno_sto_new              DECIMAL(15,2) DEFAULT 0,
            empeno_sto_new_lotes        SMALLINT      DEFAULT 0,
            fund_empeno_sto_renew       DECIMAL(15,2) DEFAULT 0,
            fund_empeno_sto_renew_lotes SMALLINT      DEFAULT 0,

            -- MOTOR / CAR
            empeno_motor_car            DECIMAL(15,2) DEFAULT 0,
            empeno_motor_car_lotes      SMALLINT      DEFAULT 0,

            -- MC
            mc_out                      DECIMAL(15,2) DEFAULT 0,
            mc_out_lotes                SMALLINT      DEFAULT 0,

            -- SILVER
            empeno_silver               DECIMAL(15,2) DEFAULT 0,
            empeno_silver_lotes         SMALLINT      DEFAULT 0,

            -- RESCATE JEWELRY
            rescate_jewelry             DECIMAL(15,2) DEFAULT 0,
            rescate_jewelry_lotes       SMALLINT      DEFAULT 0,

            -- RESCATE STORAGE
            cr_storage                  DECIMAL(15,2) DEFAULT 0,
            cr_storage_lotes            SMALLINT      DEFAULT 0,
            rescate_silver              DECIMAL(15,2) DEFAULT 0,
            rescate_silver_lotes        SMALLINT      DEFAULT 0,
            res_storage                 DECIMAL(15,2) DEFAULT 0,
            res_storage_lotes           SMALLINT      DEFAULT 0,
            res_motor                   DECIMAL(15,2) DEFAULT 0,
            res_motor_lotes             SMALLINT      DEFAULT 0,

            -- OSF
            osf_storage                 DECIMAL(15,2) DEFAULT 0,
            osf_storage_lotes           SMALLINT      DEFAULT 0,
            osf_silver                  DECIMAL(15,2) DEFAULT 0,
            osf_silver_lotes            SMALLINT      DEFAULT 0,
            osf_motor                   DECIMAL(15,2) DEFAULT 0,
            osf_motor_lotes             SMALLINT      DEFAULT 0,

            -- INSURANCE
            insurance_20                DECIMAL(15,2) DEFAULT 0,
            insurance_philam_60         DECIMAL(15,2) DEFAULT 0,
            insurance_philam_90         DECIMAL(15,2) DEFAULT 0,

            created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_dt_brand_a (date, branch, corporation)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── 2. Other / e-wallet / remittance services ─────────────────────────
    "other_services_tbl_brand_a": """
        CREATE TABLE IF NOT EXISTS other_services_tbl_brand_a (
            id                              INT AUTO_INCREMENT PRIMARY KEY,
            date                            DATE NOT NULL,
            branch                          VARCHAR(120),
            corporation                     VARCHAR(120),
            username                        VARCHAR(120),

            palawan_send_out                DECIMAL(15,2) DEFAULT 0,
            palawan_send_out_lotes          SMALLINT      DEFAULT 0,
            palawan_sc                      DECIMAL(15,2) DEFAULT 0,
            palawan_sc_lotes                SMALLINT      DEFAULT 0,
            palawan_pay_out                 DECIMAL(15,2) DEFAULT 0,
            palawan_pay_out_lotes           SMALLINT      DEFAULT 0,
            palawan_pay_out_incentives      DECIMAL(15,2) DEFAULT 0,
            palawan_pay_out_incentives_lotes SMALLINT     DEFAULT 0,
            palawan_pay_cash_in_sc          DECIMAL(15,2) DEFAULT 0,
            palawan_pay_cash_in_sc_lotes    SMALLINT      DEFAULT 0,
            palawan_pay_bills_sc            DECIMAL(15,2) DEFAULT 0,
            palawan_load_sc                 DECIMAL(15,2) DEFAULT 0,
            palawan_pay_cash_out            DECIMAL(15,2) DEFAULT 0,
            palawan_pay_cash_out_lotes      SMALLINT      DEFAULT 0,
            palawan_suki_card               DECIMAL(15,2) DEFAULT 0,
            palawan_pay_cash_out_sc         DECIMAL(15,2) DEFAULT 0,

            sendah_load_sc                  DECIMAL(15,2) DEFAULT 0,
            sendah_load_sc_lotes            SMALLINT      DEFAULT 0,
            sendah_bills_sc                 DECIMAL(15,2) DEFAULT 0,
            sendah_bills_sc_lotes           SMALLINT      DEFAULT 0,

            smart_money_sc                  DECIMAL(15,2) DEFAULT 0,
            smart_money_sc_lotes            SMALLINT      DEFAULT 0,
            smart_money_po                  DECIMAL(15,2) DEFAULT 0,
            smart_money_po_lotes            SMALLINT      DEFAULT 0,

            gcash_in                        DECIMAL(15,2) DEFAULT 0,
            gcash_in_lotes                  SMALLINT      DEFAULT 0,
            gcash_out                       DECIMAL(15,2) DEFAULT 0,
            gcash_out_lotes                 SMALLINT      DEFAULT 0,
            gcash_padala_sendah             DECIMAL(15,2) DEFAULT 0,
            gcash_padala_sendah_lotes       SMALLINT      DEFAULT 0,

            abra_so_sc                      DECIMAL(15,2) DEFAULT 0,
            abra_po                         DECIMAL(15,2) DEFAULT 0,
            bdo_sc                          DECIMAL(15,2) DEFAULT 0,
            bdo_po                          DECIMAL(15,2) DEFAULT 0,
            ayanah_sc                       DECIMAL(15,2) DEFAULT 0,
            ayanah_out                      DECIMAL(15,2) DEFAULT 0,

            remitly                         DECIMAL(15,2) DEFAULT 0,
            remitly_lotes                   SMALLINT      DEFAULT 0,
            paymaya_in                      DECIMAL(15,2) DEFAULT 0,
            paymaya_in_lotes                SMALLINT      DEFAULT 0,
            paymaya_out                     DECIMAL(15,2) DEFAULT 0,
            ria_in_sc                       DECIMAL(15,2) DEFAULT 0,
            ria_in_sc_lotes                 SMALLINT      DEFAULT 0,
            ria_out                         DECIMAL(15,2) DEFAULT 0,
            transfast                       DECIMAL(15,2) DEFAULT 0,
            transfast_lotes                 SMALLINT      DEFAULT 0,
            moneygram                       DECIMAL(15,2) DEFAULT 0,
            moneygram_lotes                 SMALLINT      DEFAULT 0,

            i2i_remittance_in               DECIMAL(15,2) DEFAULT 0,
            i2i_remittance_in_lotes         SMALLINT      DEFAULT 0,
            i2i_remittance_out              DECIMAL(15,2) DEFAULT 0,
            i2i_bills_payment               DECIMAL(15,2) DEFAULT 0,
            i2i_bills_payment_lotes         SMALLINT      DEFAULT 0,
            i2i_bank_transfer               DECIMAL(15,2) DEFAULT 0,
            i2i_pesonet                     DECIMAL(15,2) DEFAULT 0,
            i2i_instapay                    DECIMAL(15,2) DEFAULT 0,
            i2i_instapay_lotes              SMALLINT      DEFAULT 0,

            fixco                           DECIMAL(15,2) DEFAULT 0,

            created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_os_brand_a (date, branch, corporation)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── 3. P&L (income / expense) ─────────────────────────────────────────
    "PL_tbl_brand_a": """
        CREATE TABLE IF NOT EXISTS PL_tbl_brand_a (
            id                              INT AUTO_INCREMENT PRIMARY KEY,
            date                            DATE NOT NULL,
            branch                          VARCHAR(120),
            corporation                     VARCHAR(120),
            username                        VARCHAR(120),

            -- Income / charges
            interest                        DECIMAL(15,2) DEFAULT 0,
            penalty                         DECIMAL(15,2) DEFAULT 0,
            stamp                           DECIMAL(15,2) DEFAULT 0,
            rescuardo_affidavit             DECIMAL(15,2) DEFAULT 0,
            jew_ai                          DECIMAL(15,2) DEFAULT 0,
            service_charge                  DECIMAL(15,2) DEFAULT 0,
            habol_renew_tubos               DECIMAL(15,2) DEFAULT 0,
            habol_rt_interest_stamp         DECIMAL(15,2) DEFAULT 0,
            storage_ai                      DECIMAL(15,2) DEFAULT 0,
            osf_storage                     DECIMAL(15,2) DEFAULT 0,
            cr_storage_int_penalty          DECIMAL(15,2) DEFAULT 0,
            silver_ai                       DECIMAL(15,2) DEFAULT 0,
            osf_silver                      DECIMAL(15,2) DEFAULT 0,
            res_storage_int_penalty         DECIMAL(15,2) DEFAULT 0,
            motor_ai                        DECIMAL(15,2) DEFAULT 0,
            osf_motor                       DECIMAL(15,2) DEFAULT 0,
            penalty_motor                   DECIMAL(15,2) DEFAULT 0,
            miscellaneous_fee               DECIMAL(15,2) DEFAULT 0,

            -- Rebates / discounts
            palawan_suki_discounts          DECIMAL(15,2) DEFAULT 0,
            palawan_suki_rebates            DECIMAL(15,2) DEFAULT 0,
            storage_rebates                 DECIMAL(15,2) DEFAULT 0,
            silver_rebates                  DECIMAL(15,2) DEFAULT 0,
            palawan_suki_card               DECIMAL(15,2) DEFAULT 0,

            -- PC / Expenses
            pc_transpo                      DECIMAL(15,2) DEFAULT 0,
            pc_salary                       DECIMAL(15,2) DEFAULT 0,
            pc_inc_motor                    DECIMAL(15,2) DEFAULT 0,
            pc_inc_emp                      DECIMAL(15,2) DEFAULT 0,
            pc_inc_suki_card                DECIMAL(15,2) DEFAULT 0,
            pc_inc_insurance                DECIMAL(15,2) DEFAULT 0,
            pc_inc_mc                       DECIMAL(15,2) DEFAULT 0,
            pc_supplies_xerox_maintenance   DECIMAL(15,2) DEFAULT 0,
            pc_electric                     DECIMAL(15,2) DEFAULT 0,
            pc_water                        DECIMAL(15,2) DEFAULT 0,
            pc_internet                     DECIMAL(15,2) DEFAULT 0,
            pc_rental                       DECIMAL(15,2) DEFAULT 0,
            pc_permits_bir_payments         DECIMAL(15,2) DEFAULT 0,
            pc_lbc_jrs_jnt                  DECIMAL(15,2) DEFAULT 0,

            created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_pl_brand_a (date, branch, corporation)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
}


def create_tables():
    print("Creating supplementary Brand-A report tables…\n")
    for table_name, ddl in TABLES.items():
        try:
            db_manager.execute_query(ddl.strip())
            print(f"  ✅  {table_name}")
        except Exception as e:
            print(f"  ❌  {table_name}: {e}")
    print("\nDone.")


if __name__ == "__main__":
    create_tables()
