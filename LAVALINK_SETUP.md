# 🎵 Lavalink Setup Guide

Athan bot uses **Lavalink** for reliable voice playback. Lavalink is a standalone audio server that handles all voice connections, solving the common Discord voice connection issues (like error 4006).

## 🔧 Why Lavalink?

- ✅ **Reliable voice connections** - No more "joining and leaving" issues
- ✅ **Better performance** - Offloads audio processing from the bot
- ✅ **Industry standard** - Used by major Discord music bots
- ✅ **No FFmpeg required** - Handles all audio processing

---

## 📦 Quick Setup (Windows)

### Option 1: Download Prebuilt Lavalink (Easiest)

1. **Download Lavalink JAR**:
   ```powershell
   # Create lavalink directory
   mkdir lavalink
   cd lavalink
   
   # Download latest Lavalink (v4.x)
   Invoke-WebRequest -Uri "https://github.com/lavalink-devs/Lavalink/releases/download/4.0.4/Lavalink.jar" -OutFile "Lavalink.jar"
   ```

2. **Create configuration file** (`application.yml`):
   ```yaml
   server:
     port: 2333
     address: 0.0.0.0
   
   lavalink:
     server:
       password: "youshallnotpass"
       sources:
         local: true
   
   logging:
     level:
       root: INFO
       lavalink: INFO
   ```

3. **Run Lavalink**:
   ```powershell
   java -jar Lavalink.jar
   ```

4. **Keep it running** in a separate terminal while your bot runs.

---

### Option 2: Using Docker (Recommended for Production)

1. **Create `docker-compose.yml`**:
   ```yaml
   version: '3.8'
   services:
     lavalink:
       image: ghcr.io/lavalink-devs/lavalink:4
       container_name: lavalink
       restart: unless-stopped
       environment:
         - JAVA_OPTS=-Xmx512M
       volumes:
         - ./lavalink-config.yml:/opt/Lavalink/application.yml
       ports:
         - "2333:2333"
   ```

2. **Create `lavalink-config.yml`**:
   ```yaml
   server:
     port: 2333
     address: 0.0.0.0
   
   lavalink:
     server:
       password: "youshallnotpass"
       sources:
         local: true
   
   logging:
     level:
       root: INFO
   ```

3. **Run with Docker**:
   ```bash
   docker-compose up -d
   ```

---

## 🔑 Configure Bot

Update your `.env` file with Lavalink connection details:

```env
# Lavalink Configuration (Optional - defaults shown)
LAVALINK_HOST=localhost
LAVALINK_PORT=2333
LAVALINK_PASSWORD=youshallnotpass
```

---

## ✅ Verify Lavalink is Running

Check if Lavalink is accessible:

```powershell
# Should return Lavalink version info
curl http://localhost:2333/version
```

Or open in browser: http://localhost:2333/version

---

## 🚀 Run the Bot

After Lavalink is running:

```powershell
# In a NEW terminal (keep Lavalink running in the other one)
cd C:\Users\Admin\Desktop\coding\Projects\Athan
.\run.ps1
```

The bot will automatically connect to Lavalink on startup!

---

## 🔍 Troubleshooting

### "Failed to connect to Lavalink"

**Solution**: Make sure Lavalink is running:
```powershell
# Check if Lavalink is responding
curl http://localhost:2333/version
```

### "Connection refused"

**Solutions**:
1. Check if Lavalink is running in another terminal
2. Verify port 2333 is not blocked by firewall
3. Check `LAVALINK_HOST` and `LAVALINK_PORT` in `.env`

### "Invalid password"

**Solution**: Make sure `LAVALINK_PASSWORD` in `.env` matches the password in `application.yml`

---

## 📝 Production Deployment

For production, consider:

1. **Use Docker** for easier management
2. **Change default password** in `application.yml`
3. **Set up auto-restart** (systemd, PM2, or Docker restart policy)
4. **Monitor Lavalink logs** for issues

Example systemd service (`/etc/systemd/system/lavalink.service`):

```ini
[Unit]
Description=Lavalink Audio Server
After=network.target

[Service]
Type=simple
User=lavalink
WorkingDirectory=/opt/lavalink
ExecStart=/usr/bin/java -Xmx512M -jar Lavalink.jar
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🎉 Success!

Once Lavalink is running, your bot will:
- ✅ Connect reliably to voice channels
- ✅ No more error 4006 or "joining/leaving" issues
- ✅ Play Adhan audio smoothly
- ✅ Handle multiple guilds without problems

---

## 📚 Additional Resources

- **Lavalink Documentation**: https://github.com/lavalink-devs/Lavalink
- **Wavelink (Python client)**: https://github.com/PythonistaGuild/Wavelink
- **Discord Support**: Join the Lavalink Discord for help

---

**Note**: You need Java 17+ installed to run Lavalink. Check with `java -version`.

