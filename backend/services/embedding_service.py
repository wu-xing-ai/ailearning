"""Embedding service using API (OpenAI-compatible).

Supports multiple embedding providers via API:
- OpenAI (text-embedding-ada-002, text-embedding-3-small, etc.)
- Zhipu (智谱)
- SiliconFlow
- Other OpenAI-compatible APIs

No local model required - much faster Docker builds!
"""

import os
import json
import logging
import httpx
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

# 默认嵌入模型配置
DEFAULT_EMBEDDING_CONFIG = {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "api_url": "https://api.openai.com/v1",
    "api_key": "",
    "dimensions": 1536,  # 向量维度
}


class EmbeddingService:
    def __init__(self):
        self._config = self._load_config()
        self._embedding_config = self._get_embedding_config()
        self._initialized = False

    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
        return {}

    def _get_embedding_config(self) -> dict:
        """获取嵌入模型配置"""
        # 优先使用专门的 embedding 配置
        if "embedding" in self._config:
            return self._config["embedding"]

        # 否则使用主模型的 API 配置
        config = DEFAULT_EMBEDDING_CONFIG.copy()

        # 尝试从 custom_models 获取 API key
        custom_models = self._config.get("custom_models", [])
        api_keys = self._config.get("api_keys", {})

        # 优先使用智谱的 embedding（免费额度大）
        if api_keys.get("zhipu"):
            config.update({
                "provider": "zhipu",
                "model": "embedding-3",
                "api_url": "https://open.bigmodel.cn/api/paas/v4",
                "api_key": api_keys["zhipu"],
                "dimensions": 1024,
            })
        elif api_keys.get("openai"):
            config.update({
                "provider": "openai",
                "model": "text-embedding-3-small",
                "api_url": "https://api.openai.com/v1",
                "api_key": api_keys["openai"],
                "dimensions": 1536,
            })
        elif custom_models:
            # 使用第一个自定义模型的配置
            first_model = custom_models[0]
            config.update({
                "provider": "custom",
                "model": "text-embedding-3-small",
                "api_url": first_model.get("api_url", ""),
                "api_key": first_model.get("api_key", ""),
                "dimensions": 1536,
            })

        return config

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self._embedding_config.get('api_key', '')}",
            "Content-Type": "application/json",
        }

    async def _call_embedding_api(self, texts: List[str]) -> List[List[float]]:
        """调用嵌入 API"""
        api_url = self._embedding_config.get("api_url", "")
        model = self._embedding_config.get("model", "text-embedding-3-small")

        if not api_url:
            logger.warning("嵌入 API URL 未配置")
            return []

        payload = {
            "model": model,
            "input": texts,
        }

        # 某些 API 支持指定维度
        dimensions = self._embedding_config.get("dimensions")
        if dimensions and "openai" in api_url:
            payload["dimensions"] = dimensions

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{api_url}/embeddings",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # 提取嵌入向量
                embeddings = [item["embedding"] for item in data["data"]]
                return embeddings

            except httpx.HTTPStatusError as e:
                logger.error(f"嵌入 API HTTP 错误: {e.response.status_code} - {e.response.text}")
                return []
            except httpx.RequestError as e:
                logger.error(f"嵌入 API 连接错误: {str(e)}")
                return []
            except Exception as e:
                logger.error(f"嵌入 API 未知错误: {str(e)}")
                return []

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """生成单个文本的嵌入向量（同步接口，内部用异步）"""
        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = loop.run_in_executor(pool, self._run_async_embedding, [text])
                    embeddings = asyncio.get_event_loop().run_until_complete(result)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                embeddings = loop.run_until_complete(self._call_embedding_api([text]))
                loop.close()

            if embeddings:
                return embeddings[0]
            return None
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            return None

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量（同步接口，内部用异步）"""
        if not texts:
            return []

        try:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = loop.run_in_executor(pool, self._run_async_batch, texts)
                    all_embeddings = asyncio.get_event_loop().run_until_complete(result)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                all_embeddings = loop.run_until_complete(self._call_embedding_api(texts))
                loop.close()

            return all_embeddings if all_embeddings else []
        except Exception as e:
            logger.error(f"批量生成嵌入向量失败: {e}")
            return []

    def _run_async_embedding(self, texts: List[str]) -> List[List[float]]:
        """在新事件循环中运行异步嵌入"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._call_embedding_api(texts))
        finally:
            loop.close()

    def _run_async_batch(self, texts: List[str]) -> List[List[float]]:
        """在新事件循环中运行批量嵌入"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 分批处理，每批最多 100 个
            batch_size = 100
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = loop.run_until_complete(self._call_embedding_api(batch))
                if embeddings:
                    all_embeddings.extend(embeddings)
            return all_embeddings
        finally:
            loop.close()

    def index_document_chunks(self, doc_id: str, chunks: list) -> int:
        """索引文档块（存储到数据库）

        Args:
            doc_id: 文档 ID
            chunks: 文档块列表，每个块有 .index 和 .text 属性

        Returns:
            索引的块数量
        """
        if not chunks:
            return 0

        from core.database import get_db
        from models.embedding import EmbeddingVector

        db = next(get_db())
        try:
            # 删除旧的嵌入向量
            db.query(EmbeddingVector).filter(EmbeddingVector.doc_id == doc_id).delete()

            # 生成嵌入向量
            texts = [ch.text for ch in chunks]
            embeddings = self.generate_embeddings_batch(texts)

            if not embeddings:
                logger.warning(f"文档 {doc_id} 生成嵌入向量失败，跳过索引")
                return 0

            # 存储到数据库
            for i, (ch, embedding) in enumerate(zip(chunks, embeddings)):
                vector_record = EmbeddingVector(
                    id=f"{doc_id}_{ch.index}",
                    doc_id=doc_id,
                    chunk_index=ch.index,
                    text=ch.text[:500],  # 只存储前 500 字符作为预览
                    embedding=json.dumps(embedding),
                )
                db.add(vector_record)

            db.commit()
            logger.info(f"文档 {doc_id} 索引了 {len(chunks)} 个块")
            return len(chunks)

        except Exception as e:
            db.rollback()
            logger.error(f"索引文档失败: {e}")
            return 0
        finally:
            db.close()

    def search(self, query: str, top_k: int = 10, doc_ids: Optional[List[str]] = None) -> List[Dict]:
        """语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_ids: 可选的文档 ID 过滤

        Returns:
            搜索结果列表
        """
        from core.database import get_db
        from models.embedding import EmbeddingVector
        import numpy as np

        try:
            # 生成查询向量
            query_embedding = self.generate_embedding(query)
            if query_embedding is None:
                logger.warning("生成查询向量失败，返回空结果")
                return []
            query_embedding = np.array(query_embedding)

            db = next(get_db())
            try:
                # 构建查询
                q = db.query(EmbeddingVector)
                if doc_ids:
                    q = q.filter(EmbeddingVector.doc_id.in_(doc_ids))

                vectors = q.all()

                if not vectors:
                    return []

                # 计算余弦相似度
                results = []
                for v in vectors:
                    vec = np.array(json.loads(v.embedding))
                    # 余弦相似度
                    similarity = np.dot(query_embedding, vec) / (np.linalg.norm(query_embedding) * np.linalg.norm(vec))

                    results.append({
                        "chunk_id": v.id,
                        "doc_id": v.doc_id,
                        "chunk_index": v.chunk_index,
                        "text": v.text,
                        "score": float(similarity),
                    })

                # 按相似度排序
                results.sort(key=lambda x: x["score"], reverse=True)
                return results[:top_k]
            finally:
                db.close()

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []

    def delete_document(self, doc_id: str):
        """删除文档的嵌入向量"""
        from core.database import get_db
        from models.embedding import EmbeddingVector

        db = next(get_db())
        try:
            db.query(EmbeddingVector).filter(EmbeddingVector.doc_id == doc_id).delete()
            db.commit()
        except Exception as e:
            logger.error(f"删除文档嵌入失败: {e}")
        finally:
            db.close()

    def get_stats(self) -> Dict:
        """获取嵌入服务状态"""
        from core.database import get_db
        from models.embedding import EmbeddingVector

        try:
            db = next(get_db())
            count = db.query(EmbeddingVector).count()
            db.close()

            return {
                "model_name": self._embedding_config.get("model", "未配置"),
                "provider": self._embedding_config.get("provider", "未配置"),
                "collection_count": count,
                "status": "ready" if self._embedding_config.get("api_key") else "未配置 API Key",
            }
        except Exception as e:
            return {
                "model_name": self._embedding_config.get("model", "未配置"),
                "provider": self._embedding_config.get("provider", "未配置"),
                "collection_count": 0,
                "status": f"unavailable: {str(e)}",
            }


# 全局单例
embedding_service = EmbeddingService()
