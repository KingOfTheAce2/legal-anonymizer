"""
Document chunking for large text processing.

Provides:
- Intelligent splitting for documents >50KB
- Paragraph-aware chunking to preserve context
- Overlap handling for entity boundaries
- Progress reporting for long operations
"""

from typing import List, Optional, Any
import re


class DocumentChunk:
    """Represents a chunk of a document."""

    def __init__(
        self,
        text: str,
        start_offset: int,
        end_offset: int,
        chunk_index: int,
        original_size: int,
    ):
        """
        Initialize document chunk.

        Args:
            text: Chunk text content
            start_offset: Character offset in original document
            end_offset: Character offset in original document
            chunk_index: Index of this chunk
            original_size: Total size of original document
        """
        self.text = text
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.chunk_index = chunk_index
        self.original_size = original_size
        self.size = len(text)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DocumentChunk(index={self.chunk_index}, "
            f"size={self.size}, "
            f"offset={self.start_offset}-{self.end_offset})"
        )


class DocumentChunker:
    """Intelligently chunks documents for processing."""

    # Default chunk size: 50KB
    DEFAULT_CHUNK_SIZE = 50 * 1024

    # Overlap between chunks to catch entities at boundaries
    DEFAULT_OVERLAP = 2 * 1024

    # Minimum chunk size to avoid too many small chunks
    MIN_CHUNK_SIZE = 10 * 1024

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        min_chunk_size: int = MIN_CHUNK_SIZE,
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in bytes
            overlap: Overlap between chunks in bytes
            min_chunk_size: Minimum chunk size
        """
        self.chunk_size = max(chunk_size, min_chunk_size)
        self.overlap = min(overlap, self.chunk_size // 4)  # Cap overlap at 25%
        self.min_chunk_size = min_chunk_size

    def chunk_document(
        self,
        text: str,
        progress_callback: Optional[callable] = None,
    ) -> List[DocumentChunk]:
        """
        Split document into chunks intelligently.

        For documents smaller than chunk_size, returns single chunk.
        For larger documents, splits on paragraph boundaries.
        Maintains overlap for entity boundary handling.

        Args:
            text: Document text to chunk
            progress_callback: Optional callback for progress (takes percent 0-100)

        Returns:
            List of DocumentChunk objects
        """
        # Single chunk for small documents
        if len(text) <= self.chunk_size:
            return [
                DocumentChunk(
                    text=text,
                    start_offset=0,
                    end_offset=len(text),
                    chunk_index=0,
                    original_size=len(text),
                )
            ]

        chunks: List[DocumentChunk] = []
        current_offset = 0
        chunk_index = 0

        while current_offset < len(text):
            # Report progress
            if progress_callback:
                progress_percent = int((current_offset / len(text)) * 100)
                progress_callback(progress_percent)

            # Calculate chunk boundaries
            chunk_start = current_offset
            chunk_end = min(current_offset + self.chunk_size, len(text))

            # Find a good split point (paragraph boundary)
            if chunk_end < len(text):
                # Look for paragraph break near the target end
                split_point = self._find_split_point(text, chunk_start, chunk_end)
                if split_point > chunk_start:
                    chunk_end = split_point

            # Extract chunk text
            chunk_text = text[chunk_start:chunk_end]

            # Create chunk
            chunks.append(
                DocumentChunk(
                    text=chunk_text,
                    start_offset=chunk_start,
                    end_offset=chunk_end,
                    chunk_index=chunk_index,
                    original_size=len(text),
                )
            )

            # Move to next chunk, accounting for overlap
            if chunk_end >= len(text):
                break

            # Advance with overlap
            current_offset = chunk_end - self.overlap
            chunk_index += 1

        # Report completion
        if progress_callback:
            progress_callback(100)

        return chunks

    def _find_split_point(self, text: str, start: int, preferred_end: int) -> int:
        """
        Find a good split point (paragraph boundary) near preferred_end.

        Args:
            text: Full text
            start: Start of search range
            preferred_end: Preferred end position

        Returns:
            Character offset for split point, or preferred_end if no good split found
        """
        # Search window around preferred_end
        search_start = max(start, preferred_end - 2000)
        search_end = min(len(text), preferred_end + 1000)

        # Look for paragraph breaks (double newline or similar)
        search_text = text[search_start:search_end]

        # Try patterns in order of preference
        patterns = [
            r"\n\n+",  # Double newline (paragraph)
            r"\n(?=\s*[-*•])",  # List item
            r"\n(?=[A-Z])",  # Capitalized line (likely new paragraph)
            r"\.\s*\n",  # Sentence end with newline
        ]

        for pattern in patterns:
            match = re.search(pattern, search_text)
            if match:
                # Return the end of the match in absolute offset
                absolute_offset = search_start + match.end()
                if absolute_offset > start + self.min_chunk_size:
                    return absolute_offset

        # Fallback: split at word boundary
        search_text_forward = text[preferred_end : min(len(text), preferred_end + 500)]
        word_break = re.search(r"\s+", search_text_forward)
        if word_break:
            return preferred_end + word_break.start()

        return preferred_end

    @staticmethod
    def merge_chunks(chunks: List[DocumentChunk]) -> str:
        """
        Merge chunks back into original document.

        When processing chunks separately and wanting to reconstruct,
        this removes overlaps properly.

        Args:
            chunks: List of chunks to merge

        Returns:
            Merged text (without duplicated overlap regions)
        """
        if not chunks:
            return ""

        if len(chunks) == 1:
            return chunks[0].text

        # Build merged text with proper offset handling
        merged_parts = []
        last_end = 0

        for chunk in chunks:
            # Skip any characters already covered by the previous chunk (overlap region).
            # max(0, ...) handles the case where there is no overlap (gap between chunks).
            skip_chars = max(0, last_end - chunk.start_offset)
            merged_parts.append(chunk.text[skip_chars:])
            last_end = chunk.end_offset

        return "".join(merged_parts)

    def estimate_chunk_count(self, text: str) -> int:
        """
        Estimate number of chunks needed for a document.

        Args:
            text: Document text

        Returns:
            Estimated number of chunks
        """
        if len(text) <= self.chunk_size:
            return 1

        # Account for overlap reducing chunk count
        step_size = self.chunk_size - self.overlap
        return (len(text) + step_size - 1) // step_size


class ChunkProcessor:
    """Process documents in chunks with result aggregation."""

    def __init__(
        self,
        chunk_size: int = DocumentChunker.DEFAULT_CHUNK_SIZE,
        overlap: int = DocumentChunker.DEFAULT_OVERLAP,
    ):
        """Initialize chunk processor."""
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            overlap=overlap,
        )

    def process_chunks(
        self,
        text: str,
        process_func: callable,
        aggregate_func: Optional[callable] = None,
        progress_callback: Optional[callable] = None,
    ) -> Any:
        """
        Process document in chunks, aggregating results.

        Args:
            text: Document to process
            process_func: Function to apply to each chunk (takes chunk text, returns result)
            aggregate_func: Function to combine results from chunks
            progress_callback: Optional progress callback

        Returns:
            Aggregated result or list of per-chunk results
        """
        chunks = self.chunker.chunk_document(text, progress_callback)
        chunk_results = []

        for i, chunk in enumerate(chunks):
            # Process chunk
            result = process_func(chunk.text)
            chunk_results.append(
                {
                    "chunk_index": chunk.chunk_index,
                    "start_offset": chunk.start_offset,
                    "end_offset": chunk.end_offset,
                    "result": result,
                }
            )

        # Aggregate results if function provided
        if aggregate_func:
            return aggregate_func(chunk_results)

        return chunk_results
