import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ✅ Correct folder paths
folder_path = r"C:\Users\SaiMo\Downloads\AI Based Legal Reference\Data"
output_file = r"C:\Users\SaiMo\Downloads\AI Based Legal Reference\Milestone1\output_chunks.txt"

documents = []

# Loop through files in Data folder
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # Skip directories
    if os.path.isdir(file_path):
        continue

    # Initialize loader
    loader = None

    # Handle supported file formats
    if filename.endswith(".txt"):
        # Read directly in UTF-8
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        # Use TextLoader with in-memory string
        temp_path = file_path + "_tmp.txt"
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
        loader = TextLoader(temp_path, encoding="utf-8")

    elif filename.endswith(".pdf"):
        loader = PyPDFLoader(file_path)

    elif filename.endswith(".docx"):
        loader = Docx2txtLoader(file_path)

    elif filename.endswith(".html") or filename.endswith(".htm"):
        loader = BSHTMLLoader(file_path)

    else:
        print(f"⚠️ Skipping unsupported file: {filename}")
        continue

    print(f"📖 Reading {filename} ...")
    try:
        documents.extend(loader.load())
    except Exception as e:
        print(f"❌ Failed to load {filename}: {e}")
        continue

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    length_function=len
)
docs = text_splitter.split_documents(documents)

# Save chunks to output file
with open(output_file, "w", encoding="utf-8") as f:
    for i, doc in enumerate(docs, 1):
        f.write(f"Chunk {i}:\n{doc.page_content}\n\n{'='*50}\n\n")

print(f"✅ Done! {len(docs)} chunks saved in {output_file}")

# Optional: Remove temporary text files created
for filename in os.listdir(folder_path):
    if filename.endswith("_tmp.txt"):
        os.remove(os.path.join(folder_path, filename))
