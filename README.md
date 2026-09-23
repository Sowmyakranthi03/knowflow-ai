# KnowFlow AI

> A production-oriented knowledge intelligence platform being built from first principles with FastAPI, structured document processing, intelligent chunking, semantic retrieval, and Retrieval-Augmented Generation (RAG).

KnowFlow AI is an evolving AI knowledge platform designed to transform unstructured documents into structured, searchable, retrieval-ready knowledge.

The current system can securely ingest PDF, DOCX, and TXT documents, extract structured content, preserve source metadata, intelligently divide that content into retrieval-ready chunks, and persist the resulting data for the next stage of the RAG pipeline.

The long-term goal is to evolve KnowFlow AI beyond document question answering into a device-independent, context-aware intelligence layer capable of supporting real-time assistants, workflow guidance, multimodal perception, and spatial computing.

---

## Current Status

**Current milestone:** Intelligent Document Chunking Engine complete.

```text
Document
   |
   v
Secure Upload
   |
   v
Document Processing
   |
   v
Structured Sections + Metadata
   |
   v
Intelligent Chunking
   |
   v
Retrieval-Ready Chunks
   |
   v
Embedding Engine          <- Next
   |
   v
Vector Search
   |
   v
Semantic Retrieval
   |
   v
RAG + LLM
   |
   v
Grounded Answers + Citations
```

### Completed

- Phase 0 - Project Foundation
- Phase 1 - Secure Document Upload
- Phase 2 - Document Processing Engine
- Phase 3A - Chunking Foundation
- Phase 3B - Intelligent Chunking Engine

### Next

- Phase 4 - Embedding Engine

---

# Why KnowFlow AI?

Large Language Models are powerful, but enterprise and personal knowledge often exists outside the model in PDFs, reports, policies, manuals, notes, and other private documents.

Simply sending entire documents to an LLM is inefficient and does not scale well.

KnowFlow AI is being designed around a structured knowledge pipeline:

```text
Raw Documents
      |
      v
Validated Documents
      |
      v
Structured Content
      |
      v
Retrieval-Ready Chunks
      |
      v
Vector Representations
      |
      v
Relevant Knowledge Retrieval
      |
      v
Grounded LLM Reasoning
```

Instead of treating RAG as only an LLM API call, the project focuses on the engineering required around it: ingestion, validation, parsing, metadata, chunking, retrieval, persistence, testing, traceability, and eventually evaluation.

---

# Architecture

The backend follows a modular service-oriented structure.

```text
API Layer
   |
   v
Service Layer
   |
   v
Repository Layer
   |
   v
Persistent Storage
```

### API Layer

FastAPI routes expose functionality through REST endpoints.

The API layer is responsible for HTTP concerns such as:

- request handling
- response models
- status codes
- API documentation

### Service Layer

The service layer contains application and domain logic.

Examples include:

- validating uploaded documents
- processing document content
- deciding how sections should be grouped
- splitting text into chunks
- calculating chunk statistics

### Repository Layer

Repositories isolate persistence logic from application logic.

They are responsible for operations such as:

- locating uploaded documents
- loading processed documents
- persisting processed JSON
- persisting generated chunks

This separation keeps storage concerns independent from the core processing logic and makes the system easier to test and extend.

---

# Phase 0 - Project Foundation

Phase 0 established the production-oriented backend foundation.

### Implemented

- Modular FastAPI application
- REST API structure
- Environment-based configuration
- Pydantic settings
- Structured application logging
- Centralized project configuration
- Health-check endpoint
- Swagger/OpenAPI documentation
- Automated testing foundation
- Development dependency management
- Ruff code-quality checks
- Git-ready repository structure

### Health Endpoint

```text
GET /api/v1/health
```

This provides a lightweight way to verify that the API is running correctly.

---

# Phase 1 - Secure Document Upload

Phase 1 introduced the document ingestion layer.

KnowFlow AI currently accepts:

- PDF
- DOCX
- UTF-8 TXT

Uploading a document involves more than simply saving the client-provided file.

The ingestion pipeline validates the document before accepting it.

## Upload Flow

