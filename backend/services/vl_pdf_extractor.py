"""
视觉模型PDF提取服务 - 使用VL模型识别PDF页面内容

通过将PDF页面渲染为图片，发送给视觉语言模型进行文字识别，
解决PDF字体编码导致的乱码问题，以及扫描版PDF无法提取文字的问题。
"""
import base64
import logging
import time

import fitz  # PyMuPDF

from core.app_config import get_vl_config

logger = logging.getLogger(__name__)

# 识别prompt
EXTRACT_PROMPT = (
    "请完整准确地识别这一页PDF中的所有文字内容。"
    "要求：\n"
    "1. 逐字逐句还原原文，不要遗漏任何内容\n"
    "2. 数学公式用 LaTeX 格式书写（如 $x^2+y^2=1$）\n"
    "3. 保留原文的段落结构\n"
    "4. 如果有图注、表格标题也要识别\n"
    "只输出识别的文字，不要添加任何解释。"
)


def _render_page_to_base64(doc: fitz.Document, page_index: int, dpi: int = 150) -> str:
    """将PDF指定页面渲染为base64编码的PNG图片（复用已打开的doc）"""
    if page_index >= len(doc):
        page_index = len(doc) - 1
    page = doc[page_index]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    return base64.b64encode(img_bytes).decode("utf-8")


def _call_vl_model(image_base64: str, prompt: str) -> str:
    """调用视觉语言模型API"""
    import httpx

    cfg = get_vl_config()

    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=120) as client:
        resp = client.post(cfg["api_url"], json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def extract_pdf_with_vl(pdf_bytes: bytes) -> str:
    """使用视觉模型提取PDF中间页（从bytes）

    策略：提取中间一页，用于辅助生成知识点或增强乱码内容。
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        total_pages = len(doc)
        if total_pages == 0:
            return ""

        sample_page = total_pages // 2
        logger.info(f"VL提取: PDF共{total_pages}页，提取第{sample_page + 1}页")
        image_b64 = _render_page_to_base64(doc, sample_page)
        result = _call_vl_model(image_b64, EXTRACT_PROMPT)
        logger.info(f"VL提取完成，长度: {len(result)}")
        return result
    except Exception as e:
        logger.warning(f"VL提取失败，跳过: {e}")
        return ""
    finally:
        doc.close()


def extract_scanned_pdf_with_vl(pdf_bytes: bytes) -> str:
    """对扫描版PDF使用VL模型提取内容（从bytes）

    策略：均匀选取5个页面进行识别。
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        total_pages = len(doc)
        if total_pages == 0:
            return ""

        start_page = 3
        end_page = total_pages - 1
        num_samples = min(5, end_page - start_page + 1)

        if num_samples <= 0:
            return ""

        step = (end_page - start_page) / max(num_samples - 1, 1)
        page_indices = sorted(set(int(start_page + i * step) for i in range(num_samples)))

        all_text = []
        for idx in page_indices:
            try:
                logger.info(f"VL扫描提取: 第{idx + 1}页/{total_pages}页")
                image_b64 = _render_page_to_base64(doc, idx)
                text = _call_vl_model(image_b64, EXTRACT_PROMPT)
                if text.strip():
                    all_text.append(f"--- 第{idx + 1}页 ---\n{text}")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"VL第{idx + 1}页提取失败: {e}")
                continue

        result = "\n\n".join(all_text)
        logger.info(f"VL扫描提取完成，共{len(page_indices)}页，总长度: {len(result)}")
        return result
    finally:
        doc.close()


def extract_pdf_with_vl_from_path(file_path: str) -> str:
    """从文件路径提取PDF中间页（直接打开文件，不读入内存）"""
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        if total_pages == 0:
            return ""

        sample_page = total_pages // 2
        logger.info(f"VL提取(path): PDF共{total_pages}页，提取第{sample_page + 1}页")
        image_b64 = _render_page_to_base64(doc, sample_page)
        result = _call_vl_model(image_b64, EXTRACT_PROMPT)
        logger.info(f"VL提取完成，长度: {len(result)}")
        return result
    except Exception as e:
        logger.warning(f"VL提取失败，跳过: {e}")
        return ""
    finally:
        doc.close()


def extract_scanned_pdf_with_vl_from_path(file_path: str) -> str:
    """从文件路径提取扫描版PDF（直接打开文件，不读入内存）"""
    doc = fitz.open(file_path)
    try:
        total_pages = len(doc)
        if total_pages == 0:
            return ""

        start_page = 3
        end_page = total_pages - 1
        num_samples = min(5, end_page - start_page + 1)

        if num_samples <= 0:
            return ""

        step = (end_page - start_page) / max(num_samples - 1, 1)
        page_indices = sorted(set(int(start_page + i * step) for i in range(num_samples)))

        all_text = []
        for idx in page_indices:
            try:
                logger.info(f"VL扫描提取(path): 第{idx + 1}页/{total_pages}页")
                image_b64 = _render_page_to_base64(doc, idx)
                text = _call_vl_model(image_b64, EXTRACT_PROMPT)
                if text.strip():
                    all_text.append(f"--- 第{idx + 1}页 ---\n{text}")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"VL第{idx + 1}页提取失败: {e}")
                continue

        result = "\n\n".join(all_text)
        logger.info(f"VL扫描提取完成，共{len(page_indices)}页，总长度: {len(result)}")
        return result
    finally:
        doc.close()
