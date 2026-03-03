# Google Sheets Integration Guide

This guide will walk you through setting up Google Sheets integration for your book generation system. This enables a human-in-the-loop workflow where editors can request books, review outlines, and provide feedback all through a Google Sheet.

---

## Overview

**What This Does:**
- Editors add book titles and notes to a Google Sheet
- System polls the sheet every 2 minutes for new requests
- AI generates outlines and writes them back to the sheet
- Editors review outlines and either approve or request changes
- System proceeds to chapter generation when approved

**Time Required:** 20-25 minutes for first-time setup

---

## Step 1: Google Cloud Console Setup (15 minutes)

### 1.1 Create a New Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Sign in with your Google account
3. Click **"Select a Project"** at the top of the page
4. Click **"NEW PROJECT"** button
5. Name your project: `BookGenerator`
6. Click **"CREATE"**
7. Wait for the project to be created (takes ~30 seconds)

### 1.2 Enable Required APIs

1. In the left sidebar, click **"APIs & Services"** → **"Library"**
2. Search for `Google Sheets API`
3. Click on it → Click **"ENABLE"**
4. Wait for it to enable (~10 seconds)
5. Click the back button in your browser
6. Search for `Google Drive API`
7. Click on it → Click **"ENABLE"**

### 1.3 Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"** (left sidebar)
2. Click **"CREATE CREDENTIALS"** button at the top
3. Select **"Service Account"**
4. Fill in the details:
   - Service account name: `bookgenerator-service`
   - Service account ID: (auto-filled, leave as is)
   - Description: `Service account for automated book generation`
5. Click **"CREATE AND CONTINUE"**
6. Skip the optional steps (Grant access, Grant users access)
7. Click **"DONE"**

### 1.4 Download JSON Credentials

1. You'll see your service account listed in the credentials page
2. Click on the service account email (looks like `bookgenerator-service@your-project.iam.gserviceaccount.com`)
3. Go to the **"KEYS"** tab
4. Click **"ADD KEY"** → **"Create new key"**
5. Choose **JSON** format
6. Click **"CREATE"**
7. A JSON file will download automatically
8. **IMPORTANT:** Rename this file to `credentials.json`
9. **IMPORTANT:** Move it to your project folder: `h:\automated_book_generation\credentials.json`

**⚠️ Security Note:** This file contains sensitive credentials. Never commit it to git or share it publicly.

---

## Step 2: Create Google Sheet (5 minutes)

### 2.1 Create the Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Click **"Blank"** to create a new spreadsheet
3. Name it **exactly** `BookGenerator` (capital B and G)

### 2.2 Set Up Column Headers

In Row 1, add these **exact** headers (case-sensitive):

| Column | Header Name |
|--------|-------------|
| A1 | `title` |
| B1 | `notes_on_outline_before` |
| C1 | `outline` |
| D1 | `notes_on_outline_after` |
| E1 | `status_outline_notes` |
| F1 | `book_status` |

**What Each Column Does:**
- **A (title):** Book title entered by editor
- **B (notes_on_outline_before):** Instructions for outline generation
- **C (outline):** AI-generated outline (automatically filled)
- **D (notes_on_outline_after):** Editor feedback for revision
- **E (status_outline_notes):** Editor's decision (`no`, `yes`, or `no_notes_needed`)
- **F (book_status):** System status updates (automatically filled)

### 2.3 Share Sheet with Service Account

