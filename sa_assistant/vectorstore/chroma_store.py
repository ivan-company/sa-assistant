from typing import List, Dict, Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class VectorStore:
    def __init__(self, persist_directory: Optional[str] = None,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        if chromadb is None or Settings is None:
            raise ImportError(
                "chromadb is not installed. "
                "Please install it to use VectorStore."
            )
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Please install it to use VectorStore."
            )
        self.client = chromadb.PersistentClient(
            path=persist_directory or ".vector_store")
        self.embedding_model = SentenceTransformer(
            embedding_model
        )
        self.collections = {}

    def _get_collection(self, source: str):
        if source not in self.collections:
            self.collections[source] = self.client.get_or_create_collection(
                source
            )
        return self.collections[source]

    def add_documents(self, source: str, documents: List[Dict]):
        collection = self._get_collection(source)
        texts = [doc["text"] for doc in documents]
        ids = [doc["id"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        embeddings = self.embedding_model.encode(texts).tolist()
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, source: Optional[str] = None,
               top_k: int = 5) -> List[Dict]:
        sources = [source] if source else self.collections.keys()
        results = []
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        for src in sources:
            collection = self._get_collection(src)
            res = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            for i in range(len(res["ids"][0])):
                results.append({
                    "id": res["ids"][0][i],
                    "text": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i],
                    "distance": res["distances"][0][i],
                    "source": src
                })
        results.sort(key=lambda x: x["distance"])
        return results[:top_k]

    def delete_document(self, doc_id: str, source: Optional[str] = None):
        sources = [source] if source else self.collections.keys()
        for src in sources:
            collection = self._get_collection(src)
            collection.delete(ids=[doc_id])

    def has_collection(self, source: str) -> bool:
        return source in self.collections
