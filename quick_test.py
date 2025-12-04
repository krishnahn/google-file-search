#!/usr/bin/env python3
"""
Quick test to verify the RAG system works end-to-end.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.file_search_client import FileSearchClient
from src.document_processor import DocumentProcessor
from src.search_manager import SearchManager

def quick_test():
    """Quick test of the RAG system functionality."""
    print("🚀 Quick RAG System Test")
    print("=" * 40)
    
    try:
        # Initialize components
        print("1. Initializing components...")
        client = FileSearchClient()
        doc_processor = DocumentProcessor(client)
        search_manager = SearchManager(client)
        print("   ✅ All components initialized")
        
        # Create store
        print("2. Creating virtual store...")
        store_name = "quick-test-store"
        client.create_store(store_name)
        print("   ✅ Store created")
        
        # Check if sample document exists
        data_dir = Path("data/documents")
        sample_doc = data_dir / "sample_document.txt"
        
        if not sample_doc.exists():
            print("3. Creating sample document...")
            data_dir.mkdir(parents=True, exist_ok=True)
            sample_content = """
Google File Search RAG System

This is a Retrieval Augmented Generation system that uses Google's File Search API 
instead of traditional vector databases. 

Key Features:
- Semantic search using Google's embeddings
- Citation support with source attribution  
- Multi-format document support (PDF, TXT, DOCX, HTML, Markdown)
- No infrastructure management required
- Built-in document processing and indexing

The system eliminates the complexity of managing vector databases while providing 
enterprise-grade semantic search capabilities.
"""
            sample_doc.write_text(sample_content.strip())
            print("   ✅ Sample document created")
        
        # Upload document
        print("4. Uploading sample document...")
        doc_processor.upload_document(
            file_path=str(sample_doc),
            store_name=store_name,
            document_type="demo"
        )
        print("   ✅ Document uploaded")
        
        # Test search
        print("5. Testing search functionality...")
        query = "What are the key features of this system?"
        response = search_manager.search_and_generate(
            query=query,
            store_name=store_name
        )
        
        print(f"   Query: {query}")
        print(f"   Answer: {response.answer[:200]}...")
        print(f"   ✅ Search completed successfully")
        
        # List store contents
        files = client.list_files_in_store(store_name)
        print(f"6. Store contents: {len(files)} files")
        for file_info in files:
            print(f"   - {file_info['display_name']}")
        
        print("\n🎉 Quick test completed successfully!")
        print("Your Google File Search RAG system is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)