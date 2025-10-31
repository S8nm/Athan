# 🕌 Athan - Discord Prayer Times Bot

A production-ready Discord bot that provides accurate Islamic prayer times and plays the Adhan (call to prayer) in voice channels.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://github.com/Rapptz/discord.py)

## ✨ Features

- 🕌 **Accurate Prayer Times** - Supports cities worldwide via MuslimSalat.com API
- 🔔 **Automated Notifications** - Sends notifications at every prayer time
- 🎙️ **Voice Adhan** - Plays the call to prayer in voice channels
- ⚙️ **Flexible Configuration** - Multiple calculation methods and time offsets
- 🌍 **Timezone Support** - Automatic timezone detection for any city
- 📊 **Rich Embeds** - Beautiful Discord embeds for prayer times
- 💾 **Persistent Settings** - Per-server configuration saved in SQLite database

## 📋 Prerequisites

- **Python 3.10+**
- **FFmpeg** (for voice playback)
- **Discord Bot Token** ([Get one here](https://discord.com/developers/applications))
- **MuslimSalat API Key** ([Get one here](https://muslimsalat.com))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/S8nm/Athan.git
cd Athan
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your tokens
# DISCORD_TOKEN=your_token_here
# MUSLIMSALAT_API_KEY=your_api_key_here
```

### 3. Install Dependencies

**Option A: Using UV (Recommended)**
```bash
pip install uv
uv sync
```

**Option B: Using pip**
```bash
python -m pip install -e .
```

### 4. Add Adhan Audio

Place your `adhan.mp3` file in the `assets/` directory:
```bash
mkdir -p assets
# Copy your adhan.mp3 to assets/
```

### 5. Run the Bot

**Windows:**
```powershell
.\run.ps1
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Or manually:**
```bash
python -m athan.bot
```

## 📖 Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/setup` | Configure location and timezone | `/setup city:London country:UK` |
| `/set_method` | Set calculation method (1-7) | `/set_method method:5` |
| `/set_offset` | Adjust prayer times (+/- minutes) | `/set_offset prayer:Fajr minutes:5` |
| `/subscribe` | Subscribe text channel for notifications | `/subscribe` |
| `/subscribe_vc` | Subscribe voice channel for Adhan | `/subscribe_vc` |
| `/today` | Show all prayer times for today | `/today` |
| `/next_prayer` | Show next upcoming prayer | `/next_prayer` |
| `/test` | Test notification and voice Adhan | `/test` |
| `/status` | Show current bot configuration | `/status` |

## ⚙️ Calculation Methods

The bot supports 7 Islamic calculation methods:

1. **Egyptian General Authority of Survey**
2. **University of Islamic Sciences, Karachi (Shafi)**
3. **University of Islamic Sciences, Karachi (Hanafi)**
4. **Islamic Circle of North America (ISNA)**
5. **Muslim World League (MWL)**
6. **Umm Al-Qura University**
7. **Fixed Isha**

## 🐳 Docker Deployment

```bash
# Build image
docker build -t athan-bot .

# Run container
docker run -d \
  --name athan-bot \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/assets:/app/assets \
  --env-file .env \
  athan-bot
```

## 📂 Project Structure

```
Athan/
├── src/athan/          # Main bot source code
│   ├── bot.py          # Bot client and event handlers
│   ├── commands.py     # Slash command implementations
│   ├── scheduler.py    # Prayer time scheduler
│   ├── db.py           # Database interface
│   ├── config.py       # Configuration models
│   ├── embeds.py       # Discord embed builders
│   └── time_providers/ # Prayer time API providers
├── assets/             # Audio files (adhan.mp3)
├── data/               # SQLite database (auto-generated)
├── tests/              # Unit and integration tests
├── run.ps1             # Windows startup script
├── run.sh              # Linux/Mac startup script
├── pyproject.toml      # Project dependencies
├── Dockerfile          # Docker configuration
└── README.md           # This file
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/athan --cov-report=html

# Run specific test file
pytest tests/test_time_providers.py
```

## 🛠️ Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Format code
black src tests

# Lint code
ruff check src tests --fix

# Type checking
mypy src
```

## 🔐 Security & Privacy

- Bot tokens and API keys are **never** committed to Git
- All sensitive data is stored in `.env` (gitignored)
- Database contains only server IDs, channel IDs, and prayer settings
- No user personal data is collected
- See [PRIVACY_POLICY.md](PRIVACY_POLICY.md) for full details

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/S8nm/Athan/issues)
- **Discord**: [Join our server](#) *(Add your Discord server link)*

## 📝 Acknowledgments

- Prayer times provided by [MuslimSalat.com](https://muslimsalat.com)
- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Inspired by the Muslim community's need for reliable prayer time notifications

---

**Made with ❤️ for the Muslim Ummah**

