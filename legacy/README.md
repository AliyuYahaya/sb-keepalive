# Legacy v1.0 Files

This folder contains the original Supabase keepalive implementation (v1.0).

## Files

- `keepalive.py` - Original standalone keepalive script
- `projects.py` - Original static configuration file

## Purpose

These files are kept for:
1. Reference during migration
2. Rollback capability if needed
3. Understanding the original implementation

## Migration

To migrate from these files to v2.0:

```bash
cd ..
python migrate.py
```

This will import all projects from `projects.py` into the SQLite database.

## After Migration

Once you've verified v2.0 works correctly, you can safely delete this folder:

```bash
cd ..
rm -rf legacy/
```

## Using v1.0 Files (Not Recommended)

If you need to use the old script:

```bash
python legacy/keepalive.py
```

Note: You must update the import path in `keepalive.py` if projects.py is in the legacy folder:

```python
# Change this line in keepalive.py:
from projects import PROJECTS
# To:
from legacy.projects import PROJECTS
```

## Recommendation

Use v2.0 instead. It provides all v1.0 functionality plus:
- Project management via CLI
- Status tracking
- Terminal dashboard
- No configuration file editing needed

See the main [README.md](../README.md) for v2.0 documentation.
