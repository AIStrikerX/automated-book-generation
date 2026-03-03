"""
Notifier Module
Handles email and MS Teams notifications for key events
"""
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import Config


class Notifier:
    """Handles notifications for book generation events"""
    
    def __init__(self):
        """Initialize notifier with configuration"""
        self.smtp_configured = bool(Config.SMTP_USER and Config.SMTP_PASSWORD)
        teams_url = Config.TEAMS_WEBHOOK_URL or ''
        self.teams_configured = bool(teams_url and teams_url.startswith('http'))
    
    def notify(self, subject: str, message: str, to_email: Optional[str] = None):
        """
        Send notification via all configured channels
        
        Args:
            subject: Notification subject/title
            message: Notification message body
            to_email: Optional email recipient (uses SMTP_USER if not provided)
        """
        if self.smtp_configured:
            self.send_email(subject, message, to_email)
        
        if self.teams_configured:
            self.send_teams_message(subject, message)
        
        # Always log to console
        print(f"\n{'='*60}")
        print(f"NOTIFICATION: {subject}")
        print(f"{'-'*60}")
        print(message)
        print(f"{'='*60}\n")
    
    def send_email(self, subject: str, message: str, to_email: Optional[str] = None):
        """
        Send email notification via SMTP
        
        Args:
            subject: Email subject
            message: Email body
            to_email: Recipient email (defaults to SMTP_USER)
        """
        if not self.smtp_configured:
            print("Email not configured. Skipping email notification.")
            return
        
        try:
            recipient = to_email or Config.SMTP_USER
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Book Generation] {subject}"
            msg['From'] = Config.SMTP_USER
            msg['To'] = recipient
            
            # Create HTML version
            html_message = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2C3E50;">{subject}</h2>
                <div style="background-color: #ECF0F1; padding: 15px; border-left: 4px solid #3498DB;">
                  <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{message}</pre>
                </div>
                <hr>
                <p style="color: #7F8C8D; font-size: 12px;">
                  This is an automated notification from the Book Generation System.
                </p>
              </body>
            </html>
            """
            
            part1 = MIMEText(message, 'plain')
            part2 = MIMEText(html_message, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✓ Email sent to {recipient}")
            
        except Exception as e:
            print(f"✗ Failed to send email: {str(e)}")
    
    def send_teams_message(self, title: str, message: str):
        """
        Send notification to MS Teams via webhook
        
        Args:
            title: Message title
            message: Message body
        """
        if not self.teams_configured:
            print("MS Teams not configured. Skipping Teams notification.")
            return
        
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": "0078D7",
                "title": f"📚 Book Generation: {title}",
                "sections": [
                    {
                        "activityTitle": "Automated Book Generation System",
                        "text": message,
                        "markdown": True
                    }
                ]
            }
            
            response = requests.post(
                Config.TEAMS_WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print("✓ Teams notification sent")
            else:
                print(f"✗ Teams notification failed: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Failed to send Teams message: {str(e)}")
    
    # Predefined notification templates
    
    def notify_outline_ready(self, book_id: str, title: str):
        """Notify that outline is ready for review"""
        subject = "Outline Ready for Review"
        message = f"""The book outline has been generated and is ready for your review.

Book ID: {book_id}
Title: {title}

Action Required:
- Review the outline in the database
- Add notes if changes are needed (notes_after field)
- Set status_outline_notes to:
  * 'yes' if you have notes/changes
  * 'no_notes_needed' to proceed to chapter generation
  * 'no' to pause the process
"""
        self.notify(subject, message)
    
    def notify_waiting_for_chapter_notes(self, book_id: str, title: str, chapter_number: int):
        """Notify that a chapter needs review"""
        subject = f"Chapter {chapter_number} Ready for Review"
        message = f"""Chapter {chapter_number} has been generated and needs your review.

Book ID: {book_id}
Title: {title}
Chapter: {chapter_number}

Action Required:
- Review the chapter content in the database
- Add notes if changes are needed
- Set chapter_notes_status to:
  * 'yes' if you have notes/changes
  * 'no_notes_needed' to proceed to next chapter
  * 'no' to pause
"""
        self.notify(subject, message)
    
    def notify_final_draft_ready(self, book_id: str, title: str, file_paths: dict):
        """Notify that final draft is compiled"""
        subject = "Final Book Draft Completed"
        
        files_info = "\n".join([f"- {fmt.upper()}: {path}" for fmt, path in file_paths.items()])
        
        message = f"""🎉 The final book draft has been successfully compiled!

Book ID: {book_id}
Title: {title}

Output Files:
{files_info}

The book is now ready for final review and distribution.
"""
        self.notify(subject, message)
    
    def notify_error(self, book_id: str, title: str, error: str):
        """Notify about an error"""
        subject = "Error in Book Generation"
        message = f"""⚠️ An error occurred during book generation.

Book ID: {book_id}
Title: {title}

Error: {error}

Please check the logs for more details.
"""
        self.notify(subject, message)
    
    def notify_paused(self, book_id: str, title: str, reason: str):
        """Notify that process is paused"""
        subject = "Book Generation Paused"
        message = f"""⏸️ Book generation has been paused.

Book ID: {book_id}
Title: {title}

Reason: {reason}

Please provide the required input to continue.
"""
        self.notify(subject, message)
