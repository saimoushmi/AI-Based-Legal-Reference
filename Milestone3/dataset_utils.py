from datasets import load_dataset
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    UnstructuredHTMLLoader,
    TextLoader
)
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import os
from config import PINECONE_API_KEY

# Path to Input
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
INPUT_PATH = os.path.join(project_root, "Legal_Chatbot_Inputs")

# Setup Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
PINECONE_INDEX_NAME = "legal-chatbot-index"

if PINECONE_INDEX_NAME not in [idx["name"] for idx in pc.list_indexes()]:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )


# Embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)

# File loader
def loadFile(f_path):
    if f_path.endswith(".pdf"):
        loader = PyPDFLoader(f_path)
    elif f_path.endswith(".docx"):
        loader = Docx2txtLoader(f_path)
    elif f_path.endswith(".txt"):
        loader = TextLoader(f_path, encoding="utf-8", autodetect_encoding=True)
    elif f_path.endswith(".html"):
        loader = UnstructuredHTMLLoader(f_path)
    else:
        return []
    return loader.load()

# Process local files
for fileName in os.listdir(INPUT_PATH):
    file_path = os.path.join(INPUT_PATH, fileName)
    if os.path.isfile(file_path):
        print(f"Loading: {fileName}")
        docs = loadFile(file_path)
        if not docs:
            continue

        # Split into chunks
        final_docs = []
        for doc in docs:
            chunks = splitter.split_text(doc.page_content)
            for chunk in chunks:
                final_docs.append(Document(page_content=chunk, metadata={"source": fileName}))

        # Store in Pinecone
        PineconeVectorStore.from_documents(
            documents=final_docs,
            embedding=embedding_model,
            index_name=PINECONE_INDEX_NAME
        )
        print(f"Stored {len(final_docs)} chunks from {fileName}")