```text
Client
  |
  v
FastAPI Upload Endpoint
  |
  v
Filename Validation
  |
  v
Extension Validation
  |
  v
MIME Validation
  |
  v
Chunked File Write
  |
  v
File Size Validation
  |
  v
Content / Signature Validation
  |
  v
Safe UUID Filename
  |
  v
Persistent Storage
  |
  v
Structured Upload Response
```

## Security and Validation

Implemented protections include:

- supported-extension validation
- MIME-type validation
- configurable upload-size limits
- file-content validation
- PDF signature validation
- DOCX ZIP structure validation
- UTF-8 TXT validation
- null-byte protection for text files
- UUID-based server filenames
- protection against client filename collisions
- cleanup of incomplete or invalid uploads

Files are written incrementally rather than reading an entire upload into memory at once.

---

# Phase 2 - Document Processing Engine

After a document is securely stored, KnowFlow AI converts it into structured textual information.

Different document formats require different extraction strategies.

The processing engine therefore uses format-specific parsers behind a common processing workflow.

## Supported Processing

### PDF

- page-level text extraction
- page metadata preservation
- page statistics

### DOCX

- paragraph extraction
- table extraction
- structured metadata

### TXT

- UTF-8 text processing
- paragraph-level extraction

## Processing Flow

```text
Stored Document
      |
      v
Document Repository
      |
      v
Parser Selection
      |
      +------ PDF Parser
      |
      +------ DOCX Parser
      |
      +------ TXT Parser
      |
      v
Structured Sections
      |
      v
Document Statistics
      |
      v
Processed JSON
```

The processing engine generates structured sections instead of returning only one large text string.

A section can contain information such as:

- section number
- section type
- extracted text
- character count
- word count
- source metadata

The processing stage also calculates document-level statistics and rejects documents from which meaningful text cannot be extracted.

Processed output is persisted as JSON so later pipeline stages do not need to parse the original document again.

---

# Phase 3A - Chunking Foundation

Large documents cannot be used efficiently as single retrieval units.

Phase 3A introduced the foundation required to transform processed sections into smaller units called **chunks**.

A chunk is a retrieval-ready portion of document text.

## Chunk Model

Each chunk contains information such as:

```text
chunk_id
document_id
chunk_number
text
word_count
character_count
token_estimate
source_section_numbers
page_numbers
metadata
```

This allows later retrieval stages to find relevant text while still knowing where that information originated.

## Configurable Chunking

The chunking engine currently uses configurable values for:

- target chunk size
- chunk overlap
- minimum chunk size
- maximum chunks per document

Current development defaults use approximately:

```text
Target chunk size : 180 words
Overlap           : 30 words
Minimum size      : 40 words
```

These values are configuration rather than hard-coded retrieval assumptions and can later be tuned using retrieval evaluation.

---

# Phase 3B - Intelligent Chunking Engine

Phase 3B converted the chunking foundation into a complete document chunking pipeline.

The goal is not simply to cut text every N words.

The engine attempts to preserve useful document structure and retrieval context while producing consistently sized chunks.

## Chunking Flow

```text
Processed Document
        |
        v
Validate Sections
        |
        v
Inspect Section Metadata
        |
        v
Group Compatible Sections
        |
        v
Build Combined Text
        |
        v
Word-Based Splitting
        |
        v
Apply Overlap
        |
        v
Handle Tiny Tail Chunks
        |
        v
Attach Provenance
        |
        v
Generate Deterministic Chunk IDs
        |
        v
Calculate Statistics
        |
        v
Persist Chunk JSON
        |
        v
Chunking API Response
```

---

## Section-Aware Grouping

Document sections are considered before splitting.

Compatible adjacent sections can be grouped so that very small paragraphs do not automatically become isolated retrieval units.

Where page metadata is available, page boundaries are considered when deciding whether sections should be grouped.

This gives the chunking engine more structural awareness than blindly splitting the entire document as one string.

---

## Chunk Overlap

Neighbouring chunks intentionally share some words.

For example:

```text
Chunk 1:
[A B C D E F]

Chunk 2:
[E F G H I J]
```

The repeated portion is the overlap.

