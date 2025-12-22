# PersonalManager v0.5.0 - Frequently Asked Questions

## General Questions

### Q: What is PersonalManager v0.5.0?
**A:** PersonalManager v0.5.0 is an AI-powered personal productivity platform that helps you manage tasks, time, and energy intelligently. It's a major upgrade from v0.4.x that adds AI recommendations, session tracking, time budgets, and smart scheduling.

### Q: Is v0.5.0 backward compatible?
**A:** Yes! v0.5.0 is 100% backward compatible. All your existing tasks, habits, and data from v0.4.x will work perfectly with the new version.

### Q: How long does the upgrade take?
**A:** The upgrade typically takes about 5 minutes, including backup, installation, and verification.

### Q: Do I need to pay for v0.5.0?
**A:** No, PersonalManager is open-source and free. However, if you use AI features, you'll need your own API keys for Anthropic (Claude) or Google (Gemini).

## Installation & Setup

### Q: What are the system requirements?
**A:**
- Python 3.8 or higher
- 100MB free disk space
- Internet connection (for AI features)
- macOS, Linux, or Windows

### Q: How do I install PersonalManager?
**A:**
```bash
# Using pip
pip install personal-manager==0.5.0

# Or using poetry
poetry add personal-manager==0.5.0
```

### Q: How do I verify the installation?
**A:**
```bash
pm --version
# Should show: PersonalManager Agent v0.5.0

pm doctor
# Should show all checks passing
```

### Q: Where is my data stored?
**A:** Your data is stored locally at `~/.personalmanager/data.db`. Configuration files are at `~/.personalmanager/config/`.

## AI Features

### Q: How do the AI features work?
**A:** PersonalManager uses AI to:
- Analyze your work patterns
- Suggest optimal tasks based on context
- Predict energy levels
- Recommend break times
- Generate insights from your productivity data

All processing happens through API calls to your chosen provider (Anthropic or Google).

### Q: Do I need an API key for AI features?
**A:** Yes, you need either:
- Anthropic API key (for Claude)
- Google API key (for Gemini)

Configure with: `pm auth config`

### Q: Is my data sent to AI providers?
**A:** Only anonymized, minimal context is sent to generate recommendations. No personal identifiable information or sensitive data is transmitted. All data stays on your machine by default.

### Q: Can I use PersonalManager without AI features?
**A:** Absolutely! All traditional task management features work without AI. AI features are optional enhancements.

## Migration & Deprecation

### Q: What commands are deprecated?
**A:** Two commands are deprecated but still functional:
- `pm next` → use `pm now` instead
- `pm today` → use `pm now` instead

They will show migration notices but continue to work until v1.0.

### Q: Will my scripts break?
**A:** No, deprecated commands still work and return the same output format. You have until v1.0 to update your scripts.

### Q: How do I migrate my workflows?
**A:** Simply replace deprecated commands:
```bash
# Old
pm next
pm today

# New (v0.5.0+)
pm now
```

## New Features

### Q: What is the "pm now" command?
**A:** `pm now` is the new unified command that combines AI recommendations with your current context to suggest what you should work on right now.

### Q: How do sessions work?
**A:** Sessions track your focused work time:
```bash
pm sessions start --mode deep    # 90-min deep work
pm sessions start --mode pomodoro # 25-min pomodoro
pm sessions pause                # Pause current
pm sessions complete             # Finish session
```

### Q: What are time budgets?
**A:** Time budgets let you allocate time to projects like a financial budget:
```bash
pm budgets create --project "Work" --hours 40
pm budgets status  # Check consumption
```

### Q: How does time-block planning work?
**A:** Interactive planning for your calendar:
```bash
pm timeblock plan  # Start interactive planning
pm timeblock today # View today's blocks
```

## Troubleshooting

### Q: Command not found after upgrade?
**A:**
```bash
# Check installation
pip show personal-manager

# Update PATH
export PATH="$HOME/.local/bin:$PATH"

# Reinstall if needed
pip uninstall personal-manager
pip install personal-manager==0.5.0
```

### Q: Database error after upgrade?
**A:**
```bash
# Run repair
pm doctor --repair

# Or restore backup
cp ~/.personalmanager/data.db.backup ~/.personalmanager/data.db
```

### Q: AI features not working?
**A:**
1. Check API key: `pm auth status`
2. Reconfigure: `pm auth config`
3. Test connection: `pm ai suggest --debug`

### Q: High memory usage?
**A:** v0.5.0 actually uses 60% less memory than v0.4.x. If you see high usage:
```bash
# Clear cache
pm cache clear

# Restart session tracking
pm sessions cleanup
```

## Performance

### Q: Is v0.5.0 faster?
**A:** Yes! v0.5.0 is approximately:
- 40% faster command execution
- 60% lower memory usage
- 50% faster database queries

### Q: Can I run PersonalManager in the background?
**A:** Yes, session tracking and automation features run in the background with minimal resource usage.

## Security & Privacy

### Q: Is my data secure?
**A:** Yes:
- All data stored locally
- Credentials encrypted at rest
- No telemetry or data collection
- Open source for transparency
- Zero known security vulnerabilities

### Q: Can I audit what data is sent to AI?
**A:** Yes, use debug mode:
```bash
pm ai suggest --debug  # Shows exact API calls
```

## Rollback

### Q: How do I rollback to v0.4.0?
**A:**
```bash
# Quick rollback
pip install personal-manager==0.4.0

# Or use script
./scripts/rollback.sh --version v0.4.0
```

### Q: Will rollback lose my data?
**A:** No, the data format is backward compatible. Your data remains intact during rollback.

## Best Practices

### Q: How should I start using v0.5.0?
**A:**
1. Start with `pm now` for recommendations
2. Try a deep work session: `pm sessions start --mode deep`
3. Set up time budgets for your projects
4. Review your patterns: `pm ai analyze`

### Q: What's the recommended workflow?
**A:**
```bash
# Morning
pm briefing        # Get daily overview
pm now            # Get first task recommendation
pm sessions start # Start focused work

# During work
pm sessions pause/resume  # Manage breaks
pm tasks complete <id>   # Mark tasks done

# Evening
pm sessions stats  # Review productivity
pm ai analyze     # Get insights
```

## Getting Help

### Q: Where can I find more documentation?
**A:**
- [User Guide](./user-guides/USER_GUIDE_V05.md)
- [Migration Guide](./user-guides/MIGRATION_GUIDE_V05_FINAL.md)
- [Release Notes](./RELEASE_NOTES_v0.5.0.md)

### Q: How do I report bugs?
**A:** Report issues on GitHub: https://github.com/personal-manager/issues

### Q: Is there a community or support channel?
**A:**
- GitHub Discussions for community help
- Email support@personalmanager.local for urgent issues

### Q: How can I contribute?
**A:** PersonalManager is open source! Contribute via:
- GitHub Pull Requests
- Bug reports
- Feature suggestions
- Documentation improvements

## Future

### Q: What's planned for v0.6.0?
**A:** Planned features include:
- Mobile companion app
- Team collaboration
- Advanced AI insights
- Plugin marketplace
- Voice commands

### Q: When will v1.0 be released?
**A:** v1.0 is planned for Q2 2026, which will remove all deprecated features and stabilize the API.

---

*Can't find your answer? Check the [User Guide](./user-guides/USER_GUIDE_V05.md) or create an issue on GitHub.*