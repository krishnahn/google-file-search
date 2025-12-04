"""
System prompts and templates for the RAG system.
"""

class PromptTemplates:
    """Collection of prompt templates for different use cases."""
    
    RAG_SYSTEM_PROMPT = """
You are a helpful assistant that answers questions based on the provided documents.
When answering:
1. Use information from the retrieved documents when available
2. Be specific and cite sources when possible
3. If the answer isn't in the documents, say so clearly
4. Provide concise but complete answers
5. Use proper formatting for readability
"""

    SEARCH_PROMPT_TEMPLATE = """
Based on the provided documents, please answer the following question:

Question: {query}

Please provide a detailed answer based on the information found in the documents.
If you cannot find relevant information, please state that clearly.
"""

    SUMMARIZATION_PROMPT = """
Please provide a comprehensive summary of the following documents:
- Include key topics and main points
- Organize information logically
- Highlight important details
- Keep the summary concise but informative
"""

    QUESTION_ANSWERING_PROMPT = """
Answer the following question using only the information provided in the documents.
If the information is not available in the documents, clearly state that.

Question: {query}

Provide a clear, accurate answer with specific references to the source material when possible.
"""

    @classmethod
    def format_search_prompt(cls, query: str) -> str:
        """Format the search prompt with the user query."""
        return cls.SEARCH_PROMPT_TEMPLATE.format(query=query)
    
    @classmethod
    def format_qa_prompt(cls, query: str) -> str:
        """Format the question-answering prompt with the user query."""
        return cls.QUESTION_ANSWERING_PROMPT.format(query=query)