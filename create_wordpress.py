import os
import sys
import subprocess
import requests
import zipfile
import io
import time
import random
import string
import mysql.connector
import shutil
import argparse

# Configuration variables for Laravel Herd
WP_PATH = "D:\\domains"  # Windows path for domains directory
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "elcana100"
SITE_TITLE = "WordPress"
ADMIN_USER = "admin"
ADMIN_PASS = "elcana100"
ADMIN_EMAIL = "admin@example.com"

def create_wordpress_site(site_name, wp_path=WP_PATH, db_host=DB_HOST, db_user=DB_USER, db_pass=DB_PASS, 
                         site_title=SITE_TITLE, admin_user=ADMIN_USER, admin_pass=ADMIN_PASS, admin_email=ADMIN_EMAIL):
    """
    Create a fresh WordPress site in Laravel Herd environment
    
    Args:
        site_name: Name of the site (will be used for folder and database name)
        wp_path: Base path for WordPress sites
        db_host: Database host
        db_user: Database username
        db_pass: Database password
        site_title: Title for the WordPress site
        admin_user: WordPress admin username
        admin_pass: WordPress admin password
        admin_email: WordPress admin email
    """
    
    # Define paths - use normpath to handle path separators correctly
    domains_path = os.path.normpath(wp_path)
    site_path = os.path.normpath(os.path.join(domains_path, site_name))
    
    # Check if site directory already exists
    if os.path.exists(site_path):
        print(f"Error: Site '{site_name}' already exists at {site_path}")
        return False
    
    print(f"Creating new WordPress site: {site_name}")
    print("=" * 60)
    
    # Create the site directory
    print(f"Creating directory: {site_path}")
    os.makedirs(site_path, exist_ok=True)
    
    # Download WordPress
    print("Downloading latest WordPress...")
    wp_url = "https://wordpress.org/latest.zip"
    response = requests.get(wp_url, stream=True)
    
    if response.status_code == 200:
        wp_zip = zipfile.ZipFile(io.BytesIO(response.content))
        
        # Extract WordPress
        print("Extracting WordPress files...")
        wp_zip.extractall(site_path)
        
        # Move files from wordpress folder to root
        wordpress_dir = os.path.join(site_path, "wordpress")
        for item in os.listdir(wordpress_dir):
            item_path = os.path.join(wordpress_dir, item)
            dest_path = os.path.join(site_path, item)
            os.rename(item_path, dest_path)
            
        # Remove empty wordpress directory
        os.rmdir(wordpress_dir)
    else:
        print(f"Error downloading WordPress: {response.status_code}")
        return False
    
    # Create database
    db_name = site_name.replace("-", "_")
    print(f"Creating database: {db_name}")
    
    try:
        # Using mysqladmin to create the database
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {db_name}")
    except mysql.connector.Error as e:
        print(f"Error creating database: {e}")
        return False
    
    # Generate salts
    print("Generating security keys...")
    salts_url = "https://api.wordpress.org/secret-key/1.1/salt/"
    try:
        salts = requests.get(salts_url).text
    except:
        # Generate random strings as fallback
        def random_string(length=64):
            chars = string.ascii_letters + string.digits + string.punctuation
            return ''.join(random.choice(chars) for _ in range(length))
            
        salts = "\n".join([
            f"define('AUTH_KEY',         '{random_string()}');",
            f"define('SECURE_AUTH_KEY',  '{random_string()}');",
            f"define('LOGGED_IN_KEY',    '{random_string()}');",
            f"define('NONCE_KEY',        '{random_string()}');",
            f"define('AUTH_SALT',        '{random_string()}');",
            f"define('SECURE_AUTH_SALT', '{random_string()}');",
            f"define('LOGGED_IN_SALT',   '{random_string()}');",
            f"define('NONCE_SALT',       '{random_string()}');"
        ])
    
    # Create wp-config.php
    print("Creating wp-config.php...")
    sample_config_path = os.path.join(site_path, "wp-config-sample.php")
    config_path = os.path.join(site_path, "wp-config.php")
    
    with open(sample_config_path, 'r') as f:
        config_content = f.read()
    
    # Replace database details
    config_content = config_content.replace("database_name_here", db_name)
    config_content = config_content.replace("username_here", db_user)
    config_content = config_content.replace("password_here", db_pass)
    config_content = config_content.replace("localhost", db_host)
    
    # Replace salts - FIX THE ISSUE WITH DUPLICATED CONSTANTS
    salt_pattern = "define( 'AUTH_KEY',         'put your unique phrase here' );"
    salt_section_end = "define( 'NONCE_SALT',       'put your unique phrase here' );"

    # Find starting position of salt definitions
    start_pos = config_content.find(salt_pattern)
    if start_pos >= 0:
        # Find ending position (include the line)
        end_pos = config_content.find(salt_section_end)
        end_pos = config_content.find("\n", end_pos) if end_pos >= 0 else -1
        
        if end_pos >= 0:
            # Replace the entire section
            config_content = config_content[:start_pos] + salts + config_content[end_pos+1:]
        else:
            # Fallback if structure is different
            config_content = config_content.replace(salt_pattern, salts)
    else:
        # Fallback
        config_content = config_content.replace(salt_pattern, salts)
    
    # Write configuration file
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    # Register site with Herd
    print("Registering site with Laravel Herd...")
    try:
        subprocess.run(f'herd park {site_path}', shell=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("Command timed out but may have still completed. Continuing...")
    
    # Secure the site (optional, for HTTPS)
    print("Securing site with SSL certificate...")
    try:
        subprocess.run(f'herd secure {site_name}.test', shell=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("Command timed out but may have still completed. Continuing...")
    
    # Install WordPress via WP-CLI
    print("Completing WordPress installation...")
    try:
        # Check for WP-CLI in composer path
        wp_cli_path = os.path.normpath("D:\\open538\\userdata\\composer\\vendor\\bin\\wp.BAT")
        wp_cli_phar = os.path.normpath("D:\\open538\\userdata\\composer\\vendor\\wp-cli\\wp-cli\\wp-cli.phar")
        
        # Try different WP-CLI options
        if os.path.exists(wp_cli_path):
            wp_cli = wp_cli_path.replace('\\', '\\\\')
            
            # Fix WP-CLI batch file if needed
            try:
                with open(wp_cli_path, 'r') as f:
                    bat_content = f.read()
                    if 'sh "%BIN_TARGET%"' in bat_content:
                        print("Detected 'sh' in WP-CLI batch file. Creating fixed version...")
                        # Create fixed version of batch file
                        fixed_bat_path = os.path.join(os.path.dirname(wp_cli_path), "wp-fixed.bat")
                        with open(fixed_bat_path, 'w') as fw:
                            # Replace 'sh' with 'cmd /c'
                            fixed_content = bat_content.replace('sh "%BIN_TARGET%" %*', 'cmd /c php "%BIN_TARGET%" %*')
                            fw.write(fixed_content)
                        print(f"Created fixed WP-CLI batch file at: {fixed_bat_path}")
                        # Use the fixed version
                        wp_cli = fixed_bat_path.replace('\\', '\\\\')
            except Exception as e:
                print(f"Error fixing WP-CLI batch file: {e}")
        elif os.path.exists(wp_cli_phar):
            wp_cli = f"php {wp_cli_phar.replace('\\', '\\\\')}"
        else:
            wp_cli = shutil.which('wp.bat') or shutil.which('wp') or 'wp'
            
            # Use custom WP-CLI if available
            if os.path.exists("C:\\wp-cli\\wp-cli.phar"):
                wp_cli = 'php "C:\\wp-cli\\wp-cli.phar"'
            
        # Command as a string for Windows compatibility
        install_command = f'"{wp_cli}" core install --url=https://{site_name}.test --title="{site_title}" --admin_user={admin_user} --admin_password={admin_pass} --admin_email={admin_email} --path="{site_path}"'
        print(install_command); exit();
        # Use shell=True for Windows
        try:
            result = subprocess.run(install_command, shell=True, check=False, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print("WP-CLI command timed out. Trying alternative methods...")
            result = subprocess.CompletedProcess(args=install_command, returncode=1, stdout="", stderr="Command timed out")
        
        if result.returncode == 0:
            print("WordPress installation completed successfully!")
        else:
            print(f"WP-CLI error: {result.stderr}")
            
            # Check if this is the "sh not found" error
            if "'sh' is not recognized" in result.stderr:
                print("\nDETECTED 'SH' ERROR - This is a common error on Windows systems")
                print("Command that failed:")
                print(f"  {install_command}")
            
            print("Attempting alternative installation method...")
            
            # Alternative: Create wp-cli.yml file and try again
            with open(os.path.join(site_path, "wp-cli.yml"), "w") as f:
                f.write(f"path: {site_path}\n")
            
            # Try again with simpler command - use cmd.exe explicitly for Windows
            alt_command = f'cd "{site_path}" && cmd /c "{wp_cli}" core install --url=https://{site_name}.test --title="{site_title}" --admin_user={admin_user} --admin_password={admin_pass} --admin_email={admin_email}'
            try:
                alt_result = subprocess.run(alt_command, shell=True, check=False, capture_output=True, text=True, timeout=30)
            except subprocess.TimeoutExpired:
                print("Alternative command timed out. Trying next method...")
                alt_result = subprocess.CompletedProcess(args=alt_command, returncode=1, stdout="", stderr="Command timed out")
            
            if alt_result.returncode != 0:
                # Check for sh error in the alternative command
                if alt_result.stderr and "'sh' is not recognized" in alt_result.stderr:
                    print("\nDETECTED 'SH' ERROR in alternative method - This is a common error on Windows systems")
                    print("Command that failed:")
                    print(f"  {alt_command}")
                
                # Try PowerShell as a last resort
                ps_command = f'powershell -Command "cd \'{site_path}\'; & \'{wp_cli}\' core install --url=https://{site_name}.test --title=\'{site_title}\' --admin_user={admin_user} --admin_password={admin_pass} --admin_email={admin_email}"'
                try:
                    ps_result = subprocess.run(ps_command, shell=True, check=False, capture_output=True, text=True, timeout=30)
                except subprocess.TimeoutExpired:
                    print("PowerShell command timed out.")
                    ps_result = subprocess.CompletedProcess(args=ps_command, returncode=1, stdout="", stderr="Command timed out")
                
                if ps_result.returncode != 0:
                    # Check for sh error in PowerShell method
                    if ps_result.stderr and "'sh' is not recognized" in ps_result.stderr:
                        print("\nDETECTED 'SH' ERROR in PowerShell method - This is a common error on Windows systems")
                        print("Command that failed:")
                        print(f"  {ps_command}")
                    
                    # Try to find the actual wp-cli script to examine it
                    if os.path.exists(wp_cli_path) and wp_cli_path.lower().endswith('.bat'):
                        try:
                            print("\nExamining WP-CLI batch file contents to find the issue:")
                            with open(wp_cli_path, 'r') as f:
                                bat_content = f.read()
                                print(bat_content)
                                # Look for sh in the batch file
                                if 'sh' in bat_content:
                                    print("\nFound 'sh' references in the WP-CLI batch file. This is likely causing the error.")
                        except Exception as e:
                            print(f"Error reading WP-CLI batch file: {e}")
                    
                    # Try using PHP directly to set up WordPress if we can find the script
                    wp_cli_php = os.path.normpath(os.path.join(os.path.dirname(wp_cli_path), "../wp-cli/wp-cli/bin/wp"))
                    if os.path.exists(wp_cli_php):
                        print("\nTrying direct PHP execution method...")
                        php_command = f'php "{wp_cli_php}" core install --url=https://{site_name}.test --title="{site_title}" --admin_user={admin_user} --admin_password={admin_pass} --admin_email={admin_email} --path="{site_path}"'
                        php_result = subprocess.run(php_command, shell=True, check=False)
                        
                        if php_result.returncode == 0:
                            print("WordPress installed successfully using direct PHP method!")
                            return True
                    
                    raise Exception("All installation methods failed")
            
    except Exception as e:
        print(f"Error completing WordPress installation: {e}")
        print("Please complete the installation manually at:")
        print(f"https://{site_name}.test/wp-admin/install.php")
        print("Use the following details:")
        print(f"  Site Title: {site_title}")
        print(f"  Username: {admin_user}")
        print(f"  Password: {admin_pass}")
        print(f"  Email: {admin_email}")
        
        # Solution for the 'sh' not found error
        if "'sh' is not recognized" in str(e):
            print("\nSOLUTION FOR 'SH' ERROR:")
            print("The error is caused by WP-CLI trying to use the 'sh' shell which is not available on Windows.")
            print("Options to fix this:")
            print("1. Install Git Bash which provides 'sh' on Windows")
            print("2. Edit the WP-CLI batch file to use 'cmd' instead of 'sh'")
            print("3. Use the WordPress web installer manually (recommended for Windows users)")
    
    # Done!
    print("\nWordPress site created successfully!")
    print(f"Site URL: https://{site_name}.test")
    print(f"Site directory: {site_path}")
    print(f"Database name: {db_name}")
    
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create a fresh WordPress site in Laravel Herd environment")
    parser.add_argument("site_name", help="Name of the site (will be used for folder and database name)", nargs="?")
    parser.add_argument("--wp-path", default=WP_PATH, help=f"Base path for WordPress sites (default: {WP_PATH})")
    parser.add_argument("--db-host", default=DB_HOST, help=f"Database host (default: {DB_HOST})")
    parser.add_argument("--db-user", default=DB_USER, help=f"Database username (default: {DB_USER})")
    parser.add_argument("--db-pass", default=DB_PASS, help=f"Database password (default: {DB_PASS})")
    parser.add_argument("--title", default=SITE_TITLE, help=f"WordPress site title (default: {SITE_TITLE})")
    parser.add_argument("--admin-user", default=ADMIN_USER, help=f"WordPress admin username (default: {ADMIN_USER})")
    parser.add_argument("--admin-pass", default=ADMIN_PASS, help=f"WordPress admin password (default: {ADMIN_PASS})")
    parser.add_argument("--admin-email", default=ADMIN_EMAIL, help=f"WordPress admin email (default: {ADMIN_EMAIL})")
    
    args = parser.parse_args()
    
    # If site_name wasn't provided as positional argument, prompt for it
    site_name = args.site_name if args.site_name else input("Enter site name: ")
    
    # Create WordPress site with the provided or default arguments
    create_wordpress_site(
        site_name=site_name,
        wp_path=args.wp_path,
        db_host=args.db_host,
        db_user=args.db_user,
        db_pass=args.db_pass,
        site_title=args.title,
        admin_user=args.admin_user,
        admin_pass=args.admin_pass,
        admin_email=args.admin_email
    )