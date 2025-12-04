"""
Search manager for semantic search, query processing, and result retrieval.
"""
import google.generativeai as genai
from google.generativeai import types
from typing import List, Optional, Dict, Any
import time

from src.file_search_client import FileSearchClient
from src.response_handler import ResponseHandler, SearchResponse
from config.settings import settings
from config.prompts import PromptTemplates

class SearchManager:
    """Manages search operations and query processing with File Search API."""
    
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
    
    def search_and_generate(
        self,
        query: str,
        store_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> SearchResponse:
        """
        Perform semantic search and generate response using uploaded files.
        
        Args:
            query: User query
            store_name: File store to search
            system_prompt: Optional system prompt override
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
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
            
            # Prepare the prompt
            formatted_query = PromptTemplates.format_search_prompt(query)
            
            print(f"🔍 Searching {len(file_names)} files in store '{store_name}' for: {query[:100]}...")
            
            # Create model instance
            model = genai.GenerativeModel(model_name=self.model_name)
            
            # Generate response with file context
            response = model.generate_content([
                formatted_query,
                *[genai.get_file(file_name) for file_name in file_names]
            ])
            
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
            
            if max_tokens:
                config.max_output_tokens = max_tokens
            
            # Set system instruction
            system_instruction = system_prompt or PromptTemplates.RAG_SYSTEM_PROMPT
            
            print(f"🔍 Searching in store '{store_name}' for: {query[:100]}...")
            
            # Generate response
            model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tools,
                system_instruction=system_instruction
            )
            response = model.generate_content(
                contents=formatted_query,
                generation_config=config
            )
            
            # Process the response
            search_response = self.response_handler.process_response(
                response=response,
                query=query,
                model_name=self.model_name
            )
            
            print(f"✅ Found {len(search_response.citations)} relevant sources")
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
        Search across multiple File Search stores.
        
        Args:
            query: User query
            store_names: List of File Search store names to search
            system_prompt: Optional system prompt override
            temperature: Generation temperature
            
        Returns:
            SearchResponse combining results from all stores
        """
        try:
            formatted_query = PromptTemplates.format_search_prompt(query)
            
            # Configure tools and generation
            tools = [
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=store_names
                    )
                )
            ]
            
            config = types.GenerationConfig(temperature=temperature)
            system_instruction = system_prompt or PromptTemplates.RAG_SYSTEM_PROMPT
            
            print(f"🔍 Searching across {len(store_names)} stores for: {query[:100]}...")
            
            model = genai.GenerativeModel(
                model_name=self.model_name,
                tools=tools,
                system_instruction=system_instruction
            )
            response = model.generate_content(
                contents=formatted_query,
                generation_config=config
            )
            
            search_response = self.response_handler.process_response(
                response=response,
                query=query,
                model_name=self.model_name
            )
            
            print(f"✅ Found {len(search_response.citations)} relevant sources across {len(store_names)} stores")
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
        context: Optional[str] = None
    ) -> SearchResponse:
        """
        Ask a specific question with optional additional context.
        
        Args:
            question: Direct question to ask
            store_name: File Search store to search
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
                temperature=0.0  # More deterministic for Q&A
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
        focus_topic: Optional[str] = None
    ) -> SearchResponse:
        """
        Generate a summary of documents in a store.
        
        Args:
            store_name: File Search store to summarize
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
                temperature=0.3  # Slightly more creative for summaries
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
            store_name: File Search store to search
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