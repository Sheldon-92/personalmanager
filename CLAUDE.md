# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

PersonalManager is a minimal CLI tool that integrates Google Calendar and Google Tasks for terminal-based schedule and task management.

## Running the Application

```bash
# Primary way to run
./bin/pm-local <command>

# Or direct Python execution
PYTHONPATH=src python3 -m pm.cli.main <command>
```

## Available Commands

| Command | Description |
|---------|-------------|
| `pm today` | View today's schedule and tasks |
| `pm inbox` | View pending tasks |
| `pm sync` | Connect and verify Google account |
| `pm add <title>` | Add a new task |
| `pm cal` | View upcoming calendar |
| `pm version` | Show version |

## Project Structure

```
personal-manager/
├── bin/
│   ├── pm-local          # Main launcher script
│   └── pm-inbox          # Shortcut for inbox
├── src/pm/
│   ├── cli/main.py       # CLI entry (6 commands)
│   ├── core/config.py    # Configuration
│   ├── integrations/     # Google API (auth, calendar, tasks)
│   ├── models/task.py    # Task model
│   └── security/secrets.py
├── docs/
│   └── INDEX.md          # Documentation index
├── README.md
├── PROJECT_STATUS.md
├── pyproject.toml
└── poetry.lock
```

## Development

```bash
# Install dependencies
poetry install

# Run tests
python3 -m pytest

# Format code
black src/
```

## Tech Stack

- Python 3.9+
- Typer (CLI)
- Rich (terminal output)
- Google Calendar/Tasks API
