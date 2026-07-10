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