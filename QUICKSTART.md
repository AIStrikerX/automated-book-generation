# 🚀 Quick Start Guide

Get your book generation system running in under 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- (Optional) Supabase account for persistence

## Installation Steps

### Step 1: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

This installs:
- `groq` - For AI generation
- `supabase` - For database
- `python-docx` - For Word documents
- `python-dotenv` - For configuration
- `requests` - For notifications

### Step 2: Test Setup (30 seconds)

```bash
python test_setup.py
```

This verifies:
- All packages installed correctly
- Configuration is valid
- Groq API key works
- Modules load properly

### Step 3: Run Demo (1 minute)

```bash
python demo.py
```

Choose demo 1 for a quick overview!

## That's It! 🎉

The system is now ready to use. The Groq API key is already configured in the `.env` file.

---

## Understanding the Demo

### Demo 1: Full Automated Workflow
Shows complete book generation from start to finish in demo mode (no database needed).

### Demo 2: Workflow with Editor Feedback
Demonstrates the feedback and regeneration loop.

### Demo 3: Context Chaining
Shows how chapters build on previous chapters using summaries.

### Demo 4: Final Book Compilation
Generates actual .docx and .txt files you can open.

### Demo 5: Simple API Usage
Shows how to integrate this into your own applications.

---

## Using with Database (Optional)

If you want to persist data:

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project (free tier is fine)
3. Wait for project to be ready (~2 minutes)

### 2. Set Up Database

1. Open SQL Editor in Supabase dashboard
2. Copy contents of `schema.sql`
3. Paste and run

### 3. Update Configuration

Edit `.env` file:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Find these in: Project Settings → API

### 4. Test Again

```bash
python test_setup.py
```

Should now show Supabase configured!

---

## Basic Usage

### Create a Book

```python
from main import BookGenerationOrchestrator

orchestrator = BookGenerationOrchestrator()

book_id = orchestrator.start_new_book(
    title="Your Book Title",
    notes_on_outline_before="""
    Your requirements for the outline.
    What topics to cover, structure, etc.
    """
)

print(f"Book created: {book_id}")
```

### Run Workflow

```python
# This will run until it hits a review gate
orchestrator.run_full_workflow(book_id)
```

### Check Status

```python
orchestrator.print_status(book_id)
```

### Approve and Continue

In database (or via code):
```python
# Approve outline
orchestrator.db.update_outline_notes(
    book_id, 
    "", 
    "no_notes_needed"
)

# Continue workflow
orchestrator.run_full_workflow(book_id)
```

---

## Common Tasks

### Generate Outline Only

```python
book_id = orchestrator.start_new_book(title, notes)
# Outline is generated automatically
# Check database or logs for the outline
```

### Generate Single Chapter

```python
outline = orchestrator.db.get_outline(book_id)
chapters = orchestrator.outline_gen.parse_outline_into_chapters(outline['outline_text'])

# Generate first chapter
orchestrator.generate_chapter(book_id, chapters[0])
```

### Compile Book

```python
# After all chapters are approved
file_paths = orchestrator.compile_final_book(book_id, format='both')
print(f"DOCX: {file_paths['docx']}")
print(f"TXT: {file_paths['txt']}")
```

---

## File Locations

### Generated Books
- **Location**: `output/` directory
- **Formats**: `.docx` and `.txt`
- **Naming**: `{title}_{book_id}_{timestamp}.{ext}`

### Configuration
- **File**: `.env`
- **Contains**: API keys, database credentials, email settings

### Logs
- **Database**: `logs` table (if Supabase configured)
- **Console**: Real-time output
- **Notifications**: Email/Teams if configured

---

## Troubleshooting

### "GROQ_API_KEY is required"

**Solution**: Check `.env` file has the API key:
```env
GROQ_API_KEY=gsk_xxxx_YOUR_GROQ_KEY_1_HERE
```

### "Module not found"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### "Supabase credentials not configured"

**Note**: This is just a warning. System works in demo mode without Supabase.

To fix:
1. Create Supabase project
2. Run `schema.sql`
3. Update `.env` with credentials

### Demo doesn't start

**Check**:
1. Python version: `python --version` (should be 3.8+)
2. Packages installed: `pip list | grep groq`
3. Test setup: `python test_setup.py`

---

## Next Steps

### Explore the Code
- **main.py** - See the orchestration logic
- **chapter_generator.py** - See context chaining
- **db.py** - See database operations

### Read Documentation
- **README.md** - Complete user guide
- **ARCHITECTURE.md** - Technical deep dive
- **SUBMISSION.md** - Project overview

### Customize
- Change LLM model in `config.py`
- Modify prompts in generator files
- Add new output formats in `compiler.py`
- Extend notification channels in `notifier.py`

---

## Example: Complete Book Generation

```python
from main import BookGenerationOrchestrator
from config import Config

# Initialize
orc = BookGenerationOrchestrator()

# Create book
book_id = orc.start_new_book(
    title="Python for Data Science",
    notes_on_outline_before="""
    Create a practical guide for data scientists.
    Cover: Python basics, NumPy, Pandas, visualization,
    machine learning with scikit-learn, and real projects.
    Target: 10 chapters
    """
)

# Approve outline (normally editor does this)
orc.db.update_outline_notes(book_id, "", Config.NOTES_NOT_NEEDED)

# Generate all chapters
orc.generate_all_chapters(book_id)

# Approve each chapter (or use loop)
outline = orc.db.get_outline(book_id)
chapters = orc.outline_gen.parse_outline_into_chapters(outline['outline_text'])

for ch in chapters:
    orc.db.update_chapter_notes(
        book_id, 
        ch['chapter_number'], 
        "", 
        Config.NOTES_NOT_NEEDED
    )

# Compile final book
files = orc.compile_final_book(book_id)

print(f"✓ Book complete!")
print(f"DOCX: {files['docx']}")
print(f"TXT: {files['txt']}")
```

---

## Support

### Check Logs
```python
logs = orchestrator.db.get_logs(book_id)
for log in logs:
    print(f"{log['action']}: {log['status']}")
```

### Status Check
```python
status = orchestrator.get_book_status(book_id)
print(status)
```

### Re-run Test
```bash
python test_setup.py
```

---

## Tips

💡 **Start with Demo**: Run `python demo.py` first to understand the workflow

💡 **Demo Mode**: System works perfectly without Supabase for testing

💡 **Iterative**: Generate one chapter, review, then continue

💡 **Context Matters**: Previous chapter summaries are key to quality

💡 **Version Control**: Every outline and chapter iteration is saved

💡 **Notifications**: Set up email/Teams for real-world usage

---

**You're all set! Run `python demo.py` and see the magic happen! ✨**
