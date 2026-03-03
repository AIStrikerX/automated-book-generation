"""
Main Orchestrator for Automated Book Generation System
Implements the complete workflow with gating logic and human-in-the-loop review
"""
from typing import Optional, Dict, List
from db import DatabaseManager
from outline_generator import OutlineGenerator
from chapter_generator import ChapterGenerator
from summarizer import Summarizer
from compiler import BookCompiler
from notifier import Notifier
from config import Config


class BookGenerationOrchestrator:
    """
    Main orchestrator that manages the entire book generation workflow
    with conditional branching and human-in-the-loop gating
    """
    
    def __init__(self):
        """Initialize all components"""
        self.db = DatabaseManager()
        self.outline_gen = OutlineGenerator()
        self.chapter_gen = ChapterGenerator()
        self.summarizer = Summarizer()
        self.compiler = BookCompiler()
        self.notifier = Notifier()
    
    # ==================== STAGE 1: OUTLINE GENERATION ====================
    
    def start_new_book(self, title: str, notes_on_outline_before: str = "") -> str:
        """
        Start a new book generation process
        
        Args:
            title: Book title
            notes_on_outline_before: Editor notes for outline generation
            
        Returns:
            book_id: Unique identifier for the book
        """
        print(f"\n{'='*60}")
        print(f"Starting new book: {title}")
        print(f"{'='*60}\n")
        
        # Create book entry in database
        book = self.db.create_book(title, notes_on_outline_before)
        book_id = book['id']
        
        self.db.log_action(book_id, "book_created", Config.STATUS_COMPLETED, 
                          f"Book '{title}' created")
        
        # Check if we can generate outline
        if not notes_on_outline_before:
            self.db.log_action(book_id, "outline_generation", Config.STATUS_PENDING,
                             "Waiting for notes_on_outline_before")
            self.notifier.notify_paused(book_id, title, 
                                       "Missing notes_on_outline_before. Please add notes to proceed.")
            print("⏸️  Process paused: notes_on_outline_before is required")
            return book_id
        
        # Generate outline
        try:
            self.generate_outline(book_id)
        except Exception as e:
            self.db.log_action(book_id, "outline_generation", Config.STATUS_ERROR, 
                             error_message=str(e))
            self.notifier.notify_error(book_id, title, str(e))
            raise
        
        return book_id
    
    def generate_outline(self, book_id: str) -> None:
        """Generate outline for a book"""
        book = self.db.get_book(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")
        
        title = book['title']
        notes_before = book.get('notes_on_outline_before', '')
        
        print(f"📝 Generating outline for: {title}")
        
        # Generate outline using LLM
        outline_text = self.outline_gen.generate_outline(title, notes_before)
        
        # Save to database
        self.db.create_outline(book_id, outline_text, notes_before)
        self.db.log_action(book_id, "outline_generated", Config.STATUS_COMPLETED,
                          f"Outline generated with {len(outline_text)} characters")
        
        # Notify editor for review
        self.notifier.notify_outline_ready(book_id, title)
        
        print(f"✓ Outline generated and saved")
        print(f"\n{outline_text}\n")
        print("⏸️  Waiting for editor review...")
    
    def check_outline_status(self, book_id: str) -> str:
        """
        Check outline status and determine next action
        
        Returns:
            Status: 'ready_for_chapters', 'needs_regeneration', 'waiting', or 'paused'
        """
        outline = self.db.get_outline(book_id)
        if not outline:
            return 'no_outline'
        
        status = outline.get('status_outline_notes', '')
        
        if status == Config.NOTES_NOT_NEEDED:
            return 'ready_for_chapters'
        elif status == Config.NOTES_YES:
            notes_after = outline.get('notes_after', '')
            if notes_after:
                return 'needs_regeneration'
            else:
                return 'waiting'  # Waiting for notes to be added
        elif status == Config.NOTES_NO:
            return 'paused'
        else:
            return 'waiting'
    
    def regenerate_outline(self, book_id: str) -> None:
        """Regenerate outline based on editor feedback"""
        book = self.db.get_book(book_id)
        outline = self.db.get_outline(book_id)
        
        if not outline:
            raise ValueError("No outline found to regenerate")
        
        notes_after = outline.get('notes_after', '')
        if not notes_after:
            raise ValueError("No editor notes found for regeneration")
        
        print(f"📝 Regenerating outline based on feedback...")
        
        # Regenerate outline
        new_outline_text = self.outline_gen.regenerate_outline(
            book['title'],
            outline['outline_text'],
            notes_after
        )
        
        # Save new version
        self.db.regenerate_outline(book_id, new_outline_text, notes_after)
        self.db.log_action(book_id, "outline_regenerated", Config.STATUS_COMPLETED,
                          f"Outline regenerated (version {outline['version'] + 1})")
        
        print(f"✓ Outline regenerated and saved")
        print(f"\n{new_outline_text}\n")
    
    # ==================== STAGE 2: CHAPTER GENERATION ====================
    
    def generate_all_chapters(self, book_id: str) -> None:
        """
        Generate all chapters with context chaining
        Implements gating logic for each chapter
        """
        book = self.db.get_book(book_id)
        outline = self.db.get_outline(book_id)
        
        if not outline:
            raise ValueError("No outline found. Generate outline first.")
        
        # Parse outline into chapters
        chapters_info = self.outline_gen.parse_outline_into_chapters(outline['outline_text'])
        
        print(f"\n{'='*60}")
        print(f"Generating {len(chapters_info)} chapters")
        print(f"{'='*60}\n")
        
        for chapter_info in chapters_info:
            self.generate_chapter(book_id, chapter_info)
            
            # Check if we should continue
            status = self.check_chapter_status(book_id, chapter_info['chapter_number'])
            
            if status == 'waiting':
                print(f"⏸️  Paused: Waiting for review of Chapter {chapter_info['chapter_number']}")
                return
            elif status == 'paused':
                print(f"⏸️  Process paused at Chapter {chapter_info['chapter_number']}")
                return
    
    def generate_chapter(self, book_id: str, chapter_info: Dict) -> None:
        """Generate a single chapter with context from previous chapters"""
        book = self.db.get_book(book_id)
        chapter_number = chapter_info['chapter_number']
        
        # Check if chapter already exists
        existing_chapter = self.db.get_chapter(book_id, chapter_number)
        if existing_chapter:
            print(f"ℹ️  Chapter {chapter_number} already exists (skipping)")
            return
        
        print(f"\n📖 Generating Chapter {chapter_number}: {chapter_info['title']}")
        
        # Get previous chapter summaries for context
        previous_summaries = self.db.get_previous_chapter_summaries(book_id, chapter_number)
        
        if previous_summaries:
            print(f"   Using context from {len(previous_summaries)} previous chapters")
        
        # Generate chapter
        chapter_content = self.chapter_gen.generate_chapter(
            title=book['title'],
            chapter_number=chapter_number,
            chapter_title=chapter_info['title'],
            chapter_description=chapter_info['description'],
            previous_summaries=previous_summaries
        )
        
        # Generate summary for context chaining
        print(f"   Creating summary for context chaining...")
        chapter_summary = self.summarizer.summarize_chapter(
            chapter_content,
            chapter_number,
            chapter_info['title']
        )
        
        # Save to database
        self.db.create_chapter(
            book_id=book_id,
            chapter_number=chapter_number,
            content=chapter_content,
            summary=chapter_summary,
            outline_section=chapter_info['description']
        )
        
        self.db.log_action(book_id, f"chapter_{chapter_number}_generated", 
                          Config.STATUS_COMPLETED,
                          f"Chapter {chapter_number} generated ({len(chapter_content)} chars)")
        
        # Notify for review
        self.notifier.notify_waiting_for_chapter_notes(book_id, book['title'], chapter_number)
        
        print(f"✓ Chapter {chapter_number} generated and saved")
        print(f"   Preview: {chapter_content[:200]}...\n")
    
    def check_chapter_status(self, book_id: str, chapter_number: int) -> str:
        """
        Check chapter status and determine next action
        
        Returns:
            'approved', 'needs_regeneration', 'waiting', or 'paused'
        """
        chapter = self.db.get_chapter(book_id, chapter_number)
        if not chapter:
            return 'not_generated'
        
        status = chapter.get('chapter_notes_status', '')
        
        if status == Config.NOTES_NOT_NEEDED:
            return 'approved'
        elif status == Config.NOTES_YES:
            notes = chapter.get('notes', '')
            if notes:
                return 'needs_regeneration'
            else:
                return 'waiting'
        elif status == Config.NOTES_NO:
            return 'paused'
        else:
            return 'waiting'
    
    def regenerate_chapter(self, book_id: str, chapter_number: int) -> None:
        """Regenerate a chapter based on editor feedback"""
        book = self.db.get_book(book_id)
        chapter = self.db.get_chapter(book_id, chapter_number)
        
        if not chapter:
            raise ValueError(f"Chapter {chapter_number} not found")
        
        notes = chapter.get('notes', '')
        if not notes:
            raise ValueError("No editor notes found for regeneration")
        
        print(f"\n📖 Regenerating Chapter {chapter_number} based on feedback...")
        
        # Get previous chapter summaries
        previous_summaries = self.db.get_previous_chapter_summaries(book_id, chapter_number)
        
        # Regenerate chapter
        new_content = self.chapter_gen.regenerate_chapter(
            title=book['title'],
            chapter_number=chapter_number,
            chapter_title=chapter.get('title', f'Chapter {chapter_number}'),
            original_content=chapter['content'],
            chapter_notes=notes,
            previous_summaries=previous_summaries
        )
        
        # Generate new summary
        new_summary = self.summarizer.summarize_chapter(
            new_content,
            chapter_number,
            chapter.get('title', f'Chapter {chapter_number}')
        )
        
        # Save new version
        self.db.regenerate_chapter(book_id, chapter_number, new_content, new_summary, notes)
        self.db.log_action(book_id, f"chapter_{chapter_number}_regenerated",
                          Config.STATUS_COMPLETED,
                          f"Chapter {chapter_number} regenerated (version {chapter['version'] + 1})")
        
        print(f"✓ Chapter {chapter_number} regenerated and saved")
    
    # ==================== STAGE 3: FINAL COMPILATION ====================
    
    def compile_final_book(self, book_id: str, format: str = 'both') -> Dict[str, str]:
        """
        Compile all chapters into final book format
        
        Args:
            book_id: Book identifier
            format: 'docx', 'txt', or 'both'
            
        Returns:
            Dictionary with file paths
        """
        book = self.db.get_book(book_id)
        chapters = self.db.get_all_chapters(book_id)
        
        if not chapters:
            raise ValueError("No chapters found to compile")
        
        print(f"\n{'='*60}")
        print(f"Compiling final book: {book['title']}")
        print(f"Total chapters: {len(chapters)}")
        print(f"{'='*60}\n")
        
        # Compile based on format
        if format == 'docx':
            file_path = self.compiler.compile_to_docx(book['title'], chapters, book_id)
            file_paths = {'docx': file_path}
        elif format == 'txt':
            file_path = self.compiler.compile_to_txt(book['title'], chapters, book_id)
            file_paths = {'txt': file_path}
        else:  # both
            file_paths = self.compiler.compile_both_formats(book['title'], chapters, book_id)
        
        # Update book status
        self.db.update_book_status(book_id, Config.STATUS_COMPLETED)
        self.db.log_action(book_id, "book_compiled", Config.STATUS_COMPLETED,
                          f"Book compiled to {', '.join(file_paths.keys())}")
        
        # Notify completion
        self.notifier.notify_final_draft_ready(book_id, book['title'], file_paths)
        
        print(f"\n✓ Book compiled successfully!")
        for fmt, path in file_paths.items():
            print(f"   {fmt.upper()}: {path}")
        
        return file_paths
    
    # ==================== WORKFLOW AUTOMATION ====================
    
    def run_full_workflow(self, book_id: str) -> None:
        """
        Run the complete workflow with automatic progression
        where possible (respecting gating logic)
        """
        print(f"\n{'='*60}")
        print("AUTOMATED BOOK GENERATION WORKFLOW")
        print(f"{'='*60}\n")
        
        book = self.db.get_book(book_id)
        
        # Stage 1: Outline
        outline_status = self.check_outline_status(book_id)
        
        if outline_status == 'no_outline':
            print("Stage 1: Generating outline...")
            self.generate_outline(book_id)
            return  # Wait for review
        elif outline_status == 'needs_regeneration':
            print("Stage 1: Regenerating outline based on feedback...")
            self.regenerate_outline(book_id)
            return  # Wait for review
        elif outline_status == 'waiting':
            print("⏸️  Waiting for outline review")
            return
        elif outline_status == 'paused':
            print("⏸️  Process paused at outline stage")
            return
        
        print("✓ Stage 1 Complete: Outline approved")
        
        # Stage 2: Chapters
        print("\nStage 2: Generating chapters...")
        self.generate_all_chapters(book_id)
        
        # Check if all chapters are approved
        outline = self.db.get_outline(book_id)
        chapters_info = self.outline_gen.parse_outline_into_chapters(outline['outline_text'])
        
        all_approved = True
        for chapter_info in chapters_info:
            status = self.check_chapter_status(book_id, chapter_info['chapter_number'])
            if status != 'approved':
                all_approved = False
                break
        
        if not all_approved:
            print("\n⏸️  Waiting for chapter reviews")
            return
        
        print("\n✓ Stage 2 Complete: All chapters approved")
        
        # Stage 3: Final Compilation
        print("\nStage 3: Compiling final book...")
        self.compile_final_book(book_id)
        
        print(f"\n{'='*60}")
        print("🎉 BOOK GENERATION COMPLETE!")
        print(f"{'='*60}\n")
    
    # ==================== UTILITY METHODS ====================
    
    def get_book_status(self, book_id: str) -> Dict:
        """Get comprehensive status of a book"""
        book = self.db.get_book(book_id)
        outline = self.db.get_outline(book_id)
        chapters = self.db.get_all_chapters(book_id)
        logs = self.db.get_logs(book_id)
        
        return {
            'book': book,
            'outline': outline,
            'chapters': chapters,
            'chapter_count': len(chapters),
            'logs': logs,
            'outline_status': self.check_outline_status(book_id)
        }
    
    def print_status(self, book_id: str) -> None:
        """Print human-readable status"""
        status = self.get_book_status(book_id)
        
        print(f"\n{'='*60}")
        print(f"BOOK STATUS: {status['book']['title']}")
        print(f"{'='*60}")
        print(f"Book ID: {book_id}")
        print(f"Status: {status['book']['status']}")
        print(f"Outline Status: {status['outline_status']}")
        print(f"Chapters Generated: {status['chapter_count']}")
        print(f"{'='*60}\n")


# ==================== GOOGLE SHEETS INTEGRATION ====================

def poll_google_sheets():
    """
    Check Google Sheet every 2 minutes for new books to process.
    
    This function implements the human-in-the-loop workflow:
    1. Monitors sheet for new book requests (title + notes provided)
    2. Generates outlines and writes them back to the sheet
    3. Waits for editor approval or feedback
    4. Regenerates outlines based on feedback
    5. Proceeds to chapter generation when approved
    """
    from sheets_connector import GoogleSheetsConnector
    import time
    
    try:
        sheets = GoogleSheetsConnector()
    except Exception as e:
        print(f"❌ Failed to connect to Google Sheets: {e}")
        print("📝 Make sure you've completed the Google Cloud setup steps.")
        return
    
    orchestrator = BookGenerationOrchestrator()
    
    # Track books we've already started to avoid duplicates
    processed_books = {}
    
    print("\n" + "="*60)
    print("🔄 GOOGLE SHEETS POLLING STARTED")
    print("="*60)
    print("📊 Checking sheet every 2 minutes for new books...")
    print("📝 Add a title + notes to your sheet to start!")
    print("="*60 + "\n")
    
    while True:
        try:
            # Check for new books waiting for outline generation
            pending = sheets.get_pending_books()
            
            for book_data in pending:
                title = book_data['title']
                row_num = book_data['row_number']
                
                # Skip if we've already processed this row
                if row_num in processed_books:
                    continue
                
                print(f"\n📖 Found new book: {title}")
                sheets.update_book_status(row_num, 'generating_outline')
                
                # Generate outline using Groq
                book_id = orchestrator.start_new_book(
                    title=title,
                    notes_on_outline_before=book_data['notes_on_outline_before']
                )
                
                # Get the generated outline from DB
                outline = orchestrator.db.get_outline(book_id)
                
                # Write it back to Google Sheet
                sheets.write_outline(row_num, outline['outline_text'])
                sheets.update_book_status(row_num, 'outline_ready_for_review')
                
                # Track this book
                processed_books[row_num] = {
                    'book_id': book_id,
                    'title': title,
                    'stage': 'waiting_for_outline_approval'
                }
                
                print(f"✅ Outline ready! Check your Google Sheet row {row_num}")
            
            # Check for approved outlines ready for next steps
            check_approved_outlines(sheets, orchestrator, processed_books)
            
        except Exception as e:
            print(f"❌ Error in polling loop: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait 2 minutes before checking again
        print(f"\n⏰ Next check in 2 minutes... (Press Ctrl+C to stop)")
        time.sleep(120)


def check_approved_outlines(sheets, orchestrator, processed_books):
    """
    Check if editor approved or requested changes to any outlines.
    
    Args:
        sheets: GoogleSheetsConnector instance
        orchestrator: BookGenerationOrchestrator instance
        processed_books: Dict tracking books and their current stage
    """
    books_for_processing = sheets.get_all_books_for_processing()
    
    for book_data in books_for_processing:
        row_num = book_data['row_number']
        action = book_data['action']
        title = book_data['title']
        
        # Get the book_id if we've already processed this row
        if row_num in processed_books:
            book_id = processed_books[row_num]['book_id']
            current_stage = processed_books[row_num]['stage']
        else:
            # This shouldn't happen, but handle it gracefully
            print(f"⚠️  Row {row_num} ({title}) not found in processed books - skipping")
            continue
        
        # Handle outline approval
        if action == 'start_chapters' and current_stage == 'waiting_for_outline_approval':
            print(f"\n✅ Outline approved for: {title}")
            print(f"📝 Starting chapter generation...")
            sheets.update_book_status(row_num, 'chapters_in_progress')
            
            # Generate all chapters
            outline = orchestrator.db.get_outline(book_id)
            chapter_titles = orchestrator.outline_gen.parse_outline_into_chapters(
                outline['outline_text']
            )
            
            for i, chapter_title in enumerate(chapter_titles, 1):
                print(f"  Generating Chapter {i}: {chapter_title}")
                orchestrator.generate_chapter(
                    book_id=book_id,
                    chapter_number=i,
                    chapter_title=chapter_title,
                    notes_on_chapter_before=""
                )
            
            # Compile final book
            orchestrator.compile_final_book(book_id)
            sheets.update_book_status(row_num, 'complete')
            
            # Update tracking
            processed_books[row_num]['stage'] = 'complete'
            
            print(f"🎉 Book complete: {title}")
        
        # Handle outline regeneration request
        elif action == 'regenerate_outline' and current_stage == 'waiting_for_outline_approval':
            notes_after = book_data['notes_on_outline_after']
            print(f"\n📝 Regenerating outline with feedback for: {title}")
            print(f"   Feedback: {notes_after[:100]}...")
            sheets.update_book_status(row_num, 'regenerating_outline')
            
            # Regenerate outline
            new_outline_data = orchestrator.regenerate_outline(book_id, notes_after)
            
            # Write updated outline back to sheet
            sheets.write_outline(row_num, new_outline_data['outline_text'])
            sheets.update_book_status(row_num, 'outline_ready_for_review')
            
            print(f"✅ Updated outline ready! Check row {row_num}")


if __name__ == "__main__":
    # Start Google Sheets polling
    poll_google_sheets()
