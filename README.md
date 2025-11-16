# RAG Backend - Document Q&A and Booking System

## Introduction

This is a backend system that lets you upload documents and ask questions about them using AI. It uses Retrieval-Augmented Generation to find relevant information from your documents and generate accurate answers with source citations. The system also includes a booking feature where you can create appointments through natural language. Built with FastAPI, it uses Qdrant for vector search, Redis for conversation memory, and Groq's LLM for generating responses. I have also tried to follow production standards and also flexed a little bit of **MLOPs** skills.

## Key Features and Tools

### Document Processing
- Extracts text from PDF and TXT files.
- Splits content into fixed-size or recursive semantic chunks.
- **Tools:** pdfplumber, LangChain text splitters

### Vector Store (Qdrant)
- Generates 384-dimensional embeddings using sentence-transformers.
- Stores vectors and performs fast similarity search for relevant chunks.
- **Tools:** all-MiniLM-L6-v2, Qdrant

### Conversational AI
- Answers questions using retrieved document chunks with citations.
- Maintains conversation context using Redis for follow-up queries.
- **Tools:** Groq API (llama-3.1-8b-instant), Redis

### Booking System
- Extracts appointment details from natural language.
- Validates email, date, and business hours before saving.
- **Tools:** Groq API (entity extraction), SQLite


## Getting Started

You need a Groq API key to use this system. Get one free at console.groq.com

### Option 1: Using Docker Hub Image

This is the fastest way to get started. You just need Docker installed on your computer.

Create a new folder and add a file called `docker-compose.yml` and paste the below code:

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  rag-backend:
    image: kishorishere/rag-backend:latest ## My docker image which is public 
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=your_groq_api   ## Insert your api here 
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379
    depends_on:
      - qdrant
      - redis

volumes:
  qdrant_storage:
  redis_data:
```

Replace your_groq_api with your actual Groq API key, then run:

```bash
docker-compose up
```

The application will start on http://localhost:8000

Access the frontend at http://localhost:8000/frontend or the API documentation at http://localhost:8000/docs

### Option 2: Running from Source

Clone the repository:

```bash
git clone https://github.com/Kishorishere/RAG-Document-QnA-backend.git
cd RAG-Document-QnA-backend
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install email-validator
```

Create a .env file in the project root:

```bash
cp .env.example .env
```

Edit the .env file and add your Groq API key:

```
GROQ_API_KEY=your_groq_api
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
```

Start Qdrant and Redis using Docker:

```bash
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

Run the application:

```bash
python run.py
```

The application will start on http://localhost:8000

## Using the Application

### 1. Web Interface

Go to http://localhost:8000/frontend to use the web interface. You can upload documents, ask questions, and create bookings all from one page.

Upload a document by selecting a PDF or TXT file and choosing the chunking strategy. The system will process it and give you a document ID.

Ask questions in the chat section. Just type your question and the system will search through your documents and give you an answer with sources.

Create bookings by typing something like "Book an appointment for Sarah on 2025-12-20 at 3pm, email sarah@example.com"

### 2. API Documentation

Go to http://localhost:8000/docs for interactive API documentation. You can test all endpoints directly from your browser.

Main endpoints:
- POST /api/v1/ingest - Upload documents
- POST /api/v1/chat - Ask questions
- POST /api/v1/booking - Create bookings
- GET /api/v1/documents - List uploaded documents
- GET /api/v1/chat/history/{session_id} - View conversation history

### Docker Hub

Pre-built image: kishorishere/rag-backend

The image is automatically built and published through GitHub Actions whenever code is pushed to the master branch.

### Author

Kishor Timilsena
GitHub: github.com/Kishorishere
Docker Hub: hub.docker.com/u/kishorishere


Thanks for checking out this project. If you have any suggestions or run into issues, feel free to open an issue on GitHub.