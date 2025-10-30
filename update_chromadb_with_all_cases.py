"""
Script to update ChromaDB collection with all 8,573 cases from constitution.json
"""
import json
import chromadb
from sentence_transformers import SentenceTransformer
import tqdm

# Load cases from JSON
with open('./data/constitution/constitution.json', 'r', encoding='utf-8') as f:
    cases = json.load(f)

print(f"Loaded {len(cases)} cases from constitution.json")

# Initialize ChromaDB
client = chromadb.PersistentClient(path="./data/chromadb")
collection_name = "indian_legal_cases"

# Remove existing collection if present
try:
    client.delete_collection(collection_name)
    print(f"Deleted existing collection: {collection_name}")
except Exception:
    pass

collection = client.create_collection(collection_name)

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Prepare data for ChromaDB
ids = []
embeddings = []
documents = []
metadatas = []

for i, case in enumerate(tqdm.tqdm(cases, desc="Encoding cases")):
    case_id = case.get('id', f"case_{i}")
    text = case.get('content') or case.get('full_text') or case.get('summary') or case.get('title', '')
    if not text:
        continue
    embedding = model.encode(text)
    ids.append(str(case_id))
    embeddings.append(embedding.tolist())
    documents.append(text)
    # Convert list-type metadata fields to comma-separated strings
    metadata = {}
    for k, v in case.items():
        if k in ('content', 'full_text', 'summary'):
            continue
        if isinstance(v, list):
            metadata[k] = ', '.join(str(x) for x in v)
        else:
            metadata[k] = v
    metadatas.append(metadata)

print(f"Prepared {len(ids)} cases for ChromaDB")

# Add to ChromaDB in batches
batch_size = 100
for i in range(0, len(ids), batch_size):
    end = min(i + batch_size, len(ids))
    collection.add(
        ids=ids[i:end],
        embeddings=embeddings[i:end],
        documents=documents[i:end],
        metadatas=metadatas[i:end]
    )
    print(f"Added cases {i} to {end} to ChromaDB")

print("✅ All cases added to ChromaDB!")
