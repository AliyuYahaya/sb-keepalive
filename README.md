# Supabase Keepalive v2.0

A terminal-based management tool for keeping multiple Supabase free-tier databases active.

## What's New in v2.0

- SQLite-backed project management (no more config files)
- Terminal dashboard with Rich tables
- Interactive CLI for project management
- Status tracking and history
- Simple, headless, SSH-friendly

## Features

- Manage unlimited Supabase projects from the terminal
- View project status in a clean table format
- Sequential keepalive execution (low memory footprint)
- SQLite storage for configuration and history
- No web UI, no daemons, no background processes
- Works great on 1GB RAM VPS

## Requirements

- Ubuntu Server (or any Linux with Python 3.8+)
- Python 3.8+
- SSH access

## Project Structure

```
sb-keepalive/
├── app/
│   ├── __init__.py       # Package initialization
│   ├── db.py             # SQLite database operations
│   ├── models.py         # Data models
│   ├── keepalive.py      # Keepalive engine
│   └── dashboard.py      # Terminal dashboard
├── data/
│   └── sb.db             # SQLite database (auto-created)
├── cli.py                # CLI entry point
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Installation

### 1. Upload to Server

```bash
# Option A: Using git
git clone <your-repo-url> /opt/sb-keepalive
cd /opt/sb-keepalive

# Option B: Upload directly
scp -r sb-keepalive/ user@your-server:/opt/
ssh user@your-server
cd /opt/sb-keepalive
```

### 2. Setup Python Environment

```bash
# Update system
sudo apt update

# Install Python 3 and venv if not installed
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Make CLI Executable (Optional)

```bash
chmod +x cli.py
```

## Usage

All commands assume you're in the virtual environment:

```bash
source venv/bin/activate
```

### Dashboard - View Projects

```bash
# Show all projects
python cli.py dashboard

# Show only enabled projects
python cli.py dashboard --enabled
```

**Example Output:**

```
┏━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ ID ┃ Name           ┃ Enabled ┃ Method     ┃ Last Status   ┃ Last Checked        ┃
┡━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│  1 │ production-db  │ ✓ Yes   │ RPC        │ SUCCESS       │ 2h ago              │
│  2 │ staging-db     │ ✓ Yes   │ Table:users│ SUCCESS       │ 2h ago              │
│  3 │ dev-db         │ ✗ No    │ RPC        │ FAILED: ...   │ 1 day ago           │
└────┴────────────────┴─────────┴────────────┴───────────────┴─────────────────────┘

Total: 3 projects (2 enabled, 1 disabled)
```

### Add a Project

```bash
# Interactive mode (recommended)
python cli.py add

# Non-interactive mode
python cli.py add \
  --name "my-project" \
  --url "https://xxxxx.supabase.co" \
  --key "your-anon-or-service-key" \
  --method rpc

# Add with table method
python cli.py add \
  --name "my-project" \
  --url "https://xxxxx.supabase.co" \
  --key "your-key" \
  --method table \
  --table users
```

**Interactive Example:**

```
Add New Supabase Project

Project name [my-project]: production-db
Supabase URL [https://xxxxx.supabase.co]: https://abcdef.supabase.co
API key (anon or service_role): eyJhbGc...
Keepalive method [rpc/table] (rpc): rpc

✓ Project added successfully (ID: 1)
  Name: production-db
  Method: rpc
  Enabled: Yes
```

### Run Keepalive

```bash
# Run keepalive for all enabled projects
python cli.py run

# Quiet mode (minimal output)
python cli.py run --quiet
```

**Example Output:**

```
============================================================
Supabase Keepalive - Starting
============================================================
2026-01-08 10:30:00 [INFO] Processing: production-db
2026-01-08 10:30:01 [INFO] production-db: SUCCESS (rpc)
2026-01-08 10:30:01 [INFO] Processing: staging-db
2026-01-08 10:30:02 [INFO] staging-db: SUCCESS (table: users)
============================================================
2026-01-08 10:30:02 [INFO] Summary: 2/2 succeeded, 0/2 failed
============================================================
```

### Enable/Disable Projects

```bash
# Enable a project
python cli.py enable 1

# Disable a project
python cli.py disable 1
```

### Show Project Details

```bash
# Show detailed information for a project
python cli.py show 1
```

**Example Output:**

```
Project Details: production-db

Field              Value
ID                 1
Name               production-db
URL                https://abcdef.supabase.co
API Key            eyJh...xyz9
Keepalive Method   rpc
Enabled            Yes
Last Status        SUCCESS
Last Checked       2026-01-08T10:30:01
Created At         2026-01-08T09:00:00
Updated At         2026-01-08T10:30:01
```

### Delete a Project

```bash
# Delete with confirmation
python cli.py delete 1

# Force delete (skip confirmation)
python cli.py delete 1 --force
```

### List Projects

```bash
# Alias for dashboard
python cli.py list

# Show only enabled
python cli.py list --enabled
```

### Version

```bash
python cli.py version
```

## Deployment with Cron

### Setup Cron Job

```bash
# Edit crontab
crontab -e

# Add one of these entries:
```

**Option 1: Every 6 hours**

```cron
0 */6 * * * /opt/sb-keepalive/venv/bin/python /opt/sb-keepalive/cli.py run --quiet >> /var/log/sb-keepalive.log 2>&1
```

**Option 2: Twice daily (9 AM and 9 PM)**

```cron
0 9,21 * * * /opt/sb-keepalive/venv/bin/python /opt/sb-keepalive/cli.py run --quiet >> /var/log/sb-keepalive.log 2>&1
```

