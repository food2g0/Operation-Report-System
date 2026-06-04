# Operation Report System - Data Flow & Issue Analysis

## Executive Summary

This analysis identifies the data flow issues causing:
1. **Old ending balance persisting after admin reset & edit post**
2. **Empeno JEW amounts remaining in fields after posting**

Both issues stem from incomplete field clearing and missing automatic data refresh triggers after successful posting.

---

## 1. EMPENO JEW FIELD PERSISTENCE - ROOT CAUSE

### Problem Statement
After posting a report with Empeno JEW NEW/RENEW amounts, these values remain in the UI when loading the next day's report, even though they should be cleared.

### Root Cause Chain

#### Step 1: Data is stored in cache during entry [Client/client_dashboard.py - L4287-L4500]
```
_setup_empeno_jew_buttons() creates:
  - self._jew_dialogs = {}          (caches dialog instances)
  - self._jew_computed = {
      "Empeno JEW. (NEW)": 0.0,     (stores computed total)
      "Empeno JEW (RENEW)": 0.0
    }
  - self._jew_computed_b = {}       (for Brand B)
```

When user opens the Empeno JEW dialog and enters amounts:
- Dialog values are stored in `self._jew_dialogs[field_label]`
- Computed total is written to `self._jew_computed[key]`
- The `Jew. A.I` field gets updated with: `jew_ai.setText(f"{total:.2f}")` [L4336]

#### Step 2: Fields are cleared on date change [Client/client_dashboard.py - L2540]
When user changes the date (or clicks "Move to next day" after posting):
```python
on_date_changed() [L2427]:
    for tab in (self.cash_flow_tab_a, self.cash_flow_tab_b, self.palawan_tab):
        if hasattr(tab, 'clear_fields'):
            tab.clear_fields()  # ← Clears widget text
```

#### Step 3: The bug - cache is NOT cleared [Client/cash_flow_tab.py - L902]
```python
def clear_fields(self):
    """In CashFlowTab"""
    for field in list(self.debit_inputs.values()) + \
                 list(self.debit_lotes_inputs.values()) + \
                 list(self.credit_inputs.values()) + \
                 list(self.credit_lotes_inputs.values()):
        field.clear()                           # ← Clears widget text
    
    self.mc_currency_details = {'MC In': [], 'MC Out': []}  # ← Resets MC cache
    
    # ✗ MISSING: Does NOT reset _jew_computed or _jew_dialogs!
```

#### Step 4: New data is loaded, showing cached values [Client/client_dashboard.py - L5230]
```python
_load_brand_report_data() [L5230]:
    # 1. Clear fields first
    if hasattr(cf_tab, 'clear_fields'):
        cf_tab.clear_fields()  # ← clears text but not _jew_computed
    
    # 2. Load data from database
    for label, widget in cf_tab.debit_inputs.items():
        value = data.get(db_col, 0)
        if value:
            widget.setText(f"{float(value):.2f}")
    
    # 3. For Empeno JEW fields, if database has stored the previous day's value:
    #    The widget shows the DB value, BUT _jew_computed still has old cached value
```

### Example Scenario
1. **Day 1**: User enters Empeno JEW NEW = 5000
   - `_jew_computed["Empeno JEW. (NEW)"] = 5000.0`
   - `_jew_dialogs["Empeno JEW. (NEW)"] = <dialog with entry data>`
   - `Jew. A.I` field displays "5000.00"

2. **User changes to Day 2**: 
   - `clear_fields()` clears the text widget "5000.00" ✓
   - BUT `_jew_computed["Empeno JEW. (NEW)"]` STILL = 5000.0 ✗
   - AND `_jew_dialogs["Empeno JEW. (NEW)"]` STILL has cached dialog ✗

3. **Data loads for Day 2**:
   - Database has 0 for Empeno JEW NEW (no entry for that day yet)
   - Widget text becomes "" or "0.00"
   - BUT the `_jew_computed` dict still has 5000.0 value in memory

4. **User re-opens Empeno JEW dialog**:
   - Dialog loads `existing_entries = self.mc_currency_details.get(field_type, [])` 
   - OR if clicking the + button, it re-populates with previous cached dialog state

