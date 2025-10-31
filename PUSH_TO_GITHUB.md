# 🚀 Push Athan Bot to GitHub

This guide will help you upload your Athan bot to GitHub **WITHOUT exposing any secrets**.

## ✅ What's Protected

The following files are **AUTOMATICALLY EXCLUDED** by `.gitignore`:

- ✅ `.env` - Your environment variables
- ✅ `DISCORD_TOKEN.txt` - Your bot token
- ✅ `data/` - Your SQLite database
- ✅ `*.db` - All database files
- ✅ `__pycache__/` - Python cache
- ✅ `venv/` - Virtual environment
- ✅ `.vscode/` - VS Code settings

## 🔐 Security Checklist

Before pushing, verify no secrets are in the code:

```powershell
# Search for your Discord token in the code
Select-String -Path "src\*" -Pattern "MTQzMzQ2MzMxMjAyMDE0NDE4OQ" -Recurse

# Search for API keys in the code
Select-String -Path "src\*" -Pattern "98bf8d87cba26cf8385073856fad9229" -Recurse
```

**Both commands should return NO results!** ✅

## 📤 Push to GitHub

### Step 1: Initialize Git (if not already done)

```bash
git init
```

### Step 2: Add All Files

```bash
git add .
```

### Step 3: Check What Will Be Committed

```bash
# This should NOT show .env, DISCORD_TOKEN.txt, or data/
git status
```

**⚠️ If you see sensitive files, STOP and update .gitignore!**

### Step 4: Commit

```bash
git commit -m "Initial commit: Athan Discord bot with prayer times and voice Adhan"
```

### Step 5: Add Remote Repository

```bash
git remote add origin https://github.com/S8nm/Athan.git
```

### Step 6: Push to GitHub

```bash
# For first push
git push -u origin main

# Or if your branch is 'master'
git push -u origin master
```

## 🔄 Future Updates

After the initial push, update your GitHub repo with:

```bash
git add .
git commit -m "Your commit message here"
git push
```

## 📝 Update README

Don't forget to replace `SETUP_GITHUB.md` with `README.md`:

```bash
# Backup current README
mv README.md README_OLD.md

# Use the GitHub-ready README
mv SETUP_GITHUB.md README.md

# Commit the change
git add README.md README_OLD.md
git commit -m "docs: Update README for GitHub"
git push
```

## 🌟 Make Repository Public (Optional)

1. Go to https://github.com/S8nm/Athan/settings
2. Scroll down to "Danger Zone"
3. Click "Change repository visibility"
4. Select "Make public"

## 🎉 Done!

Your bot is now on GitHub! Share the link:
**https://github.com/S8nm/Athan**

---

## ⚠️ EMERGENCY: Leaked Token?

If you accidentally pushed your Discord token:

1. **IMMEDIATELY** regenerate your token:
   - Go to https://discord.com/developers/applications/1433463312020144189/bot
   - Click "Reset Token"
   - Update your `.env` file with the new token

2. **Remove the token from Git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env DISCORD_TOKEN.txt" \
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   ```

3. **Or use BFG Repo-Cleaner** (easier):
   - Download: https://rtyley.github.io/bfg-repo-cleaner/
   - Run: `bfg --replace-text secrets.txt`

---

**Remember: Never commit secrets to GitHub!** 🔐

