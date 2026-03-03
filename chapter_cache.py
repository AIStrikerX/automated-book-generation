"""
Chapter caching system to persist generated chapters locally
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class ChapterCache:
    """Manages persistent storage of generated chapters"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_path(self, book_id: str) -> str:
        """Get the cache file path for a book"""
        return os.path.join(self.cache_dir, f"{book_id}.json")
    
    def save_chapter(self, book_id: str, chapter_number: int, chapter_data: Dict) -> None:
        """Save a single chapter to cache"""
        cache_path = self._get_cache_path(book_id)
        
        # Load existing cache if it exists
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        else:
            cache = {
                'book_id': book_id,
                'created_at': datetime.now().isoformat(),
                'chapters': {}
            }
        
        # Save chapter
        cache['chapters'][str(chapter_number)] = chapter_data
        cache['updated_at'] = datetime.now().isoformat()
        
        # Write to disk
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Cached chapter {chapter_number} for book {book_id}")
    
    def load_chapters(self, book_id: str) -> Optional[List[Dict]]:
        """Load all chapters for a book from cache"""
        cache_path = self._get_cache_path(book_id)
        
        if not os.path.exists(cache_path):
            return None
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        # Convert dict back to list
        chapters = []
        for i in sorted([int(k) for k in cache['chapters'].keys()]):
            chapters.append(cache['chapters'][str(i)])
        
        return chapters
    
    def get_cached_chapter_count(self, book_id: str) -> int:
        """Get the number of cached chapters for a book"""
        cache_path = self._get_cache_path(book_id)
        
        if not os.path.exists(cache_path):
            return 0
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        return len(cache.get('chapters', {}))
    
    def clear_cache(self, book_id: str) -> None:
        """Delete cache for a book"""
        cache_path = self._get_cache_path(book_id)
        if os.path.exists(cache_path):
            os.remove(cache_path)
            print(f"🗑️ Cleared cache for book {book_id}")
    
    def cache_exists(self, book_id: str) -> bool:
        """Check if cache exists for a book"""
        return os.path.exists(self._get_cache_path(book_id))
    
    def save_outline(self, book_id: str, title: str, outline: str) -> None:
        """Save book outline to cache"""
        cache_path = self._get_cache_path(book_id)
        
        cache = {
            'book_id': book_id,
            'title': title,
            'outline': outline,
            'created_at': datetime.now().isoformat(),
            'chapters': {}
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Cached outline for book {book_id}")
    
    def get_book_info(self, book_id: str) -> Optional[Dict]:
        """Get book info from cache"""
        cache_path = self._get_cache_path(book_id)
        
        if not os.path.exists(cache_path):
            return None
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        return {
            'book_id': cache.get('book_id'),
            'title': cache.get('title'),
            'outline': cache.get('outline'),
            'chapter_count': len(cache.get('chapters', {})),
            'created_at': cache.get('created_at'),
            'updated_at': cache.get('updated_at')
        }
