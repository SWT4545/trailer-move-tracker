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

### 19. Trailer Inventory Mismatch on Streamlit Cloud (RESOLVED)
**Date:** 2025-08-15
**Issue:** Streamlit Cloud showing 32 trailers (11 NEW, 21 OLD) instead of 38 (15 NEW, 23 OLD)
**Cause:** Update scripts not running on cloud deployment
**Solution:** Added `fix_trailer_inventory()` function that runs on every app load
  - Checks current counts
  - If wrong (32 instead of 38), rebuilds with correct data
  - Hardcoded exact trailer lists to ensure consistency
**Files Affected:** `app.py` (added fix_trailer_inventory function)
**Prevention:** Always include data fixes in main app initialization
**Implementation:** Enhanced trailer metrics to show:
  - Old Trailers count (for pickup)
  - New Trailers count (for delivery)
  - Total Available count
  - New Trailer percentage
**Solution:** 
  - Check for `is_new` column in trailers table
  - If exists, use it to separate old (is_new=0) and new (is_new=1)
  - If not, identify based on ACTUAL production data patterns
**Files Affected:** `app.py` - `show_overview_metrics()` function
**Benefits:**
  - Better visibility into trailer swap inventory
  - Helps track old trailer pickup needs
  - Shows new trailer delivery availability

### 19. Incorrect Trailer Pattern Recognition (RESOLVED)
**Date:** 2025-08-15
**Issue:** Wrong trailer split - incorrect pattern matching for old/new
**Root Cause:** Initial pattern was guessed, not based on actual data
**Actual Data Analysis:**
  - **NEW trailers (is_new=1)**: 190xxx, 18Vxxxxx, and special case 7728
  - **OLD trailers (is_new=0)**: 3xxx, 4xxx, 5xxx, 6xxx, 7xxx (except 7728)
**Evidence from moves:**
  - All `new_trailer` fields: 18V00327, 190030, 190011, 7728, 190033, etc.
  - All `old_trailer` fields: 6014, 7144, 7131, 5906, 7162, etc.
**Solution:** Updated pattern matching to match actual production data
**Files Affected:** `app.py` lines 527-548
**Prevention:** Always analyze actual data before implementing pattern matching

### 20. Trailer Count Should Include ALL Status Types (RESOLVED)
**Date:** 2025-08-15
**Issue:** Dashboard only counting "available" trailers, not total fleet
**User Clarification:** Count should include ALL trailers regardless of status
**Actual Fleet Inventory:**
  - **NEW trailers (11 total)**: 
    - 190033 (at FedEx Indy)
    - 190046 (in process to FedEx Indy)
    - 18V00298 (at FedEx Indy)
    - 7728 (at FedEx Chicago)
    - 190011 (at FedEx Indy)
    - 190030 (at FedEx Memphis)
    - 18V00327 (at FedEx Memphis)
    - 18V00406 (at FedEx Memphis)
    - 18V00409 (at FedEx Memphis)
    - 18V00414 (at FedEx Memphis)
    - 18V00407 (in process to FedEx Indy)
  - **OLD trailers (21 total)**:
    - At FedEx locations (12): 7155, 7146, 5955, 6024, 6061, 3170, 7153, 6015, 7160, 6783, 3083, 6231
    - At Fleet Memphis (9): 7162, 7131, 5906, 7144, 6014, 6981, 5950, 5876, 4427
**Solution:** 
  - Count ALL trailers regardless of status (available, in_transit, delivered)
  - Show total count with available count in parentheses
  - Display format: "21 (9 avail)" for old, "11 (2 avail)" for new
**Files Affected:** `app.py` show_overview_metrics() function
**Benefits:** Accurate fleet inventory visibility

### 21. TypeError with Dynamically Imported Modules (RESOLVED)
**Date:** 2025-08-15
**Error:** `TypeError: Failed to fetch dynamically imported module`
**URL Pattern:** `https://trailer-move-team-tracker.streamlit.app/~/+/static/js/index.*.js`
**Cause:** Stale cache on Streamlit Cloud causing module loading failures
**Solution:** 
  - Added automatic cache clearing on app start
  - Implemented hourly cache refresh to prevent stale modules
  - Cache clears both data and resource caches
**Files Affected:** `app.py` lines 29-37
**Prevention:** Regular cache clearing prevents module loading issues

### 22. Video Login Enhancement (RESOLVED)
**Date:** 2025-08-15
**Request:** Ensure video on login page is muted and loops
**Implementation:** 
  - Video already configured with `loop=True, autoplay=True, muted=True`
  - Centered video in middle column
  - Added fallback to static logo if video fails
  - Video file: company_logo_animation.mp4.MOV
**Files Affected:** `app.py` login() function
**Benefits:** Professional animated branding on login page

