"""
Summarizer Module
Creates concise summaries of chapters for context chaining
"""
from groq import Groq
from config import Config
from api_key_manager import APIKeyManager


class Summarizer:
    """Handles chapter summarization"""
    
    def __init__(self):
        """Initialize API Key Manager"""
        Config.validate()
        self.api_manager = APIKeyManager(Config.GROQ_API_KEYS)
        self.model = Config.GROQ_MODEL
    
    def summarize_chapter(self, chapter_content: str, chapter_number: int, 
                         chapter_title: str) -> str:
        """
        Create a concise summary of a chapter for context chaining
        
        Args:
            chapter_content: The full chapter text
            chapter_number: Chapter number
            chapter_title: Chapter title
            
        Returns:
            Concise summary (150-200 words)
        """
        prompt = f"""Summarize the following chapter from a book. Create a concise summary (150-200 words) that captures:
- Main topics covered
- Key concepts and ideas
- Important takeaways
- Any critical information needed for continuity

This summary will be used as context for writing subsequent chapters, so focus on content that maintains narrative and thematic continuity.

**Chapter {chapter_number}: {chapter_title}**

{chapter_content}

Provide just the summary, without any preamble:"""

        try:
            summary = self.api_manager.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating concise, informative summaries that capture the essence of content while maintaining all critical information for continuity."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.5,  # Lower temperature for more focused summaries
                max_tokens=500
            )
            
            return summary.strip()
            
        except Exception as e:
            raise Exception(f"Failed to summarize chapter {chapter_number}: {str(e)}")
    
    def summarize_outline(self, outline: str) -> str:
        """
        Create a brief summary of the book outline
        
        Args:
            outline: The full outline text
            
        Returns:
            Brief summary of the outline
        """
        prompt = f"""Provide a brief summary (100-150 words) of this book outline that captures:
- The book's main theme
- Key topics covered
- The logical flow of chapters

{outline}

Provide just the summary:"""

        try:
            summary = self.api_manager.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating concise summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=300
            )
            
            return summary.strip()
            
        except Exception as e:
            raise Exception(f"Failed to summarize outline: {str(e)}")
