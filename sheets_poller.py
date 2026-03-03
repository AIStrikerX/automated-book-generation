"""
Google Sheets poller with Supabase database sync
Polls Google Sheets for book generation tasks and syncs results to Supabase
"""
from sheets_connector import GoogleSheetsConnector
from outline_generator import OutlineGenerator
from chapter_generator import ChapterGenerator
from summarizer import Summarizer
from compiler import BookCompiler
from notifier import Notifier
from config import Config
from chapter_cache import ChapterCache
from db import DatabaseManager
import time
import traceback


class SimpleBookGenerator:
    """Book generator with Supabase database sync"""
    
    def __init__(self):
        """Initialize components"""
        self.outline_gen = OutlineGenerator()
        self.chapter_gen = ChapterGenerator()
        self.summarizer = Summarizer()
        self.compiler = BookCompiler()
        self.cache = ChapterCache()
        print("✅ Book generator initialized")
        print("✅ Chapter caching enabled")
    
    def generate_outline(self, title: str, notes: str) -> str:
        """Generate outline"""
        print(f"\n📝 Generating outline for: {title}")
        try:
            outline = self.outline_gen.generate_outline(title, notes)
            print(f"✅ Outline generated ({len(outline)} chars)")
            return outline
        except Exception as e:
            print(f"❌ Error generating outline: {e}")
            raise
    
    def regenerate_outline(self, title: str, old_outline: str, feedback: str) -> str:
        """Regenerate outline with feedback"""
        print(f"\n🔄 Regenerating outline with feedback...")
        outline = self.outline_gen.regenerate_outline(
            title,
            old_outline,
            feedback
        )
        return outline
    
    def generate_full_book(self, title: str, outline: str, db: 'DatabaseManager' = None, db_book_id: str = None) -> str:
        """Generate all chapters and compile"""
        print(f"\n📚 Starting full book generation for: {title}")
        
        # Generate a stable book_id based on title (for cache consistency)
        import hashlib
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        book_id = f"book_{title_hash}"
        
        # Check if we have cached chapters
        cached_chapters = self.cache.load_chapters(book_id)
        if cached_chapters:
            print(f"📂 Found {len(cached_chapters)} cached chapters, resuming...")
            chapters = cached_chapters
            chapter_data_list = self.outline_gen.parse_outline_into_chapters(outline)
            start_from = len(cached_chapters) + 1
        else:
            # Save outline to cache
            self.cache.save_outline(book_id, title, outline)
            chapters = []
            start_from = 1
        
        # Parse outline into chapters
        chapter_data_list = self.outline_gen.parse_outline_into_chapters(outline)
        print(f"  Found {len(chapter_data_list)} chapters")
        
        if start_from > 1:
            print(f"  Starting from chapter {start_from}/{len(chapter_data_list)}")
        
        # Build previous summaries from cached chapters
        previous_summaries = []
        for cached in chapters:
            # Use first 500 chars as summary
            previous_summaries.append(cached['content'][:500] + "...")
        
        # Generate remaining chapters
        for chapter_info in chapter_data_list[start_from-1:]:
            i = chapter_info['chapter_number']
            chapter_title = chapter_info['title']
            chapter_description = chapter_info['description']
            
            print(f"\n  📖 Chapter {i}/{len(chapter_data_list)}: {chapter_title}")
            
            try:
                # Generate chapter with context from previous chapters
                chapter_text = self.chapter_gen.generate_chapter(
                    title=title,
                    chapter_number=i,
                    chapter_title=chapter_title,
                    chapter_description=chapter_description,
                    previous_summaries=previous_summaries,
                    chapter_notes=""
                )
                
                chapter_data = {
                    'chapter_number': i,
                    'chapter_title': chapter_title,
                    'content': chapter_text
                }
                chapters.append(chapter_data)
                
                # Save to cache immediately
                self.cache.save_chapter(book_id, i, chapter_data)
                
                # Create summary for next chapter's context (skip if rate limited)
                chapter_summary = ""
                try:
                    summary = self.summarizer.summarize_chapter(
                        chapter_text,
                        i,
                        chapter_title
                    )
                    chapter_summary = summary
                    previous_summaries.append(summary)
                except Exception as e:
                    if 'rate_limit' in str(e).lower() or '429' in str(e):
                        print(f"    ⚠️  Rate limit reached, skipping summary (chapters will still be generated)")
                        # Use a simple excerpt as fallback summary
                        fallback_summary = chapter_text[:500] + "..."
                        chapter_summary = fallback_summary
                        previous_summaries.append(fallback_summary)
                    else:
                        raise
                
                # Sync chapter to Supabase (non-fatal)
                if db and db_book_id:
                    try:
                        db.create_chapter(
                            book_id=db_book_id,
                            chapter_number=i,
                            content=chapter_text,
                            summary=chapter_summary,
                            outline_section=chapter_title
                        )
                        db.log_action(db_book_id, 'chapter_generated', 'completed',
                                      f'Chapter {i}: {chapter_title}')
                        print(f"    💾 Synced chapter {i} to Supabase")
                    except Exception as db_err:
                        print(f"    ⚠️  DB sync error (non-fatal): {db_err}")
            
            except Exception as e:
                if 'rate_limit' in str(e).lower() or '429' in str(e):
                    print(f"\n⏸️  Rate limit reached on chapter {i}. Progress saved!")
                    print(f"    Generated {len(chapters)}/{len(chapter_data_list)} chapters so far")
                    print(f"    The system will resume automatically when the rate limit resets")
                    return None  # Exit gracefully, will retry on next poll
                else:
                    raise
        
        print(f"\n✅ All {len(chapters)} chapters generated!")
        
        # Clear cache since we're done
        self.cache.clear_cache(book_id)
        
        # Compile the book (use timestamp-based ID for final output)
        import time
        output_book_id = f"book_{int(time.time())}"
        print(f"\n📦 Compiling final book...")
        result = self.compiler.compile_both_formats(
            title=title,
            chapters=chapters,
            book_id=output_book_id
        )
        
        print(f"\n🎉 Book complete!")
        print(f"   📄 DOCX: {result['docx']}")
        print(f"   📝 TXT:  {result['txt']}")
        if result.get('pdf'):
            print(f"   📕 PDF:  {result['pdf']}")
        
        return result['docx']


