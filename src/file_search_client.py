"""
Core Google File Search API client wrapper.
"""
import google.generativeai as genai
from google.generativeai import types
from typing import List, Optional, Dict, Any
import os
import time
import json
from pathlib import Path

from config.settings import settings

class FileSearchClient:
    """Wrapper class for Google AI File operations and RAG functionality."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with API key."""
        self.api_key = api_key or settings.api_key
        genai.configure(api_key=self.api_key)
        self.stores_file = Path("data/stores.json")
        self.uploaded_files = self._load_stores()
    
    def _load_stores(self) -> Dict[str, List[Dict]]:
        """Load stores from persistent storage."""
        if self.stores_file.exists():
            try:
                with open(self.stores_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Could not load stores: {e}")
        return {}
    
    def _save_stores(self):
        """Save stores to persistent storage."""
        try:
            self.stores_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stores_file, 'w') as f:
                json.dump(self.uploaded_files, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save stores: {e}")
        
    def create_store(self, store_name: str) -> str:
        """
        Create a virtual store for organizing uploaded files.
        
        Args:
            store_name: Display name for the store
            
        Returns:
            Store name for future operations
        """
        try:
            if store_name not in self.uploaded_files:
                self.uploaded_files[store_name] = []
                self._save_stores()
            print(f"✅ Created virtual store: {store_name}")
            return store_name
        except Exception as e:
            print(f"❌ Error creating store '{store_name}': {e}")
            raise
    
    def list_stores(self) -> List[Dict[str, Any]]:
        """
        List all virtual stores.
        
        Returns:
            List of store information dictionaries
        """
        try:
            stores = []
            for store_name, files in self.uploaded_files.items():
                stores.append({
                    'name': store_name,
                    'display_name': store_name,
                    'file_count': len(files),
                    'create_time': 'N/A'
                })
            return stores
        except Exception as e:
            print(f"❌ Error listing stores: {e}")
            raise
    
    def delete_store(self, store_name: str, force: bool = True) -> bool:
        """
        Delete a virtual store and its files.
        
        Args:
            store_name: Name of the store to delete
            force: Whether to force deletion
            
        Returns:
            True if successful
        """
        try:
            if store_name in self.uploaded_files:
                # Delete all files in the store
                for file_info in self.uploaded_files[store_name]:
                    try:
                        genai.delete_file(file_info['name'])
                    except:
                        pass  # File might already be deleted
                del self.uploaded_files[store_name]
                self._save_stores()
                print(f"✅ Deleted virtual store: {store_name}")
                return True
            else:
                print(f"⚠️  Store '{store_name}' not found")
                return False
        except Exception as e:
            print(f"❌ Error deleting store '{store_name}': {e}")
            raise
    
    def upload_document(
        self, 
        file_path: str, 
        store_name: str, 
        display_name: Optional[str] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Upload a document to Google AI and track it in a virtual store.
        
        Args:
            file_path: Path to the file to upload
            store_name: Name of the target store
            display_name: Optional display name for the file
            metadata: Optional metadata for the file
            
        Returns:
            File name from Google AI
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check file size
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            if file_size_mb > settings.max_file_size_mb:
                raise ValueError(f"File size ({file_size_mb:.1f}MB) exceeds limit ({settings.max_file_size_mb}MB)")
            
            print(f"🔄 Uploading {file_path_obj.name} ({file_size_mb:.1f}MB)...")
            
            # Upload to Google AI
            uploaded_file = genai.upload_file(
                path=str(file_path_obj),
                display_name=display_name or file_path_obj.name
            )
            
            # Wait for file to be processed
            while uploaded_file.state.name == "PROCESSING":
                print("⏳ Processing upload...")
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name != "ACTIVE":
                raise Exception(f"Upload failed: {uploaded_file.state}")
            
            # Track file in virtual store
            if store_name not in self.uploaded_files:
                self.uploaded_files[store_name] = []
            
            file_info = {
                'name': uploaded_file.name,
                'display_name': uploaded_file.display_name,
                'size_bytes': file_path_obj.stat().st_size,
                'mime_type': uploaded_file.mime_type,
                'metadata': metadata or {}
            }
            self.uploaded_files[store_name].append(file_info)
            self._save_stores()
            
            print(f"✅ Successfully uploaded: {file_path_obj.name}")
            return uploaded_file.name
            
        except Exception as e:
            print(f"❌ Error uploading file '{file_path}': {e}")
            raise
    
    def upload_from_url(
        self,
        url: str,
        store_name: str,
        display_name: Optional[str] = None
    ) -> str:
        """
        Upload a document from URL to File Search store.
        
        Args:
            url: URL of the document to upload
            store_name: Name of the target store
            display_name: Optional display name for the file
            
        Returns:
            Upload operation name
        """
        try:
            try:
                import httpx
            except ImportError:
                raise ImportError("httpx is required for URL uploads. Install with: pip install httpx")
            
            # Download the file temporarily
            response = httpx.get(url)
            response.raise_for_status()
            
            # Create temporary file
            temp_file = Path(f"temp_{int(time.time())}_{url.split('/')[-1]}")
            temp_file.write_bytes(response.content)
            
            try:
                # Upload the file
                operation_name = self.upload_document(
                    str(temp_file), 
                    store_name, 
                    display_name or url.split('/')[-1]
                )
                return operation_name
            finally:
                # Clean up temporary file
                if temp_file.exists():
                    temp_file.unlink()
                    
        except Exception as e:
            print(f"❌ Error uploading from URL '{url}': {e}")
            raise
    
    def list_files_in_store(self, store_name: str) -> List[Dict[str, Any]]:
        """
        List all files in a virtual store.
        
        Args:
            store_name: Name of the store
            
        Returns:
            List of file information dictionaries
        """
        try:
            if store_name not in self.uploaded_files:
                return []
            return self.uploaded_files[store_name]
        except Exception as e:
            print(f"❌ Error listing files in store '{store_name}': {e}")
            raise
    
    def get_store_by_name(self, display_name: str) -> Optional[str]:
        """
        Get store name by display name.
        
        Args:
            display_name: Display name to search for
            
        Returns:
            Store name if found, None otherwise
        """
        try:
            if display_name in self.uploaded_files:
                return display_name
            return None
        except Exception as e:
            print(f"❌ Error searching for store '{display_name}': {e}")
            return None
    
    def get_files_for_generation(self, store_name: str) -> List[str]:
        """
        Get list of file names for use in content generation.
        
        Args:
            store_name: Name of the store
            
        Returns:
            List of file names
        """
        if store_name not in self.uploaded_files:
            return []
        return [file_info['name'] for file_info in self.uploaded_files[store_name]]