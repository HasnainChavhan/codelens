"""
CodeLens — Diff-Based Incremental Re-Documentation Engine
Only re-documents changed functions — avoids redundant API calls.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CACHE_FILE = ".codelens_cache.json"


class DiffEngine:
    """
    Tracks code changes using content hashing to enable incremental re-documentation.

    On the first run, all functions are documented and their hashes cached.
    On subsequent runs, only functions whose source code has changed are re-documented,
    dramatically reducing API call count and time for large codebases.
    """

    def __init__(self, cache_path: str = CACHE_FILE):
        self.cache_path = Path(cache_path)
        self._cache: dict[str, str] = self._load_cache()

    def _load_cache(self) -> dict[str, str]:
        """Load the hash cache from disk."""
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text())
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        """Persist the hash cache to disk."""
        self.cache_path.write_text(json.dumps(self._cache, indent=2))

    def _hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _item_key(self, file_path: str, item_name: str) -> str:
        return f"{file_path}::{item_name}"

    def has_changed(self, file_path: str, item_name: str, source_code: str) -> bool:
        """
        Check if a function or class has changed since last documentation run.

        Args:
            file_path: Path to the source file
            item_name: Function or class name
            source_code: Current source code of the item

        Returns:
            True if content has changed (needs re-documentation), False if unchanged
        """
        key = self._item_key(file_path, item_name)
        current_hash = self._hash(source_code)
        cached_hash = self._cache.get(key)
        return cached_hash != current_hash

    def mark_documented(self, file_path: str, item_name: str, source_code: str):
        """Record that an item has been documented at its current hash."""
        key = self._item_key(file_path, item_name)
        self._cache[key] = self._hash(source_code)
        self._save_cache()

    def batch_mark_documented(self, items: list[dict]):
        """Efficiently record multiple documented items at once."""
        for item in items:
            key = self._item_key(item["file_path"], item["name"])
            self._cache[key] = self._hash(item["source_code"])
        self._save_cache()

    def get_changed_items(self, modules: list) -> dict:
        """
        Return only the functions and classes that need re-documentation.

        Args:
            modules: List of ModuleInfo objects from ASTExtractor

        Returns:
            Dict with 'functions' and 'classes' lists of changed items
        """
        changed_functions = []
        changed_classes = []
        unchanged_count = 0

        for module in modules:
            for func in module.functions:
                if self.has_changed(func.file_path, func.name, func.source_code):
                    changed_functions.append(func)
                else:
                    unchanged_count += 1

            for cls in module.classes:
                if self.has_changed(cls.file_path, cls.name,
                                    "\n".join(m.source_code for m in cls.methods)):
                    changed_classes.append(cls)
                else:
                    unchanged_count += 1

        total = len(changed_functions) + len(changed_classes) + unchanged_count
        logger.info(
            f"Diff analysis: {len(changed_functions)} functions, "
            f"{len(changed_classes)} classes need re-documentation "
            f"({unchanged_count}/{total} unchanged — skipped)"
        )

        return {
            "functions": changed_functions,
            "classes": changed_classes,
            "unchanged_count": unchanged_count,
        }

    def clear_cache(self):
        """Clear the cache — forces full re-documentation on next run."""
        self._cache = {}
        if self.cache_path.exists():
            self.cache_path.unlink()
        logger.info("Diff cache cleared")

    def cache_stats(self) -> dict:
        return {
            "cached_items": len(self._cache),
            "cache_path": str(self.cache_path),
            "cache_size_bytes": self.cache_path.stat().st_size if self.cache_path.exists() else 0,
        }