def poll_google_sheets_simple():
    """
    Google Sheets polling with Supabase database sync
    """
    try:
        sheets = GoogleSheetsConnector()
    except Exception as e:
        print(f"❌ Failed to connect to Google Sheets: {e}")
        print("📝 Make sure you've completed the Google Cloud setup steps.")
        print("\nSteps:")
        print("1. Enable Google Sheets API & Drive API for your project")
        print("2. Download credentials.json to this folder")
        print("3. Share your 'BookGenerator' sheet with the service account email")
        return
    
    generator = SimpleBookGenerator()
    notifier = Notifier()
    db = DatabaseManager()
    
    # Track processed books to avoid duplicates
    processed_books = {}
    
    print("\n" + "="*60)
    print("🔄 GOOGLE SHEETS POLLING STARTED")
    print("="*60)
    print("📊 Checking sheet every 2 minutes for new books...")
    print("📝 Add a title + notes to your sheet to start!")
    if db.client:
        print("💾 Supabase database sync: ENABLED")
    else:
        print("⚠️  Supabase database sync: DISABLED (check credentials)")
    print("="*60 + "\n")
    
    while True:
        try:
            # Check for new books waiting for outline generation
            pending = sheets.get_pending_books()
            
            for book_data in pending:
                title = book_data['title']
                row_num = book_data['row_number']
                
                # Skip if already processed
                if row_num in processed_books:
                    continue
                
                print(f"\n📖 Found new book: {title}")
                sheets.update_book_status(row_num, 'generating_outline')
                
                # Create book record in Supabase (non-fatal)
                db_book_id = None
                try:
                    db_book = db.create_book(title, book_data.get('notes_on_outline_before', ''))
                    db_book_id = db_book.get('id')
                    db.log_action(db_book_id, 'book_created', 'completed', f'Sheet row {row_num}')
                    print(f"  💾 Created book record in Supabase (id: {db_book_id[:8]}...)")
                except Exception as db_err:
                    print(f"  ⚠️  DB sync error (non-fatal): {db_err}")
                
                # Generate outline
                outline = generator.generate_outline(
                    title=title,
                    notes=book_data['notes_on_outline_before']
                )
                
                # Write back to sheet
                sheets.write_outline(row_num, outline)
                sheets.update_book_status(row_num, 'outline_ready_for_review')
                
                # Sync outline to Supabase (non-fatal)
                if db_book_id:
                    try:
                        db.create_outline(db_book_id, outline, book_data.get('notes_on_outline_before', ''))
                        db.update_book_status(db_book_id, 'outline_ready_for_review')
                        db.log_action(db_book_id, 'outline_generated', 'completed')
                        print(f"  💾 Synced outline to Supabase")
                    except Exception as db_err:
                        print(f"  ⚠️  DB sync error (non-fatal): {db_err}")
                
                # Track this book
                processed_books[row_num] = {
                    'title': title,
                    'outline': outline,
                    'stage': 'waiting_for_outline_approval',
                    'db_book_id': db_book_id
                }
                
                print(f"✅ Outline ready! Check your Google Sheet row {row_num}")
                notifier.notify(
                    subject=f"Outline Ready for Review: {title}",
                    message=f"Your book outline is ready for review!\n\nTitle: {title}\n\nOutline:\n{outline}\n\nTo approve: set Column E to 'no_notes_needed'\nTo request changes: set Column E to 'yes' and add feedback in Column D"
                )
            
            # Check for approved outlines
            books_for_processing = sheets.get_all_books_for_processing()
            
            for book_data in books_for_processing:
                row_num = book_data['row_number']
                action = book_data['action']
                title = book_data['title']
                
                if row_num not in processed_books:
                    # Initialize tracking for this book (encountered after restart)
                    processed_books[row_num] = {
                        'title': title,
                        'outline': book_data['outline'],
                        'stage': 'waiting_for_outline_approval',
                        'db_book_id': None
                    }
                
                current_stage = processed_books[row_num]['stage']
                
                # Handle outline approval
                if action == 'start_chapters' and current_stage in ('waiting_for_outline_approval', 'complete'):
                    # Skip if already marked complete in this session
                    if current_stage == 'complete':
                        continue
                    print(f"\n✅ Outline approved for: {title}")
                    sheets.update_book_status(row_num, 'chapters_in_progress')
                    
                    db_book_id = processed_books[row_num].get('db_book_id')
                    
                    # If no db_book_id (e.g. restart), try to create one now
                    if db_book_id is None:
                        try:
                            db_book = db.create_book(title, book_data.get('notes_on_outline_before', ''))
                            db_book_id = db_book.get('id')
                            processed_books[row_num]['db_book_id'] = db_book_id
                            db.create_outline(db_book_id, book_data['outline'])
                            print(f"  💾 Created Supabase records for resumed book (id: {db_book_id[:8]}...)")
                        except Exception as db_err:
                            print(f"  ⚠️  DB sync error (non-fatal): {db_err}")
                    
                    if db_book_id:
                        try:
                            db.update_book_status(db_book_id, 'chapters_in_progress')
                            db.log_action(db_book_id, 'chapters_started', 'completed')
                        except Exception as db_err:
                            print(f"  ⚠️  DB sync error (non-fatal): {db_err}")
                    
                    # Generate full book (with DB sync per chapter)
                    output_path = generator.generate_full_book(
                        title=title,
                        outline=book_data['outline'],
                        db=db,
                        db_book_id=db_book_id
                    )
                    
                    if output_path is None:
                        # Rate limited mid-generation — keep as in_progress so it retries next poll
                        print(f"⏸️  Book generation paused (rate limit). Will auto-resume next poll.")
                        continue
                    
                    sheets.update_book_status(row_num, 'complete')
                    processed_books[row_num]['stage'] = 'complete'
                    
                    # Sync completion to Supabase (non-fatal)
                    if db_book_id:
                        try:
                            db.update_book_status(db_book_id, 'complete')
                            db.log_action(db_book_id, 'book_completed', 'completed', output_path)
                            print(f"  💾 Book completion synced to Supabase")
                        except Exception as db_err:
                            print(f"  ⚠️  DB sync error (non-fatal): {db_err}")
                    
                    print(f"🎉 Book complete: {title}")
                    print(f"   Location: {output_path}")
                    notifier.notify(
                        subject=f"Book Complete: {title}",
                        message=f"Your book has been generated successfully!\n\nTitle: {title}\n\nFile saved to:\n{output_path}\n\nThe book is ready to read!"
                    )
                
                # Handle outline regeneration
                elif action == 'regenerate_outline' and current_stage == 'waiting_for_outline_approval':
                    notes_after = book_data['notes_on_outline_after']
                    print(f"\n📝 Regenerating outline with feedback for: {title}")
                    print(f"   Feedback: {notes_after[:100]}...")
                    sheets.update_book_status(row_num, 'regenerating_outline')
                    
                    # Regenerate outline
                    new_outline = generator.regenerate_outline(
                        title=title,
                        old_outline=processed_books[row_num]['outline'],
                        feedback=notes_after
                    )
                    
                    # Write updated outline back to sheet
                    sheets.write_outline(row_num, new_outline)
                    sheets.update_book_status(row_num, 'outline_ready_for_review')
                    
                    # Update tracking
                    processed_books[row_num]['outline'] = new_outline
                    
                    # Sync regenerated outline to Supabase (non-fatal)
                    db_book_id = processed_books[row_num].get('db_book_id')
                    if db_book_id:
                        try:
                            db.regenerate_outline(db_book_id, new_outline, notes_after)
                            db.update_book_status(db_book_id, 'outline_ready_for_review')
                            db.log_action(db_book_id, 'outline_regenerated', 'completed')
                            print(f"  💾 Regenerated outline synced to Supabase")
                        except Exception as db_err:
                            print(f"  ⚠️  DB sync error (non-fatal): {db_err}")
                    
                    print(f"✅ Updated outline ready! Check row {row_num}")
                    notifier.notify(
                        subject=f"Outline Updated: {title}",
                        message=f"Your book outline has been revised based on your feedback!\n\nTitle: {title}\n\nUpdated Outline:\n{new_outline}\n\nTo approve: set Column E to 'no_notes_needed'\nTo request more changes: set Column E to 'yes' and update Column D"
                    )
            
        except Exception as e:
            print(f"\n❌ Error in polling loop: {e}")
            traceback.print_exc()
        
        # Wait 2 minutes before checking again
        print(f"\n⏰ Next check in 2 minutes... (Press Ctrl+C to stop)")
        time.sleep(120)


if __name__ == "__main__":
    poll_google_sheets_simple()
