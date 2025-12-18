import os
import sys
import json
import numpy as np
from tqdm import tqdm
from typing import List, Tuple

class IndexBuilder:
    def __init__(
        self,
        config, 
        embedding_model: str = "qwen3-embedding",
        working_dir: str = "./agent_working/",
    ):
        self.llm = config.llm_dict[embedding_model]
        self.embedding_model_name = embedding_model
        self.save_file_path = os.path.join(working_dir, "embeddings", "collect_data_list.npz")
        self.cache_file_path = os.path.join(working_dir, "embeddings", "cache.json")
        self.cache = {}
        self.embeddings = []
        # Load cache if it exists
        self._load_cache()
        # Load embeddings index if it exists
        self.load_index()

    def _load_cache(self):
        """Internal method to load the search and embeddings cache (with backward compatibility)."""
        if os.path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Backward compatibility: previously cache may have been a flat dict for search results
                if isinstance(loaded, dict) and ("search" in loaded or "embeddings" in loaded):
                    self.cache = loaded
                elif isinstance(loaded, dict):
                    # Migrate old flat search cache into new structured cache
                    self.cache = {"search": loaded, "embeddings": {}}
                else:
                    self.cache = {"search": {}, "embeddings": {}}
            except json.JSONDecodeError as e:
                print(f"Warning: Could not load cache from {self.cache_file_path}. File might be corrupted: {e}")
                self.cache = {"search": {}, "embeddings": {}} # Reset cache if loading fails
        else:
            print(f"No cache file found at {self.cache_file_path}. Starting with empty cache.")
            self.cache = {"search": {}, "embeddings": {}}

    def _save_cache(self):
        """Internal method to save the search cache."""
        os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
        try:
            with open(self.cache_file_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=4) # Added indent for readability
        except IOError as e:
            print(f"Error: Could not save cache to {self.cache_file_path}: {e}")
        
    async def _get_embeddings_batch(self, batch: List[str], n_retries: int = 3):
        """Helper method to get embeddings for a batch with retries and caching per-text."""
        if not isinstance(self.cache, dict):
            self.cache = {"search": {}, "embeddings": {}}
        if "embeddings" not in self.cache or not isinstance(self.cache["embeddings"], dict):
            self.cache["embeddings"] = {}

        # Prepare results aligned with input order
        results: List = [None] * len(batch)
        to_compute_indices: List[int] = []
        to_compute_texts: List[str] = []

        # Fill from cache if available
        for idx, text in enumerate(batch):
            cached = self.cache["embeddings"].get(text)
            if cached is not None:
                results[idx] = cached
            else:
                to_compute_indices.append(idx)
                to_compute_texts.append(text)

        # If everything is cached, return early
        if not to_compute_texts:
            return results

        # Compute missing embeddings with retries
        response = []
        for attempt in range(n_retries):
            try:
                response = await self.llm.generate_embeddings(to_compute_texts)
                break
            except Exception as e:
                print(f"Error getting embeddings (attempt {attempt + 1}/{n_retries}): {e}")
                if attempt == n_retries - 1:
                    print(f"Failed to get embeddings after {n_retries} attempts for a batch.")
                    response = []

        # If failed to compute, fill missing slots with empty list to avoid crashes
        if not isinstance(response, list):
            response = []

        # Map computed embeddings back to their positions and update cache
        for offset, idx in enumerate(to_compute_indices):
            if offset < len(response):
                emb = response[offset]
                # Ensure JSON serializable (convert numpy arrays to lists if any)
                if isinstance(emb, np.ndarray):
                    emb = emb.tolist()
                results[idx] = emb
                self.cache["embeddings"][batch[idx]] = emb
            else:
                results[idx] = []

        # Persist cache updates
        self._save_cache()

        return results

    async def build_index_from_analysis_result(self, analysis_result_list: List[dict], batch_size: int = 10, n_retries: int = 3):
        """Build embeddings index for a list of analysis results."""
        texts = [f"{item['report_title']}\n{item['report_content']}" for item in analysis_result_list]
        await self._build_index(texts, batch_size, n_retries)

    async def build_index_from_collect_data_list(self, collect_data_list: List, batch_size: int = 10, n_retries: int = 3):
        """Build embeddings index for a list of collected data items."""
        # Assuming CollectResult objects have a .brief_str() method
        texts = [item.brief_str() for item in collect_data_list]
        await self._build_index(texts, batch_size, n_retries)

    async def _build_index(self, texts: List[str], batch_size: int=32, n_retries: int=2):
        """Internal unified method to build the embeddings index."""
        self.embeddings = [] # Clear existing embeddings before building a new index
        # Clear search cache since index is being rebuilt - cached ids would be invalid
        if isinstance(self.cache, dict) and "search" in self.cache:
            self.cache["search"] = {}
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Building index"):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self._get_embeddings_batch(batch, n_retries)
            self.embeddings.extend(batch_embeddings)

        # Save index to file after building
        self._save_index()

    def _save_index(self):
        """Internal method to save the embeddings index."""
        if not self.embeddings:
            print("Warning: No embeddings to save. Index is empty.")
            return

        os.makedirs(os.path.dirname(self.save_file_path), exist_ok=True)
        try:
            np.savez(self.save_file_path, embeddings=np.array(self.embeddings))
        except IOError as e:
            print(f"Error: Could not save embeddings index to {self.save_file_path}: {e}")

    def load_index(self):
        """Load existing embeddings index from file."""
        if os.path.exists(self.save_file_path):
            try:
                embeddings_data = np.load(self.save_file_path)
                self.embeddings = embeddings_data['embeddings'].tolist() # Convert back to list if preferred
                print(f"Successfully loaded index with {len(self.embeddings)} embeddings from {self.save_file_path}.")
            except Exception as e:
                print(f"Warning: Could not load index from {self.save_file_path}. File might be corrupted or in wrong format: {e}")
                self.embeddings = [] # Reset if loading fails
        else:
            print(f"No index file found at {self.save_file_path}. Starting with empty index.")

    async def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search for similar items in the index."""
        if self.embeddings is None:
            print("Warning: Embeddings index is empty. Cannot perform search.")
            return []

        # Ensure structured cache
        if not isinstance(self.cache, dict):
            self.cache = {"search": {}, "embeddings": {}}
        if "search" not in self.cache or not isinstance(self.cache["search"], dict):
            # Backward compatibility: if flat, migrate
            if isinstance(self.cache, dict):
                flat = {k: v for k, v in self.cache.items() if k not in ("search", "embeddings")}
                self.cache = {"search": flat, "embeddings": self.cache.get("embeddings", {})}
            else:
                self.cache = {"search": {}, "embeddings": {}}

        if query in self.cache["search"]:
            return self.cache["search"][query]

        try:
            # Reuse the embedding cache via the batch helper
            query_embedding_list = await self._get_embeddings_batch([query])
            if not query_embedding_list or not query_embedding_list[0]:
                return []
            query_embedding = np.array(query_embedding_list[0])
            query_embedding = np.array(query_embedding)
        except Exception as e:
            print(f"Error: Could not get embedding for query '{query}': {e}")
            return []

        # Ensure embeddings are numpy array for dot product
        if not isinstance(self.embeddings, np.ndarray):
            self.embeddings = np.array(self.embeddings)

        distances = np.dot(self.embeddings, query_embedding)
        # Check if distances is empty, which can happen if embeddings is empty or not properly loaded
        if distances.size == 0:
            print("Warning: No distances computed. Embeddings array might be empty.")
            return []

        top_k_indices = np.argsort(distances)[::-1][:top_k]

        results = [{'id': int(i), 'score': float(distances[i])} for i in top_k_indices]
        self.cache["search"][query] = results
        self._save_cache() # Use the internal save method

        return results
