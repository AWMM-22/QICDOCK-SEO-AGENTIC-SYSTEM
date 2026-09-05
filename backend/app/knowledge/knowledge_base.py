import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import json
import logging
import hashlib
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeBase:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="qicdock_brand_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

    def ingest_brand_story(self, brand_story_path: str) -> int:
        with open(brand_story_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chunks = self._chunk_text(content, chunk_size=500, overlap=50)
        documents = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            doc_id = f"brand_story_{hashlib.md5(chunk.encode()).hexdigest()[:8]}"
            documents.append(chunk)
            metadatas.append({
                "source": "brand_story",
                "section": "brand_story",
                "chunk_index": i
            })
            ids.append(doc_id)

        self.collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Ingested {len(chunks)} brand story chunks")
        return len(chunks)

    def ingest_products(self, products_path: str) -> int:
        with open(products_path, 'r', encoding='utf-8') as f:
            products = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for product in products:
            content = f"""
Product: {product['product_name']}
Category: {product['category']}
Vehicle: {product.get('vehicle_make', '')} {product.get('vehicle_model', '')}
Compatibility: {product.get('compatibility', '')}
Price: INR {product.get('selling_price_inr', '')} (MRP: INR {product.get('mrp_inr', '')}, {product.get('discount_percent', '')}% off)
Description: {product.get('description', '')}
Features: {', '.join(product.get('features', []))}
            """.strip()

            doc_id = f"product_{product['sku']}"
            documents.append(content)
            metadatas.append({
                "source": "product_knowledge",
                "sku": product['sku'],
                "product_name": product['product_name'],
                "category": product['category'],
                "vehicle_make": product.get('vehicle_make', ''),
                "vehicle_model": product.get('vehicle_model', ''),
                "price_inr": product.get('selling_price_inr', 0)
            })
            ids.append(doc_id)

        self.collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Ingested {len(products)} products")
        return len(products)

    def ingest_all(self, brand_story_path: str, products_path: str) -> Dict[str, int]:
        brand_count = self.ingest_brand_story(brand_story_path)
        product_count = self.ingest_products(products_path)
        return {"brand_story_chunks": brand_count, "products": product_count}

    def query(self, query_text: str, n_results: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata
        )

        formatted = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "id": results['ids'][0][i] if results['ids'] else None
                })
        return formatted

    def query_brand_context(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        return self.query(query_text, n_results, filter_metadata={"source": "brand_story"})

    def query_product_context(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        return self.query(query_text, n_results, filter_metadata={"source": "product_knowledge"})

    def query_all_context(self, query_text: str, n_results: int = 10) -> List[Dict[str, Any]]:
        return self.query(query_text, n_results)

    def get_all_products_summary(self) -> List[Dict[str, Any]]:
        results = self.collection.get(where={"source": "product_knowledge"})
        products = []
        if results['documents']:
            for i, doc in enumerate(results['documents']):
                meta = results['metadatas'][i] if results['metadatas'] else {}
                products.append({
                    "sku": meta.get('sku', ''),
                    "product_name": meta.get('product_name', ''),
                    "category": meta.get('category', ''),
                    "vehicle": f"{meta.get('vehicle_make', '')} {meta.get('vehicle_model', '')}".strip(),
                    "price_inr": meta.get('price_inr', 0)
                })
        return products

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    def count_documents(self) -> int:
        return self.collection.count()


_knowledge_base_instance: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    global _knowledge_base_instance
    if _knowledge_base_instance is None:
        _knowledge_base_instance = KnowledgeBase()
    return _knowledge_base_instance