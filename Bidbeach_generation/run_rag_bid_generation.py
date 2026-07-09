import os
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

# ================= ⚙️ 配置区域 =================

# 请确保 Xinference (Qwen3) 正在运行
API_BASE = "http://127.0.0.1:9997/v1"
API_KEY = "empty"
MODEL_NAME = "qwen3"

# 数据路径
INPUT_DIR = "bidbench_data_output/cleaned_data/texts"
OUTPUT_DIR = "bidbench_data_output/generated_bids_rag"
DB_PATH = "bidbench_data_output/chroma_db"

os.makedirs(OUTPUT_DIR, exist_ok=True)
client = OpenAI(base_url=API_BASE, api_key=API_KEY)

# ================= 📚 模拟企业核心资产 (知识库素材) =================
# 真实场景下，这些通常是公司过去几年的中标通知书或案例 Word 文档
COMPANY_ASSETS = [
    {
        "id": "case_prison_001",
        "content": "【标杆案例】2023年某省监狱管理局智慧安防一体化项目。中标金额：5000万元。技术亮点：我司采用自研的'鹰眼'AI视觉分析系统，实现了监区无死角监控，误报率降低90%，获得了司法部'智慧监狱示范单位'荣誉称号。"
    },
    {
        "id": "case_hospital_002",
        "content": "【标杆案例】某市中心医院互联互通四级甲等测评改造项目。中标金额：1200万元。技术亮点：构建了全院级CDR临床数据中心，打通了HIS、EMR、LIS等30多个异构系统，帮助医院顺利通过国家互联互通四甲评审。"
    },
    {
        "id": "case_school_003",
        "content": "【标杆案例】某职业技术学院智慧校园双优建设项目。中标金额：800万元。技术亮点：建设了统一身份认证与数据中台，实现了全校师生'刷脸入校'与'一网通办'。"
    },
    {
        "id": "cert_001",
        "content": "【资质证书】我司拥有 CMMI5 软件成熟度认证、ITSS 二级运维服务资质、涉密信息系统集成甲级资质，是国家高新技术企业。"
    }
]


# ================= 🛠️ RAG 核心逻辑 =================

def build_knowledge_base():
    """1. 建库：把公司资产向量化存储"""
    print("🏗️ 正在构建企业知识库 (ChromaDB)...")
    chroma_client = chromadb.PersistentClient(path=DB_PATH)

    # 使用轻量级 Embedding 模型
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # 为了演示，每次重置集合
    try:
        chroma_client.delete_collection("company_assets")
    except:
        pass

    collection = chroma_client.create_collection(name="company_assets", embedding_function=emb_fn)

    collection.add(
        documents=[doc["content"] for doc in COMPANY_ASSETS],
        ids=[doc["id"] for doc in COMPANY_ASSETS]
    )
    print(f"✅ 已注入 {len(COMPANY_ASSETS)} 条核心资历数据。")
    return collection


def retrieve_evidence(collection, bid_content):
    """2. 检索：根据标书内容，找最相关的公司案例"""
    # 截取标书前 500 字作为搜索线索
    query = bid_content[:500]

    results = collection.query(
        query_texts=[query],
        n_results=1  # 找最匹配的1个案例
    )

    if results['documents'][0]:
        best_match = results['documents'][0][0]
        print(f"   💡 [联想] 发现相关案例: {best_match[:30]}...")
        return best_match
    return "暂无相关案例"


def generate_capability_chapter(filename, bid_content, evidence):
    """3. 生成：基于案例证据，写'能力综述'章节"""
    print(f"   ✍️ [撰写] 正在生成《投标人能力分析》...")

    system_prompt = "你是一位资深的投标经理。请根据【招标文件需求】和【我司过往案例】，撰写一段极具说服力的《投标人能力综述》。"
    user_prompt = f"""
    请为项目《{filename}》撰写【第三章：投标人资格与能力分析】。

    【招标文件需求摘要】
    {bid_content[:1500]}
    ...

    【我司核心优势素材 (RAG检索结果)】
    {evidence}

    【写作要求】
    1. **逻辑闭环**：论述“因为我们做过类似项目（引用素材），所以我们最懂这个项目”。
    2. **数据说话**：必须在文中显式引用素材中的金额、奖项或技术指标。
    3. **排版**：使用 Markdown，包含“总体优势”、“类似业绩描述”、“技术保障”三个小标题。

    请直接输出正文。
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content


# ================= 🚀 主程序 =================

if __name__ == "__main__":
    # 1. 初始化知识库
    kb = build_knowledge_base()

    # 2. 遍历之前清洗好的标书文本
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]

    # 过滤：只跑刚才成功的几个典型案例（监狱、医院），展示 RAG 效果
    target_keywords = ["监狱", "医院", "医疗"]

    print(f"\n🚀 开始 RAG 增强生成 (匹配关键词: {target_keywords})...\n")

    for fname in files:
        if not any(k in fname for k in target_keywords):
            continue

        print(f"📄 处理标书: {fname}")
        with open(os.path.join(INPUT_DIR, fname), 'r', encoding='utf-8') as f:
            content = f.read()

        # A. 检索 (Retrieve)
        evidence = retrieve_evidence(kb, content)

        # B. 生成 (Generate)
        chapter = generate_capability_chapter(fname, content, evidence)

        # C. 保存
        save_path = os.path.join(OUTPUT_DIR, f"RAG能力篇_{fname.replace('.txt', '.md')}")
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"# 自动生成的《投标人能力分析》\n\n")
            f.write(f"> **💡 检索到的证据**：\n> {evidence}\n\n---\n\n")
            f.write(chapter)

        print(f"   ✅ 已生成章节: {save_path}\n")