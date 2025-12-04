"""
Basic RAG example using Google File Search API.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from src.file_search_client import FileSearchClient
from src.document_processor import DocumentProcessor
from src.search_manager import SearchManager
from src.response_handler import ResponseHandler

def basic_rag_example():
    """
    Demonstrates basic RAG functionality with Google File Search.
    """
    print("🚀 Basic Google File Search RAG Example")
    print("=" * 50)
    
    try:
        # Initialize the client
        print("📡 Initializing File Search client...")
        client = FileSearchClient()
        
        # Create document processor and search manager
        doc_processor = DocumentProcessor(client)
        search_manager = SearchManager(client)
        
        # Create a new store for demo
        store_name = "demo-rag-store"
        print(f"📂 Creating File Search store: {store_name}")
        
        try:
            store_id = client.create_store(store_name)
        except Exception as e:
            # Store might already exist, try to find it
            store_id = client.get_store_by_name(store_name)
            if not store_id:
                print(f"❌ Could not create or find store: {e}")
                return
            print(f"📂 Using existing store: {store_name}")
        
        # Check if we have any documents in the data directory
        data_dir = Path(__file__).parent.parent / "data" / "documents"
        
        if not data_dir.exists() or not any(data_dir.iterdir()):
            print("\n📝 No documents found in data/documents directory.")
            print("To test the RAG system:")
            print("1. Add some PDF, TXT, or DOCX files to data/documents/")
            print("2. Re-run this example")
            print("\nFor now, let's demonstrate with a sample document...")
            
            # Create a sample document
            sample_doc = data_dir / "sample_document.txt"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            sample_content = """
# Sample Document for RAG Testing

## Introduction
This is a sample document to demonstrate the Google File Search RAG system.
The system can process various document formats including PDF, TXT, DOCX, HTML, and Markdown.

## Key Features
1. **Semantic Search**: Uses Google's embedding models for intelligent document retrieval
2. **Citation Support**: Provides source attribution for generated answers
3. **Multi-format Support**: Handles various document types automatically
4. **No Infrastructure**: No need for vector databases or custom embeddings

## Technical Details
The File Search API handles document chunking, indexing, and embedding generation automatically.
It supports files up to 100MB and PDFs up to 1000 pages.

## Use Cases
- Knowledge base search
- Document Q&A systems
- Research assistance
- Content summarization
- Technical documentation queries

## Conclusion
This RAG system provides enterprise-grade semantic search capabilities
without the complexity of managing vector databases or embedding models.
"""
            
            sample_doc.write_text(sample_content)
            print(f"📄 Created sample document: {sample_doc}")
        
        # Upload documents from the data directory
        print(f"\n📤 Uploading documents from {data_dir}...")
        operations = doc_processor.upload_directory(
            directory_path=str(data_dir),
            store_name=store_id,
            document_type="sample",
            category="demo"
        )
        
        if not operations:
            print("❌ No documents were uploaded. Please add some files to data/documents/")
            return
        
        # Wait a moment for indexing
        print("⏳ Waiting for document indexing...")
        import time
        time.sleep(3)
        
        # Example queries
        queries = [
            "What are the key features of this system?",
            "How does the File Search API work?",
            "What file formats are supported?",
            "What are the main use cases?"
        ]
        
        print(f"\n🔍 Testing {len(queries)} sample queries:")
        print("-" * 40)
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. Query: {query}")
            
            try:
                response = search_manager.search_and_generate(
                    query=query,
                    store_name=store_id
                )
                
                print(f"Answer: {response.answer[:200]}..." if len(response.answer) > 200 else f"Answer: {response.answer}")
                
                if response.citations:
                    print(f"Sources: {len(response.citations)} found")
                    for j, citation in enumerate(response.citations[:2], 1):  # Show first 2 citations
                        print(f"  {j}. {citation.file_name}")
                else:
                    print("Sources: None found")
                    
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        # Demonstrate summarization
        print(f"\n📋 Generating document summary...")
        try:
            summary_response = search_manager.summarize_documents(store_id)
            print(f"Summary: {summary_response.answer[:300]}..." if len(summary_response.answer) > 300 else f"Summary: {summary_response.answer}")
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
        
        # Show store information
        print(f"\n📊 Store Information:")
        try:
            files = client.list_files_in_store(store_id)
            print(f"Files in store: {len(files)}")
            for file_info in files:
                print(f"  - {file_info['display_name']} ({file_info['size_bytes']} bytes)")
        except Exception as e:
            print(f"❌ Error listing files: {e}")
        
        print(f"\n✅ Basic RAG example completed successfully!")
        print(f"You can now:")
        print(f"  1. Add more documents to data/documents/")
        print(f"  2. Run custom queries using the SearchManager")
        print(f"  3. Try the main.py CLI interface")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        print(f"Make sure you have:")
        print(f"  1. Set GEMINI_API_KEY in your .env file")
        print(f"  2. Installed dependencies: pip install -r requirements.txt")

if __name__ == "__main__":
    basic_rag_example()