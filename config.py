"""
Configuration module for the Automated Book Generation System
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for all system settings"""
    
    # Groq API Settings - Support multiple keys for rotation
    GROQ_API_KEYS = [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
    ]
    # Filter out None values
    GROQ_API_KEYS = [key for key in GROQ_API_KEYS if key]
    
    # Legacy single key support
    GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else None
    
    GROQ_MODEL = "llama-3.3-70b-versatile"  # High quality model for book generation
    
    # Supabase Settings
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Email Settings
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    # MS Teams Settings
    TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")
    
    # Generation Parameters
    MAX_TOKENS = 8000
    TEMPERATURE = 0.7
    
    # Status Constants
    STATUS_PENDING = "pending"
    STATUS_WAITING_FOR_NOTES = "waiting_for_notes"
    STATUS_APPROVED = "approved"
    STATUS_REGENERATION_NEEDED = "regeneration_needed"
    STATUS_COMPLETED = "completed"
    STATUS_ERROR = "error"
    
    # Notes Status Constants
    NOTES_YES = "yes"
    NOTES_NO = "no"
    NOTES_NOT_NEEDED = "no_notes_needed"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        return True
