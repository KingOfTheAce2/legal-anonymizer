import os
from typing import Callable, Dict, List, Tuple

from .preset import Preset
from .findings import Finding

"""
File Dispatcher

Purpose:
- Central routing for file anonymization
- Decides which scrubber handles which file type
- Assigns stable file_ids
- Prevents path leakage
- Enables future file types without refactors

This module is intentionally layer-agnostic.
"""


class UnsupportedFileType(Exception):
    pass


class FileDispatcher:
    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        extension: str,
        handler: Callable[
            [str, str, Preset, str, str],
            Tuple[List[Finding], Dict[str, int]],
        ],
    ) -> None:
        """
        Register a handler for a file extension.

        handler signature:
          (input_path, output_path, preset, language, file_id)
            -> (findings, summary)
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = "." + ext
        self._handlers[ext] = handler

    def supported_extensions(self) -> List[str]:
        return sorted(self._handlers.keys())

    def dispatch(
        self,
        input_path: str,
        output_path: str,
        preset: Preset,
        language: str,
        file_id: str,
    ) -> Tuple[List[Finding], Dict[str, int]]:
        ext = os.path.splitext(input_path)[1].lower()

        if ext not in self._handlers:
            raise UnsupportedFileType(ext)

        handler = self._handlers[ext]
        return handler(
            input_path,
            output_path,
            preset,
            language,
            file_id,
        )


def safe_basename(path: str) -> str:
    """
    Returns filename without directories to avoid leaking PII.
    """
    return path.replace("\\", "/").split("/")[-1]


def next_file_id(index: int) -> str:
    return f"FILE_{index:05d}"
