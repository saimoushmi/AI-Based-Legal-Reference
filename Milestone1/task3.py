import os
import json
import argparse
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ---------- File Readers ----------
def read_pdf(path):
    import fitz  # PyMuPDF
    txts = []
    doc = fitz.open(path)
    for p in range(doc.page_count):
        txts.append(doc.load_page(p).get_text("text"))
    return "\n".join(txts).strip()

def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()

def read_docx(path):
    from docx import Document
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()

def read_html(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return BeautifulSoup(f, "html.parser").get_text(separator="\n").strip()

def read_json_like(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read().strip()
        try:
            obj = json.loads(txt)
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return txt

# Map file extensions to readers
EXT_TO_READER = {
    ".pdf": read_pdf,
    ".txt": read_txt,
    ".docx": read_docx,
    ".html": read_html,
    ".htm": read_html,
    ".json": read_json_like,
    ".jsonl": read_json_like,
}

# ---------- Single File ----------
def convert_file_to_json(input_file, output_folder, chunk_size=1000, chunk_overlap=200):
    ext = Path(input_file).suffix.lower()
    reader = EXT_TO_READER.get(ext, read_txt)
    text = reader(input_file)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)

    os.makedirs(output_folder, exist_ok=True)

    # Keep original filename for JSON
    output_path = os.path.join(output_folder, f"{Path(input_file).stem}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON saved at: {output_path}")

# ---------- Folder ----------
def convert_folder_to_json(folder, output_folder, chunk_size=2000, chunk_overlap=200):
    folder = Path(folder)
    assert folder.exists(), f"Folder {folder} does not exist"
    files = [p for p in folder.iterdir() if p.is_file()]
    if not files:
        print("No files found in", folder)
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    os.makedirs(output_folder, exist_ok=True)

    for p in tqdm(sorted(files), desc="Processing Files"):
        ext = p.suffix.lower()
        reader = EXT_TO_READER.get(ext, read_txt)
        try:
            text = reader(str(p))
        except Exception as e:
            print(f"Failed to read {p.name}: {e}")
            continue
        if not text:
            continue

        chunks = splitter.split_text(text)
        output_path = os.path.join(output_folder, f"{p.stem}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Processed {len(files)} files. JSONs saved in {output_folder}")

# ---------- CLI ----------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=str, help="Path to single file")
    ap.add_argument("--folder", type=str, help="Path to folder with files")
    ap.add_argument("--out", type=str, required=True, help="Output folder for JSON files")
    ap.add_argument("--chunk_size", type=int, default=1000)
    ap.add_argument("--chunk_overlap", type=int, default=200)
    args = ap.parse_args()

    if args.file:
        convert_file_to_json(args.file, args.out, args.chunk_size, args.chunk_overlap)
    elif args.folder:
        convert_folder_to_json(args.folder, args.out, args.chunk_size, args.chunk_overlap)
    else:
        print("⚠️ Please provide either --file <path-to-file> OR --folder <folder-path>")
