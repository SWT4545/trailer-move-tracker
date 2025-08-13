"""
Update all domain references to smithwilliamstrucking.com
"""

import os
import re

def update_domain_in_files():
    """Update all email domains to smithwilliamstrucking.com"""
    
    # Files to update
    files_to_update = [
        'vernon_it_personality.py',
        'add_driver_role_to_brandon.py',
        'create_driver_profile.py',
        'create_test_driver.py',
        'app_broken.py',
        'app_complete.py',
        'show_settings.py',
        'training_system.py'
    ]
    
    old_domain = '@smithwilliams.com'
    new_domain = '@smithwilliamstrucking.com'
    
    updates_made = 0
    
    for filename in files_to_update:
        if os.path.exists(filename):
            try:
                # Read file
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count occurrences
                occurrences = content.count(old_domain)
                
                if occurrences > 0:
                    # Replace domain
                    updated_content = content.replace(old_domain, new_domain)
                    
                    # Write back
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    print(f"Updated {filename}: {occurrences} domain references changed")
                    updates_made += occurrences
                else:
                    print(f"  {filename}: No updates needed")
                    
            except Exception as e:
                print(f"Error updating {filename}: {e}")
        else:
            print(f"  {filename}: File not found")
    
    print(f"\n{'='*50}")
    print(f"Total updates made: {updates_made}")
    print(f"Domain updated to: smithwilliamstrucking.com")
    print(f"{'='*50}")
    
    return updates_made > 0

if __name__ == "__main__":
    print("Updating domain references to smithwilliamstrucking.com")
    print("="*50)
    
    if update_domain_in_files():
        print("\nDomain update complete!")
        print("\nUpdated email addresses now use:")
        print("  • vernon.it@smithwilliamstrucking.com")
        print("  • brandon@smithwilliamstrucking.com")
        print("  • support@smithwilliamstrucking.com")
        print("  • billing@smithwilliamstrucking.com")
        print("  • And all other @smithwilliamstrucking.com addresses")
    else:
        print("\nNo updates were needed.")