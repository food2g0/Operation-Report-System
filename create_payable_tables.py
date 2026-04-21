
from db_connect_pooled import db_manager


def create_payable_tables():
    """Create payable tables for both brands if they don't exist."""
    
    # Brand A payable table
    brand_a_table = """
        CREATE TABLE IF NOT EXISTS payable_tbl_brand_a (
            id INT AUTO_INCREMENT PRIMARY KEY,
            corporation VARCHAR(255) NOT NULL,
            branch VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            sendout_capital DECIMAL(15,2) DEFAULT 0,
            sendout_sc DECIMAL(15,2) DEFAULT 0,
            sendout_commission DECIMAL(15,2) DEFAULT 0,
            sendout_total DECIMAL(15,2) DEFAULT 0,
            payout_capital DECIMAL(15,2) DEFAULT 0,
            payout_sc DECIMAL(15,2) DEFAULT 0,
            payout_commission DECIMAL(15,2) DEFAULT 0,
            payout_total DECIMAL(15,2) DEFAULT 0,
            international_capital DECIMAL(15,2) DEFAULT 0,
            international_sc DECIMAL(15,2) DEFAULT 0,
            international_commission DECIMAL(15,2) DEFAULT 0,
            international_total DECIMAL(15,2) DEFAULT 0,
            skid DECIMAL(15,2) DEFAULT 0,
            skir DECIMAL(15,2) DEFAULT 0,
            cancellation DECIMAL(15,2) DEFAULT 0,
            inc DECIMAL(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_corp_branch_date_a (corporation, branch, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """
    
    # Brand B payable table (existing structure, ensure it exists)
    brand_b_table = """
        CREATE TABLE IF NOT EXISTS payable_tbl (
            id INT AUTO_INCREMENT PRIMARY KEY,
            corporation VARCHAR(255) NOT NULL,
            branch VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            sendout_capital DECIMAL(15,2) DEFAULT 0,
            sendout_sc DECIMAL(15,2) DEFAULT 0,
            sendout_commission DECIMAL(15,2) DEFAULT 0,
            sendout_total DECIMAL(15,2) DEFAULT 0,
            payout_capital DECIMAL(15,2) DEFAULT 0,
            payout_sc DECIMAL(15,2) DEFAULT 0,
            payout_commission DECIMAL(15,2) DEFAULT 0,
            payout_total DECIMAL(15,2) DEFAULT 0,
            international_capital DECIMAL(15,2) DEFAULT 0,
            international_sc DECIMAL(15,2) DEFAULT 0,
            international_commission DECIMAL(15,2) DEFAULT 0,
            international_total DECIMAL(15,2) DEFAULT 0,
            skid DECIMAL(15,2) DEFAULT 0,
            skir DECIMAL(15,2) DEFAULT 0,
            cancellation DECIMAL(15,2) DEFAULT 0,
            inc DECIMAL(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uq_corp_branch_date (corporation, branch, date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """
    
    try:

        db_manager.execute_query(brand_b_table)
        print("✅ payable_tbl (Brand B) created or already exists")
        

        db_manager.execute_query(brand_a_table)
        print("✅ payable_tbl_brand_a (Brand A) created or already exists")
        
        # Verify unique constraints exist
        for table, constraint in [
            ("payable_tbl", "uq_corp_branch_date"),
            ("payable_tbl_brand_a", "uq_corp_branch_date_a")
        ]:
            result = db_manager.execute_query("""
                SELECT COUNT(*) as cnt
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
                  AND CONSTRAINT_TYPE = 'UNIQUE'
                  AND CONSTRAINT_NAME = %s
            """, (table, constraint))
            exists = result[0]['cnt'] > 0 if result else False
            if exists:
                print(f"✅ {table}: unique constraint '{constraint}' exists")
            else:
                print(f"⚠️  {table}: unique constraint '{constraint}' not found")
        
        print("\n✅ All payable tables ready!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating payable tables: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    create_payable_tables()
