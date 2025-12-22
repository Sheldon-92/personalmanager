# PersonalManager v0.5.0 Deployment Guide

**Version**: 0.5.0
**Release Date**: September 18, 2025
**Deployment Type**: Local Installation / GitHub Release

## 🎯 Deployment Overview

PersonalManager v0.5.0 follows a **local-first architecture** with multiple deployment options to suit different user needs. This guide covers all deployment scenarios from development to production use.

## 📦 Available Distribution Formats

### 1. Python Wheel Package
```
personal_manager-0.5.0-py3-none-any.whl (824KB / 844,099 bytes)
```
- **Use Case**: Direct pip installation
- **Advantages**: Fast installation, dependency resolution
- **Target**: End users, automated deployments

### 2. Source Distribution
```
personal_manager-0.5.0.tar.gz (712KB / 728,657 bytes)
```
- **Use Case**: Source inspection, custom builds
- **Advantages**: Full source access, compilation control
- **Target**: Developers, security audits

*Note: Sizes verified on 2025-09-18T15:10:00-08:00 via `ls -lh dist/*.whl dist/*.tar.gz`*

### 3. Local Development Setup
```
git clone + poetry install
```
- **Use Case**: Development, customization, latest features
- **Advantages**: Full repository access, easy updates
- **Target**: Power users, contributors

## 🚀 Deployment Methods

### Method 1: Local Project Installation (Recommended)

**Best for**: Most users, production use, guaranteed compatibility

```bash
# 1. Clone the repository
git clone https://github.com/Sheldon-92/personalmanager.git
cd personal-manager

# 2. Verify version
git checkout v0.5.0

# 3. Use local launcher (no installation required)
./bin/pm-local --version
# Output: PersonalManager v0.5.0

# 4. First-time setup
./bin/pm-local setup

# 5. Test functionality
./bin/pm-local today
./bin/pm-local ai suggest
```

**Advantages**:
- ✅ No Python environment conflicts
- ✅ All dependencies managed automatically
- ✅ Easy updates via git pull
- ✅ Full feature compatibility
- ✅ Works with any Python 3.9+

### Method 2: Poetry Installation (Development)

**Best for**: Developers, contributors, customization

```bash
# 1. Clone and enter directory
git clone https://github.com/Sheldon-92/personalmanager.git
cd personal-manager

# 2. Install with Poetry
poetry install

# 3. Activate environment and setup
poetry shell
poetry run pm setup

# 4. Use within Poetry environment
poetry run pm --version
poetry run pm today
```

**Advantages**:
- ✅ Full development environment
- ✅ Isolated dependencies
- ✅ Easy testing and debugging
- ✅ Contributing workflow ready

### Method 3: Direct Package Installation

**Best for**: System-wide installation, CI/CD, containers

```bash
# Option A: From wheel file
pip install personal_manager-0.5.0-py3-none-any.whl

# Option B: From source
pip install personal_manager-0.5.0.tar.gz

# Option C: From GitHub release (future)
pip install https://github.com/Sheldon-92/personalmanager/releases/download/v0.5.0/personal_manager-0.5.0-py3-none-any.whl

# Verify installation
pm --version
pm setup
```

**Advantages**:
- ✅ System-wide availability
- ✅ Standard Python packaging
- ✅ CI/CD friendly
- ✅ Container deployments

## 🛠️ Environment Requirements

### System Requirements
```yaml
Python: ">=3.9"
OS: macOS, Linux (Windows compatibility in progress)
Memory: 512MB available RAM
Storage: 100MB + user data
Architecture: x86_64, arm64 (Apple Silicon)
```

### Dependency Stack
```toml
# Core Framework
python = "^3.9"
click = "^8.1.7"
rich = "^13.6.0"
typer = "^0.9.0"

# Data Processing & AI
pydantic = "^2.4.2"
PyYAML = "^6.0.1"
numpy = "<2.0.0"
pandas = "^2.3.2"
scipy = "<1.10"
scikit-learn = "<1.2"

# Integrations
anthropic = "^0.3.11"
google-api-python-client = "^2.181.0"
structlog = "^23.1.0"
watchdog = "^3.0.0"
```