**Option 3: Daily at 3 AM**

```cron
0 3 * * * /opt/sb-keepalive/venv/bin/python /opt/sb-keepalive/cli.py run --quiet >> /var/log/sb-keepalive.log 2>&1
```

### Setup Logging

```bash
# Create log file
sudo touch /var/log/sb-keepalive.log
sudo chown $USER:$USER /var/log/sb-keepalive.log

# View logs
tail -f /var/log/sb-keepalive.log

# View last 50 lines
tail -n 50 /var/log/sb-keepalive.log

# Search for failures
grep FAILED /var/log/sb-keepalive.log
```

## Keepalive Methods

### RPC Method (Recommended)

Calls a custom PostgreSQL function named `keepalive()`.

**Setup:**

1. Go to your Supabase SQL Editor
2. Create the function:

```sql
CREATE OR REPLACE FUNCTION keepalive()
RETURNS text AS $$
BEGIN
  RETURN 'alive';
END;
$$ LANGUAGE plpgsql;
```

3. Set method to `rpc` when adding project

**Advantages:**
- Clean server logs
- Explicit purpose
- Minimal overhead

### Table Method

Executes a simple `SELECT` query on a specified table.

```bash
python cli.py add --method table --table users
```

The script will run: `SELECT id FROM users LIMIT 1`

**Advantages:**
- No custom function needed
- Works with any existing table

### Fallback Method

If the primary method fails, the script automatically falls back to a basic connectivity check.

## Database Schema

SQLite database located at `data/sb.db`:

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    api_key TEXT NOT NULL,
    keepalive_method TEXT DEFAULT 'rpc',
    table_name TEXT DEFAULT NULL,
    enabled INTEGER DEFAULT 1,
    last_status TEXT DEFAULT NULL,
    last_checked TEXT DEFAULT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_enabled ON projects(enabled);
CREATE INDEX idx_name ON projects(name);
```

## Migration from v1.0

If you're upgrading from the old `projects.py` config file:

### Option 1: Use Migration Script

```bash
python migrate.py
```

This will read your old `projects.py` and import all projects into SQLite.

### Option 2: Manual Migration

```bash
# Activate environment
source venv/bin/activate

# Add each project manually
python cli.py add
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

Make sure you're running from the project root directory and the virtual environment is activated:

```bash
cd /opt/sb-keepalive
source venv/bin/activate
python cli.py dashboard
```

### "No projects found"

Add projects using the `add` command:

```bash
python cli.py add
```

### Cron job not running

Check cron logs:

```bash
grep CRON /var/log/syslog
```

Verify the crontab entry:

```bash
crontab -l
```

Test the command manually:

```bash
/opt/sb-keepalive/venv/bin/python /opt/sb-keepalive/cli.py run --quiet
```

### Connection errors

- Verify Supabase URL and API key are correct
- Check internet connectivity: `ping supabase.co`
- Ensure Supabase project is not paused (free tier)
- Check project details: `python cli.py show <id>`

### Database locked errors

SQLite is accessed sequentially, but if you see locking issues:

```bash
# Check for multiple processes
ps aux | grep cli.py

# Kill stuck processes if needed
pkill -f cli.py
```

## Resource Usage

Typical execution on a 1GB RAM DigitalOcean droplet:

- **Memory**: ~40-60MB during execution
- **CPU**: <1% for a few seconds
- **Network**: ~10-50KB per project
- **Execution time**: 1-5 seconds for multiple projects
- **Disk**: ~100KB for database

## Security Best Practices

### File Permissions

```bash
# Restrict database access
chmod 600 data/sb.db

# Restrict directory access
chmod 700 /opt/sb-keepalive
```

### API Keys

- Use `anon` (public) key for minimal permissions
- Only use `service_role` key if necessary
- Rotate keys periodically
- Never commit `data/sb.db` to public repositories

### Server Security

- Use SSH key authentication
- Configure firewall rules
- Keep system updated: `sudo apt update && sudo apt upgrade`
- Use fail2ban for SSH protection

## CLI Reference

```
Commands:
  dashboard              Show project status dashboard
  run                    Run keepalive for all enabled projects
  add                    Add a new Supabase project
  enable <id>            Enable a project
  disable <id>           Disable a project
  delete <id>            Delete a project permanently
  show <id>              Show detailed information for a project
  list                   Alias for dashboard command
  version                Show version information

Options:
  --db PATH              Database path (default: data/sb.db)
  --enabled              Show only enabled projects
  --verbose / --quiet    Verbose or quiet output
  --force                Skip confirmation prompts
  --help                 Show help message
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        cli.py                            │
│                   (Typer CLI Interface)                  │
└──────────────┬──────────────────────────────────────────┘
               │
               ├──────────────> Dashboard (display)
               │                      │
               ├──────────────> KeepaliveEngine (execution)
               │                      │
               └──────────────> Database (SQLite)
                                      │
                                   data/sb.db
```

### Components

- **cli.py**: Command-line interface using Typer
- **app/db.py**: SQLite database operations
- **app/models.py**: Data structures (Project, KeepaliveResult)
- **app/keepalive.py**: Keepalive execution engine
- **app/dashboard.py**: Terminal UI using Rich

## Contributing

This is a minimal, production-focused tool. Keep changes simple and boring.

## License

Use this however you want. No restrictions.

## Support

For issues:

1. Check this README
2. Review logs: `tail -f /var/log/sb-keepalive.log`
3. Test manually: `python cli.py run --verbose`
4. Check project details: `python cli.py show <id>`

---

Built for Ubuntu servers. Designed for simplicity. No unnecessary complexity.
