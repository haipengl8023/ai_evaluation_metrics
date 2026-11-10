import chromadb
from chromadb.utils import embedding_functions
import os

# ================= ⚙️ 配置区域 =================

# 我们用一个轻量级的本地向量库
DB_PATH = "bidbench_data_output/chroma_db"

# 模拟公司的“核心资产”文档 (真实场景下这里是几百个 Word/PDF)
COMPANY_DOCS = [
    {
        "id": "intro_001",
        "category": "公司简介",
        "content": "AI智能投标有限公司成立于2020年，专注于政府数字化转型领域。公司拥有CMMI5认证，员工300余人，总部位于北京中关村。"
    },
    {
        "id": "case_001",
        "category": "成功案例",
        "content": "【标杆案例】2023年某省监狱管理局智慧安防项目。中标金额5000万。我司通过AI视觉技术实现了监区无死角监控，获得了司法部表彰。"
    },
    {
        "id": "case_002",
        "category": "成功案例",
        "content": "【标杆案例】某市人民医院医疗大数据平台。中标金额1200万。构建了全院级数据湖，实现了电子病历互联互通四级甲等评审通过。"
    },
    {
        "id": "tech_001",
        "category": "技术方案",
        "content": "我司独创的'鹰眼'数据清洗引擎，能够支持PB级数据的实时处理，准确率高达99.9%，在并发性能上优于传统ETL工具3倍。"
    }
]


# ================= 🛠️ 建库与检索逻辑 =================

def build_knowledge_base():
    print("🏗️ 正在构建企业知识库 (Vector Database)...")

    # 1. 初始化 ChromaDB (持久化存储)
    client = chromadb.PersistentClient(path=DB_PATH)

    # 2. 使用开源的中文 Embedding 模型 (会自动下载)
    # 如果下载慢，也可以换成 OpenAI 的 text-embedding-3-small
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"  # 这里用个小的英文/多语言模型演示，生产环境建议用 'm3e-base'
    )

    # 3. 创建集合 (Collection)
    # 如果存在先删除，保证每次运行都是新的
    try:
        client.delete_collection(name="company_assets")
    except:
        pass

    collection = client.create_collection(
        name="company_assets",
        embedding_function=emb_fn
    )

    # 4. 写入数据
    print(f"📥 正在写入 {len(COMPANY_DOCS)} 条核心资产数据...")
    collection.add(
        documents=[doc["content"] for doc in COMPANY_DOCS],
        metadatas=[{"category": doc["category"]} for doc in COMPANY_DOCS],
        ids=[doc["id"] for doc in COMPANY_DOCS]
    )

    print("✅ 知识库构建完成！")
    return collection


def search_similar_case(collection, query_text):
    """
    RAG 的核心：根据标书需求，去库里找“最像的案例”
    """
    print(f"\n🔍 正在检索关键词: '{query_text}' ...")

    results = collection.query(
        query_texts=[query_text],
        n_results=1  # 只找最匹配的1个
    )

    best_match = results['documents'][0][0]
    print(f"💡 检索到的最佳素材: \n   👉 {best_match}")
    return best_match


# ================= 🚀 测试主程序 =================

if __name__ == "__main__":
    # 1. 建库
    kb = build_knowledge_base()

    # 2. 模拟实战场景：
    # 场景 A: 我们正在写那个“山西省监狱”的标书
    # AI 需要知道：我们以前做没做过监狱的项目？
    print("-" * 50)
    print("场景演示 A: 正在撰写《山西省监狱系统采购》标书...")
    retrieved_content = search_similar_case(kb, "监狱管理局 智慧安防 司法部")

    # 场景 B: 我们正在写那个“人民医院”的标书
    # AI 需要知道：我们有没有医疗大数据的经验？
    print("-" * 50)
    print("场景演示 B: 正在撰写《人民医院医疗设备》标书...")
    retrieved_content = search_similar_case(kb, "医院 大数据平台 电子病历")

    print("\n✅ RAG 检索测试通过！下一步可以把这个素材喂给 Qwen3 写正文了。")