Without overlap, useful context may be separated exactly at a chunk boundary. Overlap reduces the chance of losing that context during later semantic retrieval.

---

## Tiny-Tail Handling

Word-based splitting can sometimes produce a very small final chunk.

For example:

```text
Chunk 1 -> 180 words
Chunk 2 -> 180 words
Chunk 3 -> 12 words
```

A tiny final chunk may contain too little context to be useful independently.

The chunking engine therefore detects undersized tail chunks and merges their non-overlapping content into the previous chunk where appropriate.

The goal is to avoid both weak retrieval units and accidental text loss.

---

## Source Provenance

Retrieval is useful only if the system can trace information back to its source.

Chunks therefore preserve provenance such as:

- document ID
- source section numbers
- page numbers when available
- section metadata

This metadata will later support grounded answers and source citations.

---

## Deterministic Chunk IDs

Chunk IDs are generated deterministically from information including:

```text
document_id
+
chunk_number
+
normalized chunk text
```

A SHA-256 based identifier is generated from that identity.

This provides stable chunk identities for unchanged input and improves reproducibility and traceability across later indexing stages.

---

## Chunk Statistics

The engine calculates statistics including:

- number of chunks created
- total words
- total characters
- average chunk size
- smallest chunk
- largest chunk
- configured target size
- configured overlap

These metrics provide visibility into how a document was transformed and will later help evaluate retrieval configuration.

---

## Chunk Persistence

Generated chunks are persisted as structured JSON through the repository layer.

The persistence flow is designed around atomic file replacement so partially written output is less likely to become the final stored representation.

This means later stages such as embedding generation can load existing chunks instead of re-running document processing and chunking.

---

# API Endpoints

Current document-related API functionality includes:

```text
GET  /api/v1/health

POST /api/v1/documents/upload

GET  /api/v1/documents/supported-types

POST /api/v1/documents/{document_id}/process

GET  /api/v1/documents/chunking/configuration

POST /api/v1/documents/{document_id}/chunk/validate

POST /api/v1/documents/{document_id}/chunk
```

Interactive API documentation is available through FastAPI Swagger when the development server is running.

---

# Current End-to-End Pipeline

KnowFlow AI currently supports this working flow:

```text
                 KNOWFLOW AI

                     |
                     v

            Upload PDF/DOCX/TXT
                     |
                     v
             Security Validation
                     |
                     v
               File Storage
                     |
                     v
            Document Processing
                     |
                     v
        Structured Text + Metadata
                     |
                     v
          Intelligent Chunking
                     |
                     v
       Retrieval-Ready Document Chunks
                     |
                     v
             JSON Persistence

                     |
                     v

              EMBEDDINGS
                 NEXT
```

---

# Testing and Quality

The project uses automated tests throughout development rather than treating testing as a final step.

Current testing covers areas including:

- API health
- document uploads
- invalid uploads
- document parsing
- document processing
- chunk repository behaviour
- chunk splitting
- overlap behaviour
- tiny-tail handling
- metadata and provenance
- chunk statistics
- chunk persistence
- chunking API behaviour

Development quality checks include:

```bash
ruff check .
pytest -q
```

At the completion of the Intelligent Chunking Engine, the backend test suite contains **43 passing automated tests**.

The document pipeline has also been verified manually through Swagger using a real DOCX document across:

```text
Upload -> Process -> Chunk -> Persist
```

---

# Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

## Document Processing

- pypdf
- python-docx

## Testing and Quality

- pytest
- FastAPI TestClient
- Ruff

## Planned Knowledge Engine

- Sentence Transformers
- FAISS
- local and/or hosted LLM providers
- Retrieval-Augmented Generation

The architecture is intended to keep model and provider-specific integrations replaceable where practical.

---

# Repository Structure

