"""
Reusable CSV Repository Class with In-Memory Cache for RailBlock AI.

Serves as the primary CSV Data Access Layer, treating CSV files as the persistent
source of truth.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from app.utils.csv_utils import safe_read_csv, atomic_write_csv, sanitize_for_json


class CSVCache:
    """In-memory cache for CSV DataFrames to avoid repeated disk reads."""
    _cache: Dict[str, pd.DataFrame] = {}
    _mtime: Dict[str, float] = {}

    @classmethod
    def get(cls, path: Path) -> Optional[pd.DataFrame]:
        key = str(path.resolve())
        if key in cls._cache and path.exists():
            if path.stat().st_mtime == cls._mtime.get(key, 0):
                return cls._cache[key].copy()
        return None

    @classmethod
    def set(cls, path: Path, df: pd.DataFrame):
        key = str(path.resolve())
        cls._cache[key] = df.copy()
        if path.exists():
            cls._mtime[key] = path.stat().st_mtime

    @classmethod
    def invalidate(cls, path: Path):
        key = str(path.resolve())
        cls._cache.pop(key, None)
        cls._mtime.pop(key, None)


class CSVRepository:
    def __init__(self, file_path: Path, expected_columns: List[str] = None):
        self.file_path = Path(file_path).resolve() if Path(file_path).is_absolute() else file_path
        self.expected_columns = expected_columns

    def file_exists(self) -> bool:
        return self.file_path.exists()

    def read_csv(self, use_cache: bool = True) -> pd.DataFrame:
        if use_cache:
            cached = CSVCache.get(self.file_path)
            if cached is not None:
                return cached

        df = safe_read_csv(self.file_path, self.expected_columns)
        if use_cache:
            CSVCache.set(self.file_path, df)
        return df

    def write_csv(self, df: pd.DataFrame):
        atomic_write_csv(df, self.file_path)
        CSVCache.set(self.file_path, df)

    def append_rows(self, rows: List[Dict[str, Any]]):
        df_existing = self.read_csv(use_cache=False) if self.file_exists() else pd.DataFrame()
        df_new = pd.DataFrame(rows)
        combined = pd.concat([df_existing, df_new], ignore_index=True)
        self.write_csv(combined)

    def filter_rows(self, filters: Dict[str, Any], page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        df = self.read_csv()
        for col, val in filters.items():
            if val is not None and col in df.columns:
                if isinstance(val, list):
                    df = df[df[col].isin(val)]
                else:
                    try:
                        if pd.api.types.is_numeric_dtype(df[col]):
                            df = df[df[col] == pd.to_numeric(val, errors="coerce")]
                        else:
                            df = df[df[col].astype(str).str.lower() == str(val).lower()]
                    except Exception:
                        df = df[df[col] == val]

        total = len(df)
        start = (page - 1) * page_size
        end = start + page_size
        items = sanitize_for_json(df.iloc[start:end].to_dict("records"))
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages
        }

    def get_by_id(self, id_column: str, id_value: Any) -> Optional[Dict[str, Any]]:
        df = self.read_csv()
        if id_column not in df.columns:
            return None
        matches = df[df[id_column].astype(str) == str(id_value)]
        if len(matches) > 0:
            return sanitize_for_json(matches.iloc[0].to_dict())
        return None

    def count_rows(self) -> int:
        if not self.file_exists():
            return 0
        df = self.read_csv()
        return len(df)

    def get_file_metadata(self) -> Dict[str, Any]:
        exists = self.file_exists()
        return {
            "file_name": self.file_path.name,
            "path": str(self.file_path),
            "exists": exists,
            "row_count": self.count_rows() if exists else 0,
            "size_bytes": self.file_path.stat().st_size if exists else 0
        }
