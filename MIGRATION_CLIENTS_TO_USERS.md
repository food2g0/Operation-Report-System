# Client Table Migration Guide

## Overview
This migration removes the `clients` table from the database and consolidates all client account management into the existing `users` table. This simplifies the database schema and eliminates duplicate user storage.

## Changes Made

### 1. Database Schema Changes
- **Updated `users` table**: Added `first_name` and `last_name` columns to store client details
- **Removed `clients` table**: Eliminated the separate clients table from schema initialization

### 2. Code Changes

#### admin_manage.py
- Modified `create_client()` function to insert directly into `users` table with role='user'
- Updated `_next_username()` to generate usernames by querying `users` table with filter for 'CL-' pattern
- Updated `list_clients()` to query from `users` table where role='user'
- Removed clients table creation from `init_schema()`
- Removed password hashing logic (no longer needed; plain passwords stored in users table)

#### login.py
- Removed fallback authentication logic that checked the `clients` table
- All authentication now uses only the `users` table
- Simplified login flow without complex hash/salt verification for clients

#### admin_dashboard.py
- Updated `_preview_username()` to query `users` table with 'CL-' filter
- Updated `_refresh_client_display()` to query `users` table where role='user'
- Changed JOIN logic from corporation/branch IDs to direct string fields

### 3. Migration Files Created

#### migrate_clients_to_users.py
Python script that:
1. Adds `first_name` and `last_name` columns to `users` table if they don't exist
2. Migrates all existing client data from `clients` table to `users` table
3. Drops the `clients` table

#### migrate_clients_to_users.sql
SQL script for manual migration if preferred over Python script.

## How to Migrate

### Option 1: Using Python Script (Recommended)

1. Make sure the database is accessible and `db_connect_pooled.py` is properly configured
2. Run the migration script:
   ```powershell
   python migrate_clients_to_users.py
   ```
3. Confirm when prompted
4. The script will display progress and completion status

### Option 2: Using SQL Script

1. Connect to your MySQL database
2. Run the SQL migration script:
   ```sql
   source migrate_clients_to_users.sql;
   ```
   Or use a MySQL client to execute the file.

## Important Notes

⚠️ **BACKUP YOUR DATABASE FIRST!**

Before running the migration, make sure to back up your database:
```bash
mysqldump -u your_username -p your_database > backup_$(date +%Y%m%d).sql
```

### Password Reset Required
- Existing clients in the `clients` table used hashed passwords with salt
- The `users` table uses plain text passwords
- After migration, all migrated clients will have NULL passwords
- **Administrators must reset passwords** for these users through the admin dashboard

### New Client Accounts
- All new client accounts created after the code update will be stored in the `users` table
- Passwords are stored in plain text (matching existing users table behavior)
- Client usernames follow the pattern: CL-0001, CL-0002, etc.

## Verification

After migration, verify that:

1. All clients appear in the admin dashboard "Clients" section
2. New clients can be created successfully
3. Clients can log in after password reset
4. No references to the `clients` table remain in error logs

## Rollback

If you need to rollback:

1. Restore from your database backup
2. Revert the code changes using git:
   ```bash
   git checkout HEAD~1 admin_manage.py login.py admin_dashboard.py
   ```

## Summary

This migration consolidates user management by:
- ✅ Eliminating duplicate user storage
- ✅ Simplifying authentication logic
- ✅ Using consistent password storage across all user types
- ✅ Maintaining all client information (name, corporation, branch)
- ✅ Preserving client username format (CL-XXXX)

For questions or issues, please check the error logs or consult the development team.
