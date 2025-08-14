"""
Final Payment System
Handles client gross payments and distributes to drivers after fees
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

class FinalPaymentSystem:
    """
    Payment flow:
    1. Client pays gross amount for moves
    2. 3% factoring fee is deducted from total
    3. Service fee ($6 total, split among drivers) is deducted
    4. Remaining amount is distributed to drivers based on their moves
    """
    
    FACTORING_RATE = 0.03  # 3% factoring fee
    DEFAULT_SERVICE_FEE = 6.00  # Total service fee to split among drivers
    
    def __init__(self, db_path='trailers.db'):
        self.db_path = db_path
        self._ensure_schema()
        self._initialize_route_pricing()
    
    def _ensure_schema(self):
        """Ensure database has correct schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create submissions table for batch payments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT UNIQUE,
                client_payment REAL,
                factoring_fee REAL,
                service_fee REAL,
                num_drivers INTEGER,
                submission_date TEXT,
                payment_date TEXT,
                status TEXT DEFAULT 'pending',
                notes TEXT
            )
        ''')
        
        # Create submission_moves table to link moves to submissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submission_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT,
                move_id TEXT,
                driver_name TEXT,
                gross_amount REAL,
                net_amount REAL,
                FOREIGN KEY (submission_id) REFERENCES submissions(submission_id)
            )
        ''')
        
        # Create route_pricing table for estimates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_pricing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pickup_location TEXT,
                delivery_location TEXT,
                standard_payment REAL,
                miles REAL,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _initialize_route_pricing(self):
        """Initialize route pricing based on known payments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Known route prices from the data
        routes = [
            ('FedEx Memphis', 'Fleet Memphis', 200.00, 10),  # Local Memphis
            ('Memphis', 'Chicago', 2373.00, 530),  # Chicago run
            ('Memphis', 'FedEx Indy', 1960.00, 280),  # Indianapolis run
        ]
        
        for pickup, delivery, payment, miles in routes:
            cursor.execute('''
                INSERT OR REPLACE INTO route_pricing 
                (pickup_location, delivery_location, standard_payment, miles, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (pickup, delivery, payment, miles, datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
    
    def calculate_submission_payment(self, submission_data: Dict) -> Dict:
        """
        Calculate payment distribution for a submission
        
        Args:
            submission_data: {
                'client_payment': 6693.00,
                'moves': [
                    {'driver': 'Justin Duckett', 'gross': 200, 'move_id': 'MOV-001'},
                    {'driver': 'Justin Duckett', 'gross': 200, 'move_id': 'MOV-002'},
                    {'driver': 'Justin Duckett', 'gross': 1960, 'move_id': 'MOV-003'},
                    {'driver': 'Carl Strikland', 'gross': 1960, 'move_id': 'MOV-004'},
                    {'driver': 'Brandon Smith', 'gross': 2373, 'move_id': 'MOV-005'}
                ],
                'service_fee': 6.00  # Optional, defaults to 6.00
            }
        
        Returns:
            Payment breakdown with net amounts per driver
        """
        
        client_payment = submission_data['client_payment']
        moves = submission_data['moves']
        service_fee = submission_data.get('service_fee', self.DEFAULT_SERVICE_FEE)
        
        # Calculate factoring fee on total client payment
        factoring_fee = client_payment * self.FACTORING_RATE
        
        # Get unique drivers
        drivers = {}
        for move in moves:
            driver = move['driver']
            if driver not in drivers:
                drivers[driver] = {'gross': 0, 'moves': []}
            drivers[driver]['gross'] += move['gross']
            drivers[driver]['moves'].append(move['move_id'])
        
        num_drivers = len(drivers)
        service_fee_per_driver = service_fee / num_drivers if num_drivers > 0 else 0
        
        # Calculate net payment for each driver
        results = {
            'submission_total': client_payment,
            'factoring_fee': factoring_fee,
            'service_fee': service_fee,
            'num_drivers': num_drivers,
            'service_fee_per_driver': service_fee_per_driver,
            'driver_payments': {}
        }
        
        total_gross = sum(d['gross'] for d in drivers.values())
        
        for driver_name, driver_data in drivers.items():
            # Each driver's share of factoring fee is proportional to their gross
            driver_factoring_share = (driver_data['gross'] / total_gross) * factoring_fee if total_gross > 0 else 0
            
            # Net payment = gross - factoring share - service fee share
            net_payment = driver_data['gross'] - driver_factoring_share - service_fee_per_driver
            
            results['driver_payments'][driver_name] = {
                'gross': driver_data['gross'],
                'factoring_share': driver_factoring_share,
                'service_fee_share': service_fee_per_driver,
                'net_payment': net_payment,
                'moves': driver_data['moves']
            }
        
        return results
    
    def get_route_estimate(self, pickup: str, delivery: str) -> Optional[float]:
        """Get estimated payment for a route based on historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT standard_payment FROM route_pricing
            WHERE pickup_location = ? AND delivery_location = ?
        ''', (pickup, delivery))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def save_submission(self, submission_data: Dict, payment_breakdown: Dict) -> str:
        """Save a submission and its payment breakdown"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate submission ID
        submission_id = f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save submission
        cursor.execute('''
            INSERT INTO submissions 
            (submission_id, client_payment, factoring_fee, service_fee, 
             num_drivers, submission_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (submission_id, submission_data['client_payment'],
              payment_breakdown['factoring_fee'], payment_breakdown['service_fee'],
              payment_breakdown['num_drivers'], datetime.now().strftime('%Y-%m-%d'),
              'pending'))
        
        # Save move details
        for driver_name, driver_data in payment_breakdown['driver_payments'].items():
            for move_id in driver_data['moves']:
                # Find the gross for this specific move
                move_gross = next(m['gross'] for m in submission_data['moves'] 
                                if m['move_id'] == move_id)
                
                cursor.execute('''
                    INSERT INTO submission_moves
                    (submission_id, move_id, driver_name, gross_amount, net_amount)
                    VALUES (?, ?, ?, ?, ?)
                ''', (submission_id, move_id, driver_name, move_gross,
                      driver_data['net_payment'] * (move_gross / driver_data['gross'])))
        
        conn.commit()
        conn.close()
        
        return submission_id
    
    def format_payment_breakdown(self, breakdown: Dict) -> str:
        """Format payment breakdown for display"""
        lines = []
        lines.append("=" * 70)
        lines.append("PAYMENT BREAKDOWN")
        lines.append("=" * 70)
        lines.append(f"Client Payment: ${breakdown['submission_total']:,.2f}")
        lines.append(f"Factoring Fee (3%): -${breakdown['factoring_fee']:,.2f}")
        lines.append(f"Service Fee: -${breakdown['service_fee']:.2f}")
        lines.append(f"Number of Drivers: {breakdown['num_drivers']}")
        lines.append(f"Service Fee per Driver: ${breakdown['service_fee_per_driver']:.2f}")
        lines.append("-" * 70)
        
        for driver, data in breakdown['driver_payments'].items():
            lines.append(f"\n{driver}:")
            lines.append(f"  Gross Amount: ${data['gross']:,.2f}")
            lines.append(f"  Factoring Fee Share: -${data['factoring_share']:,.2f}")
            lines.append(f"  Service Fee Share: -${data['service_fee_share']:.2f}")
            lines.append(f"  NET PAYMENT: ${data['net_payment']:,.2f}")
            lines.append(f"  Moves: {', '.join(data['moves'])}")
        
        lines.append("=" * 70)
        
        # Verify totals
        total_net = sum(d['net_payment'] for d in breakdown['driver_payments'].values())
        total_fees = breakdown['factoring_fee'] + breakdown['service_fee']
        lines.append(f"\nVerification:")
        lines.append(f"Total Net Payments: ${total_net:,.2f}")
        lines.append(f"Total Fees: ${total_fees:,.2f}")
        lines.append(f"Sum (should equal client payment): ${total_net + total_fees:,.2f}")
        
        return "\n".join(lines)


