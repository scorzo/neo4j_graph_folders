# neo4j graph folders

## About
- Takes a folder path containing documents and creates a Neo4j relationship graph using the folder structure.
- Creates edge nodes with a summary attribute containing LLM-generated summaries of file contents.
- Edge nodes contain a file reference to the source file location.

## Instructions

1. Install the required packages:

    ```bash
    pip install neo4j dotenv openai
    ```

2. Populate environment variables in a `.env` file for OpenAI and Neo4j instance:

    ```env
    OPENAI_API_KEY=your_openai_api_key
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_neo4j_password
    ```

3. Run the application:

    ```bash
    python app.py
    ```

Make sure to replace `your_openai_api_key` and `your_neo4j_password` with your actual OpenAI API key and Neo4j password, respectively.
