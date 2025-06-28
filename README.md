# NEXUSMIND

This is a Retrieval-Augmented Generation (RAG) project built step-by-step with LLM guidance. It implements a complete RAG pipeline and provides an API.

## ✨ Features

- **📝 Document Processing**: Supports asynchronous document uploads via API, with automatic background processing and chunking.
- **🧠 RAG Q&A**: Ask questions based on the content of uploaded documents.
- **🧩 Extensible Design**: Built with a modular, interface-oriented design, making it easy to extend (e.g., adding new document processors or storage backends).
- **🔐 API-Driven & Secure**: All core features are exposed via a FastAPI server, protected by API keys.
- **🐳 Containerized**: Comes with a `Dockerfile` and `docker-compose.yml` for one-command application startup.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

### Local Development

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/NEXUSMIND.git
    cd NEXUSMIND
    ```

2.  **Install dependencies**:
    This project uses Poetry for dependency management. Run the following command to install:
    ```bash
    poetry install
    ```

3.  **Configure Environment Variables**:
    Copy the `.env.example` file (if it exists) or create a new `.env` file and add the following:
    ```env
    # API key(s) to access the application's API. You can set one or more, comma-separated.
    API_KEYS='["your-secret-api-key"]'

    # Your Large Language Model provider's API key
    OPENAI_API_KEY="sk-..." 
    ```

4.  **Run the API Server**:
    ```bash
    poetry run uvicorn main:app --reload
    ```
    The server will be running at `http://127.0.0.1:8000`.

### Running with Docker

1.  **Clone the repository** (if you haven't already).

2.  **Configure Environment Variables**:
    Create a `.env` file in the project root with the same content as above.

3.  **Build and Start the Container**:
    ```bash
    docker-compose up --build -d
    ```
    The service will be available at `http://127.0.0.1:8000`, just like in the local setup.

## ⚙️ API Usage

The following examples assume your API key is `your-secret-api-key`.

### 1. Upload a File

This operation uploads a file for processing. It's an asynchronous task and will return a `task_id` immediately.

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
-H "X-API-Key: your-secret-api-key" \
-F "file=@/path/to/your/document.txt" \
-F "brain_id=00000000-0000-0000-0000-000000000000"
```

### 2. Check Upload Status

Use the `task_id` from the previous step to check the file processing status.

```bash
curl -X GET "http://127.0.0.1:8000/upload/status/<your_task_id>" \
-H "X-API-Key: your-secret-api-key"
```

### 3. Chat with a Document

Once the file has been processed successfully, you can ask questions about its content.

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
-H "Content-Type: application/json" \
-H "X-API-Key: your-secret-api-key" \
-d '{
    "brain_id": "00000000-0000-0000-0000-000000000000",
    "question": "What is the main content of the document?"
}'
```
