# RAG API Service

The RAG API Service is a local implementation of a Retrieval-Augmented Generation (RAG) system. It efficiently processes and retrieves information from updated documentation stored in Hedgedoc, leveraging a vector database for enhanced search capabilities.

## Features

-  **Document Update Detection**: Automatically detects updates in Hedgedoc documents and processes them.
-  **Embedding Generation**: Uses SentenceTransformer to generate embeddings for document content.
-  **Vector Database Integration**: Stores and retrieves document embeddings using Qdrant for efficient search.
-  **Search and Retrieval**: Combines vector search with LLM response generation to provide accurate answers to user queries.
-  **Health Monitoring**: Provides endpoints for health checks and system statistics.

## Architecture

The system is built using the following components:

-  **PostgreSQL Listener**: Monitors changes in the Hedgedoc database and triggers document processing.
-  **Document Processor**: Generates embeddings and stores them in Qdrant.
-  **FastAPI Application**: Provides an API for searching documents and retrieving answers.

## Getting Started

### Prerequisites

-  Python 3.8+
-  PostgreSQL
-  Qdrant
-  FastAPI
-  SentenceTransformer

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/qtsone/rag-api-service
   cd rag-api-service
   ```

2. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables  
    Create a .env file in the root directory with the following variables:
    ```
    POSTGRES_DB=your_database
    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    POSTGRES_HOST=your_host
    QDRANT_HOST=your_qdrant_host
    QDRANT_PORT=your_qdrant_port
    OLLAMA_API_URL=your_ollama_api_url
    ```
### Running the Service

1.	Start the FastAPI application:
    ```sh
    uvicorn services.api.app.main:app --reload
    ```
2.	Access the API documentation at http://localhost:8000/docs.  
    Usage:  
	• Health Check: Verify the service status by accessing the `/health` endpoint.  
	• Search: Use the `/search` endpoint to query documents and receive answers augmented by LLM

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## Contact
For questions or support, please contact ibacalu@qts.one.

## License

This project is licensed under the [GPL v3](LICENSE).
