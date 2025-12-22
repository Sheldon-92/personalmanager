# PersonalManager v0.5.0 - Release Publication Runbook

**Purpose**: Step-by-step guide for completing v0.5.0 release publication
**Last Updated**: 2025-09-18T15:35:00-08:00

## Prerequisites Checklist
- [x] Git tag v0.5.0 pushed to origin
- [x] Build artifacts ready in `dist/` directory
- [x] All documentation files created
- [ ] GitHub repository write access
- [ ] GitHub web access or `gh` CLI installed

---

## 📦 Step 1: Prepare Release Artifacts

### 1.1 Verify Local Files
```bash
# Check artifacts exist and sizes match
ls -lh dist/personal_manager-0.5.0-*
# Expected:
# 824K personal_manager-0.5.0-py3-none-any.whl
# 712K personal_manager-0.5.0.tar.gz

# Verify checksums
shasum -a 256 dist/personal_manager-0.5.0-*
# Expected:
# 44c314b2d5cdad56d182f1cc9be36b20d0b13f11e608434aa50bd5cb29c05a04  whl
# fdf85e5042282fb757de2f1c99270ccd20877d8e69f7e629b8af1eceff2bbdd3  tar.gz
```

### 1.2 Stage Files for Upload
```bash
# Create temporary staging directory
mkdir -p /tmp/v0.5.0-release
cp dist/personal_manager-0.5.0-* /tmp/v0.5.0-release/

# Verify staging
ls -lh /tmp/v0.5.0-release/
```

---

## 🚀 Step 2: Create GitHub Release

### Option A: Using GitHub Web Interface

1. **Navigate to Release Creation Page**:
   ```
   https://github.com/Sheldon-92/personalmanager/releases/new
   ```

2. **Fill Release Form**:

   **Choose a tag**: `v0.5.0` (select from dropdown)

   **Release title**:
   ```
   PersonalManager v0.5.0 - AI-Powered Productivity Platform
   ```

   **Describe this release**:
   ```markdown
   # 🎉 PersonalManager v0.5.0

   A transformative release that evolves our GTD task manager into an **AI-powered productivity companion**.

   ## ✨ Highlights
   - 🤖 **AI Decision Engine**: Get instant "what to work on now" recommendations
   - 📊 **Pattern Analysis**: Discover your unique productivity patterns
   - 💰 **Time Budgets**: Manage time like money with smart alerts
   - ⏰ **Smart Time-Blocking**: Energy-aware scheduling with conflict resolution
   - 🔒 **100% Privacy**: All AI processing happens locally on your machine

   ## 📦 Downloads

   | Package | Size | SHA256 |
   |---------|------|--------|
   | [personal_manager-0.5.0-py3-none-any.whl](https://github.com/Sheldon-92/personalmanager/releases/download/v0.5.0/personal_manager-0.5.0-py3-none-any.whl) | 824KB | `44c314b2d5cdad56d182f1cc9be36b20d0b13f11e608434aa50bd5cb29c05a04` |
   | [personal_manager-0.5.0.tar.gz](https://github.com/Sheldon-92/personalmanager/releases/download/v0.5.0/personal_manager-0.5.0.tar.gz) | 712KB | `fdf85e5042282fb757de2f1c99270ccd20877d8e69f7e629b8af1eceff2bbdd3` |

   ## 🚀 Quick Start

   ```bash
   # Install from wheel
   pip install personal_manager-0.5.0-py3-none-any.whl

   # Or clone and install
   git clone https://github.com/Sheldon-92/personalmanager.git
   cd personal-manager
   git checkout v0.5.0
   poetry install

   # Start using
   pm ai suggest
   ```

   ## 📚 Documentation
   - [Full Release Notes](https://github.com/Sheldon-92/personalmanager/blob/v0.5.0/RELEASE_NOTES_v0.5.0.md)
   - [User Guide](https://github.com/Sheldon-92/personalmanager/blob/v0.5.0/docs/USER_GUIDE_V05.md)
   - [Deployment Guide](https://github.com/Sheldon-92/personalmanager/blob/v0.5.0/DEPLOYMENT_GUIDE_v0.5.0.md)
   - [Architecture Report](https://github.com/Sheldon-92/personalmanager/blob/v0.5.0/docs/reports/v0.5.0_architecture_validation.md)

   ## 📊 Key Metrics
   - **Test Coverage**: 81%
   - **Test Pass Rate**: 95.56%
   - **Performance**: <500ms AI responses
   - **Backward Compatibility**: 100%

   ## 🙏 Thank You
   To our community of early testers and contributors who helped shape this release through 6 intensive sprints.

   ---
   *PersonalManager - Your AI-Powered Productivity Companion*
   ```

3. **Attach Binary Files**:
   - Click "Attach binaries by dropping them here or selecting them"
   - Upload: `personal_manager-0.5.0-py3-none-any.whl`
   - Upload: `personal_manager-0.5.0.tar.gz`

4. **Configure Options**:
   - [x] Set as the latest release
   - [ ] Set as a pre-release (only if testing first)
   - [ ] Create a discussion for this release (optional)

5. **Publish**:
   - Click "Publish release" (or "Save draft" for review)

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI if needed
brew install gh  # macOS
# or: apt install gh  # Linux

# Authenticate
gh auth login

# Create release with files
gh release create v0.5.0 \
  --title "PersonalManager v0.5.0 - AI-Powered Productivity Platform" \
  --notes-file RELEASE_NOTES_v0.5.0.md \
  --latest \
  dist/personal_manager-0.5.0-py3-none-any.whl \
  dist/personal_manager-0.5.0.tar.gz
