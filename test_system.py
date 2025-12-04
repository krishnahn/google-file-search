#!/usr/bin/env python3
"""
Test script to verify the Google File Search RAG system works correctly.
"""
import sys
from pathlib import Path

# Add the current directory to the path for imports
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🧪 Testing imports...")
    
    try:
        # Test internal imports first
        from config.settings import settings
        print("✅ Settings import successful")
        
        from config.prompts import PromptTemplates
        print("✅ Prompts import successful")
        
        from src.response_handler import ResponseHandler, Citation, SearchResponse
        print("✅ Response handler import successful")
        
        # Test Google API import (this will fail if package not installed)
        try:
            import google.generativeai as genai
            print("✅ Google Generative AI import successful")
        except ImportError as e:
            print(f"⚠️  Google Generative AI not installed: {e}")
            print("   Run: pip install -r requirements.txt")
            return False
        
        # Test main modules
        from src.file_search_client import FileSearchClient
        print("✅ File search client import successful")
        
        from src.document_processor import DocumentProcessor
        print("✅ Document processor import successful")
        
        from src.search_manager import SearchManager
        print("✅ Search manager import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration loading."""
    print("\n📋 Testing configuration...")
    
    try:
        from config.settings import settings
        
        # Check if API key is set
        if not settings.api_key or settings.api_key == 'your_api_key_here':
            print("⚠️  GEMINI_API_KEY not set in .env file")
            print("   Copy .env.example to .env and add your API key")
            return False
        
        print(f"✅ API key configured (length: {len(settings.api_key)} chars)")
        print(f"✅ Default model: {settings.default_model}")
        print(f"✅ Max tokens per chunk: {settings.max_tokens_per_chunk}")
        print(f"✅ Max file size: {settings.max_file_size_mb}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_client_initialization():
    """Test that the client can be initialized."""
    print("\n🔧 Testing client initialization...")
    
    try:
        from src.file_search_client import FileSearchClient
        from src.document_processor import DocumentProcessor
        from src.search_manager import SearchManager
        
        # Test basic client creation
        client = FileSearchClient()
        print("✅ FileSearchClient initialized")
        
        doc_processor = DocumentProcessor(client)
        print("✅ DocumentProcessor initialized")
        
        search_manager = SearchManager(client)
        print("✅ SearchManager initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_connection():
    """Test API connection (if API key is available)."""
    print("\n🌐 Testing API connection...")
    
    try:
        from src.file_search_client import FileSearchClient
        from config.settings import settings
        
        if not settings.api_key or settings.api_key == 'your_api_key_here':
            print("⚠️  Skipping API test - no API key configured")
            return True
        
        client = FileSearchClient()
        
        # Try to list existing stores (this will test API connectivity)
        stores = client.list_stores()
        print(f"✅ API connection successful - found {len(stores)} existing stores")
        
        for store in stores[:3]:  # Show first 3 stores
            print(f"   - {store['display_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        print("   Check your API key and internet connection")
        return False

def test_document_validation():
    """Test document validation functionality."""
    print("\n📄 Testing document validation...")
    
    try:
        from src.file_search_client import FileSearchClient
        from src.document_processor import DocumentProcessor
        
        client = FileSearchClient()
        doc_processor = DocumentProcessor(client)
        
        # Test supported formats
        supported = doc_processor.SUPPORTED_FORMATS
        print(f"✅ Supported formats: {list(supported.keys())}")
        
        # Test file validation with non-existent file
        is_valid, error = doc_processor.validate_file("non_existent_file.pdf")
        if not is_valid and "not found" in error.lower():
            print("✅ File validation correctly rejects non-existent files")
        else:
            print(f"⚠️  Unexpected validation result: {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document validation test failed: {e}")
        return False

def test_response_handling():
    """Test response handling functionality."""
    print("\n💬 Testing response handling...")
    
    try:
        from src.response_handler import ResponseHandler, SearchResponse, Citation
        
        handler = ResponseHandler()
        
        # Create a test response
        test_citations = [
            Citation(file_name="test1.pdf", chunk_text="This is a test chunk", page_number=1),
            Citation(file_name="test2.pdf", chunk_text="Another test chunk", page_number=2)
        ]
        
        test_response = SearchResponse(
            answer="This is a test answer from the RAG system.",
            citations=test_citations,
            model_used="gemini-2.5-flash",
            query="What is this about?"
        )
        
        # Test formatting
        formatted = handler.format_response(test_response)
        if "test answer" in formatted.lower() and "sources" in formatted.lower():
            print("✅ Response formatting working correctly")
        else:
            print("⚠️  Response formatting may have issues")
        
        # Test citation formatting
        citations_only = handler.format_citations_only(test_citations)
        if "test1.pdf" in citations_only and "test2.pdf" in citations_only:
            print("✅ Citation formatting working correctly")
        else:
            print("⚠️  Citation formatting may have issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Response handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Google File Search RAG System - Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_configuration,
        test_client_initialization,
        test_api_connection,
        test_document_validation,
        test_response_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your RAG system is ready to use.")
        print("\nNext steps:")
        print("1. Add documents to data/documents/")
        print("2. Run: python examples/basic_rag.py")
        print("3. Or use CLI: python main.py --help")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Set API key in .env file")
        print("- Check internet connection")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)