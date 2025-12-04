"""
Document processor for handling file uploads and preprocessing.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import mimetypes

from src.file_search_client import FileSearchClient

class DocumentProcessor:
    """Handles document preprocessing, validation, and upload operations."""
    
    SUPPORTED_FORMATS = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.md': 'text/markdown',
        '.markdown': 'text/markdown'
    }
    
    def __init__(self, client: FileSearchClient):
        """Initialize with a FileSearchClient instance."""
        self.client = client
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if a file can be uploaded.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return False, f"File not found: {file_path}"
            
            # Check file extension
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                return False, f"Unsupported file format: {path.suffix}. Supported: {list(self.SUPPORTED_FORMATS.keys())}"
            
            # Check file size
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 100:  # Google's limit
                return False, f"File too large: {size_mb:.1f}MB (max 100MB)"
            
            # Check if file is readable
            try:
                with open(path, 'rb'):
                    pass
            except PermissionError:
                return False, f"Cannot read file: {file_path} (permission denied)"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validating file: {e}"
    
    def batch_validate_files(self, file_paths: List[str]) -> Dict[str, Tuple[bool, str]]:
        """
        Validate multiple files at once.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        for file_path in file_paths:
            results[file_path] = self.validate_file(file_path)
        return results
    
    def create_metadata(
        self,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create metadata for document upload.
        
        Args:
            document_type: Type of document (e.g., 'manual', 'report', 'article')
            category: Category classification
            tags: List of tags for the document
            custom_fields: Additional custom metadata fields
            
        Returns:
            List of metadata dictionaries
        """
        metadata = []
        
        if document_type:
            metadata.append({"key": "document_type", "string_value": document_type})
        
        if category:
            metadata.append({"key": "category", "string_value": category})
        
        if tags:
            metadata.append({"key": "tags", "string_value": ",".join(tags)})
        
        if custom_fields:
            for key, value in custom_fields.items():
                if isinstance(value, str):
                    metadata.append({"key": key, "string_value": value})
                elif isinstance(value, (int, float)):
                    metadata.append({"key": key, "numeric_value": value})
        
        return metadata
    
    def upload_document(
        self,
        file_path: str,
        store_name: str,
        display_name: Optional[str] = None,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Upload a document with preprocessing and metadata.
        
        Args:
            file_path: Path to the file
            store_name: Target File Search store
            display_name: Optional display name
            document_type: Document type classification
            category: Document category
            tags: List of tags
            custom_fields: Additional metadata
            
        Returns:
            Upload operation name
        """
        # Validate file first
        is_valid, error_msg = self.validate_file(file_path)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Create metadata
        metadata = self.create_metadata(
            document_type=document_type,
            category=category,
            tags=tags,
            custom_fields=custom_fields
        )
        
        # Upload the document
        return self.client.upload_document(
            file_path=file_path,
            store_name=store_name,
            display_name=display_name,
            metadata=metadata if metadata else None
        )
    
    def upload_directory(
        self,
        directory_path: str,
        store_name: str,
        recursive: bool = True,
        document_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[str]:
        """
        Upload all supported files in a directory.
        
        Args:
            directory_path: Path to the directory
            store_name: Target File Search store
            recursive: Whether to search subdirectories
            document_type: Default document type for all files
            category: Default category for all files
            
        Returns:
            List of upload operation names
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory not found or not a directory: {directory_path}")
        
        # Find all supported files
        files_to_upload = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                files_to_upload.append(file_path)
        
        if not files_to_upload:
            print(f"⚠️  No supported files found in {directory_path}")
            return []
        
        # Validate all files first
        print(f"🔍 Found {len(files_to_upload)} files to upload")
        validation_results = self.batch_validate_files([str(f) for f in files_to_upload])
        
        valid_files = [f for f, (valid, _) in validation_results.items() if valid]
        invalid_files = [f for f, (valid, msg) in validation_results.items() if not valid]
        
        if invalid_files:
            print(f"⚠️  Skipping {len(invalid_files)} invalid files:")
            for file_path in invalid_files:
                _, error_msg = validation_results[file_path]
                print(f"  - {file_path}: {error_msg}")
        
        # Upload valid files
        operation_names = []
        for file_path in valid_files:
            try:
                path = Path(file_path)
                # Use relative path as display name
                relative_path = path.relative_to(directory)
                
                operation_name = self.upload_document(
                    file_path=file_path,
                    store_name=store_name,
                    display_name=str(relative_path),
                    document_type=document_type,
                    category=category
                )
                operation_names.append(operation_name)
                
            except Exception as e:
                print(f"❌ Failed to upload {file_path}: {e}")
        
        print(f"✅ Successfully uploaded {len(operation_names)} files")
        return operation_names
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return {
            'path': str(path.absolute()),
            'name': path.name,
            'stem': path.stem,
            'suffix': path.suffix,
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'mime_type': mime_type,
            'is_supported': path.suffix.lower() in self.SUPPORTED_FORMATS,
            'modified_time': stat.st_mtime,
            'created_time': stat.st_ctime
        }