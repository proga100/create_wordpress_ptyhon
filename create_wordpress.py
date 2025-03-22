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

def create_wordpress_site(site_name, db_host="localhost", db_user="root", db_pass="elcana100"):
    """
    Create a fresh WordPress site in Laravel Herd environment
    
    Args:
        site_name: Name of the site (will be used for folder and database name)
        db_host: Database host
        db_user: Database username
        db_pass: Database password
    """
    
    # Define paths - use normpath to handle path separators correctly
    domains_path = os.path.normpath("D:\\domains")
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
    subprocess.run(f'herd park {site_path}', shell=True)
    
    # Secure the site (optional, for HTTPS)
    print("Securing site with SSL certificate...")
    subprocess.run(f'herd secure {site_name}.test', shell=True)
    
    # Install WordPress via WP-CLI
    print("Completing WordPress installation...")
    try:
        # Check for WP-CLI in composer path
        wp_cli_path = os.path.normpath("D:\\open538\\userdata\\composer\\vendor\\bin\\wp.BAT")
        wp_cli_phar = os.path.normpath("D:\\open538\\userdata\\composer\\vendor\\wp-cli\\wp-cli\\wp-cli.phar")
        
        # Try different WP-CLI options
        if os.path.exists(wp_cli_path):
            wp_cli = wp_cli_path.replace('\\', '\\\\')
        elif os.path.exists(wp_cli_phar):
            wp_cli = f"php {wp_cli_phar.replace('\\', '\\\\')}"
        else:
            wp_cli = shutil.which('wp.bat') or shutil.which('wp') or 'wp'
        
        # Command as a string for Windows compatibility
        install_command = f'"{wp_cli}" core install --url=https://{site_name}.test --title=WordPress --admin_user=admin --admin_password=elcana100 --admin_email=admin@example.com --path="{site_path}"'
        
        # Use shell=True for Windows
        result = subprocess.run(install_command, shell=True, check=False, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("WordPress installation completed successfully!")
        else:
            print(f"WP-CLI error: {result.stderr}")
            print("Attempting alternative installation method...")
            
            # Alternative: Create wp-cli.yml file and try again
            with open(os.path.join(site_path, "wp-cli.yml"), "w") as f:
                f.write(f"path: {site_path}\n")
            
            # Try again with simpler command - use cmd.exe explicitly for Windows
            alt_command = f'cd "{site_path}" && cmd /c "{wp_cli}" core install --url=https://{site_name}.test --title=WordPress --admin_user=admin --admin_password=elcana100 --admin_email=admin@example.com'
            alt_result = subprocess.run(alt_command, shell=True, check=False)
            
            if alt_result.returncode != 0:
                # Try PowerShell as a last resort
                ps_command = f'powershell -Command "cd \'{site_path}\'; & \'{wp_cli}\' core install --url=https://{site_name}.test --title=WordPress --admin_user=admin --admin_password=elcana100 --admin_email=admin@example.com"'
                ps_result = subprocess.run(ps_command, shell=True, check=False)
                
                if ps_result.returncode != 0:
                    raise Exception("All installation methods failed")
            
    except Exception as e:
        print(f"Error completing WordPress installation: {e}")
        print("Please complete the installation manually at:")
        print(f"https://{site_name}.test/wp-admin/install.php")
        print("Use the following details:")
        print("  Site Title: WordPress")
        print("  Username: admin")
        print("  Password: elcana100")
        print("  Email: admin@example.com")
    
    # Done!
    print("\nWordPress site created successfully!")
    print(f"Site URL: https://{site_name}.test")
    print(f"Site directory: {site_path}")
    print(f"Database name: {db_name}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        site_name = sys.argv[1]
    else:
        site_name = input("Enter site name: ")
    
    create_wordpress_site(site_name)