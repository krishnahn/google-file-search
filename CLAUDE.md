# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval Augmented Generation) system using Google's File Search API that eliminates the need for traditional vector databases. The system uses Google AI's native file upload and Gemini models for semantic search and natural language generation.

## Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment (requires GEMINI_API_KEY)
cp .env.example .env
# Edit .env and add your API key from https://aistudio.google.com/apikey
```

### CLI Usage
```bash
# Create a new document store
python main.py create-store <store_name>

# Upload files
python main.py upload <file_path> <store_name>
python main.py upload-dir <directory_path> <store_name>

# Query documents
python main.py search "query text" <store_name>
python main.py ask "question" <store_name>
python main.py summarize <store_name>

# Interactive mode
python main.py interactive <store_name>

# List available stores
python main.py list-stores
```

### Testing
```bash
# Quick system verification
python quick_test.py

# Full system test
python test_system.py
```

## Architecture

### Core Components

**FileSearchClient** (`src/file_search_client.py`)
- Manages file uploads to Google AI using `genai.upload_file()`
- Implements "virtual stores" - a local JSON-based organization layer (stored in `data/stores.json`)
- Note: Google AI API doesn't have persistent file stores, so this system tracks uploaded files locally and retrieves them by file ID when needed
- Files are uploaded directly to Google AI and remain accessible via their file IDs

**SearchManager** (`src/search_manager.py`)
- Orchestrates RAG queries by combining uploaded files with user queries
- Uses `GenerativeModel` with files passed as content parts alongside the query
- Google AI performs semantic search internally - no explicit embedding or vector search needed
- Supports single-store, multi-store, Q&A, and document summarization modes

**DocumentProcessor** (`src/document_processor.py`)
- Validates files before upload (format, size, permissions)
- Supports: PDF, TXT, DOCX, HTML, Markdown
- Max file size: 100MB (Google AI limit)
- Handles batch directory uploads with recursive scanning

**ResponseHandler** (`src/response_handler.py`)
- Processes Gemini model responses
- Extracts citations and grounding metadata when available
- Formats output for CLI display

### Key Design Decisions

1. **Virtual Stores**: Since Google AI File API doesn't provide persistent stores, the system implements a local tracking mechanism using JSON. Each "store" maps to a list of uploaded file IDs.

2. **No Vector DB**: The system relies entirely on Google AI's internal semantic search capabilities. When you pass files to `GenerativeModel.generate_content()`, Google handles embedding, indexing, and retrieval automatically.

3. **File Context Pattern**: Files are passed directly as content parts to the generative model:
   ```python
   content = [formatted_query]
   for file_name in file_names:
       file_obj = genai.get_file(file_name)
       content.append(file_obj)
   response = model.generate_content(content)
   ```

4. **Temperature Settings**:
   - Search queries: 0.1 (focused, factual)
   - Q&A: 0.0 (deterministic)
   - Summarization: 0.3 (slightly creative)

## Configuration

**Settings** (`config/settings.py`)
- API key loaded from `.env` file
- Default model: `gemini-2.5-flash` (configurable via `DEFAULT_MODEL` env var)
- Chunking config: 500 tokens per chunk, 50 token overlap
- File size limit: 100MB

**Prompts** (`config/prompts.py`)
- System prompts for different query types
- Templates use format strings with `{query}` placeholder
- Customizable for domain-specific applications

## Important Implementation Notes

1. **File Processing**: After uploading with `genai.upload_file()`, files may be in "PROCESSING" state. The system polls until state is "ACTIVE" before proceeding.

2. **Error Handling**: The system returns `SearchResponse` objects even on errors, with error messages in the answer field and empty citations.

3. **Store Resolution**: CLI commands accept either store display names or direct store IDs. The system checks display name first, then falls back to treating input as direct ID.

4. **Metadata**: Document metadata is supported but stored only in the local `stores.json` file, not passed to Google AI (the API doesn't support custom metadata on files).

5. **Rate Limiting**: Batch operations include configurable delays between requests to avoid hitting API rate limits.

## API Limits and Costs

- Free tier: 1 GB storage
- File size: 100MB max per file
- PDF: 1000 pages max
- Model: Uses standard Gemini API pricing (gemini-2.5-flash is cost-effective)
