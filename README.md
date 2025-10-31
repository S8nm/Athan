# 🕌 Athan Discord Bot

A production-ready Discord bot that posts accurate prayer times and plays the Adhan in voice channels.

## ✨ Features

- **🌍 Worldwide Prayer Times**: Supports any city via MuslimSalat.com API
- **🔔 Auto Notifications**: Scheduled messages at each prayer time
- **🎵 Voice Adhan**: Plays call to prayer in voice channels
- **⏰ Custom Offsets**: Adjust timing for each prayer
- **👥 Role Mentions**: Ping a role (e.g., @athan) at prayer times
- **💾 Persistent Settings**: Per-server configuration
- **⚡ Slash Commands**: Modern Discord UI

## 🚀 Quick Start

### Option 1: One-Command Setup (Windows)
```powershell
.\run.ps1
```

### Option 2: One-Command Setup (Linux/Mac)
```bash
./run.sh
```

### Option 3: Manual Setup
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -e .

# 3. Add your Discord bot token
echo "YOUR_TOKEN_HERE" > DISCORD_TOKEN.txt

# 4. Add Adhan audio file
# Place adhan.mp3 in the assets/ folder

# 5. Run bot
python -m athan.bot
```

## 📋 Required Files

1. **Discord Token**: Create `DISCORD_TOKEN.txt` with your bot token
2. **Adhan Audio**: Place `adhan.mp3` in `assets/` folder

## 🎮 Discord Commands

### Setup Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/setup` | Configure location & timezone | `/setup city:London country:UK daylight_saving:true` |
| `/set_method` | Set calculation method (1-7) | `/set_method method:5` |
| `/set_offset` | Adjust prayer time | `/set_offset prayer:Fajr offset:5` |

### Subscription Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/subscribe` | Enable notifications in current channel | `/subscribe ping_role:@athan` |
| `/subscribe_vc` | Enable voice Adhan | `/subscribe_vc voice_channel:#VoiceChannel` |
| `/unsubscribe` | Disable notifications | `/unsubscribe` |

### Information Commands
| Command | Description |
|---------|-------------|
| `/next_prayer` | Show next prayer time |
| `/today` | Show all prayer times for today |
| `/test` | Test notification & voice Adhan |
| `/status` | Bot health check |

## 🌍 Supported Locations

The bot automatically detects the correct timezone for **any city** supported by MuslimSalat.com API, including:

- **UK**: London, Manchester, Birmingham
- **Middle East**: Doha, Dubai, Riyadh, Jeddah, Makkah, Medina
- **North America**: New York, Los Angeles, Chicago, Toronto, Vancouver
- **Europe**: Paris, Berlin, Rome, Madrid
- **And thousands more cities worldwide!**

## 📊 Calculation Methods

| ID | Method |
|----|--------|
| 1 | Egyptian General Authority of Survey |
| 2 | University Of Islamic Sciences, Karachi (Shafi) |
| 3 | University Of Islamic Sciences, Karachi (Hanafi) |
| 4 | Islamic Circle of North America (ISNA) |
| 5 | Muslim World League (MWL) |
| 6 | Umm Al-Qura |
| 7 | Fixed Isha |

**Note**: MuslimSalat.com API provides times based on location. The method setting is stored but may not directly affect API-provided times.

## 🐳 Docker Deployment

```bash
# Build
docker build -t athan-bot .

# Run
docker run -d \
  --name athan \
  -e DISCORD_TOKEN=your_token_here \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/assets:/app/assets \
  --restart unless-stopped \
  athan-bot
```

## 🔧 Development

### Run Tests
```bash
pytest tests/
```

### Format & Lint
```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/ --fix
```

### Project Structure
```
Athan/
├── src/athan/
│   ├── bot.py              # Main bot & event handlers
│   ├── commands.py         # Slash command handlers
│   ├── scheduler.py        # Prayer time scheduler
│   ├── config.py           # Settings & models
│   ├── db.py               # SQLite persistence
│   ├── embeds.py           # Discord embeds
│   ├── utils.py            # Helper functions
│   └── time_providers/
│       └── muslimsalat.py  # MuslimSalat.com API client
├── assets/
│   └── adhan.mp3           # Adhan audio (you provide)
├── tests/                  # Unit & integration tests
├── data/                   # SQLite database (auto-created)
├── pyproject.toml          # Dependencies
├── Dockerfile              # Container config
├── run.ps1                 # Windows startup script
└── run.sh                  # Linux/Mac startup script
```

## 🔑 Required Bot Permissions

When inviting the bot, enable:
- ✅ Send Messages
- ✅ Embed Links
- ✅ Manage Roles (to create @athan role)
- ✅ Connect & Speak (for voice Adhan)
- ✅ Use Slash Commands

## 🛠️ Environment Variables

Create `.env` file (optional, `DISCORD_TOKEN.txt` takes priority):
```env
DISCORD_TOKEN=your_bot_token_here
MUSLIMSALAT_API_KEY=98bf8d87cba26cf8385073856fad9229
```

## 📝 Example Workflow

1. **Server owner runs setup**:
   ```
   /setup city:London country:UK daylight_saving:true
   ```

2. **Enable text notifications**:
   ```
   /subscribe ping_role:@athan
   ```
   (Bot creates @athan role if it doesn't exist and has permissions)

3. **Enable voice Adhan** (optional):
   ```
   /subscribe_vc voice_channel:#prayer-room
   ```

4. **Check next prayer**:
   ```
   /next_prayer
   ```

5. **View all today's prayers**:
   ```
   /today
   ```

Done! The bot will now:
- ✅ Send automatic notifications at each prayer time
- ✅ Mention @athan role
- ✅ Play Adhan in voice channel (if configured)
- ✅ Handle timezone changes automatically (DST/GMT)

## ❓ Troubleshooting

### "Unknown interaction" errors
- Discord caches slash commands for up to 1 hour
- Run `sync_commands.py` to force sync
- Or kick/re-invite the bot

### Prayer times are wrong
- Re-run `/setup` with correct location and `daylight_saving` setting
- Timezone is auto-detected from API for accurate times

### Voice Adhan not working
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check bot has Connect & Speak permissions
- Verify `assets/adhan.mp3` exists

### Bot won't start
- Check `DISCORD_TOKEN.txt` exists and has valid token
- Run `.\run.ps1` (Windows) or `./run.sh` (Linux/Mac) for automated setup

## 📜 License

MIT License - See LICENSE file for details

## 🙏 Credits

- Prayer times: [MuslimSalat.com API](https://muslimsalat.com)
- Built with [discord.py](https://github.com/Rapptz/discord.py)

## 📧 Support

For issues, questions, or feature requests, please open a GitHub issue.

---

**Made with ❤️ for the Muslim community**
