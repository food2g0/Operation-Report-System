from db_connect import db_manager

# cols = [
#     # Debit
#     'rescate_jewelry','interest','penalty','stamp','resguardo_affidavit','habol_renew_tubos',
#     'habol_rt_interest_stamp','jew_ai','sc','fund_transfer_from_branch','sendah_load_sc',
#     'ppay_co_sc','palawan_send_out','palawan_sc','palawan_suki_card','palawan_pay_cash_in_sc',
#     'palawan_pay_bills_sc','palawan_load','palawan_change_receiver','mc_in','handling_fee',
#     'other_penalty','cash_shortage_overage',
#     # Credit
#     'empeno_jew_new','empeno_jew_renew','fund_transfer_to_head_office','fund_transfer_to_branch',
#     'palawan_pay_out','palawan_pay_out_incentives','palawan_pay_cash_out','mc_out','pc_salary',
#     'pc_rental','pc_electric','pc_water','pc_internet','pc_lbc_jrs_jnt','pc_permits_bir_payments',
#     'pc_supplies_xerox_maintenance','pc_transpo','palawan_cancel','palawan_suki_discounts','palawan_suki_rebates','others'
# ]

# added = []
# for c in cols:
#     lotes = c + '_lotes'
#     q = "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='daily_reports' AND COLUMN_NAME = %s"
#     res = db_manager.execute_query(q, (lotes,))
#     if not res:
#         try:
#             alter = f"ALTER TABLE daily_reports ADD COLUMN `{lotes}` INT DEFAULT 0"
#             print('Adding column', lotes)
#             r = db_manager.execute_query(alter)
#             print('Result:', r)
#             added.append(lotes)
#         except Exception as e:
#             print('Failed to add', lotes, e)
#     else:
#         print('Exists:', lotes)

# print('\nAdded columns:')
# for a in added:
#     print(a)
from db_connect import db_manager

cols = [
    # ===== Brand A main fields =====
    'rescate_jewelry',
    'interest',
    'rescuardo_affidavit',
    'penalty',
    'stamp',
    'resguardo_affidavit',
    'habol_renew_tubos',
    'habol_rt_interest_stamp',
    'cr_storage',
    'cr_storage_int_penalty',
    'rescate_silver',
    'silver_interest',
    'res_storage',
    'res_storage_int_penalty',
    'res_motor',
    'penalty_motor',
    'jew_ai',
    'service_charge',
    'osf_storage',
    'storage_ai',
    'silver_ai',
    'osf_silver',
    'motor_ai',
    'osf_motor',
    'miscellaneous_fee',
    'insurance_20',
    'insurance_philam_30',
    'insurance_philam_60',
    'insurance_philam_90',
    'fund_transfer_from_branch',
    'ayanah_sc',
    'sendah_load_sc',
    'smart_money_sc',
    'gcash_in',
    'gcash_out_sc',
    'abra_so_sc',
    'bdo_sc',
    'palawan_pay_cash_out_sc',
    'ria_in_sc',
    'paymaya_in',
    'i2i_remittance_in',
    'i2i_bills_payment',
    'i2i_bank_transfer',
    'i2i_pesonet',
    'i2i_instapay',
    'sendah_bills_sc',
    'palawan_send_out',
    'palawan_sc',
    'palawan_suki_card',
    'palawan_pay_cash_in_sc',
    'palawan_load_sc',
    'palawan_pay_bills_sc',
    'palawan_change_receiver',
    'mc_in',
    'handling_fee',
    'other_penalty',
    'cash_overage',

    # ===== Other fields =====
    'empeno_jew_new',
    'empeno_jew_renew',
    'empeno_sto_new',
    'fund_empeno_sto_renew',
    'empeno_motor_car',
    'empeno_silver',
    'gcash_out',
    'gcash_padala_sendah',
    'abra_po',
    'bdo_po',
    'i2i_remittance_out',
    'remitly',
    'smart_money_po',
    'fund_transfer_to_head_office',
    'fund_transfer_to_branch',
    'ayanah_out',
    'palawan_pay_out',
    'palawan_pay_out_incentives',
    'palawan_pay_cash_out',
    'mc_out',
    'pc_inc_emp',
    'pc_inc_motor',
    'pc_inc_suki_card',
    'pc_inc_insurance',
    'pc_inc_mc',
    'pc_salary',
    'pc_rental',
    'pc_electric',
    'pc_water',
    'pc_internet',
    'pc_lbc_jrs_jnt',
    'pc_permits_bir_payments',
    'pc_supplies_xerox_maintenance',
    'pc_transpo',
    'transfast',
    'paymaya_out',
    'ria_out',
    'fixco',
    'moneygram',
    'palawan_cancel',
    'palawan_suki_discounts',
    'palawan_suki_rebates',
    'storage_rebates',
    'silver_rebates',
    'others',
]

added = []
for c in cols:
    lotes = c + '_lotes'
    q = """
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'daily_reports_brand_a'
          AND COLUMN_NAME = %s
    """
    res = db_manager.execute_query(q, (lotes,))
    if not res:
        try:
            alter = f"ALTER TABLE daily_reports_brand_a ADD COLUMN `{lotes}` INT DEFAULT 0"
            print('Adding column', lotes)
            r = db_manager.execute_query(alter)
            print('Result:', r)
            added.append(lotes)
        except Exception as e:
            print('Failed to add', lotes, e)
    else:
        print('Exists:', lotes)

print('\nAdded columns:')
for a in added:
    print(a)
