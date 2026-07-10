# KnowFlow AI

KnowFlow AI is a production-oriented enterprise knowledge assistant built using
Retrieval-Augmented Generation.

The platform will allow users to upload company documents, perform semantic
search, and ask natural-language questions with source citations.

## Project Goals

KnowFlow AI is designed to demonstrate:

- Python backend engineering
- FastAPI and REST API development
- Retrieval-Augmented Generation
- Semantic search
- Vector databases
- LLM application development
- Modular software architecture
- Testing and production engineering practices

## Current Status

### Phase 0: Production Foundation

Completed:

- Modular FastAPI backend
- Environment-based configuration
- Structured application logging
- Health-check API
- Swagger API documentation
- Automated endpoint tests
- Development dependency management
- Git-ready repository structure

## Planned Features

- PDF, DOCX, and TXT upload
- Secure file validation
- Automatic text extraction
- Text chunking with metadata
- Embedding generation
- Vector indexing
- Semantic search
- RAG-based question answering
- Page-level source citations
- Confidence scores
- Multi-document support
- Conversation history
- Streaming responses
- Enterprise dashboard
- Authentication and role-based access
- Docker deployment
- Cloud deployment

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── main.py
├── tests/
├── requirements.txt
└── requirements-dev.txt



### Phase 2: Document Processing Engine

- PDF page-level text extraction
- DOCX paragraph and table extr## Phase 1: Secure Document Upload

Phase 1 introduced a secure document ingestion pipeline for KnowFlow AI.

The API now accepts enterprise documents in PDF, DOCX, and UTF-8 TXT formats, validates them before storage, and returns structured upload metadata.

### Features

- PDF upload support
- DOCX upload support
- UTF-8 TXT upload support
- File extension validation
- MIME type validation
- File signature and content validation
- Configurable file-size limits
- Chunked file writing
- UUID-based stored filenames
- Protection against filename collisions
- Protection against unsafe client filenames
- Automatic cleanup of invalid or incomplete uploads
- Centralized upload exception handling
- Structured upload metadata responses
- Automated upload API tests

### Upload Flow

```text
Client uploads document
        ↓
FastAPI upload endpoint
        ↓
Filename validation
        ↓
Extension and MIME validation
        ↓
Chunked file write
        ↓
File-size validation
        ↓
File-content validation
        ↓
UUID filename generation
        ↓
Document stored securely
        ↓
Upload metadata returned
- UTF-8 TXT paragraph extraction
- Text normalization
- Structured section metadata
- Page, paragraph, table, word, and character statistics
- Processed JSON persistence
- Parser factory architecture
- Processing-specific exception handling
- Empty and image-only document detection
- Automated parser and processing tests