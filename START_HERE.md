# 🎯 START HERE - Athan Bot

**Welcome!** This is the simplest guide to get started.

---

## ⚡ Super Quick Start (5 minutes)

### Step 1: Get Discord Bot Token
1. Go to https://discord.com/developers/applications
2. Create application → Go to "Bot" → Copy token
3. Save to file:
   ```
   echo YOUR_TOKEN_HERE > DISCORD_TOKEN.txt
   ```

### Step 2: Add Adhan Audio
Download an Adhan MP3 and save it as `assets/adhan.mp3`

### Step 3: Run Bot
```powershell
# Windows
.\run.ps1

# Linux/Mac
./run.sh
```

**Done!** Bot is now running.

---

## 📱 In Discord

### 1. Setup Your Server
```
/setup city:London country:UK daylight_saving:true
```
(Replace London with your city)

### 2. Subscribe to Notifications
```
/subscribe
```

### 3. Done! 
The bot will now automatically post prayer times.

---

## 📚 Need More Help?

| File | What's In It |
|------|--------------|
| **QUICKSTART.md** | Detailed 3-step guide |
| **README.md** | Full documentation |
| **PROJECT_STATUS.md** | What's ready & working |

---

## 🆘 Common Issues

### Bot not responding?
Wait 5 minutes (Discord caches commands) or kick/re-invite bot

### Wrong prayer times?
Re-run `/setup` with correct `daylight_saving` setting

### Voice not working?
Install FFmpeg and make sure `assets/adhan.mp3` exists

---

## ✅ Everything Working?

You're all set! The bot will:
- ✅ Send notifications at prayer times
- ✅ Play Adhan in voice (if configured)
- ✅ Handle timezone changes automatically

**May Allah accept your efforts! 🤲**

