import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


STRUCTURE_VERSION = "rule-v1"


@dataclass
class Chunk:
    index: int
    text: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None


def normalize_text(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    # 移除VL模型识别标记前缀（如 [VL模型识别]、[VL模型识别参考 - 用于辅助理解] 等）
    text = re.sub(r'\[VL模型识别[^\]]*\]\s*', '', text)
    # collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_chunks(text: str, max_chars: int = 1000) -> List[Chunk]:
    text = normalize_text(text)
    if not text:
        return []

    blocks = [b.strip() for b in re.split(r"\n\n+", text) if b.strip()]

    chunks: List[Chunk] = []
    cursor = 0

    def _append_chunk(chunk_text: str, start: int, end: int):
        idx = len(chunks)
        chunks.append(Chunk(index=idx, text=chunk_text, start_char=start, end_char=end))

    for block in blocks:
        start = text.find(block, cursor)
        if start == -1:
            start = cursor
        end = start + len(block)
        cursor = end

        if len(block) <= max_chars:
            _append_chunk(block, start, end)
            continue

        # Secondary split for long blocks: by sentence punctuation / newline.
        parts = re.split(r"(?<=[。！？!?；;\.])\s+|\n", block)
        buf = ""
        buf_start = start
        running = start
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if not buf:
                buf_start = running
            # add space between sentences
            candidate = (buf + " " + p).strip() if buf else p
            if len(candidate) > max_chars and buf:
                _append_chunk(buf, buf_start, buf_start + len(buf))
                buf = p
                buf_start = running
            else:
                buf = candidate
            running += len(p) + 1
        if buf:
            _append_chunk(buf, buf_start, buf_start + len(buf))

    return chunks


def _title_level_from_prefix(line: str) -> Optional[Tuple[int, str]]:
    s = line.strip()

    # Markdown headings
    m = re.match(r"^(#{1,6})\s+(.+)$", s)
    if m:
        return (len(m.group(1)), m.group(2).strip())

    # 1. / 1.1 / 1.1.1
    m = re.match(r"^(\d+(?:\.\d+){0,5})[\s、.．]+(.+)$", s)
    if m:
        level = m.group(1).count(".") + 1
        return (level, m.group(2).strip())

    # 第X章
    m = re.match(r"^第\s*(\d+)\s*章\s*(.+)$", s)
    if m:
        return (1, m.group(2).strip())

    # 一、 二、 三、
    m = re.match(r"^([一二三四五六七八九十]+)、\s*(.+)$", s)
    if m:
        return (1, m.group(2).strip())

    # （一）（二）
    m = re.match(r"^（([一二三四五六七八九十]+)）\s*(.+)$", s)
    if m:
        return (2, m.group(2).strip())

    return None


def is_likely_title(text: str) -> Optional[Tuple[int, str]]:
    # use first non-empty line
    for raw in text.splitlines():
        line = raw.strip()
        if line:
            first = line
            break
    else:
        return None

    info = _title_level_from_prefix(first)
    if not info:
        return None

    level, title = info

    # title heuristics: not too long, not ending with sentence punctuation
    if len(first) > 120:
        return None
    if re.search(r"[。！？!?]$", first):
        return None

    return (level, title)


def build_outline(chunks: List[Chunk], document_title: str = "") -> Dict[str, Any]:
    root: Dict[str, Any] = {
        "title": document_title or "文档",
        "level": 0,
        "children": [],
    }

    stack: List[Dict[str, Any]] = [root]

    for ch in chunks:
        title_info = is_likely_title(ch.text)
        if not title_info:
            continue

        level, title = title_info
        node = {
            "title": title,
            "level": level,
            "chunk_index": ch.index,
            "children": [],
        }

        while stack and stack[-1]["level"] >= level:
            stack.pop()
        parent = stack[-1] if stack else root
        parent["children"].append(node)
        stack.append(node)

    # Fallback: if no structured titles found, auto-generate sections from chunks
    if not root["children"] and chunks:
        section_size = max(3, len(chunks) // 8) or 3
        for i in range(0, len(chunks), section_size):
            group = chunks[i:i + section_size]
            first_line = group[0].text.split('\n')[0].strip()[:30]
            title = first_line if 2 <= len(first_line) <= 30 else f"第{i // section_size + 1}部分"
            root["children"].append({
                "title": title,
                "level": 1,
                "chunk_index": group[0].index,
                "children": [],
            })

    return root


def extract_knowledge_points(chunks: List[Chunk], outline: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Map chunk_index -> node_path using closest preceding outline node.
    nodes_in_order: List[Tuple[int, List[str]]] = []

    def walk(node: Dict[str, Any], path: List[str]):
        for child in node.get("children", []):
            child_path = path + [child["title"]]
            if "chunk_index" in child:
                nodes_in_order.append((child["chunk_index"], child_path))
            walk(child, child_path)

    walk(outline, [])
    nodes_in_order.sort(key=lambda x: x[0])

    def path_for_chunk(idx: int) -> List[str]:
        p: List[str] = []
        for cidx, cpath in nodes_in_order:
            if cidx <= idx:
                p = cpath
            else:
                break
        return p

    points: List[Dict[str, Any]] = []
    seen = set()

    bullet_re = re.compile(r"^\s*(?:[-*•]|\d+\)|\d+[\.、]\s*|（\d+）)\s+(.+)$")
    trigger_re = re.compile(r"^(?:定义|注意|提示|结论|优点|缺点|适用场景|定理|公式|性质|推论|引理)[:：]\s*(.+)$")
    summary_re = re.compile(r"^(?:包含以下内容|主要内容|重点内容)[:：]\s*(.*)$")

    # 数学教材专用模式
    # 定理/公式/定义声明
    theorem_re = re.compile(r"^(?:定理|定义|公理|公式|性质|推论|引理|法则|原理)\s*(\d*\.?\d*)\s*[:：]?\s*(.{4,150})")
    # 例题
    example_re = re.compile(r"^例\s*(\d+)\s*[\.．]?\s*(.{4,150})")
    # "一般地"等引出定义的句式
    definition_re = re.compile(r"^一般地[，,]?\s*(.{10,150})")
    # "如果...那么"型定理
    conditional_re = re.compile(r"^如果\s*(.{5,80}?)\s*(?:，|，)?\s*那么\s*(.{5,80})")

    def add_point(text: str, point_type: str, chunk_index: int, node_path: List[str]):
        text = re.sub(r"\s+", " ", text).strip("：:;；，,。. ")
        if not (4 <= len(text) <= 300):
            return
        key = (point_type, text)
        if key in seen:
            return
        seen.add(key)
        points.append({
            "text": text,
            "type": point_type,
            "chunk_index": chunk_index,
            "node_path": node_path,
        })

    for ch in chunks:
        node_path = path_for_chunk(ch.index)
        lines = [ln.strip() for ln in ch.text.splitlines() if ln.strip()]
        chunk_point_start = len(points)

        for ln in lines:
            m = bullet_re.match(ln)
            if m:
                add_point(m.group(1), "bullet", ch.index, node_path)

        for ln in lines:
            m = trigger_re.match(ln)
            if m:
                add_point(m.group(1), "trigger", ch.index, node_path)

        # 数学专用: 定理/定义/公式
        for ln in lines:
            m = theorem_re.match(ln)
            if m:
                label = m.group(1)
                content = m.group(2).strip()
                if label:
                    add_point(f"{label} {content}", "theorem", ch.index, node_path)
                else:
                    add_point(content, "theorem", ch.index, node_path)

        # 数学专用: 例题
        for ln in lines:
            m = example_re.match(ln)
            if m:
                num = m.group(1)
                content = m.group(2).strip()
                add_point(f"例{num}: {content}", "example", ch.index, node_path)

        # 数学专用: "一般地"引导的定义
        for ln in lines:
            m = definition_re.match(ln)
            if m:
                add_point(m.group(1), "definition", ch.index, node_path)

        # 数学专用: 条件式定理
        for ln in lines:
            m = conditional_re.match(ln)
            if m:
                add_point(f"如果{m.group(1)}，那么{m.group(2)}", "theorem", ch.index, node_path)

        for i, ln in enumerate(lines):
            m = summary_re.match(ln)
            if not m:
                continue
            trailing = m.group(1).strip()
            if trailing:
                add_point(trailing, "summary", ch.index, node_path)
            for follow in lines[i + 1:]:
                bullet_match = bullet_re.match(follow)
                if bullet_match:
                    add_point(bullet_match.group(1), "summary-item", ch.index, node_path)
                else:
                    break

        if len(points) == chunk_point_start and ch.text:
            sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*", ch.text) if s.strip()]
            if len(sentences) == 1 and 8 <= len(sentences[0]) <= 80 and not is_likely_title(sentences[0]):
                add_point(sentences[0], "sentence", ch.index, node_path)

    # Fallback: if no knowledge points found, extract key sentences from each chunk
    if not points and chunks:
        for ch in chunks[:20]:
            node_path = path_for_chunk(ch.index)
            sentences = [s.strip() for s in re.split(r"(?<=[。！？!?；;])\s*", ch.text) if s.strip()]
            for s in sentences[:3]:
                if 8 <= len(s) <= 300:
                    add_point(s, "concept", ch.index, node_path)

    return points


def build_structure(text: str, filename: str) -> Tuple[List[Chunk], Dict[str, Any], List[Dict[str, Any]]]:
    chunks = split_into_chunks(text)
    outline = build_outline(chunks, document_title=filename)
    points = extract_knowledge_points(chunks, outline)
    return chunks, outline, points


def dumps_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)
