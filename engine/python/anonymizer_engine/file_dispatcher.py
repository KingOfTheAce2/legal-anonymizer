"""
File Dispatcher - Routes files to appropriate handlers based on type.

Purpose:
- Central routing for file anonymization
- Decides which scrubber handles which file type
- Assigns stable file_ids
- Prevents path leakage
- Enables future file types without refactors

Supports:
- DOCX (Word documents)
- PDF (Portable Document Format)
- TXT (Plain text)

This module is intentionally layer-agnostic.
"""

import os
from typing import Callable, Dict, List, Tuple, Optional
from dataclasses import dataclass

from .preset import Preset
from .findings import Finding


class UnsupportedFileType(Exception):
    """Raised when a file type has no registered handler."""
    pass


@dataclass
class DispatchResult:
    """Result from dispatching a file."""
    findings: List[Finding]
    summary: Dict[str, int]
    output_path: str
    success: bool
    error: Optional[str] = None


class FileDispatcher:
    """
    Central router for file anonymization.

    Handlers are registered for file extensions and called when
    files of that type are dispatched.
    """

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
        """Return sorted list of supported file extensions."""
        return sorted(self._handlers.keys())

    def is_supported(self, path: str) -> bool:
        """Check if a file type is supported."""
        ext = os.path.splitext(path)[1].lower()
        return ext in self._handlers

    def dispatch(
        self,
        input_path: str,
        output_path: str,
        preset: Preset,
        language: str,
        file_id: str,
    ) -> Tuple[List[Finding], Dict[str, int]]:
        """
        Dispatch a file to its handler.

        Args:
            input_path: Path to input file
            output_path: Path for output file
            preset: Anonymization preset
            language: Language code
            file_id: Unique file identifier

        Returns:
            Tuple of (findings, summary)

        Raises:
            UnsupportedFileType: If no handler for the file type
        """
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

    def dispatch_safe(
        self,
        input_path: str,
        output_path: str,
        preset: Preset,
        language: str,
        file_id: str,
    ) -> DispatchResult:
        """
        Dispatch a file with error handling.

        Returns DispatchResult instead of raising exceptions.
        """
        try:
            findings, summary = self.dispatch(
                input_path, output_path, preset, language, file_id
            )
            return DispatchResult(
                findings=findings,
                summary=summary,
                output_path=output_path,
                success=True,
            )
        except UnsupportedFileType as e:
            return DispatchResult(
                findings=[],
                summary={},
                output_path="",
                success=False,
                error=f"Unsupported file type: {e}",
            )
        except Exception as e:
            return DispatchResult(
                findings=[],
                summary={},
                output_path="",
                success=False,
                error=str(e),
            )


def safe_basename(path: str) -> str:
    """
    Returns filename without directories to avoid leaking PII.
    """
    return path.replace("\\", "/").split("/")[-1]


def next_file_id(index: int) -> str:
    """Generate a file ID from an index."""
    return f"FILE_{index:05d}"


# ============================================================================
# Default Dispatcher with Built-in Handlers
# ============================================================================


def _make_docx_handler():
    """Create DOCX handler."""
    def handler(
        input_path: str,
        output_path: str,
        preset: Preset,
        language: str,
        file_id: str,
    ) -> Tuple[List[Finding], Dict[str, int]]:
        from .docx_scrubber import scrub_docx
        return scrub_docx(input_path, output_path, preset, language, file_id)
    return handler


def _make_pdf_handler():
    """Create PDF handler."""
    def handler(
        input_path: str,
        output_path: str,
        preset: Preset,
        language: str,
        file_id: str,
    ) -> Tuple[List[Finding], Dict[str, int]]:
        from .pdf_scrubber import scrub_pdf
        return scrub_pdf(input_path, output_path, preset, language, file_id)
    return handler


def _make_txt_handler():
    """Create TXT handler."""
    def handler(
        input_path: str,
        output_path: str,
        preset: Preset,
        language: str,
        file_id: str,
    ) -> Tuple[List[Finding], Dict[str, int]]:
        from .layer1 import analyze_layer1_text

        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

        redacted, findings, summary = analyze_layer1_text(text, preset, language)

        # Update findings with file info
        basename = safe_basename(input_path)
        for fd in findings:
            fd.file_id = file_id
            fd.original_filename = basename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(redacted)

        return findings, summary
    return handler


def create_default_dispatcher() -> FileDispatcher:
    """
    Create a dispatcher with all built-in handlers registered.

    Returns:
        FileDispatcher with handlers for .docx, .pdf, .txt
    """
    dispatcher = FileDispatcher()
    dispatcher.register(".docx", _make_docx_handler())
    dispatcher.register(".pdf", _make_pdf_handler())
    dispatcher.register(".txt", _make_txt_handler())
    return dispatcher


# Module-level default dispatcher
default_dispatcher = create_default_dispatcher()
