# Google File Search RAG System

A RAG (Retrieval Augmented Generation) system built using Google's File Search API that eliminates the need for traditional vector databases and embedding infrastructure.

## Features

- 🔍 **Native Semantic Search**: Leverages Google's File Search API for document indexing and retrieval
- 📄 **Multi-format Support**: PDF, TXT, DOCX, HTML, Markdown files
- 🤖 **Gemini Integration**: Uses Gemini models for natural language generation
- 📚 **Citation Support**: Automatic source attribution and grounding metadata
- ⚡ **No Infrastructure**: No need for vector databases or custom embedding models

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key**:
   - Get your API key from [Google AI Studio](https://aistudio.google.com/apikey)
   - Copy `.env.example` to `.env` and add your API key:
     ```bash
     cp .env.example .env
     # Edit .env and add your GEMINI_API_KEY
     ```

3. **Run the example**:
   ```bash
   python main.py
   ```

## Usage

### Basic RAG Query
```python
from src.file_search_client import FileSearchClient
from src.search_manager import SearchManager

# Initialize
client = FileSearchClient()
search_manager = SearchManager(client)

# Upload documents
store_name = client.create_store("my-documents")
client.upload_document("document.pdf", store_name)

# Search and generate
response = search_manager.search_and_generate(
    query="What is the main topic of the document?",
    store_name=store_name
)

print(response.answer)
print(response.citations)
```

### Advanced Features
- Custom document metadata
- Multi-store search
- Configurable chunking strategies
- Response filtering and processing

## Project Structure

```
google_file_search/
├── src/                     # Core modules
├── config/                  # Configuration files
├── data/documents/          # Document storage
├── examples/               # Usage examples
└── main.py                # CLI interface
```

## API Limits

- **Free Tier**: 1 GB storage
- **File Size**: 100MB max per file
- **Formats**: PDF (1000 pages max), TXT, DOCX, HTML, MD

## License

MIT License