### Files Involved
- **[Client/client_dashboard.py](Client/client_dashboard.py#L4287-L4500)** - `_setup_empeno_jew_buttons()` creates caches
- **[Client/cash_flow_tab.py](Client/cash_flow_tab.py#L902)** - `clear_fields()` doesn't reset `_jew_computed`
- **[Client/client_dashboard.py](Client/client_dashboard.py#L2540)** - `on_date_changed()` calls `clear_fields()`

---

## 2. ENDING BALANCE PERSISTENCE - ROOT CAUSE

### Problem Statement
After admin resets and user edits+posts a report, the old ending balance displays instead of the newly calculated one.

### Data Flow Analysis

#### Post Success Flow [Client/client_dashboard.py - L3330-L3380]
```python
def handle_post(self):
    # ... posting logic ...
    
    if successes:  # Entry posted successfully
        # L3344: Show success message
        self._msg_success(f"✓ Entry Saved\n\nDate: {sd}...")
        
        # L3347-3349: Prompt to move to next day
        if dialog's "Yes" button clicked:
            self.clear_all_fields()  # ← Clears fields
            self.date_picker.setDate(...)  # ← Triggers on_date_changed()
        
        # L3351-3356: If "No" button clicked:
        # NOTHING happens - fields stay populated!
```

#### On Date Changed [Client/client_dashboard.py - L2427-2540]
```python
def on_date_changed(self):
    sd = self.date_picker.date().toString("yyyy-MM-dd")
    
    # Clear inputs
    for bb in (self.beginning_balance_input_a, self.beginning_balance_input_b):
        bb.clear()
    
    # Clear all tabs
    for tab in (self.cash_flow_tab_a, self.cash_flow_tab_b, self.palawan_tab):
        if hasattr(tab, 'clear_fields'):
            tab.clear_fields()  # ✓ Clears field widgets
    
    # Load Palawan data
    self._restore_palawan_payable(sd)
    
    # Check status
    status_a = self.check_existing_entry(sd, "Brand A")
    status_b = self.check_existing_entry(sd, "Brand B")
    
    # If unlocked (admin reset):
    if status == "unlocked":
        self._load_brand_report_data(brand, sd)  # ← Loads from DB
```

#### Load Brand Data [Client/client_dashboard.py - L5230-L5310]
```python
def _load_brand_report_data(self, brand, date_str):
    # 1. Clear stale state first
    if hasattr(cf_tab, 'clear_fields'):
        cf_tab.clear_fields()  # ✓ Clears widgets
    
    # 2. Query database
    results = db_manager.execute_query(
        f"SELECT * FROM {table_name} WHERE date=%s AND branch=%s",
        (date_str, self.branch)
    )
    
    # 3. Populate from database row
    data = results[0]
    beginning_balance = data.get('beginning_balance', 0)
    
    # Populate debit fields
    for label, widget in cf_tab.debit_inputs.items():
        value = data.get(db_col, 0)
        if value:
            widget.setText(f"{float(value):.2f}")
    
    # Populate credit fields
    for label, widget in cf_tab.credit_inputs.items():
        value = data.get(db_col, 0)
        if value:
            widget.setText(f"{float(value):.2f}")
    
    # 4. Recalculate ending balance from current values
    self.recalculate_all()  # ← Should show NEW ending balance
```

#### Recalculate All [Client/client_dashboard.py - L2731-L2751]
```python
def recalculate_all(self):
    for brand in ("a", "b"):
        bb = getattr(self, f"beginning_balance_input_{brand}")
        cft = getattr(self, f"cash_flow_tab_{brand}")
        eb = getattr(self, f"ending_balance_display_{brand}")  # ← QLabel widget
        
        # Get current beginning balance from input
        beg = float(bb.text().strip().replace(",", "") or 0)
        
        # Get current debit/credit totals from field widgets
        deb = cft.get_debit_total()      # Sum of debit fields
        cred = cft.get_credit_total()    # Sum of credit fields
        
        # Recalculate ending balance
        end = beg + deb - cred           # ← Formula
        
        # Update display label with NEW value
        eb.setText(f"{end:,.2f}")        # ← Should show NEW calculated value!
```

### Why Old Balance Still Shows - Hypothesis

The ending balance display (`ending_balance_display_a` / `ending_balance_display_b`) is a **QLabel widget** that is updated when `recalculate_all()` runs.

**Possible causes for seeing old value:**
1. **`recalculate_all()` isn't called after load** - BUT code shows it IS called [L5308]
2. **UI isn't refreshed** - QLabel.setText() should trigger display update
3. **Beginning balance or debit/credit fields have cached/stale values** when recalculating
4. **The database query returns the OLD ending_balance value and something displays that directly** instead of the calculated value

### Critical Code Paths

The ending balance display should be **CALCULATED, not retrieved from database**:
```python
# ✓ CORRECT - recalculate_all() computes from current fields
eb.setText(f"{end:,.2f}")  # [L2745]

# ✗ If code instead did:
eb.setText(data.get('ending_balance', 0))  # This would show old DB value
```

### Code that might show DB ending_balance directly
Searching [Client/client_dashboard.py](Client/client_dashboard.py#L5230) - NO direct display of DB ending_balance found in `_load_brand_report_data()`. 

**Likely issue**: One of the field values being loaded is wrong, causing recalculate to get wrong result:
- Beginning balance loaded as old value instead of new
- Debit/credit fields loaded but with stale cached values
- The recalculation uses `cft.get_debit_total()` and `cft.get_credit_total()` which might not reflect newly loaded values if widgets weren't cleared first

### Files Involved
- **[Client/client_dashboard.py](Client/client_dashboard.py#L2427)** - `on_date_changed()` - triggers load
- **[Client/client_dashboard.py](Client/client_dashboard.py#L5230)** - `_load_brand_report_data()` - loads and recalculates
- **[Client/client_dashboard.py](Client/client_dashboard.py#L2731)** - `recalculate_all()` - computes ending balance
- **[Client/cash_flow_tab.py](Client/cash_flow_tab.py#L902)** - `clear_fields()` - clears but may not fully clear

---

## 3. DATA REFRESH MECHANISM - COMPLETE FLOW

### A. On Successful Post [Client/client_dashboard.py - L3315-L3380]
```
handle_post() success
    ↓
Show success message dialog
    ↓
Ask "Move to next day?"
    ├─ YES → clear_all_fields() + advance date
    │         ↓
    │         on_date_changed() triggered
    │         ↓
    │         _load_brand_report_data()
    │
    └─ NO → Stay on same date
            ↓
            User must manually clear or change date
```

**ISSUE**: No automatic clearing if user clicks "No"

### B. On Date Change [Client/client_dashboard.py - L2427-L2545]
```
on_date_changed() triggered
    ↓
Clear inputs: beginning_balance_input_a/b
Clear inputs: cash_count_input_a/b
    ↓
For each tab: clear_fields()
    ├─ Clears: debit_inputs, credit_inputs
    ├─ Clears: debit_lotes_inputs, credit_lotes_inputs
    ├─ Resets: mc_currency_details (sets to {})
    └─ ✗ NOT cleared: _jew_computed, _jew_dialogs caches
    ↓
_restore_palawan_payable(sd)
    ├─ Loads palawan data from database
    └─ Calls palawan_tab.load_data()
    ↓
check_existing_entry() for each brand
    ├─ If locked: disable inputs, show "Submitted"
    └─ If unlocked: _load_brand_report_data()
         ↓
         _load_brand_report_data() [L5230]
            ├─ clear_fields() called first ✓
            ├─ Query database
            ├─ Load values into widgets
            └─ recalculate_all()  ← Updates ending_balance display
```

### C. Load Brand Data Details [Client/client_dashboard.py - L5230-L5310]
```
_load_brand_report_data(brand, date_str)
    ↓
Query: SELECT * FROM table WHERE date=? AND branch=?
    ↓
For each field (debit/credit):
    ├─ Get value from database row
    ├─ Block signals
    ├─ widget.setText(value)
    ├─ Unblock signals
    └─ Also load lotes values
    ↓
Force recalculation: recalculate_all()
    ├─ Get beginning balance from input widget
    ├─ Sum debit fields
    ├─ Sum credit fields
    ├─ Calculate: ending = beginning + debit - credit
    └─ Update ending_balance_display label
```

### D. Clear Fields - CashFlowTab [Client/cash_flow_tab.py - L902]
```
clear_fields()
    ↓
For each field in debit_inputs/credit_inputs:
    └─ field.clear()  ← Clears QLineEdit text
    ↓
For each field in debit_lotes_inputs/credit_lotes_inputs:
    └─ field.clear()
    ↓
Reset: mc_currency_details = {'MC In': [], 'MC Out': []}
    ↓
✗ Does NOT reset:
    - _jew_computed dict
    - _jew_dialogs cache
    - _ft_ho_breakdowns dict
    - _pc_salary_breakdown dict
```

### E. Clear All Fields - Dashboard [Client/client_dashboard.py - L3860]
```
clear_all_fields()
    ↓
Ask: "Report posted! Move to next day?"
    ↓
If YES:
    ├─ For each tab: call clear_fields()
    ├─ Reset _jew_computed values to 0.0 ✓
    ├─ recalculate_all()
    └─ Advance date (triggers on_date_changed)
    ↓
If NO:
    └─ Return without clearing
```

---

## 4. SUMMARY TABLE - FIELD CLEARING COMPLETENESS

| Field Type | Location | Cleared? | Notes |
|------------|----------|----------|-------|
| Debit Amounts | CashFlowTab.clear_fields() | ✓ YES | QLineEdit.clear() |
| Debit Lotes | CashFlowTab.clear_fields() | ✓ YES | QLineEdit.clear() |
| Credit Amounts | CashFlowTab.clear_fields() | ✓ YES | QLineEdit.clear() |
| Credit Lotes | CashFlowTab.clear_fields() | ✓ YES | QLineEdit.clear() |
| MC Currency Details | CashFlowTab.clear_fields() [L910] | ✓ YES | Reset dict |
| **Empeno JEW Computed** | ❌ MISSING | ✗ NO | Dict not reset |
| **Empeno JEW Dialogs** | ❌ MISSING | ✗ NO | Cache not cleared |
| **Fund Transfer Breakdowns** | ❌ MISSING | ✗ NO | Not cleared |
| **PC Salary Breakdown** | ❌ MISSING | ✗ NO | Not cleared |
| Palawan Fields | PalawanPayableTab.clear_fields() [L305] | ✓ YES | All sections cleared |
| Cash Count | on_date_changed() [L2432] | ✓ YES | Input cleared |
| Beginning Balance | on_date_changed() [L2432] | ✓ YES | Input cleared |
| Ending Balance Display | recalculate_all() [L2745] | ✓ YES | Recalculated |

---

## 5. ROOT CAUSE LOCATIONS - QUICK REFERENCE

### Issue: Old Ending Balance Persists
**Primary Locations to Investigate**:
1. [Client/client_dashboard.py:5230-5310](Client/client_dashboard.py#L5230) - `_load_brand_report_data()`
   - Check if beginning_balance or field values are being cached
2. [Client/client_dashboard.py:2731-2751](Client/client_dashboard.py#L2731) - `recalculate_all()`
   - Verify it's using current widget values, not cached values
3. [Client/cash_flow_tab.py:902](Client/cash_flow_tab.py#L902) - `clear_fields()`
   - Check if stale values in debit/credit totals aren't being cleared

**Hypothesis**: The `cft.get_debit_total()` or `cft.get_credit_total()` might be returning cached values instead of summing current widgets.

### Issue: Empeno JEW Amounts Persist After Posting
**Primary Fix Locations**:
1. [Client/cash_flow_tab.py:902](Client/cash_flow_tab.py#L902) - `clear_fields()`
   - **FIX**: Add clearing of `_jew_computed` and `_jew_dialogs`
2. [Client/client_dashboard.py:4287-4500](Client/client_dashboard.py#L4287) - `_setup_empeno_jew_buttons()`
   - May need to add reset method to be called from clear_fields()

**Quick Fix**:
```python
# In CashFlowTab.clear_fields(), add:
if hasattr(self.parent, '_jew_computed'):
    for k in self.parent._jew_computed:
        self.parent._jew_computed[k] = 0.0

if hasattr(self.parent, '_jew_dialogs'):
    self.parent._jew_dialogs = {}
```

---

## 6. RECOMMENDED INVESTIGATION STEPS

### For Ending Balance Issue
1. Add logging at [L5283]: Log field values BEFORE clear
2. Add logging at [L5300]: Log widget text values AFTER load  
3. Add logging at [L2745]: Log calculated values in recalculate_all
4. Check `get_debit_total()` and `get_credit_total()` implementations
5. Verify `blockSignals()` calls don't prevent updates

### For Empeno JEW Issue
1. Confirm `clear_fields()` in CashFlowTab is being called
2. Add logging in `_setup_empeno_jew_buttons()` when dialog is created
3. Add logging when `_jew_computed` values are updated
4. Check if dialog is being re-populated from cache instead of starting fresh

---

## 7. COMPLETE FUNCTION REFERENCE

| Function | File | Lines | Purpose |
|----------|------|-------|---------|
| `handle_post()` | Client/client_dashboard.py | 2988 | Main post entry handler |
| `recalculate_all()` | Client/client_dashboard.py | 2731 | Recalculates ending balance |
| `on_date_changed()` | Client/client_dashboard.py | 2427 | Triggers on date picker change |
| `_load_brand_report_data()` | Client/client_dashboard.py | 5230 | Loads report from DB |
| `clear_all_fields()` | Client/client_dashboard.py | 3860 | Clears all UI fields |
| `clear_table()` | Client/client_dashboard.py | 3835 | Clears with user confirmation |
| `_setup_empeno_jew_buttons()` | Client/client_dashboard.py | 4287 | Sets up Empeno JEW UI |
| `clear_fields()` | Client/cash_flow_tab.py | 902 | Clears cash flow fields |
| `clear_fields()` | Client/palawan_payable_tab.py | 305 | Clears palawan fields |
| `clear_fields()` | Client/palawan_details_tab.py | (in class) | Clears palawan B fields |
| `_restore_palawan_payable()` | Client/client_dashboard.py | 2597 | Loads palawan data |
| `validate_calculations()` | Client/client_dashboard.py | 2845 | Validates before post |

