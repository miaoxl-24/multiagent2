"""Redis 数据库查询工具"""
import redis
import json

class RedisQuery:
    def __init__(self, url="redis://localhost:6379"):
        self.client = redis.from_url(url)
    
    def test_connection(self):
        """测试连接"""
        try:
            return self.client.ping()
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def get_hash_info(self, hash_name="poi_data"):
        """获取 Hash 信息"""
        count = self.client.hlen(hash_name)
        print(f"Hash '{hash_name}' 包含 {count} 条数据")
        return count
    
    def get_hash_items(self, hash_name="poi_data", limit=10):
        """获取 Hash 中的数据"""
        items = []
        count = min(limit, self.client.hlen(hash_name))
        
        for i in range(count):
            item = self.client.hget(hash_name, str(i))
            if item:
                try:
                    data = json.loads(item.decode('utf-8'))
                    items.append(data)
                except:
                    items.append(item.decode('utf-8'))
        
        return items
    
    def search_by_keyword(self, hash_name="poi_data", keyword=""):
        """按关键词搜索"""
        results = []
        count = self.client.hlen(hash_name)
        
        for i in range(count):
            item = self.client.hget(hash_name, str(i))
            if item:
                content = item.decode('utf-8')
                if keyword.lower() in content.lower():
                    try:
                        data = json.loads(content)
                        results.append(data)
                    except:
                        results.append(content)
        
        return results


if __name__ == "__main__":
    query = RedisQuery()
    
    if query.test_connection():
        print("Redis 连接成功!\n")
        
        # 获取数据统计
        query.get_hash_info()
        
        # 查询前5条数据
        print("\n前5条数据:")
        items = query.get_hash_items(limit=5)
        for i, item in enumerate(items):
            print(f"\n第{i}条:")
            if isinstance(item, dict):
                for key, value in item.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {item}")
        
        # 搜索功能
        keyword = input("\n输入关键词搜索（回车跳过）: ")
        if keyword.strip():
            results = query.search_by_keyword(keyword=keyword)
            print(f"\n找到 {len(results)} 条匹配结果:")
            for i, result in enumerate(results[:5]):  # 最多显示5条
                print(f"\n匹配 {i+1}:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {result}")
    else:
        print("Redis 连接失败，请检查服务是否运行")