### 23. ValueError in show_completed_moves (RESOLVED)
**Date:** 2025-08-15
**Error:** `ValueError: This app has encountered an error. The original error message is redacted...`
**Cause:** Column count mismatch in show_completed_moves() function
**Root Issue:** Query returned 9 columns but DataFrame expected 10 (missing 'Return Trailer')
**Solution:** 
  - Added proper schema detection for old_trailer column
  - Ensured all query branches return exactly 10 columns
  - Used dynamic column detection before building queries
**Files Affected:** `app.py` lines 1576-1625
**Prevention:** Always ensure query result columns match DataFrame column definitions

### 24. Video Autoplay on Mobile Devices (RESOLVED)
**Date:** 2025-08-15
**Issue:** Video on login page requires user to press play button on mobile devices
**Cause:** Streamlit's st.video() doesn't fully support autoplay on all devices
**Solution:** 
  - Replaced st.video() with HTML5 video tag using base64 encoding
  - Added playsinline attribute for iOS Safari compatibility
  - Ensured muted, loop, and autoplay attributes are set
  - HTML5 video provides better cross-device compatibility
**Files Affected:** `app.py` login() function
**Benefits:** Video plays automatically on all devices without user interaction

### 25. Vernon Data Protection Footer (RESOLVED)
**Date:** 2025-08-15
**Request:** Add Vernon's title and data protection notice to all app pages
**Implementation:**
  - Added footer to sidebar: "Data Protected by Vernon - Senior IT Security Manager"
  - Added footer to main content area on all dashboard pages
  - Added protection notice on login page
  - Vernon's security credentials visible on every page
**Files Affected:** `app.py` - show_sidebar(), main(), login()
**Benefits:** Reinforces data security and Vernon's role as IT Security Manager

### 26. PDF Invoice Clarity (RESOLVED)
**Date:** 2025-08-15
**Issue:** PDF invoices needed clearer factoring fee display
**Solution:**
  - Updated breakdown to show: Gross → Factoring (3%) → Total After Factoring
  - Added disclaimer: "Service fees are not included in this total"
  - Removed word "professional" from invoice generation
  - Example: $1960 - $58.80 (3%) = $1901.20
**Files Affected:** `pdf_generator.py`, `app.py`
**Benefits:** Clear, accurate payment calculations

### 27. TypeError in create_new_move (RESOLVED)
**Date:** 2025-08-15
**Error:** `TypeError` at line 758 - cursor.fetchone() called twice
**Cause:** Double call to cursor.fetchone() - first call consumed result, second returned None
**Solution:** 
  - Store fetchone() result in variable before checking
  - Changed: `cursor.fetchone()[0] if cursor.fetchone() else 1`
  - To: `fleet_result = cursor.fetchone(); fleet_id = fleet_result[0] if fleet_result else 1`
**Files Affected:** `app.py` line 758
**Prevention:** Always store database results before checking/using them

### 28. Database Column Reference Errors (RESOLVED)
**Date:** 2025-08-17
**Error:** `sqlite3.OperationalError: no such column: delivery_location`
**Multiple Locations:** Lines 1323, 1471, 1560, 1873, 1881, 1891, 1902, 2053, 2065, 2076, 2421, 2431, 2440, 2494
**Cause:** Code was referencing non-existent columns:
  - `pickup_location` (should be `origin_location`)
  - `delivery_location` when used alone (should check both `destination_location` and `delivery_location`)
**Root Issue:** Database schema has `origin_location` and `destination_location` as primary columns, with `delivery_location` as a backup
**Solution:** 
  - Changed all `pickup_location` references to `origin_location`
  - Used COALESCE for all location queries: `COALESCE(m.destination_location, m.delivery_location, 'Unknown')`
  - Applied fix globally across 14+ queries
**Files Affected:** `app.py` (multiple queries throughout)
**Prevention:** 
  - Always use COALESCE when accessing location columns
  - Check actual database schema before writing queries
  - Never assume column names - verify with PRAGMA table_info

### 29. No Active Moves to Reassign (RESOLVED)
**Date:** 2025-08-17
**Issue:** Admin panel showing "No active moves to reassign"
**Cause:** Query was failing due to column reference errors
**Solution:** Fixed underlying column reference issues in queries
**Files Affected:** `app.py` lines 2400-2450

### 30. Return Trailer Tracking Not Available (RESOLVED)
**Date:** 2025-08-17
**Issue:** Warning "Return trailer tracking not available in this database schema"
**Cause:** Code checking for wrong columns or queries failing
**Solution:** 
  - Fixed column references in return trailer queries
  - Ensured old_trailer and new_trailer columns are properly queried
**Files Affected:** `app.py` lines 2505-2565

---

Last Updated: 2025-08-17