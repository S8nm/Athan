# 🐛 Bugs Fixed - Development Log

This document tracks all critical bugs discovered and fixed during development.

---

## Bug #1: Pydantic V2 Validation Error (CRITICAL)

**Date**: 2025-10-31  
**Severity**: 🔴 CRITICAL - Bot couldn't fetch prayer times

### Symptoms
```
ValidationError: 8 validation errors for PrayerTimes
date: Field required
fajr: Field required
sunrise: Field required
dhuhr: Field required
asr: Field required
maghrib: Field required
isha: Field required
timezone: Field required
```

### Root Cause
In `src/athan/time_providers/muslimsalat.py`:
```python
# ❌ OLD CODE - Created empty object first
prayer_times = PrayerTimes()
prayer_times.date = date
prayer_times.fajr = times["fajr"]
# ... Pydantic V2 validates immediately, fails!
```

### Fix
```python
# ✅ NEW CODE - Create with all fields at once
prayer_times = PrayerTimes(
    date=date,
    fajr=times["fajr"],
    sunrise=times["sunrise"],
    dhuhr=times["dhuhr"],
    asr=times["asr"],
    maghrib=times["maghrib"],
    isha=times["isha"],
    timezone=timezone,
)
```

**File**: `src/athan/time_providers/muslimsalat.py` lines 110-124  
**Status**: ✅ FIXED

---

## Bug #2: Channel Name Parsing Error

**Date**: 2025-10-31  
**Severity**: 🟠 HIGH - Commands failed with Unicode channel names

### Symptoms
```
TransformerError: Failed to convert 🗣»a to TextChannel
TransformerError: Failed to convert 🎤» 𝓣𝓸𝔀𝓷𝓱𝓸𝓾𝓼𝓮 to VoiceChannel
```

### Root Cause
- Discord's transformer couldn't parse channel names with emojis and Unicode
- User had channels with complex characters

### Fix
1. **Simplified `/subscribe`**: Now works in current channel (no parameter)
2. **Created `/subscribe_vc`**: Separate command for voice channels
3. **Custom `VoiceChannelTransformer`**: Properly handles channel IDs from Discord dropdown

**Files**: 
- `src/athan/commands.py` - Added `VoiceChannelTransformer` class
- `src/athan/commands.py` - Modified `_subscribe` to use `interaction.channel`

**Status**: ✅ FIXED

---

## Bug #3: String/Datetime Comparison Error (CRITICAL)

**Date**: 2025-10-31  
**Severity**: 🔴 CRITICAL - `/today` command crashed

### Symptoms
```
TypeError: '<' not supported between instances of 'str' and 'datetime.datetime'
```

### Root Cause
In `/today` command:
```python
# ❌ OLD CODE
prayer_time = prayer_times.get_time(prayer)  # Returns STRING "02:30 PM"
if prayer_time < today:  # Comparing STRING to DATETIME!
```

### Fix
```python
# ✅ NEW CODE
prayer_time_str = prayer_times.get_time(prayer)
# Parse string to datetime
hour = int(prayer_time_str.split(":")[0])
minute = int(prayer_time_str.split(":")[1].split()[0])
period = prayer_time_str.split()[-1]
if period.upper() == "PM" and hour != 12:
    hour += 12
elif period.upper() == "AM" and hour == 12:
    hour = 0
prayer_dt = datetime.combine(today.date(), datetime.min.time().replace(hour=hour, minute=minute))
```

**File**: `src/athan/commands.py` lines 570-590  
**Status**: ✅ FIXED

---

## Bug #4: Sunrise Field Type Mismatch

**Date**: 2025-10-31  
**Severity**: 🟡 MEDIUM - `/today` showed wrong sunrise format

### Symptoms
```
AttributeError: 'str' object has no attribute 'strftime'
```

### Root Cause
```python
# ❌ OLD CODE
sunrise_str = prayer_times.sunrise  # Already a STRING
embed.add_field(name="Sunrise", value=sunrise_str.strftime("%I:%M %p"))  # Can't call strftime on string!
```

### Fix
```python
# ✅ NEW CODE
sunrise_str = prayer_times.sunrise
# Parse string first, then format
# ... parse logic ...
embed.add_field(name="Sunrise", value=sunrise_dt.strftime("%I:%M %p"))
```