### Development Dependencies
```toml
# Code Quality
black = "^23.9.1"
isort = "^5.12.0"
flake8 = "^6.1.0"
mypy = "^1.6.0"

# Testing
pytest = "^7.4.2"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.1"
```

## 🔧 Configuration & Setup

### Initial Setup Process
```bash
# 1. Run setup wizard (any deployment method)
pm setup

# 2. Verify core functionality
pm doctor

# 3. Check integrations
pm integrations status

# 4. Test AI features (requires historical data)
pm ai suggest
```

### Configuration Files
```
~/.pm/
├── config.yaml          # Main configuration
├── credentials.json     # API credentials (encrypted)
├── personal_manager.db  # Local database
├── sessions/           # Session data
├── projects/          # Project definitions
└── logs/             # Application logs
```

### Environment Variables
```bash
# Optional: Override default paths
export PM_CONFIG_DIR="~/.pm"
export PM_DB_PATH="~/.pm/personal_manager.db"
export PM_LOG_LEVEL="INFO"

# Optional: API keys (if using external integrations)
export ANTHROPIC_API_KEY="your-key-here"
export GOOGLE_CREDENTIALS_PATH="~/.pm/credentials.json"
```

## 🔄 Migration & Upgrades

### From Previous Versions (v0.1.0 - v0.4.x)

```bash
# 1. Backup existing data (recommended)
cp ~/.pm/personal_manager.db ~/.pm/personal_manager.db.backup

# 2. Update to v0.5.0
git pull origin main
git checkout v0.5.0

# 3. Run migration script
python scripts/run_migration.py

# 4. Verify upgrade
./bin/pm-local --version
./bin/pm-local doctor

# 5. Test new features
./bin/pm-local ai suggest
./bin/pm-local session list
```

### Migration Safety
- ✅ **Fully backward compatible** - no breaking changes
- ✅ **Reversible migration** - rollback capability
- ✅ **Data preservation** - all existing data maintained
- ✅ **Zero downtime** - existing workflows continue working

## 📊 Performance Tuning

### Database Optimization
```bash
# Run after migration for optimal performance
pm database optimize

# Verify performance
pm database stats
```

### Memory Configuration
```yaml
# ~/.pm/config.yaml
performance:
  max_memory_usage: "512MB"
  cache_size: "64MB"
  background_tasks: true
  ai_batch_size: 100
```

### AI Performance Settings
```yaml
# ~/.pm/config.yaml
ai:
  recommendation_cache_ttl: 300  # 5 minutes
  pattern_analysis_interval: 3600  # 1 hour
  energy_prediction_window: 7  # days
  min_data_points: 50  # for reliable AI
```

## 🔒 Security Configuration

### Data Protection
```yaml
# ~/.pm/config.yaml
security:
  encrypt_credentials: true
  audit_logging: true
  session_timeout: 3600
  backup_encryption: true
```

### Network Security
```yaml
# ~/.pm/config.yaml
network:
  allow_external_apis: false  # Local-first mode
  tls_verify: true
  timeout_seconds: 30
```

### Privacy Settings
```yaml
# ~/.pm/config.yaml
privacy:
  data_collection: false
  telemetry: false
  crash_reporting: false
  analytics: false
```

## 🐳 Container Deployment

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY dist/personal_manager-0.5.0-py3-none-any.whl .
RUN pip install personal_manager-0.5.0-py3-none-any.whl

# Create data volume
VOLUME ["/data"]
ENV PM_CONFIG_DIR=/data

