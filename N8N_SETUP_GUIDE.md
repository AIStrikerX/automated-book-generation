# n8n Automation Workflow - Complete Setup Guide

## 🎯 Overview

This n8n workflow provides a **visual, no-code automation** alternative to the Python-based system. It connects:
- ✅ **Google Sheets** (Human-in-the-loop interface)
- ✅ **Groq API** (AI text generation with 3-key rotation)
- ✅ **Email Notifications** (Gmail SMTP)
- ✅ **Automated Book Generation** (Outline → Chapters → Compilation)

---

## 📋 Prerequisites

### 1. n8n Installation

**Option A: Cloud (Recommended for Beginners)**
```bash
# Sign up at n8n.cloud
https://n8n.cloud
```

**Option B: Self-Hosted (Docker)**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

**Option C: Self-Hosted (npm)**
```bash
npm install n8n -g
n8n start
```

### 2. Required Accounts
- ✅ Google Cloud Console (already set up)
- ✅ Groq API (3 keys configured)
- ✅ Gmail Account (already configured)

---

## 🚀 Step-by-Step Setup

### Step 1: Install n8n

1. **Access n8n**:
   - Cloud: Log into your n8n.cloud account
   - Self-hosted: Open `http://localhost:5678`

2. **Create Account** (first time only):
   - Set up your admin credentials
   - Complete the welcome wizard

### Step 2: Configure Credentials

#### A. Google Sheets OAuth2

1. In n8n, go to **Credentials** → **New**
2. Select **Google Sheets OAuth2 API**
3. Fill in:
   ```
   Client ID: (from Google Cloud Console)
   Client Secret: (from Google Cloud Console)
   ```
4. Click **Connect my account**
5. Authorize access to Google Sheets

**Get OAuth Credentials:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project: `bookgenerator-489115`
3. Go to **APIs & Services** → **Credentials**
4. Click **+ CREATE CREDENTIALS** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Name: `n8n-book-generator`
7. Authorized redirect URIs:
   - `https://your-n8n-instance.com/rest/oauth2-credential/callback`
   - OR `http://localhost:5678/rest/oauth2-credential/callback`
8. Copy **Client ID** and **Client Secret**

#### B. Gmail SMTP

1. In n8n, go to **Credentials** → **New**
2. Select **SMTP**
3. Fill in:
   ```
   User: hussain.ahmad67400@gmail.com
   Password: ulta yghd sfvj twqj
   Host: smtp.gmail.com
   Port: 587
   ```
4. Save as "Gmail SMTP"

### Step 3: Set Environment Variables

1. In n8n, go to **Settings** → **Environments**
2. Add these variables:

```bash
# Groq API Keys (for rotation)
GROQ_API_KEY=gsk_xxxx_YOUR_GROQ_KEY_1_HERE
GROQ_API_KEY_2=gsk_xxxx_YOUR_GROQ_KEY_2_HERE
GROQ_API_KEY_3=gsk_xxxx_YOUR_GROQ_KEY_3_HERE

# Google Sheet ID
GOOGLE_SHEET_ID=your_google_sheet_id_here

# Email
SMTP_USER=hussain.ahmad67400@gmail.com
```

**To get your Google Sheet ID:**
- Open your "BookGenerator" sheet
- Copy the ID from the URL: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`

### Step 4: Import the Workflow

1. In n8n, click **Workflows** → **Import from File**
2. Select `n8n-workflow-book-generator.json`
3. Click **Import**
4. The workflow will appear in your canvas

### Step 5: Configure Node Connections

1. **Update Credentials** in each node:
   - All "Google Sheets" nodes → Select your Google Sheets OAuth2 credential
   - All "Email Send" nodes → Select your Gmail SMTP credential

2. **Verify Environment Variables**:
   - Click on any Groq API node
   - Check that `{{ $env.GROQ_API_KEY }}` is properly set

### Step 6: Activate the Workflow

1. Click the **Inactive** toggle at the top
2. It should turn to **Active**
3. The workflow is now polling Google Sheets every 2 minutes

---

## 📊 Workflow Architecture

### Visual Flow Diagram

```
┌─────────────────────┐
│  Google Sheets      │  ← Poll every 2 minutes
│  (Trigger)          │
└──────────┬──────────┘
           │
           ├────────────────────────────────┐
           │                                │
           v                                v
  ┌────────────────┐              ┌────────────────┐
  │ Needs Outline? │              │ Outline Ready? │
  └────────┬───────┘              └────────┬───────┘
           │                                │
           v                                v
  ┌────────────────┐              ┌────────────────┐
  │ Generate       │              │ Generate       │
  │ Outline        │              │ Chapters       │
  │ (Groq API)     │              │ (Groq API)     │
  └────────┬───────┘              └────────┬───────┘
           │                                │
           v                                v
  ┌────────────────┐              ┌────────────────┐
  │ Write to       │              │ Loop Through   │
  │ Google Sheet   │              │ Chapters       │
  └────────┬───────┘              └────────┬───────┘
           │                                │
           v                                v
  ┌────────────────┐              ┌────────────────┐
  │ Send Email:    │              │ Compile Book   │
  │ Outline Ready  │              │                │
  └────────────────┘              └────────┬───────┘
                                           │
                                           v
                                  ┌────────────────┐
                                  │ Send Email:    │
                                  │ Book Complete  │
                                  └────────────────┘
