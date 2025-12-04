"""
Response handler for processing API responses and extracting citations.
"""
from typing import List, Dict, Any, Optional, NamedTuple
import json
from dataclasses import dataclass

@dataclass
class Citation:
    """Represents a citation from the search results."""
    file_name: str
    chunk_text: str
    page_number: Optional[int] = None
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SearchResponse:
    """Represents a complete search and generation response."""
    answer: str
    citations: List[Citation]
    model_used: str
    query: str
    raw_response: Any = None
    grounding_metadata: Optional[Dict[str, Any]] = None

class ResponseHandler:
    """Handles processing of API responses and citation extraction."""
    
    def __init__(self):
        pass
    
    def process_response(
        self, 
        response: Any, 
        query: str, 
        model_name: str
    ) -> SearchResponse:
        """
        Process a complete API response into structured format.
        
        Args:
            response: Raw response from the API
            query: Original user query
            model_name: Name of the model used
            
        Returns:
            Processed SearchResponse object
        """
        try:
            # Extract the main answer text
            answer_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract citations from grounding metadata
            citations = self.extract_citations(response)
            
            # Extract grounding metadata
            grounding_metadata = self.extract_grounding_metadata(response)
            
            return SearchResponse(
                answer=answer_text,
                citations=citations,
                model_used=model_name,
                query=query,
                raw_response=response,
                grounding_metadata=grounding_metadata
            )
            
        except Exception as e:
            # Fallback response if processing fails
            return SearchResponse(
                answer=f"Error processing response: {e}",
                citations=[],
                model_used=model_name,
                query=query,
                raw_response=response
            )
    
    def extract_citations(self, response: Any) -> List[Citation]:
        """
        Extract citations from the response grounding metadata.
        
        Args:
            response: Raw API response
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        try:
            # Check if response has candidates and grounding metadata
            if not hasattr(response, 'candidates') or not response.candidates:
                return citations
            
            candidate = response.candidates[0]
            if not hasattr(candidate, 'grounding_metadata'):
                return citations
            
            grounding = candidate.grounding_metadata
            
            # Extract file search grounding chunks
            if hasattr(grounding, 'file_search_grounding') and grounding.file_search_grounding:
                chunks = grounding.file_search_grounding.grounding_chunks
                
                for chunk in chunks:
                    citation = Citation(
                        file_name=self._extract_file_name(chunk),
                        chunk_text=self._extract_chunk_text(chunk),
                        page_number=self._extract_page_number(chunk),
                        score=self._extract_score(chunk),
                        metadata=self._extract_chunk_metadata(chunk)
                    )
                    citations.append(citation)
            
            # Remove duplicates based on file name and chunk text
            citations = self._deduplicate_citations(citations)
            
        except Exception as e:
            print(f"⚠️  Error extracting citations: {e}")
        
        return citations
    
    def extract_grounding_metadata(self, response: Any) -> Optional[Dict[str, Any]]:
        """
        Extract complete grounding metadata from response.
        
        Args:
            response: Raw API response
            
        Returns:
            Grounding metadata dictionary or None
        """
        try:
            if not hasattr(response, 'candidates') or not response.candidates:
                return None
            
            candidate = response.candidates[0]
            if not hasattr(candidate, 'grounding_metadata'):
                return None
            
            grounding = candidate.grounding_metadata
            
            # Convert to dictionary for easier handling
            metadata = {
                'support_score': getattr(grounding, 'support_score', None),
                'file_search_grounding': None
            }
            
            if hasattr(grounding, 'file_search_grounding') and grounding.file_search_grounding:
                file_search = grounding.file_search_grounding
                metadata['file_search_grounding'] = {
                    'chunk_count': len(file_search.grounding_chunks) if file_search.grounding_chunks else 0
                }
            
            return metadata
            
        except Exception as e:
            print(f"⚠️  Error extracting grounding metadata: {e}")
            return None
    
    def format_response(self, search_response: SearchResponse, include_citations: bool = True) -> str:
        """
        Format a SearchResponse into readable text.
        
        Args:
            search_response: SearchResponse to format
            include_citations: Whether to include citation information
            
        Returns:
            Formatted response string
        """
        formatted = f"**Answer:**\n{search_response.answer}\n"
        
        if include_citations and search_response.citations:
            formatted += f"\n**Sources ({len(search_response.citations)} found):**\n"
            
            for i, citation in enumerate(search_response.citations, 1):
                formatted += f"{i}. **{citation.file_name}**"
                
                if citation.page_number:
                    formatted += f" (Page {citation.page_number})"
                
                if citation.score:
                    formatted += f" (Relevance: {citation.score:.2f})"
                
                formatted += "\n"
                
                if citation.chunk_text:
                    # Truncate long chunks
                    chunk = citation.chunk_text[:200] + "..." if len(citation.chunk_text) > 200 else citation.chunk_text
                    formatted += f"   _{chunk}_\n"
                
                formatted += "\n"
        
        return formatted
    
    def format_citations_only(self, citations: List[Citation]) -> str:
        """
        Format only the citations part of a response.
        
        Args:
            citations: List of Citation objects
            
        Returns:
            Formatted citations string
        """
        if not citations:
            return "No sources found."
        
        formatted = f"**Sources ({len(citations)} found):**\n"
        
        for i, citation in enumerate(citations, 1):
            formatted += f"{i}. {citation.file_name}"
            
            if citation.page_number:
                formatted += f" (Page {citation.page_number})"
            
            formatted += "\n"
        
        return formatted
    
    def _extract_file_name(self, chunk: Any) -> str:
        """Extract file name from grounding chunk."""
        try:
            if hasattr(chunk, 'file_name'):
                return chunk.file_name
            elif hasattr(chunk, 'source') and hasattr(chunk.source, 'file_name'):
                return chunk.source.file_name
            return "Unknown File"
        except:
            return "Unknown File"
    
    def _extract_chunk_text(self, chunk: Any) -> str:
        """Extract chunk text from grounding chunk."""
        try:
            if hasattr(chunk, 'chunk_text'):
                return chunk.chunk_text
            elif hasattr(chunk, 'content'):
                return chunk.content
            return ""
        except:
            return ""
    
    def _extract_page_number(self, chunk: Any) -> Optional[int]:
        """Extract page number from grounding chunk."""
        try:
            if hasattr(chunk, 'page_number'):
                return chunk.page_number
            elif hasattr(chunk, 'source') and hasattr(chunk.source, 'page_number'):
                return chunk.source.page_number
            return None
        except:
            return None
    
    def _extract_score(self, chunk: Any) -> Optional[float]:
        """Extract relevance score from grounding chunk."""
        try:
            if hasattr(chunk, 'score'):
                return chunk.score
            elif hasattr(chunk, 'relevance_score'):
                return chunk.relevance_score
            return None
        except:
            return None
    
    def _extract_chunk_metadata(self, chunk: Any) -> Optional[Dict[str, Any]]:
        """Extract metadata from grounding chunk."""
        try:
            metadata = {}
            if hasattr(chunk, 'metadata'):
                metadata.update(chunk.metadata)
            return metadata if metadata else None
        except:
            return None
    
    def _deduplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """Remove duplicate citations based on file name and chunk text."""
        seen = set()
        unique_citations = []
        
        for citation in citations:
            key = (citation.file_name, citation.chunk_text[:100])  # Use first 100 chars for dedup
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
        
        return unique_citations