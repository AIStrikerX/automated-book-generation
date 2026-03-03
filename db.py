"""
Database module for Supabase operations
Handles all database interactions for books, outlines, chapters, and logs
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from config import Config


class DatabaseManager:
    """Manages all database operations for the book generation system"""
    
    def __init__(self):
        """Initialize Supabase client"""
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            print("WARNING: Supabase credentials not configured. Running in demo mode.")
            self.client = None
        else:
            self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # ==================== BOOKS TABLE ====================
    
    def create_book(self, title: str, notes_on_outline_before: str = "") -> Dict:
        """Create a new book entry"""
        data = {
            "title": title,
            "notes_on_outline_before": notes_on_outline_before,
            "status": Config.STATUS_PENDING,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if self.client:
            response = self.client.table("books").insert(data).execute()
            return response.data[0]
        else:
            # Demo mode - return mock data
            data["id"] = "demo-book-id"
            return data
    
    def get_book(self, book_id: str) -> Optional[Dict]:
        """Get a book by ID"""
        if self.client:
            response = self.client.table("books").select("*").eq("id", book_id).execute()
            return response.data[0] if response.data else None
        return None
    
    def update_book_status(self, book_id: str, status: str) -> None:
        """Update book status"""
        if self.client:
            self.client.table("books").update({"status": status}).eq("id", book_id).execute()
    
    def get_all_books(self) -> List[Dict]:
        """Get all books"""
        if self.client:
            response = self.client.table("books").select("*").order("created_at", desc=True).execute()
            return response.data
        return []
    
    # ==================== OUTLINES TABLE ====================
    
    def create_outline(self, book_id: str, outline_text: str, notes_before: str = "") -> Dict:
        """Create an outline entry"""
        data = {
            "book_id": book_id,
            "outline_text": outline_text,
            "notes_before": notes_before,
            "notes_after": "",
            "status_outline_notes": Config.STATUS_PENDING,
            "version": 1,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if self.client:
            response = self.client.table("outlines").insert(data).execute()
            return response.data[0]
        else:
            data["id"] = "demo-outline-id"
            return data
    
    def get_outline(self, book_id: str) -> Optional[Dict]:
        """Get the latest outline for a book"""
        if self.client:
            response = self.client.table("outlines").select("*").eq("book_id", book_id).order("version", desc=True).limit(1).execute()
            return response.data[0] if response.data else None
        return None
    
    def update_outline_notes(self, book_id: str, notes_after: str, status: str) -> None:
        """Update outline with editor notes"""
        if self.client:
            outline = self.get_outline(book_id)
            if outline:
                self.client.table("outlines").update({
                    "notes_after": notes_after,
                    "status_outline_notes": status
                }).eq("id", outline["id"]).execute()
    
    def regenerate_outline(self, book_id: str, new_outline_text: str, notes_after: str) -> Dict:
        """Create a new version of the outline"""
        if self.client:
            outline = self.get_outline(book_id)
            new_version = (outline["version"] + 1) if outline else 1
            
            data = {
                "book_id": book_id,
                "outline_text": new_outline_text,
                "notes_before": outline["notes_before"] if outline else "",
                "notes_after": notes_after,
                "status_outline_notes": Config.NOTES_NOT_NEEDED,
                "version": new_version,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("outlines").insert(data).execute()
            return response.data[0]
        return {}
    
    # ==================== CHAPTERS TABLE ====================
    
    def create_chapter(self, book_id: str, chapter_number: int, content: str, 
                       summary: str, outline_section: str = "") -> Dict:
        """Create a chapter entry"""
        data = {
            "book_id": book_id,
            "chapter_number": chapter_number,
            "content": content,
            "summary": summary,
            "outline_section": outline_section,
            "notes": "",
            "chapter_notes_status": Config.STATUS_PENDING,
            "version": 1,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if self.client:
            response = self.client.table("chapters").insert(data).execute()
            return response.data[0]
        else:
            data["id"] = f"demo-chapter-{chapter_number}"
            return data
    
    def get_chapter(self, book_id: str, chapter_number: int) -> Optional[Dict]:
        """Get a specific chapter"""
        if self.client:
            response = self.client.table("chapters").select("*").eq("book_id", book_id).eq("chapter_number", chapter_number).order("version", desc=True).limit(1).execute()
            return response.data[0] if response.data else None
        return None
    
    def get_all_chapters(self, book_id: str) -> List[Dict]:
        """Get all chapters for a book (latest versions only)"""
        if self.client:
            # Get latest version of each chapter
            response = self.client.table("chapters").select("*").eq("book_id", book_id).order("chapter_number").execute()
            
            # Filter to get only latest versions
            chapters_dict = {}
            for chapter in response.data:
                ch_num = chapter["chapter_number"]
                if ch_num not in chapters_dict or chapter["version"] > chapters_dict[ch_num]["version"]:
                    chapters_dict[ch_num] = chapter
            
            return sorted(chapters_dict.values(), key=lambda x: x["chapter_number"])
        return []
    
    def get_previous_chapter_summaries(self, book_id: str, up_to_chapter: int) -> List[str]:
        """Get summaries of all chapters before the specified chapter number"""
        if self.client:
            chapters = self.get_all_chapters(book_id)
            summaries = [
                f"Chapter {ch['chapter_number']}: {ch['summary']}"
                for ch in chapters
                if ch["chapter_number"] < up_to_chapter
            ]
            return summaries
        return []
    
    def update_chapter_notes(self, book_id: str, chapter_number: int, 
                            notes: str, status: str) -> None:
        """Update chapter with editor notes"""
        if self.client:
            chapter = self.get_chapter(book_id, chapter_number)
            if chapter:
                self.client.table("chapters").update({
                    "notes": notes,
                    "chapter_notes_status": status
                }).eq("id", chapter["id"]).execute()
    
    def regenerate_chapter(self, book_id: str, chapter_number: int, 
                          new_content: str, new_summary: str, notes: str) -> Dict:
        """Create a new version of a chapter"""
        if self.client:
            chapter = self.get_chapter(book_id, chapter_number)
            new_version = (chapter["version"] + 1) if chapter else 1
            
            data = {
                "book_id": book_id,
                "chapter_number": chapter_number,
                "content": new_content,
                "summary": new_summary,
                "outline_section": chapter["outline_section"] if chapter else "",
                "notes": notes,
                "chapter_notes_status": Config.NOTES_NOT_NEEDED,
                "version": new_version,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("chapters").insert(data).execute()
            return response.data[0]
        return {}
    
    # ==================== LOGS TABLE ====================
    
    def log_action(self, book_id: str, action: str, status: str, 
                   details: str = "", error_message: str = "") -> None:
        """Log an action to the logs table"""
        data = {
            "book_id": book_id,
            "action": action,
            "status": status,
            "details": details,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.client:
            self.client.table("logs").insert(data).execute()
        else:
            print(f"LOG: {action} - {status} - {details}")
    
    def get_logs(self, book_id: str) -> List[Dict]:
        """Get all logs for a book"""
        if self.client:
            response = self.client.table("logs").select("*").eq("book_id", book_id).order("timestamp", desc=True).execute()
            return response.data
        return []
    
    # ==================== FINAL REVIEW ====================
    
    def update_final_review_status(self, book_id: str, status: str, notes: str = "") -> None:
        """Update final review status in books table"""
        if self.client:
            self.client.table("books").update({
                "final_review_notes_status": status,
                "final_review_notes": notes,
                "book_output_status": Config.STATUS_COMPLETED if status == Config.NOTES_NOT_NEEDED else Config.STATUS_PENDING
            }).eq("id", book_id).execute()
