import gspread
from google.oauth2.service_account import Credentials
import time
from config import Config

SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

class GoogleSheetsConnector:
    """
    Connector for Google Sheets integration with the book generation system.
    
    Enables human-in-the-loop workflow where:
    1. Editors add book titles and notes to a Google Sheet
    2. System polls the sheet for new requests
    3. Generated outlines are written back to the sheet
    4. Editors review and approve/reject with notes
    5. System proceeds based on editor decisions
    """
    
    def __init__(self):
        """Initialize connection to Google Sheets using service account credentials."""
        try:
            creds = Credentials.from_service_account_file(
                'credentials.json', 
                scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open("BookGenerator").sheet1
            print("✅ Google Sheets connected!")
        except FileNotFoundError:
            print("❌ ERROR: credentials.json not found!")
            print("📝 Follow the Google Cloud setup guide to create and download it.")
            raise
        except gspread.exceptions.SpreadsheetNotFound:
            print("❌ ERROR: Google Sheet 'BookGenerator' not found!")
            print("📝 Create a sheet named 'BookGenerator' and share it with your service account.")
            raise

    def get_pending_books(self):
        """
        Find rows where title + notes exist but outline is empty.
        
        Returns:
            list: List of dicts with book data and row numbers
        """
        all_rows = self.sheet.get_all_records()
        pending = []
        
        for i, row in enumerate(all_rows):
            if (row.get('title') and 
                row.get('notes_on_outline_before') and 
                not row.get('outline')):
                row['row_number'] = i + 2  # +2 because row 1 is headers
                pending.append(row)
        
        return pending

    def write_outline(self, row_number, outline_text):
        """
        Write generated outline back to sheet and set status to waiting for review.
        
        Args:
            row_number (int): Sheet row number (1-indexed)
            outline_text (str): Generated outline content
        """
        self.sheet.update_cell(row_number, 3, outline_text)  # Column C = outline
        self.sheet.update_cell(row_number, 5, 'no')          # Column E = waiting for review
        print(f"✅ Outline written to row {row_number}")

    def get_outline_status(self, row_number):
        """
        Check what editor decided about the outline.
        
        Args:
            row_number (int): Sheet row number
            
        Returns:
            str: 'no', 'yes', 'no_notes_needed', or empty
        """
        return self.sheet.cell(row_number, 5).value  # Column E

    def get_outline_notes_after(self, row_number):
        """
        Get editor feedback notes for outline revision.
        
        Args:
            row_number (int): Sheet row number
            
        Returns:
            str: Editor's feedback notes
        """
        return self.sheet.cell(row_number, 4).value  # Column D

    def update_book_status(self, row_number, status):
        """
        Update overall book generation status.
        
        Args:
            row_number (int): Sheet row number
            status (str): Status message (e.g., 'outline_pending', 'chapters_in_progress', 'complete')
        """
        self.sheet.update_cell(row_number, 6, status)  # Column F
        
    def get_all_books_for_processing(self):
        """
        Get all books that need processing (outline approved or feedback provided).
        
        Returns:
            list: Books ready for next stage
        """
        all_rows = self.sheet.get_all_records()
        ready_for_processing = []
        
        for i, row in enumerate(all_rows):
            row_number = i + 2
            status = row.get('status_outline_notes', '').strip().lower()
            book_status = row.get('book_status', '').strip().lower()
            
            # Skip already completed or in-progress books
            if book_status in ('complete', 'chapters_in_progress'):
                continue
            
            # Check if outline was approved
            if status == 'no_notes_needed' and row.get('outline'):
                row['row_number'] = row_number
                row['action'] = 'start_chapters'
                ready_for_processing.append(row)
            
            # Check if outline needs regeneration
            elif status == 'yes' and row.get('notes_on_outline_after'):
                row['row_number'] = row_number
                row['action'] = 'regenerate_outline'
                ready_for_processing.append(row)
        
        return ready_for_processing
    
    def get_chapter_data(self, row_number):
        """
        Get all data for a specific book by row number.
        
        Args:
            row_number (int): Sheet row number
            
        Returns:
            dict: All data for that book
        """
        row_data = self.sheet.row_values(row_number)
        
        # Map to column names
        return {
            'title': row_data[0] if len(row_data) > 0 else '',
            'notes_on_outline_before': row_data[1] if len(row_data) > 1 else '',
            'outline': row_data[2] if len(row_data) > 2 else '',
            'notes_on_outline_after': row_data[3] if len(row_data) > 3 else '',
            'status_outline_notes': row_data[4] if len(row_data) > 4 else '',
            'book_status': row_data[5] if len(row_data) > 5 else ''
        }
