"""
Demo Script for Automated Book Generation System
This demonstrates how to use the system in various scenarios
"""
from main import BookGenerationOrchestrator
from config import Config


def demo_full_workflow():
    """Demo: Complete workflow without human intervention (auto-approve mode)"""
    print("\n" + "="*80)
    print("DEMO 1: FULL AUTOMATED WORKFLOW (Demo Mode)")
    print("="*80 + "\n")
    
    orchestrator = BookGenerationOrchestrator()
    
    # Start a new book
    book_id = orchestrator.start_new_book(
        title="The Complete Guide to Python Programming",
        notes_on_outline_before="""
        Create an outline for a comprehensive Python programming book aimed at beginners to intermediate learners.
        
        Requirements:
        - Start with Python basics and installation
        - Cover fundamental concepts (variables, loops, functions)
        - Include object-oriented programming
        - Add sections on popular libraries (NumPy, Pandas)
        - Include practical projects
        - Keep it practical and hands-on
        
        Target: 10-12 chapters
        """
    )
    
    print(f"\nBook created with ID: {book_id}")
    
    # In a real scenario, you would:
    # 1. Wait for editor to review outline
    # 2. Editor sets status_outline_notes to 'no_notes_needed' or provides feedback
    # 3. Run workflow again to continue
    
    # For demo purposes, simulate approval
    print("\n[DEMO] Simulating editor approval of outline...")
    orchestrator.db.update_outline_notes(book_id, "", Config.NOTES_NOT_NEEDED)
    
    # Generate first chapter
    print("\n[DEMO] Generating first chapter...")
    outline = orchestrator.db.get_outline(book_id)
    chapters_info = orchestrator.outline_gen.parse_outline_into_chapters(outline['outline_text'])
    
    if chapters_info:
        orchestrator.generate_chapter(book_id, chapters_info[0])
        
        # Simulate chapter approval
        print("\n[DEMO] Simulating editor approval of chapter...")
        orchestrator.db.update_chapter_notes(book_id, 1, "", Config.NOTES_NOT_NEEDED)
        
        # Show status
        orchestrator.print_status(book_id)
    
    return book_id


def demo_with_feedback():
    """Demo: Workflow with editor feedback and regeneration"""
    print("\n" + "="*80)
    print("DEMO 2: WORKFLOW WITH EDITOR FEEDBACK")
    print("="*80 + "\n")
    
    orchestrator = BookGenerationOrchestrator()
    
    # Start a new book
    book_id = orchestrator.start_new_book(
        title="Artificial Intelligence for Business Leaders",
        notes_on_outline_before="""
        Create an outline for a book about AI for business executives who are not technical.
        
        Focus on:
        - Practical applications of AI in business
        - ROI and cost-benefit analysis
        - Implementation strategies
        - Managing AI teams
        - Ethics and governance
        - Real-world case studies
        
        Keep it non-technical and business-focused.
        """
    )
    
    print(f"\nBook created with ID: {book_id}")
    
    # Simulate editor feedback on outline
    print("\n[DEMO] Editor reviews outline and provides feedback...")
    orchestrator.db.update_outline_notes(
        book_id,
        notes_after="Good start, but please add a chapter on AI implementation challenges and common pitfalls. Also, expand the ethics section into its own chapter.",
        status=Config.NOTES_YES
    )
    
    # Regenerate outline
    print("\n[DEMO] Regenerating outline based on feedback...")
    orchestrator.regenerate_outline(book_id)
    
    # Approve the new outline
    print("\n[DEMO] Editor approves new outline...")
    orchestrator.db.update_outline_notes(book_id, "", Config.NOTES_NOT_NEEDED)
    
    # Show status
    orchestrator.print_status(book_id)
    
    return book_id


def demo_chapter_with_context():
    """Demo: Generate multiple chapters showing context chaining"""
    print("\n" + "="*80)
    print("DEMO 3: CONTEXT CHAINING ACROSS CHAPTERS")
    print("="*80 + "\n")
    
    orchestrator = BookGenerationOrchestrator()
    
    # Start a book
    book_id = orchestrator.start_new_book(
        title="A Journey Through Time: History of Computing",
        notes_on_outline_before="""
        Create a historical narrative about the evolution of computing from early mechanical calculators to modern AI.
        
        Structure:
        - Early mechanical computing devices
        - Vacuum tubes and early computers
        - Transistors and integrated circuits
        - Personal computing revolution
        - Internet era
        - Mobile and cloud computing
        - AI and quantum computing future
        
        Make it narrative and engaging, not just technical facts.
        """
    )
    
    # Approve outline
    orchestrator.db.update_outline_notes(book_id, "", Config.NOTES_NOT_NEEDED)
    
    # Generate first 3 chapters to show context chaining
    outline = orchestrator.db.get_outline(book_id)
    chapters_info = orchestrator.outline_gen.parse_outline_into_chapters(outline['outline_text'])
    
    for i in range(min(3, len(chapters_info))):
        chapter_info = chapters_info[i]
        print(f"\n{'='*60}")
        print(f"Generating Chapter {chapter_info['chapter_number']} with context")
        print(f"{'='*60}")
        
        # Get previous summaries to show context awareness
        previous_summaries = orchestrator.db.get_previous_chapter_summaries(
            book_id, 
            chapter_info['chapter_number']
        )
        
        if previous_summaries:
            print("\nContext from previous chapters:")
            for summary in previous_summaries:
                print(f"  - {summary[:100]}...")
        else:
            print("\nThis is the first chapter (no previous context)")
        
        orchestrator.generate_chapter(book_id, chapter_info)
        
        # Auto-approve for demo
        orchestrator.db.update_chapter_notes(
            book_id, 
            chapter_info['chapter_number'], 
            "", 
            Config.NOTES_NOT_NEEDED
        )
    
    return book_id


