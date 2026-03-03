"""
Chapter Generator Module
Generates book chapters with context chaining from previous chapters
"""
from groq import Groq
from config import Config
from api_key_manager import APIKeyManager
from typing import List, Optional


class ChapterGenerator:
    """Handles chapter generation with contextual awareness"""
    
    def __init__(self):
        """Initialize API Key Manager"""
        Config.validate()
        self.api_manager = APIKeyManager(Config.GROQ_API_KEYS)
        self.model = Config.GROQ_MODEL
    
    def generate_chapter(self, 
                        title: str,
                        chapter_number: int,
                        chapter_title: str,
                        chapter_description: str,
                        previous_summaries: List[str] = None,
                        chapter_notes: str = "") -> str:
        """
        Generate a chapter with context from previous chapters
        
        Args:
            title: The book title
            chapter_number: Current chapter number
            chapter_title: Title of this chapter
            chapter_description: Description from outline
            previous_summaries: List of summaries from previous chapters
            chapter_notes: Optional editor notes for this chapter
            
        Returns:
            Generated chapter content
        """
        prompt = self._build_chapter_prompt(
            title,
            chapter_number,
            chapter_title,
            chapter_description,
            previous_summaries,
            chapter_notes
        )
        
        try:
            chapter_content = self.api_manager.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert book writer. Write engaging, well-structured chapters with:
- Clear introduction that connects to previous chapters
- Detailed explanations with examples
- Smooth transitions between sections
- Strong conclusion that sets up the next chapter
- Professional, accessible writing style
- Proper formatting with subheadings where appropriate"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            return chapter_content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate chapter {chapter_number}: {str(e)}")
    
    def regenerate_chapter(self,
                          title: str,
                          chapter_number: int,
                          chapter_title: str,
                          original_content: str,
                          chapter_notes: str,
                          previous_summaries: List[str] = None) -> str:
        """
        Regenerate a chapter based on editor feedback
        
        Args:
            title: The book title
            chapter_number: Current chapter number
            chapter_title: Title of this chapter
            original_content: Previously generated content
            chapter_notes: Editor feedback
            previous_summaries: List of summaries from previous chapters
            
        Returns:
            Regenerated chapter content
        """
        prompt = f"""I need you to revise this book chapter based on editor feedback.

Book Title: {title}
Chapter {chapter_number}: {chapter_title}
"""
        
        if previous_summaries:
            prompt += "\n**Context from Previous Chapters:**\n"
            for summary in previous_summaries:
                prompt += f"- {summary}\n"
        
        prompt += f"""
**Original Chapter Content:**
{original_content}

**Editor Feedback:**
{chapter_notes}

Please rewrite this chapter addressing the editor's feedback while maintaining:
- Consistency with previous chapters
- The chapter's core purpose and flow
- High quality writing standards
- Proper structure and formatting"""

        try:
            chapter_content = self.api_manager.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert book editor and writer. Revise chapters based on feedback while maintaining quality and consistency."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            return chapter_content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to regenerate chapter {chapter_number}: {str(e)}")
    
    def _build_chapter_prompt(self,
                             title: str,
                             chapter_number: int,
                             chapter_title: str,
                             chapter_description: str,
                             previous_summaries: List[str] = None,
                             chapter_notes: str = "") -> str:
        """Build the prompt for chapter generation"""
        prompt = f"""Write Chapter {chapter_number} of a book titled "{title}".

**Chapter {chapter_number}: {chapter_title}**

**Chapter Objective:**
{chapter_description}
"""
        
        if previous_summaries and len(previous_summaries) > 0:
            prompt += "\n**Context from Previous Chapters:**\n"
            prompt += "To maintain continuity, here are summaries of what has been covered so far:\n\n"
            for summary in previous_summaries:
                prompt += f"- {summary}\n"
            prompt += "\nPlease ensure this chapter builds naturally on these previous topics.\n"
        else:
            prompt += "\n**Note:** This is the first chapter, so set a strong foundation for the book.\n"
        
        if chapter_notes:
            prompt += f"""
**Editor's Special Instructions:**
{chapter_notes}

Please incorporate these instructions into the chapter.
"""
        
        prompt += """
**Writing Guidelines:**
- Write 2000-3000 words
- Use clear, engaging language
- Include practical examples where relevant
- Break content into logical sections with subheadings
- Ensure smooth flow and readability
- Maintain consistency with the book's theme and previous chapters
- End with a transition that connects to the next chapter

Begin writing the chapter now:"""
        
        return prompt
