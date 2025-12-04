"""
Advanced search patterns and features demonstration.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from src.file_search_client import FileSearchClient
from src.document_processor import DocumentProcessor
from src.search_manager import SearchManager

def advanced_search_demo():
    """
    Demonstrates advanced search patterns and features.
    """
    print("🔬 Advanced Google File Search Features Demo")
    print("=" * 50)
    
    try:
        # Initialize components
        client = FileSearchClient()
        doc_processor = DocumentProcessor(client)
        search_manager = SearchManager(client)
        
        # Create multiple stores for different document types
        stores = {
            "technical-docs": "technical-documentation",
            "research-papers": "research-publications", 
            "user-manuals": "user-documentation"
        }
        
        store_ids = {}
        for key, display_name in stores.items():
            try:
                store_id = client.create_store(display_name)
                store_ids[key] = store_id
                print(f"📂 Created store: {display_name}")
            except Exception as e:
                # Try to find existing store
                store_id = client.get_store_by_name(display_name)
                if store_id:
                    store_ids[key] = store_id
                    print(f"📂 Using existing store: {display_name}")
                else:
                    print(f"⚠️  Could not create store {display_name}: {e}")
        
        if not store_ids:
            print("❌ No stores available for demo")
            return
        
        # Demonstrate metadata-rich document uploads
        print("\n📤 Demonstrating metadata-rich document uploads...")
        
        data_dir = Path(__file__).parent.parent / "data" / "documents"
        if data_dir.exists() and any(data_dir.iterdir()):
            
            # Upload with different metadata for categorization
            for file_path in data_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in doc_processor.SUPPORTED_FORMATS:
                    
                    # Determine store based on filename or extension
                    if "manual" in file_path.name.lower():
                        store_key = "user-manuals"
                        doc_type = "manual"
                        category = "user-documentation"
                    elif "research" in file_path.name.lower() or file_path.suffix == ".pdf":
                        store_key = "research-papers"
                        doc_type = "research"
                        category = "scientific"
                    else:
                        store_key = "technical-docs"
                        doc_type = "technical"
                        category = "reference"
                    
                    if store_key in store_ids:
                        try:
                            doc_processor.upload_document(
                                file_path=str(file_path),
                                store_name=store_ids[store_key],
                                document_type=doc_type,
                                category=category,
                                tags=["demo", "advanced", doc_type],
                                custom_fields={
                                    "upload_demo": "advanced_features",
                                    "version": 1.0
                                }
                            )
                        except Exception as e:
                            print(f"⚠️  Upload error for {file_path.name}: {e}")
        
        # Wait for indexing
        import time
        time.sleep(5)
        
        # Demonstrate advanced search patterns
        print("\n🔍 Advanced Search Patterns:")
        print("-" * 40)
        
        # 1. Multi-store search
        if len(store_ids) > 1:
            print("\n1. Multi-Store Search")
            response = search_manager.search_multiple_stores(
                query="What information is available about system features?",
                store_names=list(store_ids.values())
            )
            print(f"Answer: {response.answer[:200]}...")
            print(f"Sources from {len(set(c.file_name for c in response.citations))} different files")
        
        # 2. Focused question answering
        print("\n2. Focused Question Answering")
        first_store = list(store_ids.values())[0]
        qa_response = search_manager.ask_question(
            question="What is the main purpose of this system?",
            store_name=first_store,
            context="Focus on technical capabilities and use cases"
        )
        print(f"Q&A Answer: {qa_response.answer[:200]}...")
        
        # 3. Topic-focused summarization
        print("\n3. Topic-Focused Summarization")
        summary_response = search_manager.summarize_documents(
            store_name=first_store,
            focus_topic="technical features and capabilities"
        )
        print(f"Focused Summary: {summary_response.answer[:200]}...")
        
        # 4. Batch query processing
        print("\n4. Batch Query Processing")
        batch_queries = [
            "What are the system requirements?",
            "How does the search functionality work?",
            "What are the supported file formats?"
        ]
        
        batch_results = search_manager.batch_search(
            queries=batch_queries,
            store_name=first_store,
            delay_seconds=0.5
        )
        
        for i, result in enumerate(batch_results, 1):
            print(f"Batch {i}: {result.answer[:100]}... ({len(result.citations)} sources)")
        
        # 5. Model comparison
        print("\n5. Model Comparison")
        original_model = search_manager.model_name
        
        # Test with different models if available
        models_to_test = ["gemini-2.5-flash", "gemini-2.5-pro"]
        test_query = "Explain the key benefits of this system"
        
        for model in models_to_test:
            if search_manager.set_model(model):
                response = search_manager.search_and_generate(
                    query=test_query,
                    store_name=first_store,
                    temperature=0.2
                )
                print(f"{model}: {response.answer[:150]}...")
        
        # Restore original model
        search_manager.set_model(original_model)
        
        # 6. Response formatting demonstration
        print("\n6. Response Formatting Options")
        response = search_manager.search_and_generate(
            query="What are the main components of this system?",
            store_name=first_store
        )
        
        formatter = search_manager.response_handler
        
        print("Full formatted response:")
        print(formatter.format_response(response, include_citations=True)[:300] + "...")
        
        print("\nCitations only:")
        print(formatter.format_citations_only(response.citations))
        
        # 7. Store management demonstration
        print("\n📊 Store Management:")
        stores_list = client.list_stores()
        print(f"Total stores: {len(stores_list)}")
        
        for store in stores_list:
            if store['name'] in store_ids.values():
                files = client.list_files_in_store(store['name'])
                print(f"- {store['display_name']}: {len(files)} files")
        
        # 8. Model information
        print("\n🤖 Model Information:")
        model_info = search_manager.get_model_info()
        print(f"Model: {model_info.get('display_name', model_info.get('name'))}")
        print(f"Input limit: {model_info.get('input_token_limit', 'Unknown')} tokens")
        print(f"Output limit: {model_info.get('output_token_limit', 'Unknown')} tokens")
        
        print(f"\n✅ Advanced features demo completed!")
        print(f"Explored features:")
        print(f"  ✓ Multi-store search")
        print(f"  ✓ Metadata-rich uploads")
        print(f"  ✓ Focused Q&A and summarization")
        print(f"  ✓ Batch processing")
        print(f"  ✓ Model comparison")
        print(f"  ✓ Response formatting")
        print(f"  ✓ Store management")
        
    except Exception as e:
        print(f"❌ Advanced demo failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_demo_stores():
    """Clean up demo stores (optional)."""
    print("\n🧹 Cleaning up demo stores...")
    
    try:
        client = FileSearchClient()
        stores_to_cleanup = [
            "technical-documentation",
            "research-publications", 
            "user-documentation",
            "demo-rag-store"
        ]
        
        existing_stores = client.list_stores()
        for store in existing_stores:
            if store['display_name'] in stores_to_cleanup:
                try:
                    client.delete_store(store['name'])
                    print(f"✅ Deleted store: {store['display_name']}")
                except Exception as e:
                    print(f"⚠️  Could not delete {store['display_name']}: {e}")
    
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_demo_stores()
    else:
        advanced_search_demo()
        
        print(f"\nTo clean up demo stores, run:")
        print(f"python {__file__} cleanup")