ENTRYPOINT ["pm"]
CMD ["--help"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  personal-manager:
    build: .
    volumes:
      - pm_data:/data
    environment:
      - PM_CONFIG_DIR=/data
    stdin_open: true
    tty: true

volumes:
  pm_data:
```

## 🏭 Production Deployment

### System Service (Linux)
```ini
# /etc/systemd/system/personal-manager.service
[Unit]
Description=PersonalManager Background Service
After=network.target

[Service]
Type=simple
User=pm-user
WorkingDirectory=/opt/personal-manager
ExecStart=/opt/personal-manager/bin/pm-local monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Automation & Monitoring
```bash
# Health check script
#!/bin/bash
pm doctor --json | jq '.status' | grep -q "healthy" || exit 1

# Backup script
#!/bin/bash
tar -czf ~/.pm/backups/pm-backup-$(date +%Y%m%d).tar.gz ~/.pm/
```

## 🧪 Testing Deployment

### Verification Checklist
```bash
# 1. Basic functionality
pm --version                    # Version check
pm doctor                      # System health
pm today                       # Core features

# 2. AI features
pm ai suggest                  # AI recommendations
pm ai analyze                  # Pattern analysis

# 3. Session management
pm session start test         # Session tracking
pm session end               # Session completion

# 4. Integration tests
pm integrations status        # External services
pm sync calendar             # Google integration

# 5. Performance tests
time pm ai suggest           # Response time <500ms
pm database stats           # Database health
```

### Load Testing
```bash
# Simulate heavy usage
for i in {1..100}; do
    pm session start "test-$i"
    sleep 1
    pm session end
done

# Check performance impact
pm performance report
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Python Version Conflicts
```bash
# Error: Python version too old
# Solution: Use pyenv or conda
pyenv install 3.11
pyenv local 3.11
```

#### 2. Dependency Conflicts
```bash
# Error: Package version conflicts
# Solution: Use virtual environment
python -m venv pm-env
source pm-env/bin/activate
pip install personal_manager-0.5.0-py3-none-any.whl
```

#### 3. Permission Issues
```bash
# Error: Permission denied
# Solution: Fix directory permissions
chmod 755 ~/.pm
chmod 644 ~/.pm/personal_manager.db
```

#### 4. AI Features Not Working
```bash
# Error: Insufficient data for AI
# Solution: Use system for 7+ days or import historical data
pm data import --source previous_version.db
```

### Log Analysis
```bash
# Check application logs
tail -f ~/.pm/logs/application.log

# Enable debug logging
PM_LOG_LEVEL=DEBUG pm ai suggest

# System diagnostics
pm doctor --verbose
```

## 📞 Support & Maintenance

### Support Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Community support and questions
- **Documentation**: Complete guides in `/docs/` directory
- **Email**: Enterprise support available

### Maintenance Schedule
- **Daily**: Automated backup verification
- **Weekly**: Performance monitoring and optimization
- **Monthly**: Security updates and dependency refreshes
- **Quarterly**: Major feature releases and architecture reviews

### Update Strategy
```bash
# Check for updates
git fetch --tags
git tag -l | grep v0 | tail -5

# Update to latest
git checkout v0.5.1  # when available
python scripts/run_migration.py
```

## 🎯 Success Metrics

### Performance Targets
- ✅ AI recommendations: <500ms response time
- ✅ Session operations: <100ms latency
- ✅ Database queries: <50ms for simple operations
- ✅ Memory usage: <512MB baseline, <1GB peak

### Reliability Targets
- ✅ Uptime: 99.9% (local application)
- ✅ Data integrity: 100% (with backup verification)
- ✅ Migration success: 100% backward compatibility
- ✅ Performance degradation: <5% after migration

---

**Deployment Guide Version**: 1.0
**Compatible With**: PersonalManager v0.5.0
**Last Updated**: September 18, 2025
**Prepared By**: Claude (AI Assistant)

For additional support, consult the complete documentation suite in `/docs/` or reach out through our support channels.