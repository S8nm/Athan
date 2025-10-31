# Changelog

All notable changes to Athan Discord Bot.

## [Unreleased]

### Added
- Automatic timezone detection for any city worldwide via API
- `/today` command to show all prayer times for current day
- `/subscribe_vc` command for subscribing to voice Adhan
- Role mention support (pings @athan role at prayer times)
- Rich Discord embeds for all responses
- Database migration system for schema updates
- Comprehensive test suite with pytest
- One-command setup scripts (`run.ps1` and `run.sh`)
- Docker support with Dockerfile

### Changed
- **BREAKING**: Switched from Aladhan API to MuslimSalat.com API
- **BREAKING**: Simplified `/setup` to only require `city`, `country`, `daylight_saving`
- **BREAKING**: Changed `/set_method` to use numerical IDs (1-7) instead of string names
- `/subscribe` now works in current channel without parameters
- Improved error handling with timeout protection
- Updated to Python 3.13+ with `audioop-lts` support

### Fixed
- **CRITICAL**: Fixed cache expiration bug (`.seconds` → `.total_seconds()`)
- **CRITICAL**: Fixed timezone always being UTC instead of location-specific
- **CRITICAL**: Fixed Pydantic V2 validation errors in `PrayerTimes`
- **CRITICAL**: Fixed string/datetime comparison errors in `/today` command
- Fixed "Unknown interaction" errors by adding immediate deferral
- Fixed voice channel parsing with complex Unicode names
- Fixed infinite loop in voice playback with 5-minute timeout
- Fixed resource leaks in voice connections
- Fixed sunrise field type mismatch in `/today` command
- Fixed database migration for `ping_role_id` column

### Removed
- Removed Qatar MOI time provider (consolidated to MuslimSalat)
- Removed Aladhan time provider (consolidated to MuslimSalat)
- Removed complex location type options from `/setup`
- Removed latitude/longitude parameters (API handles this)
- Cleaned up temporary documentation files

## [0.1.0] - 2025-10-31

### Initial Release
- Basic prayer time notifications
- Voice Adhan support
- Per-guild and per-user settings
- Prayer time offsets
- SQLite database persistence
- Discord slash commands
- FFmpeg audio playback

---

## Version History Summary

### 2025-10-31 - Production Release
- 6 critical bugs fixed
- Timezone detection implemented
- API simplified to MuslimSalat.com only
- Commands streamlined for better UX
- Comprehensive documentation added
- All tests passing

---

**Format**: This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

