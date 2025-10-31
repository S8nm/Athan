# 🚀 Athan Bot - 3-Step Quickstart

Get the bot running in under 5 minutes!

---

## Step 1: Get Your Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Name it "Athan"
3. Go to "Bot" tab → Click "Reset Token" → Copy the token
4. Save token to file:
   ```powershell
   # Windows
   echo YOUR_TOKEN_HERE > DISCORD_TOKEN.txt
   
   # Linux/Mac
   echo "YOUR_TOKEN_HERE" > DISCORD_TOKEN.txt
   ```

5. **Enable these intents** (on the Bot page):
   - ✅ Server Members Intent
   - ✅ Message Content Intent (optional)

6. **Invite bot** to your server:
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Embed Links`, `Manage Roles`, `Connect`, `Speak`
   - Copy the generated URL and open in browser

---

## Step 2: Add Adhan Audio File

1. Download an Adhan MP3 file (e.g., from YouTube or Islamic websites)
2. Rename it to `adhan.mp3`
3. Place it in the `assets/` folder:
   ```
   Athan/
   ├── assets/
   │   └── adhan.mp3  ← Put it here!
   ```

---

## Step 3: Start the Bot

### Windows (PowerShell):
```powershell
.\run.ps1
```

### Linux/Mac (Bash):
```bash
chmod +x run.sh
./run.sh
```

### Manual Start:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
python -m athan.bot
```

---

## ✅ Done! Now Configure in Discord

### 1. Run Setup (in your Discord server):
```
/setup city:London country:UK daylight_saving:true
```
Replace with your city/country.

### 2. Subscribe to Notifications:
```
/subscribe
```
This enables notifications in the current channel.

### 3. (Optional) Enable Voice Adhan:
```
/subscribe_vc voice_channel:#prayer-room
```
Select your voice channel from the dropdown.

### 4. Check It Works:
```
/next_prayer
```
Should show the next prayer time correctly!

```
/test
```
Sends a test notification and plays Adhan in voice if configured.

---

## 📝 Quick Command Reference

| Command | What It Does |
|---------|--------------|
| `/setup` | Configure your location |
| `/subscribe` | Enable notifications |
| `/subscribe_vc` | Enable voice Adhan |
| `/next_prayer` | Show next prayer |
| `/today` | Show all today's prayers |
| `/test` | Test notification & voice |
| `/set_method` | Change calculation method |
| `/set_offset` | Adjust prayer times |

---

## 🆘 Common Issues

### Bot not responding?
- Wait 5 minutes (Discord caches commands)
- Or run: `python sync_commands.py`
- Or kick and re-invite the bot

### Wrong prayer times?
- Re-run `/setup` with correct location and `daylight_saving:true/false`

### Voice not working?
- Install FFmpeg: `winget install FFmpeg` (Windows) or `sudo apt install ffmpeg` (Linux)
- Check bot has "Connect" and "Speak" permissions
- Verify `assets/adhan.mp3` exists

### "Unknown interaction" error?
- This means Discord cached old command structure
- Wait 1 hour OR kick/re-invite bot

---

## 🎉 You're All Set!

The bot will now automatically:
- ✅ Send notifications at each prayer time
- ✅ Play Adhan in voice (if configured)
- ✅ Handle timezone changes (DST/GMT)
- ✅ Ping the @athan role (if permissions allow)

Need more help? See [README.md](README.md) for full documentation.

**May Allah accept your efforts! 🤲**
