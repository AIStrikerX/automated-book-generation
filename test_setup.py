"""
Quick Test Script
Verifies that the system is set up correctly and all components work
"""
import sys
from pathlib import Path


def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    try:
        import groq
        print("  ✓ groq")
    except ImportError:
        print("  ✗ groq - Run: pip install groq")
        return False
    
    try:
        import supabase
        print("  ✓ supabase")
    except ImportError:
        print("  ✗ supabase - Run: pip install supabase")
        return False
    
    try:
        import docx
        print("  ✓ python-docx")
    except ImportError:
        print("  ✗ python-docx - Run: pip install python-docx")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  ✓ python-dotenv")
    except ImportError:
        print("  ✗ python-dotenv - Run: pip install python-dotenv")
        return False
    
    return True


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from config import Config
        
        if Config.GROQ_API_KEY:
            print(f"  ✓ Groq API Key configured (starts with: {Config.GROQ_API_KEY[:10]}...)")
        else:
            print("  ⚠ Groq API Key not configured (will use demo mode)")
        
        if Config.SUPABASE_URL:
            print("  ✓ Supabase URL configured")
        else:
            print("  ⚠ Supabase not configured (will use demo mode)")
        
        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def test_modules():
    """Test that all custom modules load"""
    print("\nTesting custom modules...")
    
    modules = [
        "config",
        "db",
        "outline_generator",
        "chapter_generator",
        "summarizer",
        "compiler",
        "notifier",
        "main"
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}.py")
        except Exception as e:
            print(f"  ✗ {module}.py - Error: {e}")
            all_ok = False
    
    return all_ok


def test_groq_api():
    """Test Groq API connection"""
    print("\nTesting Groq API connection...")
    try:
        from groq import Groq
        from config import Config
        
        if not Config.GROQ_API_KEY:
            print("  ⚠ API key not configured, skipping API test")
            return True
        
        client = Groq(api_key=Config.GROQ_API_KEY)
        
        # Try a simple completion
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[{"role": "user", "content": "Say 'test successful' in 2 words"}],
            max_tokens=10
        )
        
        if response.choices:
            print(f"  ✓ Groq API working - Response: {response.choices[0].message.content}")
            return True
        else:
            print("  ✗ Groq API returned empty response")
            return False
            
    except Exception as e:
        print(f"  ✗ Groq API error: {e}")
        return False


def test_output_directory():
    """Test output directory creation"""
    print("\nTesting output directory...")
    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        if output_dir.exists():
            print("  ✓ Output directory ready")
            return True
        else:
            print("  ✗ Could not create output directory")
            return False
    except Exception as e:
        print(f"  ✗ Output directory error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("AUTOMATED BOOK GENERATION SYSTEM - SETUP TEST")
    print("="*60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Custom Modules", test_modules),
        ("Groq API", test_groq_api),
        ("Output Directory", test_output_directory)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n  ✗ {test_name} - Unexpected error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    all_passed = all(results.values())
    
    print("="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED - System is ready!")
        print("\nNext steps:")
        print("  1. Run: python demo.py")
        print("  2. Choose a demo to see the system in action")
    else:
        print("⚠ SOME TESTS FAILED - Please check the errors above")
        print("\nCommon fixes:")
        print("  1. Run: pip install -r requirements.txt")
        print("  2. Create .env file with your credentials")
        print("  3. Check that all Python files are present")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
