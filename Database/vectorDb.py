import chromadb
from chromadb.config import Settings
from openai import OpenAI

client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# Initialize DB once
chroma_client = chromadb.Client(Settings(
    persist_directory="vector_store",
    chroma_db_impl="duckdb+parquet"
))

collection = chroma_client.get_or_create_collection(
    name="repo_embeddings",
    metadata={"hnsw:space": "cosine"}
)

def repo_exists(repo_url):
    """Check if this repo is already stored."""
    results = collection.get(where={"repo_url": repo_url})
    return len(results["ids"]) > 0


def store_in_vector_db(text, project_name, repo_url):
    """Store repo content + metadata in vector DB, avoid duplicates."""
    
    # 1. Check duplicates
    if repo_exists(repo_url):
        print("⚠️ Repo already exists! Skipping embedding...")
        return False

    # 2. Create embedding
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    ).data[0].embedding

    # 3. Metadata
    metadata = {
        "id": repo_url,  # using URL as unique identifier
        "project_name": project_name,
        "repo_url": repo_url
    }

    # 4. Store
    collection.add(
        ids=[repo_url],
        documents=[text],
        metadatas=[metadata],
        embeddings=[embedding]
    )

    print(f"✅ Stored in vector DB for repo: {repo_url}")
    return True
