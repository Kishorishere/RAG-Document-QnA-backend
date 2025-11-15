# RAG Backend - Document Q&A & Booking System

A production-ready Retrieval-Augmented Generation (RAG) backend built with FastAPI, featuring intelligent document processing, conversational AI, and automated booking management.

## Project Overview

This system enables users to upload documents (PDF/TXT), ask questions about their content using natural language, and create bookings through conversational interfaces. It uses modern AI technologies to provide accurate, context-aware responses with source citations.

## Key Features

### Document Ingestion & Processing
- File Upload: Support for PDF and TXT documents
- Smart Chunking: Two strategies available
  - Fixed: Simple character-based splitting with configurable size and overlap
  - Recursive: Semantic-aware splitting that maintains context (recommended)
- Vector Embeddings: Automatic generation using sentence-transformers (all-MiniLM-L6-v2)
- Metadata Storage: SQLite database for document tracking and chunk managment
- Vector Storage: Qdrant for efficient semantic search

### Conversational RAG (Retrieval-Augmented Generation)
- Context-Aware Q&A: Ask questions about uploaded documents
- Multi-turn Conversations: Maintains conversation history for coherant interactions
- Source Attribution: Every answer includes citations with similarity scores
- Document Filtering: Search within specific documents or across all uploaded content
- Groq LLM Integration: Fast, accurate responses using llama-3.1-8b-instant model

### Intelligent Booking System
- Natural Language Processing: Extract booking details from conversational text
  - Example: "Book for John Doe on 2025-12-25 at 14:00, email john@example.com"
- Automatic Validation:
  - Email format verification
  - Future date validation
  - Business hours checking (9 AM - 5 PM)
- Booking Management: Create, view, update status, and delete bookings
- Session Tracking: Link bookings to conversation sessions

### Additional Features
- RESTful API with clean and well-documented endpoints
- error handling with meaningfull error messages
- Detailed application and error logs
- CORS support for frontend integration
- Health check endpoints for monitoring
- simple frontend for basic use

## Tech Stack

- Framework: FastAPI
- LLM: Groq (llama-3.1-8b-instant)
- Embeddings: sentence-transformers (all-MiniLM-L6-v2, 384 dimensions)
- Vector Database: Qdrant
- Relational Database: SQLite
- Text Processing: LangChain, pdfplumber
- Containerization: Docker & Docker Compose

## Getting Started

### Prerequisites
- Option 1 & 2: Docker & Docker Compose
- Option 3: Python 3.12+, Docker (for Qdrant only)
- All Options: Groq API key (get free at console.groq.com)

---

### Option 1: Quick Start with Docker Hub (No Code Needed)

This is the fastest way to get started if you just want to use the system without dealing with the source code.

1. Create a folder and add docker-compose.yml:
```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

  rag-backend:
    image: kishorishere/rag-backend:latest
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=your_groq_api ## add your groq api (email back if needed)
      - QDRANT_URL=http://qdrant:6333
      - GROQ_MODEL=llama-3.1-8b-instant
    depends_on:
      - qdrant

volumes:
  qdrant_storage:
```

2. Replace your_groq_api_key_here with your actual Groq API key

3. Run:
```bash
docker-compose up
```

4. Access the application:
   - Frontend UI: http://localhost:8000/frontend
   - API Documentation: http://localhost:8000/docs
   - Qdrant Dashboard: http://localhost:6333/dashboard

---

### Option 2: Clone Repository & Run with Docker

Good for development or if you want to customize the code.

1. Clone the repository:
```bash
git clone https://github.com/Kishorishere/Palm-mind-RAG-Task-Submission-Kishor-Timilsena.git
cd Palm-mind-RAG-Task-Submission-Kishor-Timilsena
```

2. Create .env file:
```bash
cp .env.example .env
```

3. Edit .env and add your Groq API key:
```bash
GROQ_API_KEY=your_groq
```

4. Run with Docker Compose:
```bash
docker-compose up --build
```

5. Access the application:
   - Frontend UI: http://localhost:8000/frontend
   - API Documentation: http://localhost:8000/docs

---

### Option 3: Manual Setup (Without Docker Compose)

Useful for development with hot reload or if you want to understand how everything works.

1. Clone the repository:
```bash
git clone https://github.com/Kishorishere/Palm-mind-RAG-Task-Submission-Kishor-Timilsena.git
cd Palm-mind-RAG-Task-Submission-Kishor-Timilsena
```

2. Create and activate virtual enviroment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install email-validator
```

4. Create .env file:
```bash
cp .env.example .env
```

5. Edit .env and add your Groq API key

6. Start Qdrant (in a separate terminal):
```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

7. Run the application:
```bash
python run.py
```

8. Access the application:
   - Frontend UI: http://localhost:8000/frontend
   - API Documentation: http://localhost:8000/docs

---

## Using the Application

### Frontend Interface (http://localhost:8000/frontend)

The web interface has three main sections:

1. Upload Document
   - Select PDF or TXT file
   - Choose chunking strategy (recursive is usualy better)
   - Upload and wait for processing
   - You'll get a document ID after upload

2. Ask Questions
   - Enter session ID (like "user-session-1")
   - Type your question about the documents you uploaded
   - Get answers with source citations
   - Your conversation history is saved

3. Create Booking
   - Use natural language to specify booking details
   - Example: "Book for Alice Smith on 2025-12-20 at 14:00, email alice@example.com"
   - System validates and creates booking automatically

### API Documentation (http://localhost:8000/docs)

Interactive Swagger UI for all endpoints:

#### Document Ingestion Endpoints
- POST /api/v1/ingest - Upload document
- GET /api/v1/documents - List all documents
- GET /api/v1/documents/{id} - Get document details
- DELETE /api/v1/documents/{id} - Delete document
- GET /api/v1/documents/{id}/chunks - View document chunks

#### Conversation Endpoints
- POST /api/v1/chat - Ask question with RAG
- GET /api/v1/chat/history/{session_id} - Get conversation history
- DELETE /api/v1/chat/history/{session_id} - Clear history
- GET /api/v1/chat/sessions - List all sessions

#### Booking Endpoints
- POST /api/v1/booking - Create booking from text
- GET /api/v1/booking - List all bookings
- GET /api/v1/booking/{id} - Get booking details
- PATCH /api/v1/booking/{id} - Update booking status
- DELETE /api/v1/booking/{id} - Delete booking
- GET /api/v1/booking/session/{session_id} - Get session bookings

---



## Docker Hub

Pre-built image available at: kishorishere/rag-backend

```bash
docker pull kishorishere/rag-backend:latest
```

---

## Architecture

- Modular Design: Clear separation of concerns with service layers
- Dependency Injection: Uses FastAPI dependencies for clean code
- Singleton Patterns: Efficient resource management for embeddings
- Error Handling: Custom exceptions with proper error responses
- Type Safety: Pydantic models for validation
- Logging: Structured logging throughout the application


## Author

Kishor Timilsena
- GitHub: @Kishorishere
- Docker Hub: kishorishere