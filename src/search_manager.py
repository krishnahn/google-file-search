"""
Search manager for semantic search, query processing, and result retrieval.
"""
import google.generativeai as genai
from typing import List, Optional, Dict, Any
import time

from src.file_search_client import FileSearchClient
from src.response_handler import ResponseHandler, SearchResponse
from config.settings import settings
from config.prompts import PromptTemplates

class SearchManager:
    """Manages search operations and query processing with Google AI files."""

    def __init__(self, client: FileSearchClient, model_name: Optional[str] = None):
        """
        Initialize SearchManager.

        Args:
            client: FileSearchClient instance
            model_name: Model to use for generation (defaults to settings)
        """
        self.client = client
        self.model_name = model_name or settings.default_model
        self.response_handler = ResponseHandler()

        # Configure the generative AI client
        genai.configure(api_key=self.client.api_key)

        # Performance optimization: Cache file objects to avoid repeated API calls
        self._file_cache: Dict[str, Any] = {}
        self._cache_ttl = 3600  # Cache files for 1 hour
        self._cache_timestamps: Dict[str, float] = {}

    def _get_file_cached(self, file_name: str) -> Any:
        """
        Get file object with caching to avoid repeated API calls.

        Args:
            file_name: Name of the file to retrieve

        Returns:
            File object from cache or API
        """
        current_time = time.time()

        # Check if file is in cache and not expired
        if file_name in self._file_cache:
            cache_age = current_time - self._cache_timestamps.get(file_name, 0)
            if cache_age < self._cache_ttl:
                return self._file_cache[file_name]

        # Fetch from API and cache
        file_obj = genai.get_file(file_name)
        self._file_cache[file_name] = file_obj
        self._cache_timestamps[file_name] = current_time
        return file_obj

    def clear_cache(self):
        """Clear the file object cache."""
        self._file_cache.clear()
        self._cache_timestamps.clear()
        print("✅ File cache cleared")

    def search_and_generate(
        self,
        query: str,
        store_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = 2048,  # OPTIMIZATION: More aggressive limit for speed
        max_files: Optional[int] = 5  # OPTIMIZATION: Default to 5 files for faster responses
    ) -> SearchResponse:
        """
        Perform semantic search and generate response using uploaded files.

        Args:
            query: User query
            store_name: File store to search
            system_prompt: Optional system prompt override
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens in response (default 8192)
            max_files: Maximum number of files to include (default: all)

        Returns:
            SearchResponse with answer and citations
        """
        try:
            # Get files from the store
            file_names = self.client.get_files_for_generation(store_name)
            if not file_names:
                return SearchResponse(
                    answer=f"No files found in store '{store_name}'. Please upload some documents first.",
                    citations=[],
                    model_used=self.model_name,
                    query=query
                )

            # OPTIMIZATION: Limit number of files with smart selection
            if max_files and len(file_names) > max_files:
                print(f"⚡ Limiting to {max_files} files (out of {len(file_names)}) for faster response")
                
                # Get file sizes and prioritize smaller files for speed
                try:
                    file_info_list = self.client.list_files_in_store(store_name)
                    file_size_map = {f['name']: f['size_bytes'] for f in file_info_list}
                    
                    # Sort files by size (smaller first for faster processing)
                    file_names_with_sizes = [(name, file_size_map.get(name, 0)) for name in file_names]
                    file_names_with_sizes.sort(key=lambda x: x[1])  # Sort by size
                    
                    # Take the smallest files up to max_files
                    file_names = [name for name, size in file_names_with_sizes[:max_files]]
                    
                    total_size_mb = sum(size for _, size in file_names_with_sizes[:max_files]) / (1024 * 1024)
                    print(f"   Selected files total size: {total_size_mb:.1f} MB")
                    
                except Exception as e:
                    print(f"   Warning: Could not optimize file selection: {e}")
                    file_names = file_names[:max_files]
            
            # Prepare the prompt
            formatted_query = PromptTemplates.format_search_prompt(query)
            
            print(f"🔍 Searching {len(file_names)} files in store '{store_name}' for: {query[:100]}...")
            
            # Create model instance
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=system_prompt or PromptTemplates.RAG_SYSTEM_PROMPT
            )
            
            # Prepare content with files (using cache for performance)
            content = [formatted_query]
            for file_name in file_names:
                try:
                    file_obj = self._get_file_cached(file_name)
                    content.append(file_obj)
                except Exception as e:
                    print(f"⚠️  Could not access file {file_name}: {e}")
            
            # Generate response with file context
            response = model.generate_content(content)
            
            # Process the response
            search_response = self.response_handler.process_response(
                response=response,
                query=query,
                model_name=self.model_name
            )
            
            print(f"✅ Generated response from {len(file_names)} files")
            return search_response
            
        except Exception as e:
            print(f"❌ Error during search and generation: {e}")
            # Return error response
            return SearchResponse(
                answer=f"Error processing query: {e}",
                citations=[],
                model_used=self.model_name,
                query=query
            )
    
    def search_multiple_stores(
        self,
        query: str,
        store_names: List[str],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1
    ) -> SearchResponse:
        """
        Search across multiple file stores.
        
        Args:
            query: User query
            store_names: List of store names to search
            system_prompt: Optional system prompt override
            temperature: Generation temperature
            
        Returns:
            SearchResponse combining results from all stores
        """
        try:
            # Collect files from all stores
            all_files = []
            for store_name in store_names:
                files = self.client.get_files_for_generation(store_name)
                all_files.extend(files)
            
            if not all_files:
                return SearchResponse(
                    answer=f"No files found in stores: {', '.join(store_names)}",
                    citations=[],
                    model_used=self.model_name,
                    query=query
                )
            
            formatted_query = PromptTemplates.format_search_prompt(query)
            
            print(f"🔍 Searching across {len(store_names)} stores ({len(all_files)} files) for: {query[:100]}...")
            
            # Create model and generate response
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.GenerationConfig(temperature=temperature),
                system_instruction=system_prompt or PromptTemplates.RAG_SYSTEM_PROMPT
            )
            
            content = [formatted_query]
            for file_name in all_files:
                try:
                    file_obj = self._get_file_cached(file_name)
                    content.append(file_obj)
                except Exception as e:
                    print(f"⚠️  Could not access file {file_name}: {e}")
            
            response = model.generate_content(content)
            
            search_response = self.response_handler.process_response(
                response=response,
                query=query,
                model_name=self.model_name
            )
            
            print(f"✅ Found response from {len(all_files)} files across {len(store_names)} stores")
            return search_response
            
        except Exception as e:
            print(f"❌ Error during multi-store search: {e}")
            return SearchResponse(
                answer=f"Error processing multi-store query: {e}",
                citations=[],
                model_used=self.model_name,
                query=query
            )
    
    def ask_question(
        self,
        question: str,
        store_name: str,
        context: Optional[str] = None,
        max_files: Optional[int] = 3  # OPTIMIZATION: Even fewer files for Q&A
    ) -> SearchResponse:
        """
        Ask a specific question with optional additional context.
        
        Args:
            question: Direct question to ask
            store_name: File store to search
            context: Optional additional context
            
        Returns:
            SearchResponse with direct answer
        """
        try:
            # Format as Q&A prompt
            formatted_prompt = PromptTemplates.format_qa_prompt(question)
            
            if context:
                formatted_prompt = f"Additional context: {context}\n\n{formatted_prompt}"
            
            return self.search_and_generate(
                query=formatted_prompt,
                store_name=store_name,
                temperature=0.0,  # More deterministic for Q&A
                max_tokens=1024,  # OPTIMIZATION: Shorter for direct Q&A
                max_files=max_files
            )
            
        except Exception as e:
            print(f"❌ Error during question answering: {e}")
            return SearchResponse(
                answer=f"Error processing question: {e}",
                citations=[],
                model_used=self.model_name,
                query=question
            )
    
    def summarize_documents(
        self,
        store_name: str,
        focus_topic: Optional[str] = None,
        max_files: Optional[int] = 7  # OPTIMIZATION: Most files for summaries but still limited
    ) -> SearchResponse:
        """
        Generate a summary of documents in a store.
        
        Args:
            store_name: File store to summarize
            focus_topic: Optional topic to focus the summary on
            
        Returns:
            SearchResponse with document summary
        """
        try:
            if focus_topic:
                query = f"{PromptTemplates.SUMMARIZATION_PROMPT}\n\nFocus particularly on information related to: {focus_topic}"
            else:
                query = PromptTemplates.SUMMARIZATION_PROMPT
            
            return self.search_and_generate(
                query=query,
                store_name=store_name,
                temperature=0.3,  # Slightly more creative for summaries
                max_tokens=3072,  # OPTIMIZATION: Reasonable summary length
                max_files=max_files
            )
            
        except Exception as e:
            print(f"❌ Error during document summarization: {e}")
            return SearchResponse(
                answer=f"Error generating summary: {e}",
                citations=[],
                model_used=self.model_name,
                query="Document summarization"
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        try:
            model = genai.get_model(f"models/{self.model_name}")
            return {
                'name': model.name,
                'display_name': model.display_name,
                'description': model.description,
                'input_token_limit': model.input_token_limit,
                'output_token_limit': model.output_token_limit,
                'supported_generation_methods': model.supported_generation_methods
            }
        except Exception as e:
            return {
                'name': self.model_name,
                'error': f"Could not retrieve model info: {e}"
            }
    
    def set_model(self, model_name: str) -> bool:
        """
        Change the model used for generation.
        
        Args:
            model_name: Name of the new model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Test if model exists and is accessible
            genai.get_model(f"models/{model_name}")
            self.model_name = model_name
            print(f"✅ Switched to model: {model_name}")
            return True
        except Exception as e:
            print(f"❌ Error switching to model '{model_name}': {e}")
            return False
    
    def batch_search(
        self,
        queries: List[str],
        store_name: str,
        delay_seconds: float = 1.0
    ) -> List[SearchResponse]:
        """
        Process multiple queries with rate limiting.
        
        Args:
            queries: List of queries to process
            store_name: File store to search
            delay_seconds: Delay between requests
            
        Returns:
            List of SearchResponse objects
        """
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"🔄 Processing query {i}/{len(queries)}: {query[:50]}...")
            
            try:
                response = self.search_and_generate(query, store_name)
                results.append(response)
                
                # Rate limiting
                if i < len(queries):  # Don't delay after last query
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                print(f"❌ Error processing query {i}: {e}")
                results.append(SearchResponse(
                    answer=f"Error processing query: {e}",
                    citations=[],
                    model_used=self.model_name,
                    query=query
                ))
        
        print(f"✅ Completed batch processing of {len(queries)} queries")
        return results