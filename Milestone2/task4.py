import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

# 2. Index details
index_name = "test-index"
dimension = 8

# 3. Create index if it does not exist
if index_name not in [index["name"] for index in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

print(f"✅ Index '{index_name}' is ready!")

# 4. Connect to index
index = pc.Index(index_name)

# 5. Insert (Upsert) vectors
vectors = [
    ("vec1", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]),
    ("vec2", [0.2, 0.1, 0.4, 0.3, 0.6, 0.5, 0.8, 0.7])
]
index.upsert(vectors)
print("✅ Vectors inserted!")

# Wait a few seconds to ensure data is ready
time.sleep(5)

# 6. Query vectors
result = index.query(
    vector=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    top_k=2,
    include_values=True
)
print("🔎 Query Result:", result)

# 7. Delete one vector
index.delete(ids=["vec1"])
print("🗑️ Deleted vec1")

# Wait before checking again
time.sleep(2)

# 8. Query again to check remaining vectors
result_after_delete = index.query(
    vector=[0.2, 0.1, 0.4, 0.3, 0.6, 0.5, 0.8, 0.7],
    top_k=2,
    include_values=True
)
print(" After delete, Query Result:", result_after_delete)
