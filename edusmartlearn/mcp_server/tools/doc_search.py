"""
mcp_server/tools/doc_search.py
==============================
Document Search Tool for RAG (Retrieval-Augmented Generation).

This tool provides semantic search over course materials, textbooks,
and documentation using vector similarity search.

Components:
- ChromaDB: Vector database for storing document embeddings
- Sentence Transformers: For generating text embeddings

Tool Scope: READ-only access to document store
Agents with access: Teacher, Retrieval, Quiz, Evaluator, Orchestrator
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

# Try to import embedding libraries
EMBEDDINGS_AVAILABLE = False
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    logger.warning("embeddings_not_available", 
                   message="Install chromadb and sentence-transformers for semantic search")


class DocumentChunk(BaseModel):
    """Represents a chunk of retrieved document."""
    chunk_id: str
    content: str
    source: str
    page: Optional[int] = None
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Result of a document search operation."""
    query: str
    chunks: List[DocumentChunk]
    total_matches: int
    search_time_ms: float
    search_method: str = "keyword"  # "keyword" or "semantic"


class DocSearchTool:
    """
    Document search tool using ChromaDB for vector similarity search.
    
    Enables RAG by:
    1. Indexing course materials into ChromaDB vector database
    2. Performing semantic search using sentence-transformers embeddings
    3. Returning ranked results with citations
    
    Supports two modes:
    - Semantic search (default): Uses ChromaDB + sentence-transformers
    - Keyword search (fallback): Simple keyword matching
    
    Usage:
        tool = DocSearchTool(data_dir=Path("./data"))
        await tool.initialize()
        results = await tool.search("What is backpropagation?", top_k=5)
    """
    
    # Tool metadata for MCP registration
    TOOL_NAME = "doc_search"
    TOOL_DESCRIPTION = "Search course materials using semantic similarity"
    TOOL_SCHEMA = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "top_k": {"type": "integer", "description": "Number of results", "default": 5},
            "filter_source": {"type": "string", "description": "Filter by source"},
            "use_semantic": {"type": "boolean", "description": "Use semantic search", "default": True}
        },
        "required": ["query"]
    }
    
    # Embedding model - lightweight and effective for educational content
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    COLLECTION_NAME = "course_materials"
    
    def __init__(self, data_dir: Path, use_embeddings: bool = True):
        """
        Initialize document search tool.
        
        Args:
            data_dir: Path to data directory containing course_materials
            use_embeddings: Whether to use embeddings (requires chromadb, sentence-transformers)
        """
        self.data_dir = data_dir
        self._initialized = False
        self._documents: List[Dict[str, Any]] = []  # Fallback in-memory store
        
        # Embedding components
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        self._embedding_model: Optional[SentenceTransformer] = None
        self._chroma_client = None
        self._collection = None
    
    async def initialize(self) -> None:
        """Initialize the document store and load documents."""
        if self._initialized:
            return
        
        materials_dir = self.data_dir / "course_materials"
        materials_dir.mkdir(parents=True, exist_ok=True)
        
        if self.use_embeddings:
            await self._initialize_embeddings()
        
        # Load documents from files
        await self._load_documents(materials_dir)
        self._initialized = True
        
        doc_count = len(self._documents)
        if self.use_embeddings and self._collection:
            doc_count = self._collection.count()
        
        logger.info("doc_search_initialized", 
                    document_count=doc_count,
                    mode="semantic" if self.use_embeddings else "keyword")
    
    async def _initialize_embeddings(self) -> None:
        """Initialize embedding model and ChromaDB."""
        try:
            # Initialize sentence transformer model
            logger.info("loading_embedding_model", model=self.EMBEDDING_MODEL)
            self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)
            
            # Initialize ChromaDB with persistent storage
            chroma_dir = self.data_dir / "chroma_db"
            chroma_dir.mkdir(parents=True, exist_ok=True)
            
            self._chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
            
            # Get or create collection
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            
            logger.info("embeddings_initialized", 
                        model=self.EMBEDDING_MODEL,
                        collection=self.COLLECTION_NAME)
            
        except Exception as e:
            logger.error("embeddings_init_failed", error=str(e))
            self.use_embeddings = False
            self._embedding_model = None
            self._chroma_client = None
            self._collection = None
    
    async def _load_documents(self, materials_dir: Path) -> None:
        """Load and chunk documents from the materials directory."""
        all_chunks = []
        all_ids = []
        all_metadatas = []
        
        for file_path in materials_dir.glob("**/*"):
            if file_path.suffix in [".txt", ".md"]:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    chunks = self._chunk_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{file_path.stem}_{i}"
                        metadata = {
                            "source": file_path.name,
                            "chunk_index": i,
                            "file_stem": file_path.stem
                        }
                        
                        # Store for keyword fallback
                        self._documents.append({
                            "id": chunk_id,
                            "content": chunk.lower(),
                            "original_content": chunk,
                            "source": file_path.name,
                            "chunk_index": i
                        })
                        
                        # Collect for batch embedding
                        if self.use_embeddings:
                            all_chunks.append(chunk)
                            all_ids.append(chunk_id)
                            all_metadatas.append(metadata)
                            
                except Exception as e:
                    logger.warning("document_load_failed", path=str(file_path), error=str(e))
        
        # Batch add to ChromaDB with embeddings
        if self.use_embeddings and all_chunks and self._collection:
            await self._add_to_chromadb(all_chunks, all_ids, all_metadatas)
    
    async def _add_to_chromadb(
        self, 
        chunks: List[str], 
        ids: List[str], 
        metadatas: List[Dict]
    ) -> None:
        """Add documents to ChromaDB with embeddings."""
        try:
            # Check which documents already exist
            existing = self._collection.get(ids=ids)
            existing_ids = set(existing['ids']) if existing['ids'] else set()
            
            # Filter to only new documents
            new_chunks = []
            new_ids = []
            new_metadatas = []
            
            for chunk, doc_id, metadata in zip(chunks, ids, metadatas):
                if doc_id not in existing_ids:
                    new_chunks.append(chunk)
                    new_ids.append(doc_id)
                    new_metadatas.append(metadata)
            
            if not new_chunks:
                logger.info("no_new_documents_to_embed")
                return
            
            # Generate embeddings in batches
            batch_size = 100
            for i in range(0, len(new_chunks), batch_size):
                batch_chunks = new_chunks[i:i + batch_size]
                batch_ids = new_ids[i:i + batch_size]
                batch_metadatas = new_metadatas[i:i + batch_size]
                
                # Generate embeddings
                embeddings = self._embedding_model.encode(
                    batch_chunks,
                    show_progress_bar=False,
                    convert_to_numpy=True
                ).tolist()
                
                # Add to collection
                self._collection.add(
                    documents=batch_chunks,
                    embeddings=embeddings,
                    ids=batch_ids,
                    metadatas=batch_metadatas
                )
                
                logger.info("batch_embedded", 
                            batch=i // batch_size + 1,
                            documents=len(batch_chunks))
            
            logger.info("documents_embedded", total=len(new_chunks))
            
        except Exception as e:
            logger.error("chromadb_add_failed", error=str(e))
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Split text into chunks with overlap for better context retention.
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in characters
            overlap: Number of characters to overlap between consecutive chunks
        
        Returns:
            List of text chunks with overlapping content
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        # Split by paragraphs to maintain semantic boundaries
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        if not paragraphs:
            return [text]
        
        chunks = []
        current_chunk = ""
        previous_chunk_end = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    previous_chunk_end = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                
                if previous_chunk_end and overlap > 0:
                    current_chunk = previous_chunk_end.strip() + "\n\n" + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Split large chunks with sliding window
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size * 1.5:
                final_chunks.extend(self._sliding_window_chunk(chunk, chunk_size, overlap))
            else:
                final_chunks.append(chunk)
        
        return final_chunks if final_chunks else [text]
    
    def _sliding_window_chunk(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Apply sliding window chunking for large text blocks."""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            
            if end < text_len:
                for boundary in ['. ', '! ', '? ', '\n']:
                    boundary_pos = text.rfind(boundary, start + chunk_size // 2, end)
                    if boundary_pos != -1:
                        end = boundary_pos + len(boundary)
                        break
                else:
                    space_pos = text.rfind(' ', start + chunk_size // 2, end)
                    if space_pos != -1:
                        end = space_pos + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < text_len else text_len
        
        return chunks
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_source: Optional[str] = None,
        use_semantic: bool = True
    ) -> SearchResult:
        """
        Search for documents relevant to the query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_source: Optional filter by source name
            use_semantic: Use semantic search if available (default True)
        """
        import time
        start_time = time.time()
        
        if not self._initialized:
            await self.initialize()
        
        if use_semantic and self.use_embeddings and self._collection:
            result = await self._semantic_search(query, top_k, filter_source)
        else:
            result = await self._keyword_search(query, top_k, filter_source)
        
        search_time = (time.time() - start_time) * 1000
        result.search_time_ms = search_time
        
        logger.info("doc_search_completed", 
                    query=query[:50], 
                    results=len(result.chunks),
                    method=result.search_method,
                    time_ms=f"{search_time:.2f}")
        
        return result
    
    async def _semantic_search(
        self,
        query: str,
        top_k: int,
        filter_source: Optional[str]
    ) -> SearchResult:
        """Perform semantic search using ChromaDB embeddings."""
        try:
            # Generate query embedding
            query_embedding = self._embedding_model.encode(
                query,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()
            
            # Build filter if source specified
            where_filter = None
            if filter_source:
                where_filter = {"source": filter_source}
            
            # Query ChromaDB
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to DocumentChunk objects
            chunks = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    
                    # Convert cosine distance to similarity
                    similarity = 1 - distance
                    
                    chunks.append(DocumentChunk(
                        chunk_id=results['ids'][0][i],
                        content=doc,
                        source=metadata.get("source", "unknown"),
                        relevance_score=similarity,
                        metadata=metadata
                    ))
            
            return SearchResult(
                query=query,
                chunks=chunks,
                total_matches=len(chunks),
                search_time_ms=0,
                search_method="semantic"
            )
            
        except Exception as e:
            logger.error("semantic_search_failed", error=str(e))
            return await self._keyword_search(query, top_k, filter_source)
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filter_source: Optional[str]
    ) -> SearchResult:
        """Perform keyword-based search (fallback)."""
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        scored_docs = []
        for doc in self._documents:
            if filter_source and doc["source"] != filter_source:
                continue
            
            score = sum(1 for term in query_terms if term in doc["content"])
            if score > 0:
                scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        chunks = []
        for doc, score in scored_docs[:top_k]:
            chunks.append(DocumentChunk(
                chunk_id=doc["id"],
                content=doc["original_content"],
                source=doc["source"],
                relevance_score=score / len(query_terms) if query_terms else 0,
                metadata={"chunk_index": doc["chunk_index"]}
            ))
        
        return SearchResult(
            query=query,
            chunks=chunks,
            total_matches=len(chunks),
            search_time_ms=0,
            search_method="keyword"
        )
    
    async def add_document(self, content: str, source: str) -> int:
        """Add a new document to the index."""
        if not self._initialized:
            await self.initialize()
        
        chunks = self._chunk_text(content)
        base_id = len(self._documents)
        
        chunk_ids = []
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{source}_{base_id + i}"
            metadata = {
                "source": source,
                "chunk_index": i,
                "file_stem": source.rsplit('.', 1)[0]
            }
            
            self._documents.append({
                "id": chunk_id,
                "content": chunk.lower(),
                "original_content": chunk,
                "source": source,
                "chunk_index": i
            })
            
            chunk_ids.append(chunk_id)
            chunk_metadatas.append(metadata)
        
        if self.use_embeddings and self._collection:
            await self._add_to_chromadb(chunks, chunk_ids, chunk_metadatas)
        
        logger.info("document_added", source=source, chunks=len(chunks))
        return len(chunks)
    
    async def reindex(self) -> int:
        """Reindex all documents (useful after adding new files)."""
        import shutil
        
        if self.use_embeddings:
            chroma_dir = self.data_dir / "chroma_db"
            if chroma_dir.exists():
                try:
                    shutil.rmtree(chroma_dir)
                    logger.info("chroma_db_deleted", path=str(chroma_dir))
                except Exception as e:
                    logger.warning("chroma_db_delete_failed", error=str(e))
            
            self._collection = None
            self._chroma_client = None
        
        self._documents = []
        self._initialized = False
        
        await self.initialize()
        
        return len(self._documents)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the document store."""
        stats = {
            "initialized": self._initialized,
            "mode": "semantic" if self.use_embeddings else "keyword",
            "keyword_docs": len(self._documents),
        }
        
        if self.use_embeddings and self._collection:
            stats["chromadb_docs"] = self._collection.count()
            stats["embedding_model"] = self.EMBEDDING_MODEL
        
        return stats