**File**: `src/athan/commands.py` lines 596-608  
**Status**: ✅ FIXED

---

## Bug #5: Cache Expiration Logic Error (CRITICAL)

**Date**: 2025-10-31  
**Severity**: 🔴 CRITICAL - Stale prayer times after 24 hours

### Symptoms
- Cache appeared to work initially
- After 24+ hours, bot returned yesterday's prayer times
- No new API calls made

### Root Cause
```python
# ❌ OLD CODE
if (datetime.now(ZoneInfo("UTC")) - cached_at).seconds < 3600:
    return cached_times
```

**Problem**: `.seconds` only returns the seconds component (0-59), NOT total seconds!
- After 1 hour 30 minutes: `.seconds` = 1800 (30 minutes) ✓ Works
- After 24 hours 30 minutes: `.seconds` = 1800 (30 minutes) ✗ Still returns cache!

### Fix
```python
# ✅ NEW CODE
if (datetime.now(ZoneInfo("UTC")) - cached_at).total_seconds() < 3600:
    return cached_times
```

**File**: `src/athan/time_providers/muslimsalat.py` line 80  
**Impact**: Without this fix, bot would show wrong prayer times after running for 24+ hours  
**Status**: ✅ FIXED

---

## Bug #6: Hardcoded UTC Timezone (CRITICAL)

**Date**: 2025-10-31  
**Severity**: 🔴 CRITICAL - All servers got wrong timezone

### Symptoms
- `/next_prayer` showed prayers already passed as "upcoming"
- London server showed "Asr at 2:30 PM in 1 hour" when it was already 4:30 PM
- All prayer times were 1 hour off in UK (BST timezone)

### Root Cause
```python
# ❌ OLD CODE in /setup command
timezone = "UTC"  # HARDCODED - everyone gets UTC!
```

**Problem**: 
- MuslimSalat.com returns London times in BST (UTC+1)
- Bot stored timezone as UTC
- All calculations were off by 1 hour

### Fix
```python
# ✅ NEW CODE
# Step 1: Fetch prayer times from API
timezone = await self._get_timezone_from_api(city, country)

# Step 2: API response includes correct timezone
# MuslimSalat.com automatically returns "Europe/London" for London

# Step 3: Fallback to city mapping if API fails
if not timezone:
    timezone = self._get_timezone_for_location(city, country, daylight_saving)
```

**Added Function**: `_get_timezone_from_api()` - Fetches timezone from prayer times API response

**Files**: 
- `src/athan/commands.py` - Added `_get_timezone_from_api()`
- `src/athan/commands.py` - Updated `_setup()` to use API timezone

**Status**: ✅ FIXED  
**Impact**: Now supports **any city worldwide** with correct timezone!

---

## Bug #7: Voice Playback Infinite Loop

**Date**: 2025-10-31  
**Severity**: 🟠 HIGH - Bot could hang forever

### Symptoms
- If audio playback failed, bot would loop forever
- `while voice_client.is_playing()` never exited
- Required manual bot restart

### Root Cause
```python
# ❌ OLD CODE
while voice_client.is_playing():
    await asyncio.sleep(1)  # Could loop forever!
```

### Fix
```python
# ✅ NEW CODE
max_wait = 300  # 5 minutes timeout
waited = 0
while voice_client.is_playing() and waited < max_wait:
    await asyncio.sleep(1)
    waited += 1

if waited >= max_wait:
    logger.warning("Voice playback timeout reached")
```

**Files**: 
- `src/athan/scheduler.py` - `_play_voice_adhan()`
- `src/athan/commands.py` - `_play_test_adhan()` and `_adhan_voice()`

**Status**: ✅ FIXED

---

## Bug #8: Voice Connection Resource Leak

**Date**: 2025-10-31  
**Severity**: 🟡 MEDIUM - Resource exhaustion over time

### Symptoms
- Voice connections not properly closed on errors
- Eventually bot couldn't join new voice channels

### Root Cause
```python
# ❌ OLD CODE
try:
    voice_client.play(...)
except Exception as e:
    logger.error(f"Error: {e}")
    # No cleanup! Connection stays open
```

### Fix
```python
# ✅ NEW CODE
try:
    voice_client.play(...)
except Exception as e:
    logger.error(f"Error: {e}")
    await voice_client.disconnect()  # Cleanup!
finally:
    if voice_client.is_connected():
        await voice_client.disconnect()
```