```text
knowflow-ai/
|
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   `-- routes/
|   |   |
|   |   |-- core/
|   |   |-- repositories/
|   |   |-- schemas/
|   |   |-- services/
|   |   |-- utils/
|   |   `-- main.py
|   |
|   |-- tests/
|   |-- requirements.txt
|   `-- requirements-dev.txt
|
|-- documents/
|   |-- processed/
|   `-- chunks/
|
|-- frontend/
|-- models/
|-- scripts/
|-- vector_store/
|
|-- README.md
|-- LICENSE
`-- .gitignore
```

The structure will continue evolving as the embedding, vector search, retrieval, RAG, UI, authentication, observability, and multimodal components are introduced.

---

# Development Roadmap

## Stage 1 - Foundation

- [x] Phase 0 - Project Foundation
- [x] Phase 1 - Secure Document Upload
- [x] Phase 2 - Document Processing Engine
- [x] Phase 3A - Chunking Foundation
- [x] Phase 3B - Intelligent Chunking Engine

## Stage 2 - Knowledge Engine

- [ ] Phase 4 - Embedding Engine
- [ ] Phase 5 - FAISS Vector Store
- [ ] Phase 6 - Semantic Retrieval
- [ ] Phase 7 - RAG + LLM Integration
- [ ] Phase 8 - Citations and Retrieval/RAG Evaluation

The completion of Phase 8 will represent the first major **KnowFlow Knowledge Engine V1** milestone.

## Stage 3 - Context and Guidance

Planned work includes:

- session context
- workflow/task state
- guidance engine
- knowledge assistant interface

## Stage 4 - Production Engineering

Planned work includes:

- authentication
- role-based access control
- Docker
- CI/CD
- deployment
- observability

## Stage 5 - Multimodal Intelligence

Longer-term development will explore:

- camera and vision input
- object detection and tracking
- context fusion
- multimodal models
- real-time event processing
- automatic workflow progression
- action verification
- adaptive guidance

## Stage 6 - Spatial and Device Integration

Future research and prototyping may include:

- phone-based AR
- spatial anchors and guidance
- XR prototypes
- device adapter APIs
- compatible smart-glasses integrations
- latency optimization
- local/edge intelligence
- caching and prefetching

---

# Long-Term Vision

KnowFlow AI begins as a document knowledge engine, but the architecture is intended to support a broader direction.

The long-term vision is a **device-independent, context-aware AI companion and real-time intelligence layer** capable of understanding authorised knowledge together with what a user is currently doing.

A future interaction loop may look like:

```text
SEE
 |
 v
UNDERSTAND
 |
 v
RETRIEVE
 |
 v
REASON
 |
 v
GUIDE
 |
 v
OBSERVE
 |
 v
VERIFY
 |
 v
ADAPT
```

The aim is not to make an LLM process every camera frame or every event.

Different components should perform the jobs they are best suited for:

```text
Object detection     -> Vision model
Object position      -> Tracker
Hand movement        -> Spatial / hand tracker
Knowledge retrieval  -> Embeddings + vector search
Workflow state       -> Deterministic state machine
Safety rules         -> Deterministic validation
Complex reasoning    -> LLM
Visual reasoning     -> VLM when required
Knowledge grounding  -> RAG
```

This keeps the system modular and creates a path from today's document knowledge engine toward future real-time contextual assistance.

---

# Engineering Principles

KnowFlow AI is being developed around several principles:

**Modularity**  
Core functionality should remain separated into APIs, services, repositories, schemas, and replaceable provider integrations.

**Traceability**  
Knowledge should remain connected to its original document and source metadata.

**Testability**  
New functionality should include automated validation before being considered complete.

**Provider Independence**  
Core knowledge and context logic should not depend unnecessarily on one model, vector database, or hardware vendor.

**Progressive Complexity**  
The project starts with a reliable knowledge engine before introducing real-time vision, spatial computing, and device integrations.

**Human Control**  
Future proactive and contextual assistance should remain controllable by the user rather than continuously demanding attention.

---

# Development Approach

Each major feature is developed incrementally:

```text
Understand the problem
        |
        v
Design the component
        |
        v
Implement a small unit
        |
        v
Test it
        |
        v
Understand the behaviour
        |
        v
Integrate it
        |
        v
Run full validation
        |
        v
Commit
```

This repository intentionally documents the evolution of the system rather than presenting KnowFlow AI as a finished product.

---

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Sowmya Kranthi.