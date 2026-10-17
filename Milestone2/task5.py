import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from docx import Document
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pinecone import Pinecone

# ---------------------------
# Load API Keys
# ---------------------------
load_dotenv()
openai_api_key = os.environ["OPENAI_API_KEY"]
pinecone_api_key = os.environ["PINECONE_API_KEY"]

# ---------------------------
# Step 1: Readers for files
# ---------------------------
def read_pdf(path):
    pdf = PdfReader(path)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    return text

def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def read_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text])

def read_html(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return BeautifulSoup(f, "html.parser").get_text(separator="\n")

EXT_TO_READER = {
    ".pdf": read_pdf,
    ".txt": read_txt,
    ".docx": read_docx,
    ".html": read_html,
    ".htm": read_html,
}

# ---------------------------
# Step 2: Chunking
# ---------------------------
def chunk_text(text, source):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    return [{"page_content": c, "metadata": {"source": source}} for c in chunks]

# ---------------------------
# Step 3: Load all docs
# ---------------------------
def load_and_chunk_documents(folder_path):
    all_chunks = []
    for filename in os.listdir(folder_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext in EXT_TO_READER:
            print(f"📄 Processing {filename} ...")
            reader = EXT_TO_READER[ext]
            text = reader(os.path.join(folder_path, filename))
            chunks = chunk_text(text, filename)
            all_chunks.extend(chunks)
    return all_chunks

# ---------------------------
# Step 4: Upload to Pinecone
# ---------------------------
def upload_to_pinecone(chunks, index_name="legal-reference-index"):
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    # Initialize Pinecone client
    pc = Pinecone(api_key=pinecone_api_key)

    # Create index if not exists
    if index_name not in [idx["name"] for idx in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=1536,   # OpenAI embeddings size
            metric="cosine"
        )
        print(f"✅ Created new Pinecone index: {index_name}")

    # Upload documents
    vectorstore = PineconeVectorStore.from_documents(
        chunks,
        embedding=embeddings,
        index_name=index_name
    )
    print(f"✅ Uploaded {len(chunks)} chunks to Pinecone index: {index_name}")
    return vectorstore

# ---------------------------
# Main Script
# ---------------------------
if __name__ == "__main__":
    folder = "./Data"   # All your docs should be placed in this folder
    chunks = load_and_chunk_documents(folder)
    upload_to_pinecone(chunks)
