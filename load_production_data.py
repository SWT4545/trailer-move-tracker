import sqlite3
from datetime import datetime

def load_production_data():
    conn = sqlite3.connect('trailers.db')
    cursor = conn.cursor()
    
    print("LOADING PRODUCTION DATA...")
    print("=" * 60)
    
    # Clear existing data
    cursor.execute("DELETE FROM moves")
    cursor.execute("DELETE FROM trailers")
    cursor.execute("DELETE FROM drivers")
    cursor.execute("DELETE FROM locations")
    cursor.execute("DELETE FROM payments")
    print("Cleared existing data")
    
    # Add locations
    locations = [
        ("Fleet Memphis", "2505 Farrisview Boulevard", "Memphis", "TN", "38114", "7082853823"),
        ("FedEx Memphis", "2903 Sprankle Ave", "Memphis", "TN", "38118", "7082853823"),
        ("FedEx Indy", "6648 South Perimeter Road", "Indianapolis", "IN", "46241", "7082853823"),
        ("FedEx Chicago", "632 West Cargo Road", "Chicago", "IL", "60666", "7082853823")
    ]
    
    for loc in locations:
        cursor.execute('''INSERT INTO locations (location_name, address, city, state, zip, phone)
                         VALUES (?, ?, ?, ?, ?, ?)''', loc)
    print(f"Added {len(locations)} locations")
    
    # Add drivers
    drivers = [
        ("Justin Duckett", "L&P Solutions", "9012184083", "4496 Meadow Cliff Dr", "Memphis", "TN", "38125",
         "3978189", "1488650", "Lpsolutions1623@gmail.com", "Folsom insurance", "KSCW4403105-00", "11/26/2025", "", "", 1, 1),
        ("Carl Strikland", "Cross State Logistics Inc.", "9014974055", "P.O. Box 402", "Collierville", "TN", "38027",
         "3737098", "1321459", "Strick750@gmail.com", "Diversified Solutions Agency Inc", "02TRM061775-01", "12/04/2025", "", "", 1, 1),
        ("Brandon Smith", "Metro Logistics", "9015551234", "123 Main St", "Memphis", "TN", "38103",
         "1234567", "7654321", "brandon@metrologistics.com", "Progressive", "POL-12345", "01/15/2026", "", "", 1, 1)
    ]
    
    for driver in drivers:
        cursor.execute('''INSERT INTO drivers (driver_name, company_name, phone, address, city, state, zip,
                         dot_number, mc_number, email, insurance_company, insurance_policy, insurance_exp,
                         cdl_number, cdl_exp, coi_uploaded, w9_uploaded)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', driver)
    print(f"Added {len(drivers)} drivers")
    
    # Add users for drivers
    cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("j_duckett", "duck123", "driver"))
    cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("c_strikland", "strik123", "driver"))
    cursor.execute("INSERT OR REPLACE INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("b_smith", "metro123", "driver"))
    print("Added driver user accounts")
    
    # Add trailers at Fleet Memphis (ready to move)
    new_trailers = ["190010", "190033", "190046", "18V00298", "7728"]
    for trailer in new_trailers:
        cursor.execute("INSERT INTO trailers (trailer_number, status, location) VALUES (?, ?, ?)",
                      (trailer, "available", "Fleet Memphis"))
    
    # Add old trailers at various locations
    old_trailers = [
        ("7155", "available", "Memphis"),
        ("7146", "available", "Memphis"),
        ("5955", "available", "Memphis"),
        ("6024", "available", "Memphis"),
        ("6061", "available", "Memphis"),
        ("6094", "available", "Memphis"),
        ("3170", "available", "Memphis"),
        ("7153", "available", "Memphis"),
        ("6015", "available", "Memphis"),
        ("7160", "available", "Memphis"),
        ("6783", "available", "Memphis"),
        ("3083", "available", "FedEx Indy"),
        ("6837", "available", "FedEx Indy"),
        ("6231", "available", "FedEx Indy")
    ]
    
    for trailer in old_trailers:
        cursor.execute("INSERT INTO trailers (trailer_number, status, location) VALUES (?, ?, ?)",
                      trailer)
    
    print(f"Added {len(new_trailers) + len(old_trailers)} trailers")
    
    # Add completed moves with accurate mileage
    completed_moves = [
        # Memphis to Memphis = 10 miles (local swap)
        ("MOV-001", "FedEx Memphis", "Fleet Memphis", "Justin Duckett", "completed", "2025-08-09", 
         10, 21.00, "2025-08-13", "6014", "18V00327"),
        ("MOV-002", "FedEx Memphis", "Fleet Memphis", "Justin Duckett", "completed", "2025-08-09",
         10, 21.00, "2025-08-13", "7144", "190030"),
        
        # Memphis to Chicago = 530 miles
        ("MOV-003", "Memphis", "Chicago", "Brandon Smith", "completed", "2025-08-11",
         530, 1113.00, "2025-08-13", "5906", "7728"),
        
        # Memphis to Indianapolis = 280 miles
        ("MOV-004", "Memphis", "FedEx Indy", "Justin Duckett", "completed", "2025-08-11",
         280, 588.00, "2025-08-13", "7131", "190011"),
        ("MOV-005", "Memphis", "FedEx Indy", "Carl Strikland", "completed", "2025-08-11",
         280, 588.00, "2025-08-13", "7162", "190033")
    ]
    
    for move in completed_moves:
        cursor.execute('''INSERT INTO moves (move_id, pickup_location, delivery_location, driver_name, 
                         status, created_date, total_miles, driver_pay, payment_date, old_trailer, new_trailer)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', move)
    
    # Add current in-progress move
    cursor.execute('''INSERT INTO moves (move_id, pickup_location, delivery_location, driver_name,
                     status, created_date, total_miles, driver_pay, old_trailer, new_trailer)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  ("MOV-006", "Memphis", "FedEx Indy", "Brandon Smith", "in_progress", "2025-08-13",
                   280, 588.00, "6981", "18V00298"))
    
    print(f"Added {len(completed_moves) + 1} moves")
    
    # Add payment records for completed moves
    payments = [
        ("Justin Duckett", "2025-08-13", 609.00, 6.00, 290, "paid", "2 moves - Memphis local and to Indy"),
        ("Brandon Smith", "2025-08-13", 1113.00, 6.00, 530, "paid", "Chicago run"),
        ("Carl Strikland", "2025-08-13", 588.00, 6.00, 280, "paid", "Indianapolis delivery")
    ]
    
    for payment in payments:
        cursor.execute('''INSERT INTO payments (driver_name, payment_date, amount, service_fee, miles, status, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', payment)
    
    print(f"Added {len(payments)} payment records")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("PRODUCTION DATA LOADED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    load_production_data()