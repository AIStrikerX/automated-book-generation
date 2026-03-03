"""
Outline Generator Module
Generates book outlines using Groq LLM based on title and editor notes
"""
from groq import Groq
from config import Config
from api_key_manager import APIKeyManager
from typing import Optional


class OutlineGenerator:
    """Handles outline generation with Groq API"""
    
    def __init__(self):
        """Initialize API Key Manager"""
        Config.validate()
        self.api_manager = APIKeyManager(Config.GROQ_API_KEYS)
        self.model = Config.GROQ_MODEL
    
    def generate_outline(self, title: str, notes_before: str = "") -> str:
        """
        Generate a book outline based on title and optional notes
        
        Args:
            title: The book title
            notes_before: Optional editor notes to guide outline generation
            
        Returns:
            Generated outline as formatted text
        """
        prompt = self._build_outline_prompt(title, notes_before)
        
        try:
            outline = self.api_manager.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert book outline creator. Create detailed, well-structured book outlines with clear chapter divisions and logical flow. Each chapter should have a brief description of its content."
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
            
            return outline.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate outline: {str(e)}")
    
    def regenerate_outline(self, title: str, original_outline: str, 
                          notes_after: str) -> str:
        """
        Regenerate outline based on editor feedback
        
        Args:
            title: The book title
            original_outline: The previously generated outline
            notes_after: Editor feedback on the original outline
            
        Returns:
            Regenerated outline
        """
        prompt = f"""I need you to revise the following book outline based on editor feedback.

Book Title: {title}

Original Outline:
{original_outline}

Editor Feedback:
{notes_after}

Please create an improved outline that addresses the editor's feedback while maintaining a clear structure and logical flow. Keep the same formatting style."""

        try:
            outline = self.api_manager.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert book outline creator. Revise outlines based on editor feedback while maintaining quality and structure."
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
            
            return outline.strip()
            
        except Exception as e:
            raise Exception(f"Failed to regenerate outline: {str(e)}")
    
    def _build_outline_prompt(self, title: str, notes_before: str) -> str:
        """Build the prompt for outline generation"""
        base_prompt = f"""Create a comprehensive book outline for the following title:

Title: "{title}"
"""
        
        if notes_before:
            base_prompt += f"""
Editor Notes/Requirements:
{notes_before}

Please incorporate these notes and requirements into the outline structure.
"""
        
        base_prompt += """
Format the outline as follows:
- Start with a brief overview of the book's main theme
- List 8-12 chapters with clear titles
- For each chapter, provide 2-3 sentences describing the key topics and content
- Ensure logical progression from one chapter to the next
- End with a conclusion chapter that ties everything together

Make the outline detailed enough to guide chapter writing but concise enough to be easily understood."""
        
        return base_prompt
    
    def parse_outline_into_chapters(self, outline: str) -> list[dict]:
        """
        Parse outline text into structured chapter data
        
        Returns:
            List of dicts with chapter_number, title, and description
        """
        chapters = []
        lines = outline.split('\n')
        current_chapter = None
        chapter_counter = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove markdown formatting (**, __, etc)
            clean_line = line.strip('*').strip('_').strip()
            
            # Check if line starts with "Chapter" followed by a number
            if clean_line.lower().startswith('chapter'):
                # Save previous chapter if exists
                if current_chapter:
                    chapters.append(current_chapter)
                
                chapter_counter += 1
                # Extract chapter title (everything after the chapter number/colon)
                parts = clean_line.split(':', 1)
                if len(parts) > 1:
                    chapter_title = parts[1].strip()
                else:
                    chapter_title = clean_line
                
                current_chapter = {
                    'chapter_number': chapter_counter,
                    'title': chapter_title,
                    'description': ''
                }
            elif current_chapter:
                # Add to current chapter description
                current_chapter['description'] += line + ' '
        
        # Add last chapter
        if current_chapter:
            chapters.append(current_chapter)
        
        # Clean up descriptions
        for chapter in chapters:
            chapter['description'] = chapter['description'].strip()
        
        return chapters
