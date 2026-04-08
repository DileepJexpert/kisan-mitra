from __future__ import annotations

from typing import Any

import chromadb
import structlog

logger = structlog.get_logger(__name__)

# Well-known collection names used across the service
COLLECTIONS = ("schemes", "legal_templates", "loan_rules", "faq")


class ChromaClient:
    """Wrapper around the ChromaDB HTTP client."""

    def __init__(self, host: str = "http://localhost:8000") -> None:
        self._host = host
        self._client: chromadb.HttpClient | None = None

    def connect(self) -> None:
        """Initialise the ChromaDB HTTP client and ensure collections exist."""
        # Parse host/port from the URL
        clean = self._host.replace("http://", "").replace("https://", "")
        parts = clean.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 8000

        logger.info("chroma.connecting", host=host, port=port)
        self._client = chromadb.HttpClient(host=host, port=port)

        # Pre-create well-known collections
        for name in COLLECTIONS:
            self._client.get_or_create_collection(name=name)
        logger.info("chroma.connected", collections=COLLECTIONS)

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Return an existing collection or create a new one."""
        return self._client.get_or_create_collection(name=name)

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """Add documents to a collection."""
        collection = self.get_or_create_collection(collection_name)
        kwargs: dict[str, Any] = {"documents": documents}
        if metadatas:
            kwargs["metadatas"] = metadatas
        if ids:
            kwargs["ids"] = ids
        else:
            kwargs["ids"] = [f"{collection_name}_{i}" for i in range(len(documents))]
        collection.add(**kwargs)
        logger.info(
            "chroma.documents_added",
            collection=collection_name,
            count=len(documents),
        )

    def search(
        self,
        collection_name: str,
        query_texts: list[str],
        n_results: int = 5,
        where: dict | None = None,
    ) -> dict:
        """Semantic search across a collection."""
        collection = self.get_or_create_collection(collection_name)
        kwargs: dict[str, Any] = {
            "query_texts": query_texts,
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        return collection.query(**kwargs)
