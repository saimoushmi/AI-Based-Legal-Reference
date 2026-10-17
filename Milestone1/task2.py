from datasets import load_dataset

# Output file
output_file = "ipc_laws_chunks.txt"

print("📂 Downloading dataset NahOR102/Indian-IPC-Laws ...")
dataset = load_dataset("NahOR102/Indian-IPC-Laws")

# Open output file
with open(output_file, "w", encoding="utf-8") as f:
    chunk_id = 1
    for item in dataset["train"]:
        messages = item["messages"]

        # Extract question (user) and answer (assistant)
        q = None
        a = None
        for msg in messages:
            if msg["role"] == "user":
                q = msg["content"]
            elif msg["role"] == "assistant":
                a = msg["content"]

        # Write only if both Q & A exist
        if q and a:
            f.write(f"Chunk {chunk_id}:\n")
            f.write(f"Q: {q}\n")
            f.write(f"A: {a}\n\n")
            f.write("="*50 + "\n\n")
            chunk_id += 1

print(f"✅ Done! Chunks saved in {output_file}")
