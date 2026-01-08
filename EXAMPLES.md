# Terminal Output Examples

This document shows example terminal outputs for various commands.

## Dashboard View

```bash
$ python cli.py dashboard
```

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

## Adding a Project (Interactive)

```bash
$ python cli.py add
```

```
Add New Supabase Project

Project name [my-project]: production-db
Supabase URL [https://xxxxx.supabase.co]: https://abcdefghijk.supabase.co
API key (anon or service_role): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Keepalive method [rpc/table] (rpc): rpc

✓ Project added successfully (ID: 1)
  Name: production-db
  Method: rpc
  Enabled: Yes
```

## Adding a Project (Non-Interactive)

```bash
$ python cli.py add \
  --name "staging-db" \
  --url "https://xyz123.supabase.co" \
  --key "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  --method table \
  --table users
```

```
Add New Supabase Project

✓ Project added successfully (ID: 2)
  Name: staging-db
  Method: table
  Enabled: Yes
```

## Running Keepalive (Verbose)

```bash
$ python cli.py run
```

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

## Running Keepalive (Quiet)

```bash
$ python cli.py run --quiet
```

```
2026-01-08 10:30:00 [INFO] ============================================================
2026-01-08 10:30:00 [INFO] Supabase Keepalive - Starting
2026-01-08 10:30:00 [INFO] ============================================================
2026-01-08 10:30:00 [INFO] Processing: production-db
2026-01-08 10:30:01 [INFO] Processing: staging-db
2026-01-08 10:30:02 [INFO] ============================================================
2026-01-08 10:30:02 [INFO] Summary: 2/2 succeeded, 0/2 failed
2026-01-08 10:30:02 [INFO] ============================================================
```

## Show Project Details

```bash
$ python cli.py show 1
```

```
Project Details: production-db

Field              Value
ID                 1
Name               production-db
URL                https://abcdefghijk.supabase.co
API Key            eyJh...xyz9
Keepalive Method   rpc
Enabled            Yes
Last Status        SUCCESS
Last Checked       2026-01-08T10:30:01
Created At         2026-01-08T09:00:00
Updated At         2026-01-08T10:30:01
```

## Enable/Disable Projects

```bash
$ python cli.py disable 3
```

```
✓ Project 'dev-db' disabled
```

```bash
$ python cli.py enable 3
```

```
✓ Project 'dev-db' enabled
```

## Delete Project

```bash
$ python cli.py delete 3
```

```
Delete project 'dev-db' (ID: 3)? [y/N]: y
✓ Project 'dev-db' deleted
```

```bash
$ python cli.py delete 3 --force
```

```
✓ Project 'dev-db' deleted
```

## Migration from v1.0

```bash
$ python migrate.py
```

```
Supabase Keepalive Migration
Migrating from projects.py to SQLite database

Found 3 project(s) to migrate

✓ Migrated: production-db (ID: 1)
✓ Migrated: staging-db (ID: 2)
✓ Migrated: dev-db (ID: 3)

Migration Complete
  Migrated: 3
  Skipped:  0
  Errors:   0

✓ Projects successfully migrated to SQLite

Next steps:
  1. View projects: python cli.py dashboard
  2. Test keepalive: python cli.py run
  3. Backup old config: mv projects.py projects.py.bak
```

## Error Scenarios

### No Projects Found

```bash
$ python cli.py dashboard
```

```
No projects found. Use 'add' command to add projects.
```

### Project Not Found

```bash
$ python cli.py show 999
```

```
Project 999 not found.
```

### Connection Error Example

```bash
$ python cli.py run
```

```
============================================================
Supabase Keepalive - Starting
============================================================
2026-01-08 10:30:00 [INFO] Processing: broken-db
2026-01-08 10:30:05 [ERROR] broken-db: FAILED - Connection timeout
============================================================
2026-01-08 10:30:05 [INFO] Summary: 0/1 succeeded, 1/1 failed
============================================================
```

## CLI Help

```bash
$ python cli.py --help
```

```
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  Supabase Keepalive - Terminal-based project management

Options:
  --help  Show this message and exit.

Commands:
  add        Add a new Supabase project.
  dashboard  Show project status dashboard.
  delete     Delete a project permanently.
  disable    Disable a project.
  enable     Enable a project.
  list       Alias for dashboard command.
  run        Run keepalive for all enabled projects.
  show       Show detailed information for a project.
  version    Show version information.
```

## Cron Log Output

Example from `/var/log/sb-keepalive.log`:

```
2026-01-08 03:00:01 [INFO] ============================================================
2026-01-08 03:00:01 [INFO] Supabase Keepalive - Starting
2026-01-08 03:00:01 [INFO] ============================================================
2026-01-08 03:00:01 [INFO] Processing: production-db
2026-01-08 03:00:02 [INFO] production-db: SUCCESS (rpc)
2026-01-08 03:00:02 [INFO] Processing: staging-db
2026-01-08 03:00:03 [INFO] staging-db: SUCCESS (table: users)
2026-01-08 03:00:03 [INFO] ============================================================
2026-01-08 03:00:03 [INFO] Summary: 2/2 succeeded, 0/2 failed
2026-01-08 03:00:03 [INFO] ============================================================
```