```

### Node Descriptions

| Node | Purpose | API Used |
|------|---------|----------|
| **Google Sheets Trigger** | Polls sheet every 2 minutes | Google Sheets API |
| **Check: Needs Outline?** | IF conditions check | None |
| **Generate Outline (Groq)** | Call Groq API to create outline | Groq API (Key 1) |
| **Write Outline to Sheet** | Update Column C | Google Sheets API |
| **Update Status** | Update Column F | Google Sheets API |
| **Send Email: Outline Ready** | Notify via email | Gmail SMTP |
| **Check: Outline Approved?** | Check if user said "no_notes_needed" | None |
| **Parse Outline into Chapters** | JavaScript code to extract chapters | None |
| **Loop Through Chapters** | SplitInBatches node | None |
| **Generate Chapter (Groq)** | Call Groq API for each chapter | Groq API (Key 1) |
| **Store Chapter** | Save to workflow memory | None |
| **Compile Book** | Merge all chapters into one document | None |
| **Send Email: Book Complete** | Notify with attachment | Gmail SMTP |

---

## 🔑 API Key Rotation (Built-in)

### How It Works

The workflow includes **3 separate Groq API nodes** for automatic fallback:

1. **Primary Node**: Uses `GROQ_API_KEY`
2. **Fallback Node 1**: Uses `GROQ_API_KEY_2` (triggers on error)
3. **Fallback Node 2**: Uses `GROQ_API_KEY_3` (final fallback)

### Retry Settings

Each Groq API node has:
- ✅ **Retry on Fail**: Enabled
- ✅ **Max Tries**: 3 attempts
- ✅ **Wait Between Tries**: 10-30 seconds

### Manual Key Rotation

If you want to manually switch keys:
1. Click on any Groq API node
2. Change `{{ $env.GROQ_API_KEY }}` to `{{ $env.GROQ_API_KEY_2 }}`
3. Save the workflow

---

## 📝 Usage Guide

### A. Generate a New Book

1. **Add to Google Sheet**:
   ```
   Column A (title): "The History of Space Exploration"
   Column B (notes_on_outline_before): "Focus on moon landing, Mars missions, and future plans"
   ```

2. **Wait 2 Minutes**:
   - n8n polls and detects new entry
   - Generates outline using Groq API
   - Writes outline to Column C
   - Updates status in Column F to "outline_ready_for_review"
   - Sends you an email notification

3. **Review Outline**:
   - Check the generated outline in Column C
   - Option 1: Approve → Write `no_notes_needed` in Column E
   - Option 2: Request changes → Write `yes` in Column E and feedback in Column D

4. **If Approved**:
   - n8n detects approval
   - Parses outline into chapters (e.g., 12 chapters)
   - Generates each chapter sequentially
   - Uses API key rotation if rate limit is hit
   - Compiles all chapters into one document
   - Updates status to "complete"
   - Sends email with the finished book

### B. Regenerate Outline with Feedback

1. **Provide Feedback**:
   ```
   Column D (notes_on_outline_after): "Add more details about SpaceX and include chapter on space tourism"
   Column E (status_outline_notes): "yes"
   ```

2. **Automatic Processing**:
   - n8n detects feedback
   - Calls Groq API with feedback
   - Updates outline in Column C
   - Clears Column D and E for next round

### C. Monitor Progress

1. **Google Sheet Status** (Column F):
   - `generating_outline` → AI is creating outline
   - `outline_ready_for_review` → Check your email and review
   - `chapters_in_progress` → Generating chapters (this takes time)
   - `complete` → Book is ready!

2. **n8n Execution Log**:
   - Go to **Executions** tab
   - See real-time progress of each workflow run
   - View errors and debug if needed

3. **Email Notifications**:
   - "📝 Book Outline Ready" → Review and approve
   - "🎉 Book Complete" → Download your book

---

## 🎨 Visual Workflow Editor

### How to Use n8n's Canvas

1. **Zoom**: Mouse wheel or pinch gesture
2. **Pan**: Click and drag background
3. **Add Node**: Click **+** or drag from existing node
4. **Edit Node**: Click on any node to open settings
5. **Test Node**: Click **Execute Node** to test individually
6. **Test Workflow**: Click **Execute Workflow** to test entire flow

### Debugging Tips

1. **View Data Flow**:
   - Click on any connection line
   - See the data passing through

2. **Inspect Errors**:
   - Failed nodes turn red
   - Click to see error message
   - Check API key validity

3. **Manual Execution**:
   - Click **Execute Workflow**
   - Manually trigger without waiting for poll

---

## ⚙️ Advanced Configuration

### A. Change Polling Frequency

1. Click on **Google Sheets Trigger** node
2. Change **Poll Times** from 2 minutes to desired interval
3. Options: Every minute, 5 minutes, hourly

### B. Customize Email Templates

1. Click on **Send Email: Outline Ready** node
2. Edit **Message** field with HTML:
   ```html
   <h1>Custom Header</h1>
   <p>Your outline for <strong>{{ $json.title }}</strong> is ready!</p>
   <a href="https://yourdomain.com">View Book</a>
   ```

### C. Add More AI Models

Want to use GPT-4, Claude, or other LLMs?

1. **Add HTTP Request Node**
2. **Configure API**:
   ```
   URL: https://api.openai.com/v1/chat/completions
   Headers: Authorization: Bearer YOUR_OPENAI_KEY
   Body: { "model": "gpt-4", "messages": [...] }
   ```
3. **Connect to workflow**

### D. Add Database Storage

1. **Add PostgreSQL/MySQL Node**
2. **Connect after "Store Chapter"**
3. **Save chapters to database**:
   ```sql
   INSERT INTO chapters (book_id, chapter_number, content)
   VALUES ({{ $json.book_id }}, {{ $json.chapter_number }}, {{ $json.content }})
   ```

### E. Add Slack/Teams Notifications

1. **Add Slack/Microsoft Teams node**
2. **Configure webhook**
3. **Send notifications** instead of/in addition to email

---

## 🔧 Troubleshooting

### Issue 1: Workflow Not Triggering

**Symptoms**: No executions showing up

**Solutions**:
1. Check workflow is **Active** (toggle at top)
2. Verify Google Sheet ID in environment variables
3. Check Google Sheets OAuth2 credential is connected
4. Manually execute to test: Click **Execute Workflow**

### Issue 2: Groq API Rate Limit

**Symptoms**: Error 429 in Groq API nodes

**Solutions**:
1. Wait for rate limit to reset (shown in error message)
2. Verify all 3 API keys are configured
3. Check fallback nodes are connected
4. Increase **Wait Between Tries** to 60 seconds

### Issue 3: Email Not Sending

**Symptoms**: Email node fails

**Solutions**:
1. Check Gmail SMTP credential
2. Verify app password (not regular Gmail password)
3. Check SMTP settings: smtp.gmail.com:587
4. Enable "Less secure app access" in Gmail settings (if needed)

### Issue 4: Chapters Not Generating

**Symptoms**: Workflow stops at "Loop Through Chapters"

**Solutions**:
1. Check outline format in Column C
2. Verify JavaScript parsing in "Parse Outline into Chapters"
3. Test with smaller book (3-5 chapters)
4. Check Groq API quota

### Issue 5: Google Sheets Permission Denied

**Symptoms**: Error accessing sheet

**Solutions**:
1. Share sheet with service account email
2. Check OAuth2 scope includes sheets.read and sheets.write
3. Refresh OAuth2 connection in n8n
4. Verify sheet ID in environment variables

---

## 📊 Performance Comparison

### n8n vs Python System

| Feature | n8n Workflow | Python System | Winner |
|---------|--------------|---------------|--------|
| **Setup Time** | 30 minutes | 2 hours | 🏆 n8n |
| **Coding Required** | No | Yes | 🏆 n8n |
| **Visual Interface** | ✅ Yes | ❌ No | 🏆 n8n |
| **Debugging** | Easy (visual) | Medium (logs) | 🏆 n8n |
| **Extensibility** | High (drag & drop) | High (code) | 🤝 Tie |
| **Performance** | Good | Excellent | 🏆 Python |
| **API Key Rotation** | Manual setup | Automatic | 🏆 Python |
| **Chapter Caching** | Workflow memory | File system | 🏆 Python |
| **Cost** | $20/mo (cloud) | Free (self-hosted) | 🏆 Python |
| **Maintenance** | Low | Medium | 🏆 n8n |

### Recommendation

- **Use n8n if**: You want visual workflow, no coding, easy setup
- **Use Python if**: You want maximum control, better performance, advanced features
- **Use Both**: n8n for simple books, Python for complex projects

---

## 🎯 Use Cases

### Use Case 1: Marketing Agency
**Scenario**: Generate eBooks for multiple clients

**Setup**:
- One Google Sheet per client
- Separate n8n workflows
- Automated delivery via email
- Client branding in templates

### Use Case 2: Educational Institution
**Scenario**: Create course materials automatically

**Setup**:
- Professors add topics to sheet
- AI generates study guides
- Review and approve before distribution
- Store in shared drive

### Use Case 3: Content Creator
**Scenario**: Write blog series or newsletter content

**Setup**:
- Add blog titles to sheet
- AI generates outlines
- Approve and generate posts
- Auto-publish to WordPress (add WP node)

---

## 🚀 Next Steps

### 1. Test Your Workflow

```bash
# Add test book to Google Sheet
Title: "Test Book"
Notes: "Write a short 3-chapter book about automation"
```

Wait 2 minutes and monitor:
- ✅ n8n execution log
- ✅ Google Sheet updates
- ✅ Email inbox

### 2. Customize for Your Needs

- Adjust polling frequency
- Modify email templates
- Add your branding
- Connect additional services

### 3. Scale Up

- Add more API keys
- Increase chapter generation speed
- Set up multiple workflows
- Add analytics tracking

### 4. Integrate with Other Tools

**Possible Integrations**:
- ✅ WordPress (auto-publish)
- ✅ Dropbox (save books)
- ✅ Airtable (database)
- ✅ Zapier (extended automation)
- ✅ Notion (documentation)
- ✅ Discord/Slack (notifications)

---

## 📚 Resources

### Official Documentation
- [n8n Documentation](https://docs.n8n.io)
- [Groq API Docs](https://console.groq.com/docs)
- [Google Sheets API](https://developers.google.com/sheets/api)

### Video Tutorials
- [n8n Crash Course](https://www.youtube.com/watch?v=RpjQTGKm-ok)
- [Google Sheets Integration](https://www.youtube.com/watch?v=_L7u8DkLkXo)

### Community
- [n8n Community Forum](https://community.n8n.io)
- [Discord Server](https://discord.gg/n8n)

---

## ✅ Checklist

Before going live, ensure:
- [ ] n8n installed and accessible
- [ ] Google Sheets OAuth2 configured
- [ ] Gmail SMTP credential added
- [ ] 3 Groq API keys in environment variables
- [ ] Google Sheet ID set correctly
- [ ] Workflow imported successfully
- [ ] All nodes have correct credentials
- [ ] Workflow activated (toggle ON)
- [ ] Test book generated successfully
- [ ] Email notifications received

---

## 🎉 Success!

Your n8n automation workflow is now ready to generate books automatically!

**Status**: ✅ Fully Configured with Visual Workflow
**Monitoring**: n8n Dashboard + Email Notifications
**Support**: Both Python and n8n systems running in parallel

Now you have **two powerful systems** working together:
1. **Python System** (sheets_poller.py) - Advanced features, API rotation, caching
2. **n8n Workflow** - Visual, no-code, easy to modify

Choose the one that fits your workflow best, or run both! 🚀