1. Open your `credentials.json` file in a text editor
2. Find the line that says `"client_email":`
3. Copy the email address (looks like `bookgenerator-service@your-project.iam.gserviceaccount.com`)
4. Go back to your Google Sheet
5. Click the **"Share"** button (top right)
6. Paste the service account email
7. Make sure it has **"Editor"** access (not just Viewer)
8. **UNCHECK** "Notify people" (it's a bot, not a person)
9. Click **"Send"** or **"Done"**

---

## Step 3: Verify Installation

The required packages (`gspread` and `google-auth`) have already been installed. 

To verify, run:

```powershell
H:/automated_book_generation/.venv/Scripts/python.exe -c "import gspread; import google.auth; print('✅ Packages installed')"
```

---

## Step 4: Test the Integration

### 4.1 Add a Test Book

In your Google Sheet, fill in row 2:

| Column | Value |
|--------|-------|
| A2 | `The Future of Artificial Intelligence` |
| B2 | `Focus on machine learning, ethics, job impact, and future predictions. Make it beginner friendly.` |
| C2 | (leave empty) |
| D2 | (leave empty) |
| E2 | (leave empty) |
| F2 | (leave empty) |

### 4.2 Start the Poller

Run the following command in your terminal:

```powershell
cd h:\automated_book_generation
.\.venv\Scripts\python.exe main.py
```

**You should see:**
```
✅ Google Sheets connected!
============================================================
🔄 GOOGLE SHEETS POLLING STARTED
============================================================
📊 Checking sheet every 2 minutes for new books...
📝 Add a title + notes to your sheet to start!
============================================================

📖 Found new book: The Future of Artificial Intelligence
...
✅ Outline ready! Check your Google Sheet row 2
```

### 4.3 Check the Sheet

Within 30-60 seconds:
- Column C should now contain a detailed outline
- Column E should show `no`
- Column F should show `outline_ready_for_review`

---

## Step 5: Editor Workflow

### To Approve an Outline

1. Read the outline in Column C
2. If you're happy with it, type `no_notes_needed` in Column E
3. On the next polling cycle (within 2 minutes), the system will:
   - Generate all chapters
   - Compile the final book
   - Save it to the `output/` folder
   - Update Column F to `complete`

### To Request Changes

1. Read the outline in Column C
2. Type your feedback in Column D (e.g., "Add more focus on AI ethics and safety concerns")
3. Type `yes` in Column E to indicate you have notes
4. On the next polling cycle, the system will:
   - Regenerate the outline with your feedback
   - Write the new outline to Column C
   - Reset Column E to `no` (waiting for your review again)

---

## Troubleshooting

### Error: "credentials.json not found"

**Solution:**
- Make sure you downloaded the JSON key from Google Cloud Console
- Rename it to exactly `credentials.json`
- Place it in `h:\automated_book_generation\` folder (same folder as main.py)

### Error: "Spreadsheet not found"

**Solution:**
- Make sure your sheet is named exactly `BookGenerator` (capital B and G)
- Make sure you shared it with the service account email from your credentials.json
- Check the service account has Editor access (not just Viewer)

### Error: "Permission denied"

**Solution:**
- Open your sheet's Share settings
- Verify the service account email is listed
- Make sure it has "Editor" permission
- Try removing and re-adding the service account

### The poller doesn't detect new books

**Solution:**
- Make sure you filled in both Column A (title) AND Column B (notes)
- Column C (outline) must be empty for it to be detected as "new"
- Wait up to 2 minutes for the next polling cycle

### Columns are out of order

**Solution:**
The headers must be in this exact order:
1. Column A = `title`
2. Column B = `notes_on_outline_before`
3. Column C = `outline`
4. Column D = `notes_on_outline_after`
5. Column E = `status_outline_notes`
6. Column F = `book_status`

---

## Usage Tips

### Running in Background (Windows)

To keep the poller running even when you close the terminal:

```powershell
Start-Process -WindowStyle Hidden -FilePath "H:/automated_book_generation/.venv/Scripts/python.exe" -ArgumentList "main.py"
```

### Stopping the Poller

- If running in foreground: Press `Ctrl+C`
- If running in background: Use Task Manager to end the python.exe process

### Adding Multiple Books

You can add multiple rows to the sheet at once. The system will process them one at a time in the order they appear.

### Monitoring Progress

Watch Column F (book_status) for real-time updates:
- `generating_outline` → AI is creating the outline
- `outline_ready_for_review` → Waiting for your review
- `regenerating_outline` → Updating based on your feedback
- `chapters_in_progress` → Generating all chapters
- `complete` → Book is done! Check the output folder

---

## File Structure Reference

After setup, your project should have:

```
h:\automated_book_generation\
├── main.py                    # Orchestrator (now with polling)
├── sheets_connector.py        # NEW: Google Sheets integration
├── credentials.json           # NEW: Your service account credentials
├── db.py                      # Database operations
├── outline_generator.py       # Outline generation
├── chapter_generator.py       # Chapter generation
├── summarizer.py              # Context summarization
├── compiler.py                # Book compilation
├── notifier.py                # Notifications
├── config.py                  # Configuration
├── demo.py                    # Demo scripts
├── test_setup.py              # Setup verification
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── output/                    # Generated books
```

---

## Next Steps

1. ✅ Complete the Google Cloud setup
2. ✅ Create and share your Google Sheet
3. ✅ Add a test book to the sheet
4. ✅ Run `python main.py` to start polling
5. ✅ Review the generated outline
6. ✅ Approve or provide feedback
7. ✅ Get your completed book!

---

## Additional Resources

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Cloud Console](https://console.cloud.google.com)
- [gspread Python Library](https://docs.gspread.org/)

---

## Questions or Issues?

If you encounter any problems not covered in this guide:

1. Check that `credentials.json` is in the right location
2. Verify the sheet name is exactly `BookGenerator`
3. Confirm the service account has Editor access
4. Make sure column headers are spelled correctly
5. Check that you filled in both title AND notes columns

The system will print detailed error messages to help you diagnose issues.