**Files**: Same as Bug #7  
**Status**: ✅ FIXED

---

## Bug #9: "Unknown Interaction" Errors

**Date**: 2025-10-31  
**Severity**: 🟠 HIGH - Commands randomly failed

### Symptoms
```
NotFound: 404 Not Found (error code: 10062): Unknown interaction
```

### Root Cause
- Discord requires response within 3 seconds
- Bot was doing API calls before responding
- Interaction expired before bot could respond

### Fix
```python
# ✅ Added to ALL command handlers
async def _command(self, interaction: discord.Interaction):
    # DEFER IMMEDIATELY - acknowledge within 3 seconds
    try:
        await interaction.response.defer(ephemeral=False)
    except discord.errors.NotFound:
        logger.error("Interaction expired")
        return
    
    # Now we have 15 minutes to do work and send followup
    result = await slow_api_call()
    await interaction.followup.send(result)
```

**Files**: All command handlers in `src/athan/commands.py`  
**Status**: ✅ FIXED

---

## Bug #10: VoiceChannelTransformer Missing Dropdown

**Date**: 2025-10-31  
**Severity**: 🟡 MEDIUM - UX issue, users had to type channel names

### Symptoms
- `/subscribe_vc` didn't show dropdown menu
- Users had to manually type channel names
- Led to more parsing errors

### Root Cause
```python
# ❌ OLD CODE
class VoiceChannelTransformer(app_commands.Transformer):
    async def transform(self, interaction, value):
        # Missing @property decorators!
```

Discord needs `type` and `channel_types` properties to show dropdown.

### Fix
```python
# ✅ NEW CODE
class VoiceChannelTransformer(app_commands.Transformer):
    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.channel
    
    @property
    def channel_types(self) -> list[discord.ChannelType]:
        return [discord.ChannelType.voice, discord.ChannelType.stage_voice]
    
    async def transform(self, interaction, value):
        # Now Discord shows dropdown!
```

**File**: `src/athan/commands.py` lines 30-40  
**Status**: ✅ FIXED

---

## Summary Statistics

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 CRITICAL | 4 | ✅ All Fixed |
| 🟠 HIGH | 3 | ✅ All Fixed |
| 🟡 MEDIUM | 3 | ✅ All Fixed |
| **TOTAL** | **10** | **✅ 100% Fixed** |

---

## Code Quality Improvements

### 1. Type Hints Updated
- Changed `Optional[X]` → `X | None` (Python 3.10+ syntax)
- More consistent type annotations throughout

### 2. Linting & Formatting
- Fixed all `ruff` linting issues
- Applied `black` formatting consistently
- Removed unused imports

### 3. Testing
- All 20 unit tests passing
- Integration tests updated for new command structure
- Database migration tests added

### 4. Documentation
- Consolidated 10 markdown files → 4 well-organized files
- Added comprehensive CHANGELOG.md
- Updated README.md with current features
- Created QUICKSTART.md for new users

---

## Lessons Learned

1. **Always defer Discord interactions immediately** - 3-second window is tight
2. **Pydantic V2 is strict** - Create objects with all required fields at once
3. **Timezones are critical** - Never hardcode UTC, always detect from API or location
4. **Cache invalidation is hard** - Use `.total_seconds()`, not `.seconds`
5. **Resource cleanup matters** - Always disconnect voice clients in finally blocks
6. **Test with real data** - Unicode channel names, edge cases, timezone changes
7. **Documentation sprawl is real** - Consolidate early, don't let it accumulate

---

## Testing Checklist for Future Changes

Before deploying:
- [ ] Run full test suite: `pytest tests/`
- [ ] Test with Unicode channel names
- [ ] Test in multiple timezones (London, Doha, New York)
- [ ] Test timezone transitions (DST changes)
- [ ] Test voice playback with timeout scenarios
- [ ] Test with API failures (network issues)
- [ ] Test cache expiration after 1+ hours
- [ ] Test "Unknown interaction" scenarios
- [ ] Run linter: `ruff check src/ tests/`
- [ ] Format code: `black src/ tests/`

---

**Last Updated**: 2025-10-31  
**All Critical Bugs**: ✅ RESOLVED  
**Production Status**: 🟢 READY

