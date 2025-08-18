"""
Workflow Management System for Smith & Williams Trucking
Handles interdependent tasks with smart assumptions and defaults
"""

import sqlite3
from datetime import datetime, date
import json

class WorkflowManager:
    def __init__(self):
        self.db_path = "smith_williams_trucking.db"
        self.init_workflow_tables()
    
    def init_workflow_tables(self):
        """Create workflow tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create workflow assumptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_assumptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,  -- 'move', 'trailer', 'location', etc.
                entity_id INTEGER,
                field_name TEXT,
                assumed_value TEXT,
                actual_value TEXT,
                assumption_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by TEXT
            )
        ''')
        
        # Create workflow dependencies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_type TEXT,  -- 'move_creation', 'payment_processing', etc.
                dependent_field TEXT,
                required_for TEXT,
                default_value TEXT,
                can_proceed_without BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0
            )
        ''')
        
        # Create role capabilities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT,
                capability TEXT,
                can_override_assumptions BOOLEAN DEFAULT 0,
                can_finalize_incomplete BOOLEAN DEFAULT 0,
                approval_required_for TEXT
            )
        ''')
        
        # Initialize default dependencies
        self.init_default_dependencies(cursor)
        
        # Initialize role capabilities
        self.init_role_capabilities(cursor)
        
        conn.commit()
        conn.close()
    
    def init_default_dependencies(self, cursor):
        """Initialize default workflow dependencies"""
        dependencies = [
            # Move creation dependencies
            ('move_creation', 'old_trailer', 'swap_completion', 'TBD', 1, 1),
            ('move_creation', 'mlbl_number', 'payment_processing', 'PENDING', 1, 2),
            ('move_creation', 'actual_miles', 'payment_calculation', '0', 1, 3),
            ('move_creation', 'delivery_date', 'status_update', None, 1, 4),
            
            # Payment processing dependencies
            ('payment_processing', 'invoice_number', 'client_billing', 'AUTO_GENERATE', 1, 1),
            ('payment_processing', 'factoring_applied', 'driver_payment', '3%', 1, 2),
            ('payment_processing', 'service_fee', 'final_calculation', 'TBD', 1, 3),
            
            # Trailer management dependencies
            ('trailer_management', 'location_address', 'route_planning', 'Address TBD', 1, 1),
            ('trailer_management', 'trailer_status', 'availability', 'available', 1, 2),
        ]
        
        for dep in dependencies:
            cursor.execute('''
                INSERT OR IGNORE INTO workflow_dependencies 
                (workflow_type, dependent_field, required_for, default_value, 
                 can_proceed_without, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', dep)
    
    def init_role_capabilities(self, cursor):
        """Initialize role-based capabilities"""
        capabilities = [
            # Owner/Driver capabilities
            ('Owner/Driver', 'create_move', 1, 1, None),
            ('Owner/Driver', 'update_mlbl', 1, 1, None),
            ('Owner/Driver', 'finalize_payment', 1, 1, None),
            ('Owner/Driver', 'manage_inventory', 1, 1, None),
            ('Owner/Driver', 'override_all', 1, 1, None),
            
            # Manager capabilities
            ('Manager', 'create_move', 1, 1, None),
            ('Manager', 'update_mlbl', 1, 1, None),
            ('Manager', 'approve_payment', 0, 1, 'Owner'),
            ('Manager', 'manage_trailers', 1, 0, None),
            
            # Coordinator capabilities
            ('Coordinator', 'view_moves', 0, 0, None),
            ('Coordinator', 'update_status', 0, 0, 'Manager'),
            ('Coordinator', 'add_notes', 0, 0, None),
            
            # Driver capabilities
            ('Driver', 'view_own_moves', 0, 0, None),
            ('Driver', 'update_move_status', 0, 0, None),
            ('Driver', 'submit_completion', 0, 0, 'Manager'),
        ]
        
        for cap in capabilities:
            cursor.execute('''
                INSERT OR IGNORE INTO role_capabilities 
                (role_name, capability, can_override_assumptions, 
                 can_finalize_incomplete, approval_required_for)
                VALUES (?, ?, ?, ?, ?)
            ''', cap)
    
    def create_move_with_assumptions(self, data, user_role):
        """Create a move with smart assumptions for missing data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        assumptions_made = []
        
        # Check and fill missing data with assumptions
        if not data.get('old_trailer'):
            # Assume OLD trailer will be determined at pickup
            data['old_trailer'] = 'TBD'
            assumptions_made.append({
                'field': 'old_trailer',
                'assumed': 'TBD',
                'reason': 'Will be selected at pickup location'
            })
        
        if not data.get('mlbl_number'):
            # Assume MLBL will be assigned later
            data['mlbl_number'] = 'PENDING'
            assumptions_made.append({
                'field': 'mlbl_number',
                'assumed': 'PENDING',
                'reason': 'MLBL to be assigned by Manager/Owner'
            })
        
        if not data.get('estimated_earnings'):
            # Calculate based on miles
            miles = data.get('estimated_miles', 450)
            data['estimated_earnings'] = miles * 2.10
            assumptions_made.append({
                'field': 'estimated_earnings',
                'assumed': f"${data['estimated_earnings']:.2f}",
                'reason': f'Calculated from {miles} miles @ $2.10/mile'
            })
        
        # Create the move with assumptions
        cursor.execute('''
            INSERT INTO moves (
                system_id, driver_name, move_date, origin_location_id,
                destination_location_id, new_trailer, old_trailer,
                estimated_miles, estimated_earnings, status,
                payment_status, mlbl_number, client
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['system_id'], data['driver_name'], data['move_date'],
            data['origin_id'], data['destination_id'], data['new_trailer'],
            data['old_trailer'], data['estimated_miles'], data['estimated_earnings'],
            'assigned', 'pending', data['mlbl_number'], data.get('client', '')
        ))
        
        move_id = cursor.lastrowid
        
        # Record assumptions
        for assumption in assumptions_made:
            cursor.execute('''
                INSERT INTO workflow_assumptions 
                (entity_type, entity_id, field_name, assumed_value, assumption_reason)
                VALUES (?, ?, ?, ?, ?)
            ''', ('move', move_id, assumption['field'], 
                  assumption['assumed'], assumption['reason']))
        
        conn.commit()
        conn.close()
        
        return {
            'move_id': move_id,
            'assumptions': assumptions_made,
            'can_proceed': True
        }
    
    def update_assumption(self, entity_type, entity_id, field_name, actual_value, user):
        """Update an assumption with actual data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update the assumption record
        cursor.execute('''
            UPDATE workflow_assumptions 
            SET actual_value = ?, resolved_at = ?, resolved_by = ?
            WHERE entity_type = ? AND entity_id = ? AND field_name = ?
        ''', (actual_value, datetime.now(), user, entity_type, entity_id, field_name))
        
        # Update the actual entity
        if entity_type == 'move':
            cursor.execute(f'''
                UPDATE moves 
                SET {field_name} = ?
                WHERE id = ?
            ''', (actual_value, entity_id))
        
        conn.commit()
        conn.close()
    
    def check_workflow_completeness(self, workflow_type, entity_id):
        """Check if a workflow can be completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get required fields for this workflow
        cursor.execute('''
            SELECT dependent_field, required_for, can_proceed_without
            FROM workflow_dependencies
            WHERE workflow_type = ?
            ORDER BY priority
        ''', (workflow_type,))
        
        dependencies = cursor.fetchall()
        
        # Check unresolved assumptions
        cursor.execute('''
            SELECT field_name, assumed_value
            FROM workflow_assumptions
            WHERE entity_type = ? AND entity_id = ? AND actual_value IS NULL
        ''', (workflow_type.split('_')[0], entity_id))
        
        unresolved = cursor.fetchall()
        
        conn.close()
        
        can_complete = True
        missing_critical = []
        
        for dep_field, required_for, can_proceed in dependencies:
            if any(u[0] == dep_field for u in unresolved):
                if not can_proceed:
                    can_complete = False
                    missing_critical.append(dep_field)
        
        return {
            'can_complete': can_complete,
            'unresolved_assumptions': unresolved,
            'missing_critical': missing_critical
        }
    
    def get_role_permissions(self, role):
        """Get capabilities for a specific role"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT capability, can_override_assumptions, 
                   can_finalize_incomplete, approval_required_for
            FROM role_capabilities
            WHERE role_name = ?
        ''', (role,))
        
        capabilities = cursor.fetchall()
        conn.close()
        
        return {
            'capabilities': [c[0] for c in capabilities],
            'can_override': any(c[1] for c in capabilities),
            'can_finalize_incomplete': any(c[2] for c in capabilities),
            'needs_approval': {c[0]: c[3] for c in capabilities if c[3]}
        }
    
    def auto_fill_missing_data(self, move_id):
        """Automatically fill missing data with smart defaults"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get move details
        cursor.execute('SELECT * FROM moves WHERE id = ?', (move_id,))
        move = cursor.fetchone()
        
        updates = {}
        
        # Auto-fill OLD trailer if at destination
        if move and not move[7]:  # old_trailer is NULL or empty
            dest_id = move[5]  # destination_location_id
            cursor.execute('''
                SELECT trailer_number FROM trailers 
                WHERE current_location_id = ? AND is_new = 0 
                AND status = 'available'
                LIMIT 1
            ''', (dest_id,))
            
            available_trailer = cursor.fetchone()
            if available_trailer:
                updates['old_trailer'] = available_trailer[0]
                cursor.execute('''
                    UPDATE moves SET old_trailer = ? WHERE id = ?
                ''', (available_trailer[0], move_id))
        
        # Auto-generate MLBL if pattern established
        if move and move[12] == 'PENDING':  # mlbl_number
            cursor.execute('''
                SELECT mlbl_number FROM moves 
                WHERE mlbl_number != 'PENDING' 
                ORDER BY id DESC LIMIT 1
            ''')
            
            last_mlbl = cursor.fetchone()
            if last_mlbl and last_mlbl[0].startswith('MLBL'):
                try:
                    num = int(last_mlbl[0].split('-')[1]) + 1
                    new_mlbl = f"MLBL-{num:06d}"
                    updates['mlbl_number'] = new_mlbl
                    cursor.execute('''
                        UPDATE moves SET mlbl_number = ? WHERE id = ?
                    ''', (new_mlbl, move_id))
                except:
                    pass
        
        conn.commit()
        conn.close()
        
        return updates

class SmartDefaults:
    """Provide smart defaults for various fields"""
    
    @staticmethod
    def get_default_miles(origin, destination):
        """Get default miles based on route"""
        routes = {
            ('Fleet Memphis', 'FedEx Memphis'): 95.24,
            ('Fleet Memphis', 'FedEx Indy'): 933.33,
            ('Fleet Memphis', 'FedEx Chicago'): 1130.0,
            ('Fleet Memphis', 'FedEx Houston'): 650.0,
            ('Fleet Memphis', 'FedEx Dallas'): 550.0,
        }
        
        return routes.get((origin, destination), 450.0)
    
    @staticmethod
    def get_default_payment(miles):
        """Calculate default payment"""
        return miles * 2.10
    
    @staticmethod
    def get_next_mlbl():
        """Generate next MLBL number"""
        conn = sqlite3.connect("smith_williams_trucking.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT mlbl_number FROM moves 
            WHERE mlbl_number LIKE 'MLBL-%'
            ORDER BY id DESC LIMIT 1
        ''')
        
        last = cursor.fetchone()
        conn.close()
        
        if last:
            try:
                num = int(last[0].split('-')[1]) + 1
                return f"MLBL-{num:06d}"
            except:
                pass
        
        return f"MLBL-{datetime.now().strftime('%Y%m%d')}001"
    
    @staticmethod
    def can_proceed_without(field):
        """Check if workflow can proceed without a field"""
        optional_fields = [
            'old_trailer',  # Can be determined at pickup
            'mlbl_number',  # Can be assigned later
            'actual_miles',  # Can use estimated
            'delivery_date',  # Can be updated when completed
            'service_fee',  # Can be calculated at payment
            'invoice_number',  # Can be generated when needed
        ]
        
        return field in optional_fields

if __name__ == "__main__":
    # Initialize workflow manager
    wf = WorkflowManager()
    print("Workflow Manager initialized")
    
    # Test smart defaults
    defaults = SmartDefaults()
    print(f"Default miles Fleet->Indy: {defaults.get_default_miles('Fleet Memphis', 'FedEx Indy')}")
    print(f"Next MLBL: {defaults.get_next_mlbl()}")
    print(f"Can proceed without old_trailer: {defaults.can_proceed_without('old_trailer')}")