```

---

## 📋 Step 3: Create v0.5.1 Milestone

1. **Navigate to Milestones**:
   ```
   https://github.com/Sheldon-92/personalmanager/milestones
   ```

2. **Click "New milestone"**

3. **Fill Milestone Details**:
   - **Title**: `v0.5.1 - Patch Release`
   - **Due date**: October 9, 2025
   - **Description**:
   ```markdown
   ## Patch Release Focus

   Addressing critical issues identified in v0.5.0:
   - Datetime timezone consistency (P1)
   - SQL validation layer enhancements (P2)
   - Database connection resource management (P1)

   Target: 2-3 week turnaround
   ```

4. **Create milestone**

---

## 🐛 Step 4: Create v0.5.1 Issues

### Issue Template

For each issue below, go to: `https://github.com/Sheldon-92/personalmanager/issues/new`

### Issue 1: Datetime Timezone
```markdown
**Title**: [v0.5.1] Fix datetime timezone handling in AI modules

**Body**:
## Problem
AI modules use `datetime.now()` without timezone awareness, causing issues for users in different timezones.

## Affected Components
- `src/pm/ai/energy_predictor.py`
- `src/pm/ai/pattern_analyzer.py`
- `src/pm/ai/decision_engine.py`

## Solution
1. Add timezone configuration to settings
2. Update all `datetime.now()` calls to be timezone-aware
3. Add timezone conversion utilities
4. Migrate existing data

## Acceptance Criteria
- [ ] All datetime operations are timezone-aware
- [ ] User can configure timezone in settings
- [ ] Existing data migrated successfully
- [ ] Tests pass in multiple timezone scenarios

**Labels**: bug, priority-1, v0.5.1
**Milestone**: v0.5.1
```

### Issue 2: SQL Validation
```markdown
**Title**: [v0.5.1] Add input validation layer for SQL queries

**Body**:
## Enhancement
While parameterized queries are safe, adding input validation provides defense-in-depth security.

## Implementation Plan
1. Create `src/pm/storage/validators.py`
2. Implement validation functions for all user inputs
3. Add validation decorators to database functions
4. Create comprehensive test suite

## Acceptance Criteria
- [ ] Input validation layer implemented
- [ ] All user inputs validated
- [ ] No performance regression
- [ ] 100% test coverage for validators

**Labels**: enhancement, security, priority-2, v0.5.1
**Milestone**: v0.5.1
```

### Issue 3: Resource Management
```markdown
**Title**: [v0.5.1] Fix database connection resource leaks

**Body**:
## Problem
Some database operations don't use context managers, potentially causing connection leaks.

## Solution
1. Audit all database functions
2. Refactor to use context managers consistently
3. Implement connection pooling
4. Add resource leak detection tests

## Acceptance Criteria
- [ ] All DB operations use context managers
- [ ] Connection pooling implemented
- [ ] No leaks in 24-hour stress test
- [ ] Memory usage stable over time

**Labels**: bug, performance, priority-1, v0.5.1
**Milestone**: v0.5.1
```

---

## ✅ Step 5: Verify Release

### 5.1 Check Release Page
```
https://github.com/Sheldon-92/personalmanager/releases/tag/v0.5.0
```
- Verify title and description
- Check download links work
- Confirm checksums displayed

### 5.2 Test Download
```bash
# Download via curl
curl -L -o test.whl \
  https://github.com/Sheldon-92/personalmanager/releases/download/v0.5.0/personal_manager-0.5.0-py3-none-any.whl

# Verify checksum
shasum -a 256 test.whl
# Should match: 44c314b2d5cdad56d182f1cc9be36b20d0b13f11e608434aa50bd5cb29c05a04

# Clean up
rm test.whl
```

### 5.3 Verify Issues & Milestone
- Check milestone created: https://github.com/Sheldon-92/personalmanager/milestones
- Verify 3 issues created and linked to milestone

---

## 📢 Step 6: Announce Release

### 6.1 Twitter/X
Post content from `docs/releases/MARKETING_SNIPPETS_v0.5.0.md`

### 6.2 LinkedIn
Post professional announcement from marketing snippets

### 6.3 Project README
Update README.md badge (if applicable):
```markdown
[![Release](https://img.shields.io/badge/release-v0.5.0-blue)](https://github.com/Sheldon-92/personalmanager/releases/tag/v0.5.0)
```

---

## 🔍 Troubleshooting

### Issue: Can't upload files
- Check file size limits (GitHub: 2GB per file)
- Verify repository permissions
- Try uploading via `gh` CLI instead

### Issue: Tag not showing
- Ensure tag was pushed: `git push origin v0.5.0`
- Refresh page and check dropdown again

### Issue: Release not marked as latest
- Edit release and check "Set as the latest release"
- Ensure no newer releases exist

---

## 📋 Final Checklist

- [ ] Release created on GitHub
- [ ] Both artifacts uploaded
- [ ] Checksums verified in release notes
- [ ] Download links tested
- [ ] v0.5.1 milestone created
- [ ] 3 issues created and assigned to milestone
- [ ] Release announced on social media
- [ ] Team notified of release

---

## 📧 Support

If you encounter issues during publication:
1. Check GitHub status: https://status.github.com
2. Review GitHub documentation: https://docs.github.com/en/repositories/releasing-projects-on-github
3. Contact repository maintainer

---

*This runbook ensures consistent, complete release publication for PersonalManager v0.5.0*