# Example usage with your data
if __name__ == "__main__":
    system = FinalPaymentSystem()
    
    # Your exact data
    submission = {
        'client_payment': 6693.00,
        'moves': [
            {'driver': 'Justin Duckett', 'gross': 200, 'move_id': 'MOV-001'},
            {'driver': 'Justin Duckett', 'gross': 200, 'move_id': 'MOV-002'},
            {'driver': 'Justin Duckett', 'gross': 1960, 'move_id': 'MOV-003'},
            {'driver': 'Carl Strikland', 'gross': 1960, 'move_id': 'MOV-004'},
            {'driver': 'Brandon Smith', 'gross': 2373, 'move_id': 'MOV-005'}
        ],
        'service_fee': 6.00
    }
    
    # Calculate payment breakdown
    breakdown = system.calculate_submission_payment(submission)
    print(system.format_payment_breakdown(breakdown))
    
    # Verify your numbers
    print("\nVERIFYING AGAINST YOUR PROVIDED NUMBERS:")
    print("-" * 70)
    for driver, expected_net in [('Justin Duckett', 2287.20), 
                                  ('Carl Strikland', 1899.20), 
                                  ('Brandon Smith', 2299.81)]:
        calculated = breakdown['driver_payments'][driver]['net_payment']
        match = "✓" if abs(calculated - expected_net) < 0.01 else "✗"
        print(f"{driver}: Expected ${expected_net:.2f}, Calculated ${calculated:.2f} {match}")
    
    # Test route estimates
    print("\nROUTE ESTIMATES:")
    print("-" * 70)
    print(f"Memphis to FedEx Indy: ${system.get_route_estimate('Memphis', 'FedEx Indy')}")
    print(f"Memphis to Chicago: ${system.get_route_estimate('Memphis', 'Chicago')}")
    print(f"FedEx Memphis to Fleet Memphis: ${system.get_route_estimate('FedEx Memphis', 'Fleet Memphis')}")