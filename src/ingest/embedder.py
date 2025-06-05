# src/ingest/embedder.py

import os
import json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

def main():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    parsed_jsonl_path = os.path.join(project_root, 'data', 'unstructured', 'parsed.jsonl')
    qdrant_host = "localhost"
    qdrant_port = 6333 # Default gRPC port for Qdrant
    collection_name = "docs" # Name of the collection in Qdrant

    print(f"Attempting to load parsed documents from: {parsed_jsonl_path}")

    # --- Load the Sentence Transformer model ---
    print("Loading Sentence Transformer model 'all-MiniLM-L6-v2'...")
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading Sentence Transformer model: {e}")
        print("Please ensure you have an internet connection or the model is cached locally.")
        return

    # --- Initialize Qdrant Client ---
    print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        # Check if Qdrant is reachable
        client.get_collections() # This will raise an error if Qdrant is not running
        print("Connected to Qdrant successfully.")
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        print("Please ensure Qdrant Docker container is running. Use 'docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant' to start it.")
        return

    # --- Create Qdrant Collection if it doesn't exist ---
    # Determine the vector size from the model
    vector_size = model.get_sentence_embedding_dimension()
    print(f"Vector size for embeddings will be: {vector_size}")

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        if collection_name not in [c.name for c in collections]:
            print(f"Creating Qdrant collection '{collection_name}'...")
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
            print(f"Collection '{collection_name}' created.")
        else:
            print(f"Collection '{collection_name}' already exists. Will add new points.")
    except Exception as e:
        print(f"Error creating/checking Qdrant collection: {e}")
        return

    # --- Read parsed documents and generate embeddings ---
    documents_to_embed = []
    if not os.path.exists(parsed_jsonl_path):
        print(f"Error: '{parsed_jsonl_path}' not found. Please run Day 2's script first.")
        return

    try:
        with open(parsed_jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                doc = json.loads(line)
                # Combine subject and body for emails, use content for PDFs
                if doc.get("type") == "email":
                    text_content = f"Subject: {doc.get('subject', '')}\n\n{doc.get('body', '')}"
                else: # Assume PDF or other types with 'content'
                    text_content = doc.get("content", "")

                if text_content: # Only embed if there's actual text
                    # Store all original doc info + the combined text_content for embedding
                    # We will now include text_content in the payload as well
                    doc_for_embedding = {
                        "id": doc["id"],
                        "filename": doc["filename"],
                        "type": doc["type"],
                        "text_content": text_content # This is the text that will be embedded and stored in payload
                    }
                    # Add other original fields from 'doc' if they are not already covered
                    for key, value in doc.items():
                        if key not in doc_for_embedding:
                            doc_for_embedding[key] = value

                    documents_to_embed.append(doc_for_embedding)
        print(f"Loaded {len(documents_to_embed)} documents from '{parsed_jsonl_path}'.")

    except Exception as e:
        print(f"Error reading '{parsed_jsonl_path}': {e}")
        return

    if not documents_to_embed:
        print("No documents found to embed. Exiting.")
        return

    # Prepare texts and payloads for embedding
    texts = [doc["text_content"] for doc in documents_to_embed]
    # UPDATED: Payloads will now include 'text_content'
    # The payload for Qdrant should be a dictionary of properties to store
    # We can directly use the doc_for_embedding as payload
    payloads = [
        {k: v for k, v in doc.items()} # Include all items, including 'text_content'
        for doc in documents_to_embed
    ]

    # Generate embeddings in batches for efficiency
    print(f"Generating embeddings for {len(texts)} documents...")
    try:
        batch_size = 32
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = model.encode(batch_texts, show_progress_bar=True)
            embeddings.extend(batch_embeddings)
        print("Embeddings generated.")
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return

    # --- Upload embeddings to Qdrant ---
    print(f"Uploading {len(embeddings)} embeddings to Qdrant collection '{collection_name}'...")
    try:
        points = []
        for i, emb in enumerate(embeddings):
            points.append(
                models.PointStruct(
                    id=i, # Qdrant requires a unique ID for each point. Using index for simplicity.
                    vector=emb.tolist(), # Convert numpy array to list
                    payload=payloads[i] # Use the full payload including text_content
                )
            )

        client.upsert(
            collection_name=collection_name,
            wait=True, # Wait for the operation to complete
            points=points
        )
        print(f"Successfully uploaded {len(embeddings)} embeddings to Qdrant.")

        # Verify by counting points in the collection
        count_result = client.count(collection_name=collection_name, exact=True)
        print(f"Total points in Qdrant collection '{collection_name}': {count_result.count}")

    except Exception as e:
        print(f"Error uploading embeddings to Qdrant: {e}")

if __name__ == "__main__":
    main()
