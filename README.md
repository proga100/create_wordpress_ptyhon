# WordPress Site Creator

A Python script to automatically create WordPress sites in a Laravel Herd environment on Windows.

## Features

- Downloads and extracts the latest WordPress version
- Creates and configures MySQL database
- Generates secure WordPress salts
- Registers the site with Laravel Herd
- Secures the site with SSL certificate
- Automatically installs WordPress via WP-CLI (with fallback methods)

## Requirements

- Python 3.6+
- Laravel Herd installed
- MySQL database server
- PHP installed and in PATH
- Required Python packages:
  - mysql-connector-python
  - requests

## Installation

1. Clone or download this repository
2. Install required Python packages:

```bash
pip install mysql-connector-python requests
```

3. Install WP-CLI (optional, the script can download it if needed):

```bash
mkdir C:\wp-cli
curl -o C:\wp-cli\wp-cli.phar https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
```

## Usage

### Basic Usage

```bash
python create_wordpress.py my-site
```

This will create a WordPress site at `D:\domains\my-site` with default settings.

### Advanced Usage

```bash
python create_wordpress.py my-site --title="My Awesome Site" --admin-user="admin" --admin-pass="secure_password" --admin-email="admin@example.com" --wp-path="D:\custom\path"
```

### Available Options

- `site_name`: Name of the site (required)
- `--wp-path`: Base path for WordPress sites (default: D:\domains)
- `--db-host`: Database host (default: localhost)
- `--db-user`: Database username (default: root)
- `--db-pass`: Database password (default: elcana100)
- `--title`: WordPress site title (default: WordPress)
- `--admin-user`: WordPress admin username (default: admin)
- `--admin-pass`: WordPress admin password (default: elcana100)
- `--admin-email`: WordPress admin email (default: admin@example.com)

## Configuration

The script uses the following default configuration variables:

```python
WP_PATH = "D:\\domains"  # Windows path for domains directory
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "elcana100"
SITE_TITLE = "WordPress"
ADMIN_USER = "admin"
ADMIN_PASS = "elcana100"
ADMIN_EMAIL = "admin@example.com"
```

You can override these defaults in two ways:
1. Using command-line arguments (recommended) as shown in the Usage section
2. Modifying the script directly by changing these variables at the top of the file

These settings determine:
- Where WordPress sites are stored (`WP_PATH`)
- Database connection details (`DB_HOST`, `DB_USER`, `DB_PASS`)
- WordPress site configuration (`SITE_TITLE`, `ADMIN_USER`, `ADMIN_PASS`, `ADMIN_EMAIL`)

## Troubleshooting

### PHP Not Found

If you encounter errors about PHP not being found:

1. Make sure PHP is installed and in your PATH
2. Alternatively, edit the script to use the full path to your PHP executable:
   ```python
   php_path = "C:/path/to/your/php.exe"
   ```

### WP-CLI 'sh' Error

If you see errors about 'sh' not being recognized:

1. The script automatically detects and fixes this issue by creating a fixed version of wp.bat
2. If issues persist, you can manually install Git Bash which provides 'sh' on Windows
3. Alternatively, complete the WordPress installation manually using the WordPress web installer

### Database Connection Errors

1. Verify your MySQL credentials
2. Make sure MySQL server is running
3. Check for database name conflicts

## Contact & Support

This WordPress automation tool was created by Rusty.

For WordPress development, site creation, or customization services:
- Email: tutyou1972@gmail.com
- LinkedIn: [https://www.linkedin.com/in/rustywordpress/](https://www.linkedin.com/in/rustywordpress/)

Feel free to reach out for professional WordPress development services or custom modifications to this tool.

## License

This project is open source and available under the MIT License. 