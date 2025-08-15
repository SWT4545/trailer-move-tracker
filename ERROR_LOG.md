# Error Log - Trailer Move Tracker

## Purpose
This log tracks all errors encountered during development to prevent recurring issues.

---

## Error History

### 1. Unicode Encoding Error (RESOLVED)
**Date:** 2025-08-15
**Error:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 43`
**Cause:** Using Unicode arrow character (→) in SQL queries and displays
**Solution:** Replaced all `→` with `->` in SQL queries and string concatenations
**Files Affected:** `app.py`
**Prevention:** Always use ASCII-safe characters in database queries

### 2. Database Structure Mismatch (RESOLVED)
**Date:** 2025-08-15
**Error:** `sqlite3.OperationalError: no such column: m.trailer_id`
**Cause:** App expected normalized database structure but actual DB uses simpler structure
**Solution:** Updated queries to match actual database schema (old_trailer, new_trailer columns)
**Files Affected:** `app.py`, `load_real_production_data.py`
**Prevention:** Always check actual database schema before writing queries

### 3. Indentation Error in Form Submit (RESOLVED)
**Date:** 2025-08-15
**Error:** Incorrect indentation after form submit button
**Cause:** Missing proper indentation when adding form submit logic
**Solution:** Fixed indentation to properly nest conditional logic
**Files Affected:** `app.py` (line 586-587)
**Prevention:** Always verify indentation when editing Python code

### 4. JSON Encoding Error (RESOLVED)
**Date:** 2025-08-15
**Error:** `The request body is not valid JSON: no low surrogate in string`
**Cause:** Unicode characters in large edit operations
**Solution:** Split large edits into smaller chunks, handle Unicode separately
**Files Affected:** `app.py`
**Prevention:** Break large file edits into smaller operations

### 5. Missing Table References (RESOLVED)
**Date:** 2025-08-15
**Error:** `sqlite3.OperationalError: no such table: drivers`
**Cause:** Assumed existence of drivers table that doesn't exist in actual DB
**Solution:** Used driver_profiles table instead
**Files Affected:** `app.py`
**Prevention:** Check sqlite_master for actual table names

### 6. Incorrect Mileage Calculations (RESOLVED)
**Date:** 2025-08-15
**Issue:** Mileage for Fleet Memphis to FedEx Indy was 385 instead of 466.67
**Impact:** Payment calculations were wrong ($1,617 instead of $1,960)
**Solution:** Updated mileage to 933.33 round trip (466.67 each way)
**Files Affected:** `load_real_production_data.py`
**Prevention:** Verify actual business data before hardcoding values

### 7. Payment Status Color Visibility (RESOLVED)
**Date:** 2025-08-15
**Issue:** Payment status colors were not visible enough
**Original:** Light green (#90EE90) and light orange (#FFE4B5) backgrounds
**Solution:** Changed to high contrast - Green (#28a745) with white text, Yellow (#ffc107) with black text
**Files Affected:** `app.py`
**Prevention:** Always test color combinations for visibility

### 8. User Role Integration (RESOLVED)
**Date:** 2025-08-15
**Issue:** Brandon's owner account needed separate login for driver functions
**Solution:** Added integrated Owner/Driver role with is_driver flag
**Files Affected:** `app.py` (user configuration)
**Prevention:** Design user roles to support multiple capabilities

### 9. Database Schema Mismatch - Trailers Table (RESOLVED)
**Date:** 2025-08-15
**Error:** `sqlite3.OperationalError` when querying trailers with non-existent columns
**Cause:** Query assumed trailers table had columns like `trailer_id` and complex location fields
**Actual Schema:** 
  - trailers: id, trailer_number, current_location, status (simple structure)
  - moves: old_trailer, new_trailer as TEXT (trailer numbers, not IDs)
**Solution:** Simplified query to match actual database schema
**Files Affected:** `app.py` (lines 482-499)
**Prevention:** Always verify actual table structure before writing queries

### 10. Unicode Characters Breaking Streamlit Cloud (RESOLVED)
**Date:** 2025-08-15
**Error:** App crashes on Streamlit Cloud due to Unicode encoding issues
**Cause:** Using Unicode emojis (🚛, ✅, 📊, etc.) throughout the app interface
**Impact:** App works locally but fails on Streamlit Cloud deployment
**Solution:** Removed ALL Unicode characters from app.py - replaced with text or removed entirely
**Files Affected:** `app.py` (entire file - over 100 Unicode characters removed)
**Prevention:** NEVER use Unicode characters/emojis in production apps - use text only

### 11. Database Column Name Mismatch on Streamlit Cloud (RESOLVED)
**Date:** 2025-08-15
**Error:** `sqlite3.OperationalError` on queries using t.current_location
**Cause:** Database has different structures - normalized vs simple
  - smith_williams_trucking.db: Uses `current_location_id` with foreign keys
  - trailer_moves.db: Uses `current_location` as text field
**Solution:** Added dynamic schema detection before queries
  - Check table structure with PRAGMA table_info
  - Build appropriate query based on available columns
**Files Affected:** `app.py` (lines 481-515, 763-793, 832-857)
**Prevention:** Always check table structure dynamically, don't assume column names

### 12. Missing Table Check Before Query (RESOLVED)
**Date:** 2025-08-15
**Error:** `sqlite3.OperationalError` when trailers table doesn't exist
**Cause:** Code assumed trailers table exists but on fresh deployment it might not
**Solution:** Added table existence check before queries
  - Check sqlite_master for table existence
  - Provide user feedback if table missing
  - Wrap queries in try-catch blocks
**Files Affected:** `app.py` (lines 483-527)
**Prevention:** Always verify table exists before querying

### 13. Duplicate cursor.fetchall() Call (RESOLVED)
**Date:** 2025-08-15
**Error:** Attempting to fetch from exhausted cursor
**Cause:** Code had duplicate `trailers = cursor.fetchall()` lines
**Solution:** Removed duplicate fetchall() call
**Files Affected:** `app.py` (line 528 removed)
**Prevention:** Careful code review after edits

### 14. AttributeError on None Values (RESOLVED)
**Date:** 2025-08-15
**Error:** `AttributeError` when calling .replace() on None value
**Cause:** `destination` variable could be None, but code tried to call .replace()
**Solution:** Added None checks before string operations
**Files Affected:** `app.py` (lines 675-705)
**Prevention:** Always check for None before calling string methods

### 15. Empty Database on Fresh Deploy (RESOLVED)
**Date:** 2025-08-15
**Issue:** App shows 0 trailers, 0 moves, 0 drivers on fresh deployment
**Cause:** Database empty and load_real_production_data.py not available on Streamlit Cloud
**Solution:** Enhanced load_initial_data() to:
  - Check if data exists
  - Try to load production data
  - Fall back to minimal demo data if needed
**Files Affected:** `app.py` (lines 215-272)
**Prevention:** Always provide fallback data initialization

---

## Common Patterns to Avoid

1. **Unicode in Database Operations**
   - Always use ASCII characters in SQL
   - Convert Unicode for display only

2. **Database Schema Assumptions**
   - Always verify table structure with PRAGMA table_info
   - Check column names before writing queries

3. **Large Edit Operations**
   - Break into smaller chunks
   - Handle special characters separately

4. **Hardcoded Values**
   - Verify with actual business data
   - Document source of constants

5. **Color Accessibility**
   - Use high contrast combinations
   - Test with different screen settings

---

## Testing Checklist Before Push

- [ ] Run app locally with `streamlit run app.py`
- [ ] Test all user roles (Owner, Driver, Manager, Coordinator)
- [ ] Verify database operations (create, read, update)
- [ ] Check color visibility on different backgrounds
- [ ] Ensure no Unicode in SQL queries
- [ ] Verify calculations match business requirements
- [ ] Test form submissions and validations

---

## Quick Reference Commands

```bash
# Check database structure
python -c "import sqlite3; conn = sqlite3.connect('trailer_moves.db'); cursor = conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"); print(cursor.fetchall())"

