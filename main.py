#!/usr/bin/env python3
"""
Main CLI interface for Google File Search RAG System.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add the current directory to the path for imports
sys.path.append(str(Path(__file__).parent))

from src.file_search_client import FileSearchClient
from src.document_processor import DocumentProcessor
from src.search_manager import SearchManager
from src.response_handler import ResponseHandler
from config.settings import settings

class RAGSystemCLI:
    """Command-line interface for the RAG system."""
    
    def __init__(self):
        """Initialize the CLI with all components."""
        try:
            self.client = FileSearchClient()
            self.doc_processor = DocumentProcessor(self.client)
            self.search_manager = SearchManager(self.client)
            self.response_handler = ResponseHandler()
            print("✅ RAG system initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize RAG system: {e}")
            print("Make sure you have set GEMINI_API_KEY in your .env file")
            sys.exit(1)
    
    def create_store(self, store_name: str) -> bool:
        """Create a new File Search store."""
        try:
            store_id = self.client.create_store(store_name)
            print(f"✅ Created store '{store_name}' with ID: {store_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to create store: {e}")
            return False
    
    def list_stores(self):
        """List all available stores."""
        try:
            stores = self.client.list_stores()
            if not stores:
                print("No stores found.")
                return
            
            print(f"📂 Found {len(stores)} stores:")
            for store in stores:
                print(f"  - {store['display_name']} (ID: {store['name']})")
                files = self.client.list_files_in_store(store['name'])
                print(f"    Files: {len(files)}")
        except Exception as e:
            print(f"❌ Error listing stores: {e}")
    
    def upload_file(self, file_path: str, store_name: str, doc_type: Optional[str] = None):
        """Upload a single file to a store."""
        try:
            # Check if store exists by display name or ID
            store_id = self.client.get_store_by_name(store_name)
            if not store_id:
                # Try using it as direct store ID
                stores = self.client.list_stores()
                if not any(s['name'] == store_name for s in stores):
                    print(f"❌ Store '{store_name}' not found. Available stores:")
                    for store in stores:
                        print(f"  - {store['display_name']}")
                    return False
                store_id = store_name
            
            operation = self.doc_processor.upload_document(
                file_path=file_path,
                store_name=store_id,
                document_type=doc_type or "document"
            )
            print(f"✅ Uploaded '{file_path}' to store '{store_name}'")
            return True
        except Exception as e:
            print(f"❌ Failed to upload file: {e}")
            return False
    
    def upload_directory(self, dir_path: str, store_name: str, recursive: bool = True):
        """Upload all files in a directory to a store."""
        try:
            store_id = self.client.get_store_by_name(store_name)
            if not store_id:
                stores = self.client.list_stores()
                if not any(s['name'] == store_name for s in stores):
                    print(f"❌ Store '{store_name}' not found")
                    return False
                store_id = store_name
            
            operations = self.doc_processor.upload_directory(
                directory_path=dir_path,
                store_name=store_id,
                recursive=recursive
            )
            print(f"✅ Uploaded {len(operations)} files from '{dir_path}'")
            return True
        except Exception as e:
            print(f"❌ Failed to upload directory: {e}")
            return False
    
    def search(self, query: str, store_name: str, format_output: bool = True):
        """Perform a search query."""
        try:
            store_id = self.client.get_store_by_name(store_name)
            if not store_id:
                stores = self.client.list_stores()
                if not any(s['name'] == store_name for s in stores):
                    print(f"❌ Store '{store_name}' not found")
                    return None
                store_id = store_name
            
            print(f"🔍 Searching in '{store_name}' for: {query}")
            response = self.search_manager.search_and_generate(
                query=query,
                store_name=store_id
            )
            
            if format_output:
                formatted = self.response_handler.format_response(response)
                print("\n" + "="*50)
                print(formatted)
            else:
                print(f"\nAnswer: {response.answer}")
                if response.citations:
                    print(f"Sources: {len(response.citations)} found")
            
            return response
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return None
    
    def ask_question(self, question: str, store_name: str):
        """Ask a direct question."""
        try:
            store_id = self.client.get_store_by_name(store_name)
            if not store_id:
                store_id = store_name
            
            response = self.search_manager.ask_question(
                question=question,
                store_name=store_id
            )
            
            print("\n" + "="*50)
            print(f"Question: {question}")
            print(f"Answer: {response.answer}")
            
            if response.citations:
                print(f"\nSources ({len(response.citations)}):")
                for i, citation in enumerate(response.citations, 1):
                    print(f"  {i}. {citation.file_name}")
            
            return response
        except Exception as e:
            print(f"❌ Question failed: {e}")
            return None
    
    def summarize(self, store_name: str, focus_topic: Optional[str] = None):
        """Generate a summary of documents in a store."""
        try:
            store_id = self.client.get_store_by_name(store_name)
            if not store_id:
                store_id = store_name
            
            response = self.search_manager.summarize_documents(
                store_name=store_id,
                focus_topic=focus_topic
            )
            
            print("\n" + "="*50)
            print("DOCUMENT SUMMARY")
            if focus_topic:
                print(f"Focus: {focus_topic}")
            print("="*50)
            print(response.answer)
            
            if response.citations:
                print(f"\nBased on {len(response.citations)} documents:")
                for citation in response.citations:
                    print(f"  - {citation.file_name}")
            
            return response
        except Exception as e:
            print(f"❌ Summarization failed: {e}")
            return None
    
    def interactive_mode(self, store_name: str):
        """Start interactive Q&A session."""
        print(f"\n🎯 Interactive mode with store: {store_name}")
        print("Type 'quit' to exit, 'help' for commands")
        print("="*50)
        
        while True:
            try:
                query = input("\n💬 Query: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if query.lower() == 'help':
                    print("""
