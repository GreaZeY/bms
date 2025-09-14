#!/usr/bin/env python3
"""
BMS Setup Script
This script helps set up the Billing Management System
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("Billing Management System (BMS) Setup")
    print("=" * 50)
    
    # Check if we're in a Frappe environment
    if not os.path.exists("apps"):
        print("Error: This script must be run from the Frappe bench directory")
        sys.exit(1)
    
    # Check if BMS app is already installed
    if os.path.exists("apps/bms"):
        print("BMS app is already installed")
        response = input("Do you want to reinstall? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled")
            sys.exit(0)
    
    # Install the app
    print("\n1. Installing BMS app...")
    if not run_command("bench get-app bms", "Installing BMS app"):
        sys.exit(1)
    
    # Install the app in the site
    print("\n2. Installing BMS in site...")
    site_name = input("Enter site name (default: localhost): ").strip()
    if not site_name:
        site_name = "localhost"
    
    if not run_command(f"bench --site {site_name} install-app bms", f"Installing BMS in site {site_name}"):
        sys.exit(1)
    
    # Create admin user
    print("\n3. Setting up admin user...")
    admin_email = input("Enter admin email (default: admin@example.com): ").strip()
    if not admin_email:
        admin_email = "admin@example.com"
    
    admin_password = input("Enter admin password: ").strip()
    if not admin_password:
        print("Error: Admin password is required")
        sys.exit(1)
    
    # Create admin user
    create_admin_cmd = f"""
    bench --site {site_name} console << EOF
    import frappe
    frappe.connect(site='{site_name}')
    
    # Create admin user if not exists
    if not frappe.db.exists('User', '{admin_email}'):
        user = frappe.new_doc('User')
        user.email = '{admin_email}'
        user.first_name = 'Admin'
        user.last_name = 'User'
        user.new_password = '{admin_password}'
        user.save()
        frappe.db.commit()
        print('Admin user created successfully')
    else:
        print('Admin user already exists')
    
    # Add BMS Admin role
    user = frappe.get_doc('User', '{admin_email}')
    if 'BMS Admin' not in user.get('roles', []):
        user.append('roles', {{'role': 'BMS Admin'}})
        user.save()
        frappe.db.commit()
        print('BMS Admin role added')
    else:
        print('BMS Admin role already exists')
    EOF
    """
    
    if not run_command(create_admin_cmd, "Creating admin user"):
        sys.exit(1)
    
    # Create sample customer
    print("\n4. Creating sample customer...")
    create_customer_cmd = f"""
    bench --site {site_name} console << EOF
    import frappe
    frappe.connect(site='{site_name}')
    
    # Create sample customer if not exists
    if not frappe.db.exists('BMS Customer', 'Sample Customer'):
        customer = frappe.new_doc('BMS Customer')
        customer.customer_name = 'Sample Customer'
        customer.customer_type = 'Individual'
        customer.email = 'sample@example.com'
        customer.phone = '+1-555-0123'
        customer.status = 'Active'
        customer.save()
        frappe.db.commit()
        print('Sample customer created successfully')
    else:
        print('Sample customer already exists')
    EOF
    """
    
    if not run_command(create_customer_cmd, "Creating sample customer"):
        sys.exit(1)
    
    # Start the development server
    print("\n5. Starting development server...")
    print("You can now start the development server with:")
    print(f"bench start --site {site_name}")
    print("\nAccess the system at:")
    print(f"- Admin Dashboard: http://{site_name}:8000/admin_dashboard")
    print(f"- User Dashboard: http://{site_name}:8000/user_dashboard")
    print(f"- Frappe Desk: http://{site_name}:8000")
    print(f"\nLogin credentials:")
    print(f"- Email: {admin_email}")
    print(f"- Password: {admin_password}")
    
    print("\n✓ BMS setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the development server: bench start")
    print("2. Access the admin dashboard to create plans and subscriptions")
    print("3. Create user accounts and assign BMS User role")
    print("4. Test the system with sample data")

if __name__ == "__main__":
    main()
