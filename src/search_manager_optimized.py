"""
OPTIMIZED Search manager with multiple performance improvements.
Addresses the primary bottleneck: Content Generation API calls.
"""
import google.generativeai as genai
from typing import List, Optional, Dict, Any
import time

from src.file_search_client import FileSearchClient
from src.response_handler import ResponseHandler, SearchResponse
from config.settings import settings
from config.prompts import PromptTemplates


class SearchManagerOptimized:
    """
    Optimized SearchManager with performance improvements:
    1. File caching (already implemented)
    2. Response length limiting
    3. Streaming support
    4. More concise prompts
    5. Optional file filtering
    """

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
        max_tokens: Optional[int] = 2048,  # OPTIMIZATION: Limit response length
        max_files: Optional[int] = None  # OPTIMIZATION: Limit number of files
    ) -> SearchResponse:
        """
        Perform semantic search and generate response using uploaded files.

        OPTIMIZATIONS:
        - Default max_tokens to 2048 instead of unlimited
        - Support max_files to limit context size
        - Use more concise prompts

        Args:
            query: User query
            store_name: File store to search
            system_prompt: Optional system prompt override
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens in response (default 2048)
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

            # OPTIMIZATION: Limit number of files if specified
            if max_files and len(file_names) > max_files:
                print(f"⚡ Limiting to {max_files} files (out of {len(file_names)}) for faster response")
                file_names = file_names[:max_files]

            # OPTIMIZATION: Use more concise prompt
            formatted_query = f"Question: {query}\n\nProvide a concise answer based on the documents."

            print(f"🔍 Searching {len(file_names)} files in store '{store_name}' for: {query[:100]}...")

            # Create model instance with response limits
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens  # Limit response length
            )

            # OPTIMIZATION: More concise system prompt
            concise_system_prompt = """Answer questions concisely using the provided documents.
If information isn't in the documents, say so. Be brief and accurate."""

            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=system_prompt or concise_system_prompt
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

            print(f"✅ Generated response from {len(file_names)} files ({len(search_response.answer)} chars)")
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

    def search_and_generate_streaming(
        self,
        query: str,
        store_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = 2048,
        max_files: Optional[int] = None
    ):
        """
        Perform semantic search with streaming response for better UX.

        OPTIMIZATION: Returns a generator that yields response chunks as they arrive.
        This provides immediate feedback to users instead of waiting for the full response.

        Args:
            query: User query
            store_name: File store to search
            system_prompt: Optional system prompt override
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            max_files: Maximum number of files to include

        Yields:
            Response chunks as they are generated
        """
        try:
            # Get files from the store
            file_names = self.client.get_files_for_generation(store_name)
            if not file_names:
                yield "No files found in store."
                return

            # OPTIMIZATION: Limit number of files if specified
            if max_files and len(file_names) > max_files:
                file_names = file_names[:max_files]

            # Use concise prompt
            formatted_query = f"Question: {query}\n\nProvide a concise answer based on the documents."

            print(f"🔍 Streaming search from {len(file_names)} files...")

            # Create model instance
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )

            concise_system_prompt = """Answer questions concisely using the provided documents.
If information isn't in the documents, say so. Be brief and accurate."""

            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=system_prompt or concise_system_prompt
            )

            # Prepare content with files
            content = [formatted_query]
            for file_name in file_names:
                try:
                    file_obj = self._get_file_cached(file_name)
                    content.append(file_obj)
                except Exception as e:
                    print(f"⚠️  Could not access file {file_name}: {e}")

            # Generate response with streaming
            response_stream = model.generate_content(content, stream=True)

            # Yield chunks as they arrive
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            yield f"Error: {e}"

    def search_multiple_stores(
        self,
        query: str,
        store_names: List[str],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = 2048,  # OPTIMIZATION: Limit response
        max_files: Optional[int] = None  # OPTIMIZATION: Limit files
    ) -> SearchResponse:
        """
        Search across multiple file stores with optimizations.

        Args:
            query: User query
            store_names: List of store names to search
            system_prompt: Optional system prompt override
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            max_files: Maximum total files to include

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

            # OPTIMIZATION: Limit total files
            if max_files and len(all_files) > max_files:
                print(f"⚡ Limiting to {max_files} files (out of {len(all_files)}) for faster response")
                all_files = all_files[:max_files]

            formatted_query = f"Question: {query}\n\nProvide a concise answer based on the documents."

            print(f"🔍 Searching across {len(store_names)} stores ({len(all_files)} files) for: {query[:100]}...")

            # Create model and generate response
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                ),
                system_instruction=system_prompt or "Answer concisely using the documents."
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
        max_tokens: int = 1024  # OPTIMIZATION: Shorter for Q&A
    ) -> SearchResponse:
        """
        Ask a specific question with optional additional context.

        Args:
            question: Direct question to ask
            store_name: File store to search
            context: Optional additional context
            max_tokens: Maximum response tokens

        Returns:
            SearchResponse with direct answer
        """
        try:
            formatted_prompt = f"Question: {question}\n\nProvide a brief, direct answer."

            if context:
                formatted_prompt = f"Context: {context}\n\n{formatted_prompt}"

            return self.search_and_generate(
                query=formatted_prompt,
                store_name=store_name,
                temperature=0.0,  # More deterministic for Q&A
                max_tokens=max_tokens
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
        max_tokens: int = 3072  # OPTIMIZATION: Limit summary length
    ) -> SearchResponse:
        """
        Generate a summary of documents in a store.

        Args:
            store_name: File store to summarize
            focus_topic: Optional topic to focus the summary on
            max_tokens: Maximum summary tokens

        Returns:
            SearchResponse with document summary
        """
        try:
            if focus_topic:
                query = f"Summarize the key information about: {focus_topic}\n\nBe concise and organized."
            else:
                query = "Summarize the key points from these documents. Be concise."

            return self.search_and_generate(
                query=query,
                store_name=store_name,
                temperature=0.3,  # Slightly more creative for summaries
                max_tokens=max_tokens
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
        """Get information about the current model."""
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
        """Change the model used for generation."""
        try:
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
        delay_seconds: float = 1.0,
        max_tokens: int = 2048  # OPTIMIZATION: Limit batch responses
    ) -> List[SearchResponse]:
        """
        Process multiple queries with rate limiting and optimizations.

        Args:
            queries: List of queries to process
            store_name: File store to search
            delay_seconds: Delay between requests
            max_tokens: Maximum tokens per response

        Returns:
            List of SearchResponse objects
        """
        results = []

        for i, query in enumerate(queries, 1):
            print(f"🔄 Processing query {i}/{len(queries)}: {query[:50]}...")

            try:
                response = self.search_and_generate(
                    query,
                    store_name,
                    max_tokens=max_tokens
                )
                results.append(response)

                # Rate limiting
                if i < len(queries):
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
