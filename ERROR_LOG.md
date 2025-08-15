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
**Files Affected:** `app.py` (全 file - over 100 Unicode characters removed)
**Prevention:** NEVER use Unicode characters/emojis in production apps - use text only

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

---

Last Updated: 2025-08-15