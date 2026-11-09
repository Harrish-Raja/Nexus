"""Turns passages into vectors, stores them, and searches them.

This is the only module that talks to the vector store.
"""

import os

# The embedding model runs on PyTorch; keep transformers away from any TensorFlow install.
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import chromadb  # noqa: E402
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from config import config

_EMBEDDING_FUNCTION = None
_BATCH_SIZE = 500


def _embedding_function():
    global _EMBEDDING_FUNCTION
    if _EMBEDDING_FUNCTION is None:
        _EMBEDDING_FUNCTION = SentenceTransformerEmbeddingFunction(
            model_name=config.EMBEDDING_MODEL_NAME, device=config.EMBEDDING_DEVICE)
    return _EMBEDDING_FUNCTION


def _client(store_path):
    return chromadb.PersistentClient(path=store_path,
                                     settings=chromadb.Settings(anonymized_telemetry=False))


def build_vector_index(chunk_records, store_path, collection_name):
    """Embed every passage and store it under its own identifier, replacing any earlier build."""
    os.makedirs(store_path, exist_ok=True)
    client = _client(store_path)
    existing = [getattr(item, "name", item) for item in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(collection_name)
    collection = client.create_collection(name=collection_name,
                                          embedding_function=_embedding_function(),
                                          metadata={"hnsw:space": "cosine"})
    for start in range(0, len(chunk_records), _BATCH_SIZE):
        batch = chunk_records[start:start + _BATCH_SIZE]
        collection.add(ids=[str(record["chunk_id"]) for record in batch],
                       documents=[str(record["chunk_text"]) for record in batch],
                       metadatas=[{"document_name": str(record["document_name"])}
                                  for record in batch])
    return collection.count()


def open_vector_index(store_path, collection_name):
    """Open the built store for searching, with the embedding it was built with."""
    if not os.path.isdir(store_path):
        raise FileNotFoundError("No vector store has been built at " + store_path)
    client = _client(store_path)
    return client.get_collection(name=collection_name, embedding_function=_embedding_function())


def search_documents(collection, query_texts, result_count, document_filter):
    """Ask one or more questions, each answered by its nearest passages, nearest first."""
    query_texts = [str(text) for text in query_texts]
    if not query_texts:
        return []
    where = {"document_name": document_filter} if document_filter else None
    reply = collection.query(query_texts=query_texts, n_results=int(result_count), where=where,
                             include=["documents", "metadatas", "distances"])
    results = []
    for position in range(len(query_texts)):
        ids = reply["ids"][position] if reply.get("ids") else []
        documents = reply["documents"][position] if reply.get("documents") else []
        metadatas = reply["metadatas"][position] if reply.get("metadatas") else []
        distances = reply["distances"][position] if reply.get("distances") else []
        passages = [{"chunk_id": str(chunk_id), "chunk_text": str(text),
                     "document_name": str((metadata or {}).get("document_name", "")),
                     "distance": float(distance)}
                    for chunk_id, text, metadata, distance
                    in zip(ids, documents, metadatas, distances)]
        passages.sort(key=lambda passage: passage["distance"])
        results.append(passages)
    return results
