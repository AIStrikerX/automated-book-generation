# n8n Quick Start - 5 Minute Setup

## 🚀 Fastest Way to Get Started

### 1. Install n8n (Choose One)

**Cloud (Easiest)**
```bash
# Go to https://n8n.cloud
# Sign up (free tier available)
# Skip to Step 2
```

**Docker (Recommended)**
```bash
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

**NPM**
```bash
npm install n8n -g
n8n start
```

### 2. Access n8n
Open: `http://localhost:5678`

### 3. Import Workflow
1. Click **Workflows** → **Import**
2. Select: `n8n-workflow-book-generator.json`
3. Click **Import**

### 4. Set Environment Variables
Click **Settings** → **Environments** → Add:

```
GROQ_API_KEY=gsk_xxxx_YOUR_GROQ_KEY_1_HERE
GROQ_API_KEY_2=gsk_xxxx_YOUR_GROQ_KEY_2_HERE
GROQ_API_KEY_3=gsk_xxxx_YOUR_GROQ_KEY_3_HERE
GOOGLE_SHEET_ID=<YOUR_SHEET_ID>
SMTP_USER=hussain.ahmad67400@gmail.com
```

**Get Sheet ID**: Copy from URL `https://docs.google.com/spreadsheets/d/[THIS_PART]/edit`

### 5. Add Credentials

**Google Sheets:**
1. **Credentials** → **New** → **Google Sheets OAuth2**
2. Use Google Cloud Console OAuth credentials
3. Click **Connect** and authorize

**Gmail SMTP:**
1. **Credentials** → **New** → **SMTP**
2. Fill in:
   ```
   Host: smtp.gmail.com
   Port: 587
   User: hussain.ahmad67400@gmail.com
   Password: ulta yghd sfvj twqj
   ```

### 6. Activate Workflow
Click **Inactive** toggle → Should turn **Active** ✅

### 7. Test It!
Add to your Google Sheet:
```
Column A: "Test Book About AI"
Column B: "Make it beginner-friendly with 5 chapters"
```

Wait 2 minutes → Check email for outline!

---

## 🎯 Workflow Overview

```
Google Sheet → n8n Detects New Book → Groq Generates Outline → 
Email Sent → You Approve → Groq Generates Chapters → 
Book Compiled → Email with Book Sent ✅
```

---

## ⚡ Key Features

- ✅ **Auto-detects** new books in Google Sheet
- ✅ **Generates** AI outlines with Groq
- ✅ **Waits** for your approval
- ✅ **Creates** all chapters automatically
- ✅ **Rotates** between 3 API keys
- ✅ **Emails** you when done

---

## 🔧 Common Issues

**Workflow not running?**
- Check toggle is **Active**
- Verify sheet ID is correct

**API errors?**
- Check all 3 Groq keys are set
- Verify keys are valid

**Email not sending?**
- Check SMTP credentials
- Use app password, not regular password

---

## 📊 What Happens Next

1. **Every 2 minutes**: n8n checks your Google Sheet
2. **New book found**: Generates outline with AI
3. **Outline ready**: Sends you email notification
4. **You approve**: Write "no_notes_needed" in Column E
5. **Chapter generation**: AI writes all chapters
6. **Book complete**: Email with finished book

---

## 🎉 You're Done!

Your n8n automation is now running 24/7!

**Dashboard**: http://localhost:5678
**Executions**: Click tab to see logs
**Stop**: docker stop n8n (or Ctrl+C)

---

## 📚 Full Documentation

For detailed setup, troubleshooting, and advanced features:
- Read: `N8N_SETUP_GUIDE.md`
- Python version: `sheets_poller.py`
- API rotation details: `API_KEY_ROTATION.md`

---

**Status**: ✅ Ready to Generate Books!
**Support**: Both Python & n8n systems available
