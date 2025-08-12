"""
Complete Role System with All User Types
Including Client and Trainee roles
"""

import streamlit as st
import json
import os
from datetime import datetime

class CompleteRoleSystem:
    """Complete role system with all user types"""
    
    def __init__(self):
        self.roles = {
            'business_administrator': {
                'name': 'Business Administrator',
                'icon': '👔',
                'level': 100,
                'permissions': [
                    'full_system_access',
                    'user_management',
                    'financial_access',
                    'system_configuration',
                    'report_generation',
                    'data_export',
                    'delete_records',
                    'modify_all_records',
                    'view_all_data'
                ],
                'description': 'Full system access with all administrative privileges',
                'features': [
                    'Complete system control',
                    'User and role management',
                    'Financial oversight',
                    'System configuration',
                    'Advanced reporting',
                    'Data management'
                ]
            },
            'operations_coordinator': {
                'name': 'Operations Coordinator',
                'icon': '📋',
                'level': 80,
                'permissions': [
                    'create_moves',
                    'edit_moves',
                    'manage_drivers',
                    'manage_trailers',
                    'view_reports',
                    'pod_management',
                    'dispatch_operations',
                    'view_financial_summary'
                ],
                'description': 'Manages day-to-day operations and logistics',
                'features': [
                    'Move creation and management',
                    'Driver assignment',
                    'Trailer tracking',
                    'POD verification',
                    'Operational reporting',
                    'Schedule management'
                ]
            },
            'driver': {
                'name': 'Driver',
                'icon': '🚛',
                'level': 40,
                'permissions': [
                    'view_assigned_moves',
                    'update_move_status',
                    'upload_pod',
                    'view_own_earnings',
                    'update_availability',
                    'view_route_info',
                    'submit_expenses'
                ],
                'description': 'Field operations and delivery execution',
                'features': [
                    'View assigned moves',
                    'Update delivery status',
                    'Upload POD documents',
                    'Track earnings',
                    'Manage availability',
                    'Access route information'
                ]
            },
            'client_viewer': {
                'name': 'Client Viewer',
                'icon': '🏢',
                'level': 30,
                'permissions': [
                    'view_company_moves',
                    'view_trailer_status',
                    'view_delivery_status',
                    'download_reports',
                    'view_pod_documents',
                    'track_shipments'
                ],
                'description': 'External client access to track their shipments',
                'features': [
                    'Real-time shipment tracking',
                    'Trailer status monitoring',
                    'POD document access',
                    'Delivery confirmations',
                    'Basic reporting',
                    'Shipment history'
                ]
            },
            'viewer': {
                'name': 'Viewer',
                'icon': '👁️',
                'level': 20,
                'permissions': [
                    'view_dashboard',
                    'view_basic_reports',
                    'view_trailer_locations',
                    'view_move_status'
                ],
                'description': 'Read-only access to system information',
                'features': [
                    'Dashboard viewing',
                    'Basic reports',
                    'Status monitoring',
                    'Location tracking'
                ]
            },
            'trainee': {
                'name': 'Trainee',
                'icon': '🎓',
                'level': 10,
                'permissions': [
                    'view_training_materials',
                    'practice_mode',
                    'view_demo_data',
                    'submit_training_tasks',
                    'view_limited_operations'
                ],
                'description': 'Learning role with guided access to system features',
                'features': [
                    'Access training modules',
                    'Practice in safe environment',
                    'View demonstration data',
                    'Submit training exercises',
                    'Guided system tours',
                    'Limited operational viewing'
                ]
            }
        }
    
    def get_role_info(self, role_key):
        """Get detailed role information"""
        return self.roles.get(role_key, None)
    
    def check_permission(self, user_role, permission):
        """Check if a role has specific permission"""
        role_info = self.roles.get(user_role)
        if not role_info:
            return False
        return permission in role_info['permissions']
    
    def get_available_features(self, user_role):
        """Get list of available features for a role"""
        role_info = self.roles.get(user_role)
        if not role_info:
            return []
        return role_info['features']
    
    def show_roles_overview(self):
        """Display comprehensive roles overview"""
        st.title("🎭 System Roles & Permissions")
        
        st.markdown("""
        ### Role Hierarchy
        Each role has specific permissions and access levels within the system.
        """)
        
        # Sort roles by level
        sorted_roles = sorted(self.roles.items(), key=lambda x: x[1]['level'], reverse=True)
        
        for role_key, role_info in sorted_roles:
            with st.expander(f"{role_info['icon']} **{role_info['name']}** (Level {role_info['level']})", expanded=False):
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.markdown(f"**Description:** {role_info['description']}")
                    
                    st.markdown("**Key Features:**")
                    for feature in role_info['features']:
                        st.write(f"• {feature}")
                
                with col2:
                    st.markdown("**Permissions:**")
                    # Show permissions in a more readable format
                    for perm in role_info['permissions'][:5]:  # Show first 5
                        perm_display = perm.replace('_', ' ').title()
                        st.write(f"✓ {perm_display}")
                    
                    if len(role_info['permissions']) > 5:
                        st.write(f"... and {len(role_info['permissions']) - 5} more")
                    
                    # Visual level indicator
                    st.progress(role_info['level'] / 100)
                    
                    # Special badges
                    if role_info['level'] >= 80:
                        st.success("🌟 Administrative Role")
                    elif role_info['level'] >= 40:
                        st.info("⚙️ Operational Role")
                    elif role_info['level'] >= 30:
                        st.warning("👀 Limited Access Role")
                    else:
                        st.info("📚 Training/View Only")
    
    def show_role_comparison(self):
        """Show role comparison matrix"""
        st.markdown("### 📊 Role Comparison Matrix")
        
        # Create comparison data
        features = [
            'System Configuration',
            'User Management',
            'Create/Edit Moves',
            'Financial Access',
            'Driver Management',
            'View Reports',
            'Upload Documents',
            'Client Data Access',
            'Training Materials'
        ]
        
        # Build comparison matrix
        comparison_data = []
        
        for feature in features:
            row = {'Feature': feature}
            for role_key, role_info in self.roles.items():
                # Check if feature matches any permission
                has_feature = False
                feature_lower = feature.lower().replace(' ', '_')
                
                for perm in role_info['permissions']:
                    if feature_lower in perm or perm in feature_lower:
                        has_feature = True
                        break
                
                # Special cases
                if feature == 'System Configuration' and role_key == 'business_administrator':
                    has_feature = True
                elif feature == 'Training Materials' and role_key == 'trainee':
                    has_feature = True
                elif feature == 'Client Data Access' and role_key == 'client_viewer':
                    has_feature = True
                
                row[role_info['name']] = '✅' if has_feature else '❌'
            
            comparison_data.append(row)
        
        # Display as table
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def show_role_assignment_guide(self):
        """Show guide for role assignment"""
        st.markdown("### 📚 Role Assignment Guide")
        
        with st.expander("When to assign each role", expanded=True):
            st.markdown("""
            **👔 Business Administrator**
            - Company owners and executives
            - System administrators
            - Finance managers
            - Anyone needing full system control
            
            **📋 Operations Coordinator**
            - Dispatch managers
            - Operations supervisors
            - Logistics coordinators
            - Senior dispatchers
            
            **🚛 Driver**
            - Company drivers
            - Owner-operators
            - Contractor drivers
            - Anyone performing deliveries
            
            **🏢 Client Viewer**
            - External customers
            - Partner companies
            - Clients tracking shipments
            - Third-party stakeholders
            
            **👁️ Viewer**
            - Accountants (read-only)
            - Auditors
            - Management (monitoring only)
            - Support staff
            
            **🎓 Trainee**
            - New employees in training
            - Temporary staff learning system
            - Interns
            - Anyone in onboarding process
            """)
    
    def get_role_based_menu(self, user_role):
        """Get menu items based on user role"""
        menus = {
            'business_administrator': [
                "📊 Dashboard",
                "🚛 Trailers",
                "➕ Create Move",
                "👤 Drivers",
                "💰 Payments",
                "📈 Reports",
                "⚙️ System Admin",
                "🤖 IT Support (Vernon)",
                "🎓 Walkthrough"
            ],
            'operations_coordinator': [
                "📊 Dashboard",
                "🚛 Trailers",
                "➕ Create Move",
                "👤 Drivers",
                "💰 Payments",
                "📸 Upload POD",
                "📈 Reports",
                "🎓 Walkthrough"
            ],
            'driver': [
                "📱 My Moves",
                "📸 Upload POD",
                "💰 My Earnings",
                "📍 Route Info",
                "🟢 My Availability"
            ],
            'client_viewer': [
                "📋 Move Status",
                "🚛 Trailer Tracking",
                "📄 Documents",
                "📊 Reports"
            ],
            'viewer': [
                "📊 Dashboard",
                "📈 Progress Dashboard",
                "🚛 Trailer Status"
            ],
            'trainee': [
                "🎓 Training Mode",
                "📚 Learning Center",
                "🎯 Practice Tasks",
                "📊 Demo Dashboard"
            ]
        }
        
        return menus.get(user_role, ["📊 Dashboard"])
    
    def enforce_permission(self, user_role, action):
        """Enforce permission check with user feedback"""
        if not self.check_permission(user_role, action):
            st.error(f"""
            ⛔ **Access Denied**
            
            Your role ({self.roles[user_role]['name']}) does not have permission to: {action.replace('_', ' ').title()}
            
            Please contact your administrator if you need access to this feature.
            """)
            return False
        return True

def show_complete_roles_page():
    """Main entry point for roles page"""
    role_system = CompleteRoleSystem()
    
    st.title("🎭 System Roles & Permissions")
    
    tabs = st.tabs(["📋 Overview", "📊 Comparison", "📚 Assignment Guide"])
    
    with tabs[0]:
        role_system.show_roles_overview()
    
    with tabs[1]:
        role_system.show_role_comparison()
    
    with tabs[2]:
        role_system.show_role_assignment_guide()
    
    # Show current user's role
    if 'user_role' in st.session_state:
        st.divider()
        current_role = st.session_state['user_role']
        role_info = role_system.get_role_info(current_role)
        
        if role_info:
            st.info(f"""
            **Your Current Role:** {role_info['icon']} {role_info['name']}
            
            You have access to {len(role_info['permissions'])} system permissions.
            """)

# Export for use in main app
__all__ = ['CompleteRoleSystem', 'show_complete_roles_page']