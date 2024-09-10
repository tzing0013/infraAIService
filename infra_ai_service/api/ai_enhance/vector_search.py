from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from fastembed.embedding import DefaultEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import logging

router = APIRouter()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchInput(BaseModel):
    query_text: str
    top_n: int = 5
    score_threshold: float = 0.7


class SearchResult(BaseModel):
    id: str
    score: float


class SearchOutput(BaseModel):
    results: List[SearchResult]


# 初始化FastEmbed模型和Qdrant客户端
fastembed_model = DefaultEmbedding()
qdrant_client = QdrantClient(url="http://localhost:6333")
collection_name = 'test_simi'

# 检查集合是否存在，如果不存在则创建
try:
    qdrant_client.get_collection(collection_name)
    print(f"Collection {collection_name} already exists")
except HTTPException as e:
    # 获取向量维度
    sample_embedding = next(fastembed_model.embed(["Sample text"]))
    vector_size = len(sample_embedding)

    # 创建集合
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"Created collection: {collection_name}")


@router.post("/query/", response_model=SearchOutput)
async def vector_search(input_data: SearchInput):
    try:
        # 检查集合是否存在
        if not qdrant_client.get_collection(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")

        # 生成查询文本的嵌入
        query_vector = list(fastembed_model.embed([input_data.query_text]))
        if not query_vector:
            raise ValueError("Failed to generate query embedding")

        # 执行向量搜索
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector[0],
            limit=input_data.top_n,
            score_threshold=input_data.score_threshold
        )

        # 转换搜索结果为输出格式
        results = [
            SearchResult(
                id=str(result.id),
                score=result.score,
                text=result.payload.get('text', 'No text available')
            )
            for result in search_results
        ]

        return SearchOutput(results=results)
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing vector search: {str(e)}")