def demo_compilation():
    """Demo: Compile a book to final format"""
    print("\n" + "="*80)
    print("DEMO 4: FINAL BOOK COMPILATION")
    print("="*80 + "\n")
    
    orchestrator = BookGenerationOrchestrator()
    
    # For this demo, let's create a simple book and compile it
    book_id = orchestrator.start_new_book(
        title="Quick Start Guide to Remote Work",
        notes_on_outline_before="""
        Create a concise guide (5-6 chapters) for professionals transitioning to remote work.
        
        Topics:
        - Setting up your home office
        - Communication tools and best practices
        - Time management and productivity
        - Maintaining work-life balance
        - Building remote team culture
        """
    )
    
    # Quick workflow for demo
    orchestrator.db.update_outline_notes(book_id, "", Config.NOTES_NOT_NEEDED)
    
    outline = orchestrator.db.get_outline(book_id)
    chapters_info = orchestrator.outline_gen.parse_outline_into_chapters(outline['outline_text'])
    
    # Generate all chapters (for demo, generate first 2)
    for chapter_info in chapters_info[:2]:
        orchestrator.generate_chapter(book_id, chapter_info)
        orchestrator.db.update_chapter_notes(
            book_id,
            chapter_info['chapter_number'],
            "",
            Config.NOTES_NOT_NEEDED
        )
    
    # Compile to both formats
    print("\n[DEMO] Compiling book to final formats...")
    file_paths = orchestrator.compile_final_book(book_id, format='both')
    
    print("\n📚 Book compiled successfully!")
    print(f"   DOCX: {file_paths['docx']}")
    print(f"   TXT: {file_paths['txt']}")
    
    return book_id, file_paths


def demo_simple_api_usage():
    """Demo: Simple API usage for integration"""
    print("\n" + "="*80)
    print("DEMO 5: SIMPLE API USAGE")
    print("="*80 + "\n")
    
    # This shows how you might use this in an API or automated system
    
    orchestrator = BookGenerationOrchestrator()
    
    # Create a book
    book_id = orchestrator.start_new_book(
        title="10 Marketing Strategies for Startups",
        notes_on_outline_before="Create a practical guide with 10 actionable marketing strategies for early-stage startups with limited budgets."
    )
    
    # Check status
    status = orchestrator.get_book_status(book_id)
    print(f"Book Status: {status['outline_status']}")
    
    # In a real system, you'd store book_id and check back later
    # When editor approves, continue workflow
    
    return book_id


def interactive_demo():
    """Interactive demo where user can choose what to run"""
    print("\n" + "="*80)
    print("AUTOMATED BOOK GENERATION SYSTEM - INTERACTIVE DEMO")
    print("="*80 + "\n")
    
    print("Available Demos:")
    print("1. Full Automated Workflow (Quick Demo)")
    print("2. Workflow with Editor Feedback")
    print("3. Context Chaining Across Chapters")
    print("4. Final Book Compilation")
    print("5. Simple API Usage Example")
    print("6. Run All Demos")
    print("0. Exit")
    
    choice = input("\nSelect demo (0-6): ").strip()
    
    if choice == "1":
        demo_full_workflow()
    elif choice == "2":
        demo_with_feedback()
    elif choice == "3":
        demo_chapter_with_context()
    elif choice == "4":
        demo_compilation()
    elif choice == "5":
        demo_simple_api_usage()
    elif choice == "6":
        print("\n🚀 Running all demos...\n")
        demo_full_workflow()
        input("\nPress Enter to continue to next demo...")
        demo_with_feedback()
        input("\nPress Enter to continue to next demo...")
        demo_chapter_with_context()
        input("\nPress Enter to continue to next demo...")
        demo_compilation()
        input("\nPress Enter to continue to next demo...")
        demo_simple_api_usage()
    elif choice == "0":
        print("\nGoodbye!")
        return
    else:
        print("\nInvalid choice. Please try again.")
        interactive_demo()


if __name__ == "__main__":
    # Run interactive demo
    # Note: In demo mode without Supabase, data is not persisted
    print("\n⚠️  NOTE: Running in DEMO MODE")
    print("To use with real database, configure Supabase credentials in .env file")
    print("="*80)
    
    interactive_demo()