Available commands:
  • Any question or query - Get AI-powered answer with citations
  • 'summarize' - Generate document summary
  • 'summarize [topic]' - Generate focused summary
  • 'files' - List files in current store
  • 'stores' - List all available stores
  • 'switch [store]' - Switch to different store
  • 'help' - Show this help
  • 'quit' - Exit interactive mode
""")
                    continue
                
                if query.lower() == 'files':
                    store_id = self.client.get_store_by_name(store_name) or store_name
                    files = self.client.list_files_in_store(store_id)
                    print(f"\n📁 Files in '{store_name}' ({len(files)}):")
                    for file_info in files:
                        size_mb = file_info['size_bytes'] / (1024 * 1024)
                        print(f"  - {file_info['display_name']} ({size_mb:.1f} MB)")
                    continue
                
                if query.lower() == 'stores':
                    self.list_stores()
                    continue
                
                if query.lower().startswith('switch '):
                    new_store = query[7:].strip()
                    if new_store:
                        store_name = new_store
                        print(f"🔄 Switched to store: {store_name}")
                    continue
                
                if query.lower().startswith('summarize'):
                    parts = query.split(' ', 1)
                    topic = parts[1] if len(parts) > 1 else None
                    self.summarize(store_name, topic)
                    continue
                
                # Regular search query
                self.search(query, store_name)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Google File Search RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new store
  python main.py create-store my-docs

  # Upload a file
  python main.py upload file.pdf my-docs

  # Upload a directory
  python main.py upload-dir ./documents my-docs

  # Search for information
  python main.py search "What is machine learning?" my-docs

  # Ask a direct question
  python main.py ask "How does this system work?" my-docs

  # Generate summary
  python main.py summarize my-docs

  # Interactive mode
  python main.py interactive my-docs

  # List all stores
  python main.py list-stores
"""
    )
    
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--model', default=settings.default_model, help='Model to use')
    parser.add_argument('--format', action='store_true', help='Format output nicely')
    
    args = parser.parse_args()
    
    try:
        cli = RAGSystemCLI()
        
        # Set model if specified
        if args.model != settings.default_model:
            cli.search_manager.set_model(args.model)
        
        # Execute commands
        if args.command == 'create-store':
            if not args.args:
                print("❌ Store name required")
                return
            cli.create_store(args.args[0])
        
        elif args.command == 'list-stores':
            cli.list_stores()
        
        elif args.command == 'upload':
            if len(args.args) < 2:
                print("❌ Usage: upload <file_path> <store_name>")
                return
            cli.upload_file(args.args[0], args.args[1])
        
        elif args.command == 'upload-dir':
            if len(args.args) < 2:
                print("❌ Usage: upload-dir <directory_path> <store_name>")
                return
            cli.upload_directory(args.args[0], args.args[1])
        
        elif args.command == 'search':
            if len(args.args) < 2:
                print("❌ Usage: search \"<query>\" <store_name>")
                return
            cli.search(args.args[0], args.args[1], args.format)
        
        elif args.command == 'ask':
            if len(args.args) < 2:
                print("❌ Usage: ask \"<question>\" <store_name>")
                return
            cli.ask_question(args.args[0], args.args[1])
        
        elif args.command == 'summarize':
            if not args.args:
                print("❌ Store name required")
                return
            focus = args.args[1] if len(args.args) > 1 else None
            cli.summarize(args.args[0], focus)
        
        elif args.command == 'interactive':
            if not args.args:
                print("❌ Store name required for interactive mode")
                return
            cli.interactive_mode(args.args[0])
        
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()