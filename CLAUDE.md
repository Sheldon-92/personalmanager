# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PersonalManager is an AI-powered personal productivity platform that integrates GTD (Getting Things Done), habit tracking, project management, and smart time-blocking features. It's built as a CLI tool using Python with a modular architecture.

## Development Commands

### Running the Application

The project uses a local launcher script that auto-detects the environment:
```bash
# Primary way to run the application (auto-detects Poetry/Python)
./bin/pm-local <command>

# Direct Python execution (fallback)
PYTHONPATH=src python3 -m pm.cli.main <command>

# Common shortcuts
./bin/pm-briefing       # Generate briefing report
./bin/pm-interactive    # Start interactive mode
./bin/pm-inbox          # View task inbox
./bin/pm-smart          # AI-powered recommendations
```

### Testing

```bash
# Run all tests
python3 -m pytest

# Run specific test file
python3 -m pytest tests/test_<module>.py

# Run with coverage
python3 -m pytest --cov=pm tests/

# Run security tests
python3 -m pytest tests/security/test_security_vectors.py -v

# Run E2E tests
python3 -m pytest tests/test_pm_local_launcher.py -v

# Full test verification suite
./verify_tests.sh
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/
```

### Dependencies

```bash
# Install dependencies using Poetry
poetry install

# Add new dependency
poetry add <package>

# Add dev dependency
poetry add --dev <package>

# Update dependencies
poetry update
```

## Architecture

### Core Module Structure

- `src/pm/cli/` - Command-line interface and command handlers
  - `main.py` - Main entry point with lazy loading for performance
  - `commands/` - Individual command modules (ai, tasks, calendar, etc.)
  - `contracts.py` - JSON output formatting for API integration

- `src/pm/core/` - Core business logic
  - `config.py` - Configuration management
  - `briefing_generator.py` - Report generation
  - `task_manager.py` - Task management logic
  - `services/` - Service layer implementations

- `src/pm/integrations/` - External service integrations
  - `google_auth.py` - Google OAuth authentication
  - `google_calendar.py` - Calendar sync
  - `google_tasks.py` - Tasks synchronization
  - `gmail_processor.py` - Email processing

- `src/pm/models/` - Data models
  - Pydantic-based models for type safety

- `src/pm/sessions/` - Session-based work tracking
  - Focus session management (deep work, pomodoro, etc.)

- `src/pm/projects/` - Project management system
  - 5 project types: Exploratory, Rhythmic, Goal, Iterative, Habitual

- `src/pm/ai/` - AI decision engine
  - Recommendation algorithms
  - Pattern analysis

- `src/pm/plugins/` - Plugin system
  - `loader.py` - Plugin discovery and loading
  - `sdk.py` - Plugin development SDK

### Data Storage

- Uses local JSON files in `~/.personalmanager/` directory
- Project status tracked via `PROJECT_STATUS.md` files
- Configuration in `config/` directory

### Key Design Patterns

1. **Lazy Loading**: Commands are loaded only when needed to improve startup time
2. **JSON API Support**: All commands support `--json` output for scripting
3. **Plugin Architecture**: Extensible through plugin system
4. **Local-First**: All data stored locally, no cloud dependencies required
5. **GTD Integration**: Task management follows GTD methodology

## Important Context

### Session Work Modes

The application supports multiple focus modes:
- `deep_work`: 90-minute focused sessions
- `pomodoro`: 25-minute sprints
- `flow`: Flexible duration
- `review`: 30-minute planning/review
- `planning`: 45-minute strategy sessions

### Project Types

Projects are automatically categorized into:
- **Exploratory**: Research and learning projects
- **Rhythmic**: Regular, predictable work
- **Goal**: Deadline-driven projects
- **Iterative**: Continuous improvement projects
- **Habitual**: Daily maintenance tasks

### AI Features

- Smart task recommendations based on energy levels and patterns
- Productivity pattern analysis
- Break timing recommendations
- Focus session optimization

### Command Conventions

- Commands use typer/click for CLI handling
- Support both interactive and non-interactive modes
- Use `--json` for programmatic output
- Use `--yes`/`--assume-no` for automation

## Testing Strategy

- Unit tests for core business logic
- Integration tests for external services
- E2E tests for CLI commands
- Security tests for input validation
- Performance benchmarks for critical paths

## Configuration Files

- `pyproject.toml` - Poetry configuration and dependencies
- `~/.personalmanager/config.json` - User configuration
- `PROJECT_STATUS.md` - Project status tracking (per project)