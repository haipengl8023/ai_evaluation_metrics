import os
import json
from openai import OpenAI
import re

# ================= ⚙️ 配置区域 =================

# 1. 选择你的模型
# 选项 A: 本地 Qwen3 (确保 Xinference 已启动)
# API_BASE = "http://127.0.0.1:9997/v1"
# API_KEY = "empty"
# MODEL_NAME = "qwen3"

# 选项 B: 云端 DeepSeek (如果你想对比效果，可以切换这个)
API_BASE = "https://api.deepseek.com"
API_KEY = "sk-e46c756f39e44fdd8899fa68cd472fda"
MODEL_NAME = "deepseek-chat"

# 2. 数据路径 (刚才清洗好的文本目录)
TEXT_DATA_DIR = "/Bidbeach_generation/bidbench_data_output/cleaned_data/texts"

# ================= 🏃 核心逻辑 =================

client = OpenAI(base_url=API_BASE, api_key=API_KEY)


def load_text_files(directory):
    """读取目录下所有的 .txt 文件"""
    texts = {}
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return texts

    for f in os.listdir(directory):
        if f.endswith(".txt"):
            path = os.path.join(directory, f)
            with open(path, "r", encoding="utf-8") as file:
                texts[f] = file.read()
    return texts


def extract_key_info(filename, content):
    """让大模型提取关键信息 (修复版)"""
    print(f"🤖 正在阅读标书: {filename}...")

    # 定义提示词 (Prompt Engineering)
    system_prompt = """
    你是一位专业的投标专员。你的任务是从招标文件中精准提取关键信息。
    请直接输出 JSON 格式，不要包含Markdown标记或多余废话。
    如果文中未提及某项信息，请填 "N/A"。
    """

    user_prompt = f"""
    请从以下招标公告文本中提取这 4 个关键字段：
    1. project_name (项目名称)
    2. budget (预算金额/最高限价, 保留单位如'万元')
    3. deadline (投标截止时间/开标时间, 精确到分钟)
    4. purchaser (采购单位名称)

    【招标文本开始】
    {content[:3000]} 
    【招标文本结束】
    (注：为了节省Token，只截取了前3000字，通常关键信息都在开头)
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}],  # 保持不变
            temperature=0.1,
        )
        raw_content = response.choices[0].message.content

        # === 核心修复：清洗 JSON ===
        # 1. 去除 <think> 标签及其内容
        clean_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL)

        # 2. 提取第一个 { ... } 包裹的内容
        match = re.search(r"\{.*\}", clean_content, re.DOTALL)
        if match:
            return match.group(0)
        else:
            return raw_content  # 如果没找到大括号，就返回原始内容供调试

    except Exception as e:
        return f"{{'error': '{str(e)}'}}"


# ================= 🚀 主程序 =================

if __name__ == "__main__":
    print(f"🚀 启动智能拆标评测 (模型: {MODEL_NAME})\n")

    # 1. 加载数据
    data_map = load_text_files(TEXT_DATA_DIR)
    if not data_map:
        print("⚠️ 没有找到文本文件，请先运行 run_data_cleaning.py")
        exit()

    print(f"📂 加载了 {len(data_map)} 份标书文本")

    # 2. 循环提取
    results = []
    for fname, text in data_map.items():
        # 调用大模型
        json_str = extract_key_info(fname, text)

        # 解析并打印结果
        try:
            info = json.loads(json_str)
            print(f"\n📄 文件: {fname}")
            print(f"   📌 项目名称: {info.get('project_name')}")
            print(f"   💰 预算金额: {info.get('budget')}")
            print(f"   ⏰ 截止时间: {info.get('deadline')}")
            print(f"   🏢 采购单位: {info.get('purchaser')}")
            print("-" * 40)
        except:
            print(f"\n📄 文件: {fname}")
            print(f"   ❌ JSON 解析失败，原始输出: {json_str}")

    print("\n✅ 评测完成。")