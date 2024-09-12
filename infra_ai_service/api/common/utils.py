from fastapi import HTTPException
from fastembed.embedding import DefaultEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


def setup_qdrant_environment():
    # 初始化FastEmbed模型和Qdrant客户端
    fastembed_model = DefaultEmbedding()
    qdrant_client = QdrantClient(url="http://localhost:6333")
    collection_name = 'test_simi'

    # 检查集合是否存在，如果不存在则创建
    try:
        qdrant_client.get_collection(collection_name)
        print(f"Collection {collection_name} already exists")
    except Exception as e:
        # 获取向量维度
        sample_embedding = next(fastembed_model.embed(["Sample text"]))
        vector_size = len(sample_embedding)

        # 创建集合
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size,
                                        distance=Distance.COSINE),
        )
        print(f"Created collection: {collection_name}")
    return fastembed_model, qdrant_client, collection_name
