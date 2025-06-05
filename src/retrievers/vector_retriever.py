# src/retrievers/vector_retriever.py

import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

def get_vector_retriever():
    """
    Initializes and returns a function to perform vector similarity search in Qdrant.
    """
    qdrant_host = "localhost"
    qdrant_port = 6333 # Default gRPC port for Qdrant
    collection_name = "docs" # Name of the collection in Qdrant

    print(f"Initializing vector retriever. Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        # Check if collection exists
        collections = client.get_collections().collections
        if collection_name not in [c.name for c in collections]:
            print(f"Error: Qdrant collection '{collection_name}' not found. Please run Day 3's embedder.py first.")
            return None
        print("Connected to Qdrant and collection 'docs' found.")

        # Load the Sentence Transformer model (same as used for embedding)
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Sentence Transformer model loaded for vector retrieval.")

        def retrieve_vectors(query_text: str, top_k: int = 3):
            """
            Performs a vector similarity search in Qdrant.
            Args:
                query_text (str): The text query to search for.
                top_k (int): The number of top similar results to retrieve.
            Returns:
                list: A list of dictionaries, each representing a retrieved document
                      with its content and metadata.
            """
            print(f"Searching Qdrant for '{query_text}' (top {top_k} results)...")
            query_embedding = model.encode(query_text).tolist()

            # Using client.search (this method is available in qdrant-client==1.7.0)
            search_result = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True # Retrieve the stored metadata (original text, filename, etc.)
            )

            results = []
            for hit in search_result:
                # The payload contains the original document information
                # 'text_content' is what was embedded, 'filename', 'type', 'id' are also there
                # Safely get content, defaulting to empty string if None
                content = hit.payload.get("text_content", "")
                results.append({
                    "score": hit.score,
                    "id": hit.id,
                    "filename": hit.payload.get("filename"),
                    "type": hit.payload.get("type"),
                    "content": content # The original text
                })
            print(f"Found {len(results)} results.")
            return results

        print("Vector retriever initialized successfully.")
        return retrieve_vectors

    except Exception as e:
        print(f"Error initializing vector retriever: {e}")
        print("Please ensure Qdrant Docker container is running and Day 3's embedder.py was run successfully.")
        return None

if __name__ == "__main__":
    # Example usage:
    vector_retriever = get_vector_retriever()
    if vector_retriever:
        print("\n--- Testing Vector Retriever ---")
        # Ensure you have some documents in parsed.jsonl that relate to these queries
        query_1 = "latest project updates"
        results_1 = vector_retriever(query_1, top_k=2)
        print(f"\nResults for '{query_1}':")
        for i, res in enumerate(results_1):
            # Safely access content and print snippet
            content_snippet = res['content'][:200] + "..." if res['content'] else "[No content available]"
            print(f"  Result {i+1} (Score: {res['score']:.4f}):")
            print(f"    Filename: {res['filename']}, Type: {res['type']}")
            print(f"    Content (snippet): {content_snippet}")

        query_2 = "product information"
        results_2 = vector_retriever(query_2, top_k=1)
        print(f"\nResults for '{query_2}':")
        for i, res in enumerate(results_2):
            # Safely access content and print snippet
            content_snippet = res['content'][:200] + "..." if res['content'] else "[No content available]"
            print(f"  Result {i+1} (Score: {res['score']:.4f}):")
            print(f"    Filename: {res['filename']}, Type: {res['type']}")
            print(f"    Content (snippet): {content_snippet}")

    else:
        print("Vector retriever could not be initialized. Cannot run example queries.")
