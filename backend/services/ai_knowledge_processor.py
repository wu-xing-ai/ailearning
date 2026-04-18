"""AI-powered knowledge structuring service.

Uses LLM to generate outlines and extract knowledge points,
falling back to rule-based processing when AI is unavailable.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from services.knowledge_processor import Chunk, split_into_chunks, dumps_json
from services.prompts import OUTLINE_GENERATION_PROMPT, KNOWLEDGE_POINT_EXTRACTION_PROMPT

STRUCTURE_VERSION_AI = "ai-v1"
PROMPT_VERSION = "v1"


def _clean_json_response(text: str) -> str:
    """Extract JSON from LLM response, handling various formatting issues."""
    if not text:
        return text
    # Remove markdown code block markers
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    # Find matching brackets using a simple stack approach
    start_char = None
    start_idx = -1
    for i, ch in enumerate(text):
        if ch in ("{", "["):
            start_char = ch
            start_idx = i
            break
    if start_idx == -1:
        return text

    end_char = "}" if start_char == "{" else "]"
    # Find the last matching closing bracket
    depth = 0
    last_end = -1
    for i in range(start_idx, len(text)):
        if text[i] == start_char:
            depth += 1
        elif text[i] == end_char:
            depth -= 1
            if depth == 0:
                last_end = i
                break
    if last_end == -1:
        # No matching close bracket, try finding the last one
        last_end = text.rfind(end_char)
        if last_end <= start_idx:
            return text

    extracted = text[start_idx : last_end + 1]

    # Fix common JSON issues from LLM output
    # Remove trailing commas before } or ]
    extracted = re.sub(r",\s*([}\]])", r"\1", extracted)
    # Remove control characters except newline/tab
    extracted = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", extracted)

    return extracted


def _safe_json_loads(text: str):
    """Try to parse JSON with multiple fallback strategies."""
    # First try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try fixing unquoted values
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting with regex for object
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except (json.JSONDecodeError, ValueError):
            pass

    # Try extracting with regex for array
    m = re.search(r"\[[\s\S]*\]", text)
    if m:
        try:
            return json.loads(m.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return None


async def generate_ai_outline(
    ai_service,
    text: str,
    filename: str,
    max_chunk_chars: int = 4000,
) -> Dict[str, Any]:
    """Call LLM to generate a structured outline from document text.

    For long documents, uses the first portion to generate outline.
    """
    content = text[:max_chunk_chars]
    if len(text) > max_chunk_chars:
        content += "\n\n...(文档内容较长，已截断)..."

    prompt = OUTLINE_GENERATION_PROMPT.replace("{content}", content)
    response = await ai_service.chat_completion(prompt, stream=False)

    if isinstance(response, dict) and "response" in response:
        raw = response["response"]
    else:
        raw = str(response)

    cleaned = _clean_json_response(raw)
    outline = _safe_json_loads(cleaned)

    if outline is None or not isinstance(outline, dict):
        outline = {}

    # Ensure minimum structure
    if "title" not in outline:
        outline["title"] = filename or "文档"
    if "level" not in outline:
        outline["level"] = 0
    if "children" not in outline:
        outline["children"] = []

    # If outline has no children, try to build from document structure
    if not outline["children"] and text.strip():
        chunks = split_into_chunks(text)
        if len(chunks) > 0:
            # Group chunks into sections (every 3-5 chunks become one section)
            section_size = max(3, len(chunks) // 8) or 3
            for i in range(0, len(chunks), section_size):
                group = chunks[i:i + section_size]
                first_line = group[0].text.split('\n')[0].strip()[:30]
                title = first_line if 2 <= len(first_line) <= 30 else f"第{i // section_size + 1}部分"
                outline["children"].append({
                    "title": title,
                    "level": 1,
                    "chunk_index": group[0].index,
                    "children": [],
                })

    return outline


async def extract_ai_knowledge_points(
    ai_service,
    text: str,
    outline: Dict[str, Any],
    max_chunk_chars: int = 5000,
) -> List[Dict[str, Any]]:
    """Call LLM to extract knowledge points from document text."""
    outline_str = json.dumps(outline, ensure_ascii=False, indent=2)[:2000]
    content = text[:max_chunk_chars]
    if len(text) > max_chunk_chars:
        content += "\n\n...(文档内容较长，已截断)..."

    prompt = KNOWLEDGE_POINT_EXTRACTION_PROMPT.replace("{outline}", outline_str).replace("{content}", content)
    response = await ai_service.chat_completion(prompt, stream=False)

    if isinstance(response, dict) and "response" in response:
        raw = response["response"]
    else:
        raw = str(response)

    cleaned = _clean_json_response(raw)
    points = _safe_json_loads(cleaned)

    if points is None or not isinstance(points, list):
        points = []

    # Normalize each point
    normalized = []
    for p in points:
        if not isinstance(p, dict) or "text" not in p:
            continue
        normalized.append({
            "text": str(p.get("text", ""))[:500],
            "type": p.get("type", "bullet"),
            "chunk_index": p.get("chunk_index", 0),
            "node_path": p.get("node_path", []),
            "importance": max(1, min(5, int(float(p.get("importance", 3))))),
            "summary": str(p.get("summary", ""))[:200] if p.get("summary") else None,
            "related_concepts": p.get("related_concepts", []),
        })

    # Fallback: if AI returned no points, extract from chunks using simple heuristics
    if not normalized and text.strip():
        chunks = split_into_chunks(text)
        for ch in chunks[:20]:
            sentences = [s.strip() for s in re.split(r"(?<=[。！？!?；;])\s*", ch.text) if s.strip()]
            for s in sentences[:3]:
                if 8 <= len(s) <= 200:
                    # Find node_path from outline
                    node_path = _find_node_path_for_chunk(outline, ch.index)
                    normalized.append({
                        "text": s,
                        "type": "concept",
                        "chunk_index": ch.index,
                        "node_path": node_path,
                        "importance": 3,
                        "summary": None,
                        "related_concepts": [],
                    })

    return normalized


async def build_ai_structure(
    ai_service,
    text: str,
    filename: str,
) -> Tuple[List[Chunk], Dict[str, Any], List[Dict[str, Any]]]:
    """Full AI structuring pipeline.

    Chunking remains rule-based for stability; outline and knowledge points
    are generated by the LLM.
    """
    chunks = split_into_chunks(text)
    outline = await generate_ai_outline(ai_service, text, filename)
    points = await extract_ai_knowledge_points(ai_service, text, outline)

    # Map points to chunk indices using node_path
    _assign_chunk_indices(points, chunks, outline)

    return chunks, outline, points


def _assign_chunk_indices(
    points: List[Dict[str, Any]],
    chunks: List[Chunk],
    outline: Dict[str, Any],
):
    """Best-effort assignment of chunk_index to AI-extracted knowledge points."""
    for point in points:
        if "chunk_index" in point and point["chunk_index"]:
            continue
        # Find chunk whose text best matches the knowledge point
        best_idx = 0
        best_overlap = 0
        pt_text = point.get("text", "").lower()
        for ch in chunks:
            overlap = len(set(pt_text) & set(ch.text.lower()))
            if overlap > best_overlap:
                best_overlap = overlap
                best_idx = ch.index
        point["chunk_index"] = best_idx


def _find_node_path_for_chunk(outline: Dict[str, Any], chunk_index: int) -> List[str]:
    """Find the outline node path that best matches a chunk index."""
    nodes_in_order: List[Tuple[int, List[str]]] = []

    def walk(node: Dict[str, Any], path: List[str]):
        for child in node.get("children", []):
            child_path = path + [child["title"]]
            if "chunk_index" in child:
                nodes_in_order.append((child["chunk_index"], child_path))
            walk(child, child_path)

    walk(outline, [])
    nodes_in_order.sort(key=lambda x: x[0])

    result: List[str] = []
    for cidx, cpath in nodes_in_order:
        if cidx <= chunk_index:
            result = cpath
        else:
            break
    return result
