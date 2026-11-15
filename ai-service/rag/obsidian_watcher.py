import os
import re
import sys
import time
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .vector_store import ObsidianVectorStore
from .embedder import OllamaEmbedder

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-vault"))
VECTOR_BLOCK_START = "<!-- VECTOR_LINKS_START -->"
VECTOR_BLOCK_END = "<!-- VECTOR_LINKS_END -->"


class ObsidianVaultSync:
    def __init__(self, vault_path: str = DEFAULT_VAULT_PATH):
        self.vault_path = os.path.abspath(vault_path)
        self.store = ObsidianVectorStore()
        self._is_updating_links = False

    @staticmethod
    def strip_vector_block(content: str) -> str:
        """Remove auto-generated vector similarity block before chunking/embedding."""
        pattern = re.compile(
            rf"\n*{re.escape(VECTOR_BLOCK_START)}.*?{re.escape(VECTOR_BLOCK_END)}\n*",
            flags=re.DOTALL
        )
        return pattern.sub("\n", content).strip()

    @staticmethod
    def extract_title(content: str, fallback_name: str) -> str:
        """Extract first H1 heading from markdown or fallback to filename."""
        for line in content.splitlines():
            line_s = line.strip()
            if line_s.startswith("# "):
                return line_s[2:].strip()
        return fallback_name

    def chunk_markdown(self, content: str, min_length: int = 40) -> list[str]:
        """Split markdown content by sections or double newlines."""
        clean_content = self.strip_vector_block(content)
        paragraphs = clean_content.split("\n\n")
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            if len(current_chunk) + len(p_strip) < 500:
                current_chunk += "\n\n" + p_strip if current_chunk else p_strip
            else:
                if len(current_chunk) >= min_length:
                    chunks.append(current_chunk)
                current_chunk = p_strip

        if len(current_chunk) >= min_length:
            chunks.append(current_chunk)

        return chunks

    def sync_file(self, file_path: str):
        """Index a single markdown file into ChromaDB."""
        if not file_path.endswith(".md"):
            return

        rel_path = os.path.relpath(file_path, self.vault_path).replace("\\", "/")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunks = self.chunk_markdown(content)
            for i, chunk in enumerate(chunks):
                doc_id = f"{rel_path}#chunk_{i}"
                metadata = {
                    "source": rel_path,
                    "chunk_index": i,
                    "file_name": os.path.basename(file_path)
                }
                self.store.add_document_chunk(doc_id, chunk, metadata)
            print(f"[OK] Indexed {len(chunks)} chunks from: {rel_path}")
        except Exception as e:
            print(f"[ERROR] Error syncing {file_path}: {e}")

    def update_vector_links_in_vault(self, files: list[str], top_k: int = 4, min_similarity: float = 0.18) -> int:
        """
        Compute ChromaDB/Embedding Cosine Similarity between all Markdown files in the vault
        and inject Obsidian [[wikilinks]] so Obsidian Graph View displays semantic vector edges.
        """
        self._is_updating_links = True
        doc_records = []
        try:
            for file_path in files:
                if not file_path.endswith(".md"):
                    continue
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                base_content = self.strip_vector_block(raw_content)
                stem = os.path.splitext(os.path.basename(file_path))[0]
                rel_path = os.path.relpath(file_path, self.vault_path).replace("\\", "/")
                rel_no_ext = os.path.splitext(rel_path)[0]
                title = self.extract_title(base_content, stem)
                emb = self.store.embedder.get_embedding(base_content)

                doc_records.append({
                    "file_path": file_path,
                    "rel_path": rel_path,
                    "rel_no_ext": rel_no_ext,
                    "stem": stem,
                    "title": title,
                    "raw_content": raw_content,
                    "base_content": base_content,
                    "embedding": emb
                })

            updated_count = 0
            for i, doc_a in enumerate(doc_records):
                similarities = []
                for j, doc_b in enumerate(doc_records):
                    if i == j:
                        continue
                    sim = OllamaEmbedder.cosine_similarity(doc_a["embedding"], doc_b["embedding"])
                    if sim >= min_similarity:
                        similarities.append((sim, doc_b))

                similarities.sort(key=lambda x: x[0], reverse=True)
                top_matches = similarities[:top_k]

                if not top_matches:
                    continue

                lines = [
                    VECTOR_BLOCK_START,
                    "---",
                    "## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)",
                    "> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*",
                    ""
                ]
                for sim, match_doc in top_matches:
                    sim_pct = round(sim * 100, 1)
                    strength = "Rất mạnh" if sim >= 0.65 else ("Mạnh" if sim >= 0.45 else "Liên quan")
                    lines.append(
                        f"- [[{match_doc['rel_no_ext']}|{match_doc['title']}]] — **Cosine Similarity: `{sim_pct}%`** *(Mức độ: {strength})*"
                    )
                lines.append(VECTOR_BLOCK_END)

                new_content = doc_a["base_content"] + "\n\n" + "\n".join(lines) + "\n"
                if new_content != doc_a["raw_content"]:
                    with open(doc_a["file_path"], "w", encoding="utf-8") as f:
                        f.write(new_content)
                    updated_count += 1

            print(f"[VECTOR-GRAPH] Updated Obsidian [[wikilinks]] vector graph in {updated_count}/{len(doc_records)} files.")
            return updated_count
        finally:
            self._is_updating_links = False

    def sync_all(self):
        """Scan, index all markdown files in the vault, and build Obsidian Vector Graph links."""
        pattern = os.path.join(self.vault_path, "**", "*.md")
        files = sorted(glob.glob(pattern, recursive=True))
        print(f"[INFO] Scanning vault at: {self.vault_path} (Found {len(files)} markdown files)")
        for file in files:
            self.sync_file(file)
        updated_links = self.update_vector_links_in_vault(files)
        stats = self.store.get_stats()
        stats["total_files"] = len(files)
        stats["vector_links_updated"] = updated_links
        print(f"[DONE] Vault sync complete. Total chunks in Vector DB: {stats['total_chunks']}")
        return stats


class VaultFileChangeHandler(FileSystemEventHandler):
    def __init__(self, syncer: ObsidianVaultSync):
        self.syncer = syncer

    def on_modified(self, event):
        if self.syncer._is_updating_links:
            return
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"[CHANGE] Detected file change: {event.src_path}")
            self.syncer.sync_file(event.src_path)

    def on_created(self, event):
        if self.syncer._is_updating_links:
            return
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"[NEW] Detected new file: {event.src_path}")
            self.syncer.sync_file(event.src_path)


def start_live_watcher(vault_path: str = DEFAULT_VAULT_PATH, sync_on_start: bool = False):
    syncer = ObsidianVaultSync(vault_path)
    if sync_on_start:
        syncer.sync_all()
    event_handler = VaultFileChangeHandler(syncer)
    observer = Observer()
    observer.schedule(event_handler, vault_path, recursive=True)
    observer.start()
    print(f"[WATCHER] Live Watcher is watching: {vault_path}")
    return observer


if __name__ == "__main__":
    syncer = ObsidianVaultSync()
    syncer.sync_all()