# Reload production data
python load_real_production_data.py

# Test streamlit app
streamlit run app.py

# Check for Unicode issues
grep -r "→" *.py
grep -r "✓" *.py
```

### 16. Global Schema Detection Missing (RESOLVED)
**Date:** 2025-08-15
**Error:** `sqlite3.OperationalError: table moves has no column named new_trailer`
**Cause:** App tried to access new_trailer/old_trailer columns without checking if they exist
**Root Issue:** Different database schemas on local vs cloud deployments
**Solution:** Added global schema detection functions:
  - `get_table_columns()` - Gets column list for any table
  - `table_exists()` - Checks if table exists
  - Updated ALL queries to check schema before accessing columns
**Files Affected:** `app.py` (20+ queries updated)
**Prevention:** 
  - ALWAYS check column existence before querying
  - Use helper functions for dynamic schema detection
  - Never assume database structure

### 17. UnboundLocalError - trailer_options Not Initialized (RESOLVED)
**Date:** 2025-08-15
**Error:** `UnboundLocalError: cannot access local variable 'trailer_options' where it is not associated with a value`
**Location:** `app.py` line 680 in `create_new_move()`
**Cause:** Variables `trailer_options` and `trailer_numbers` only initialized inside conditional blocks
**Root Issue:** If `trailers_at_fleet` was empty, variables were never initialized before use
**Solution:** Initialize `trailer_options` and `trailer_numbers` at the start of the trailers block
**Files Affected:** `app.py` (lines 656-686)
**Prevention:**
  - Always initialize variables before conditional blocks
  - Ensure all code paths define required variables
  - Initialize collections (dict, list) early in function scope

### 18. Dashboard Metrics Enhancement (RESOLVED)
**Date:** 2025-08-15
**Request:** Split available trailer count into Old/New/Total on dashboard
**Implementation:** Enhanced trailer metrics to show:
  - Old Trailers count (for pickup)
  - New Trailers count (for delivery)
  - Total Available count
  - New Trailer percentage
**Solution:** 
  - Check for `is_new` column in trailers table
  - If exists, use it to separate old (is_new=0) and new (is_new=1)
  - If not, estimate based on trailer number patterns (19*, 18V*, 77*)
  - Added two-row metric display with 7 total metrics
**Files Affected:** `app.py` - `show_overview_metrics()` function
**Benefits:**
  - Better visibility into trailer swap inventory
  - Helps track old trailer pickup needs
  - Shows new trailer delivery availability

---

Last Updated: 2025-08-15