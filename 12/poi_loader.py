import os
import csv
import json
import redis
from typing import List, Dict, Any
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore


class POILoader:
    """POI 数据加载器 - 负责将数据集导入到 Redis 数据库"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = redis.from_url(redis_url)

    def test_connection(self) -> bool:
        """测试 Redis 连接"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            print(f"Redis 连接失败: {e}")
            return False

    def load_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """加载 CSV 文件"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(dict(row))
            print(f"成功加载 CSV 文件: {file_path}, 共 {len(data)} 条记录")
        except Exception as e:
            print(f"加载 CSV 文件失败: {e}")
        return data

    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """加载 JSON 文件"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                try:
                    data = json.loads(content)
                except:
                    lines = content.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            data.append(json.loads(line))
            print(f"成功加载 JSON 文件: {file_path}, 共 {len(data)} 条记录")
        except Exception as e:
            print(f"加载 JSON 文件失败: {e}")
        return data

    def load_data_from_directory(self, directory: str) -> List[Dict[str, Any]]:
        """从目录加载所有数据文件"""
        all_data = []

        if not os.path.exists(directory):
            print(f"目录不存在: {directory}")
            return all_data

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if filename.endswith('.csv'):
                all_data.extend(self.load_csv_file(file_path))
            elif filename.endswith('.json'):
                all_data.extend(self.load_json_file(file_path))
            elif filename.endswith('.txt'):
                all_data.extend(self.load_json_file(file_path))

        print(f"总共加载了 {len(all_data)} 条 POI 记录")
        return all_data

    def save_to_redis_hash(self, data: List[Dict[str, Any]], hash_name: str = "poi_data"):
        """将数据保存为 Redis Hash"""
        try:
            self.redis_client.delete(hash_name)

            for i, item in enumerate(data):
                self.redis_client.hset(hash_name, str(i), json.dumps(item, ensure_ascii=False))

            print(f"成功将 {len(data)} 条记录保存到 Redis Hash: {hash_name}")
        except Exception as e:
            print(f"保存到 Redis Hash 失败: {e}")

    def save_to_vector_store(self, data: List[Dict[str, Any]], index_name: str = "poi"):
        """将数据保存到 Redis 向量数据库（使用 HuggingFace 免费模型）"""
        try:
            embedding_model = HuggingFaceBgeEmbeddings(
                model_name="BAAI/bge-small-zh-v1.5",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

            config = RedisConfig(
                index_name=index_name,
                redis_url=self.redis_url
            )

            vector_store = RedisVectorStore(embedding_model, config=config)

            texts = []
            metadatas = []

            for item in data:
                text_parts = []
                if 'name' in item:
                    text_parts.append(f"名称: {item['name']}")
                if 'address' in item:
                    text_parts.append(f"地址: {item['address']}")
                if 'description' in item:
                    text_parts.append(f"描述: {item['description']}")
                if 'category' in item:
                    text_parts.append(f"分类: {item['category']}")

                texts.append(" ".join(text_parts))
                metadatas.append(item)

            vector_store.add_texts(texts, metadatas=metadatas)
            print(f"成功将 {len(data)} 条记录保存到 Redis 向量数据库: {index_name}")

        except Exception as e:
            print(f"保存到向量数据库失败: {e}")
            print("提示：向量数据库导入失败不影响 Redis Hash 的数据导入")

    def load_and_import(self, data_path: str):
        """完整的加载和导入流程"""
        print("=" * 50)
        print("POI 数据导入器")
        print("=" * 50)

        if not self.test_connection():
            print("Redis 连接失败，请检查 Redis 服务是否运行")
            return

        print("Redis 连接成功")

        print(f"\n正在从 {data_path} 加载数据...")
        if os.path.isfile(data_path):
            if data_path.endswith('.csv'):
                data = self.load_csv_file(data_path)
            else:
                data = self.load_json_file(data_path)
        elif os.path.isdir(data_path):
            data = self.load_data_from_directory(data_path)
        else:
            print(f"数据路径不存在: {data_path}")
            return

        if not data:
            print("没有加载到任何数据")
            return

        print("\n正在保存到 Redis Hash...")
        self.save_to_redis_hash(data)

        print("\n正在保存到 Redis 向量数据库...")
        self.save_to_vector_store(data)

        print("\n" + "=" * 50)
        print("数据导入完成!")
        print("=" * 50)


if __name__ == "__main__":
    loader = POILoader()

    data_path = r"C:\Users\Lenovo\couplet_samll"

    loader.load_and_import(data_path)