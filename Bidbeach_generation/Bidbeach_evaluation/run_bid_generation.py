import os
import json
import re
from openai import OpenAI

# ================= ⚙️ 配置区域 =================

# 1. 本地模型配置 (Xinference - Qwen3)
API_BASE = "http://127.0.0.1:9997/v1"
API_KEY = "empty"
MODEL_NAME = "qwen3"

# 2. 路径配置
INPUT_DIR = "/bidbench_data_output/cleaned_data/texts"  # 输入：清洗后的文本
OUTPUT_DIR = "/bidbench_data_output/generated_bids"  # 输出：生成的投标函

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = OpenAI(base_url=API_BASE, api_key=API_KEY)


# ================= 🛠️ 工具函数 =================

def clean_llm_json(raw_text):
    """
    [关键修复] 清洗 LLM 输出，去除 <think> 标签，只保留 JSON 部分
    """
    # 1. 去除 <think>...</think> 思考过程
    text_no_think = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)

    # 2. 使用正则提取第一个 { ... } 代码块
    match = re.search(r"\{.*\}", text_no_think, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return "{}"  # 提取失败返回空字典


def step1_extract_info(filename, content):
    """步骤一：提取撰写投标函所需的 4 个关键变量"""
    print(f"   🔍 [Step 1] 正在提取关键信息...")

    system_prompt = "你是一位资深的投标专员。请从招标文件中提取关键信息，输出纯 JSON 格式。"
    user_prompt = f"""
    请阅读以下招标文件片段，提取生成《投标函》所需的关键字段。

    【需提取字段】
    1. project_name (项目名称)
    2. project_code (项目编号/招标编号, 如未找到填 "N/A")
    3. purchaser (采购人/招标人名称)
    4. budget_str (预算金额/最高限价原文, 如 "80万元")

    【招标文件片段】
    {content[:4000]}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(clean_llm_json(response.choices[0].message.content))
    except Exception as e:
        print(f"      ❌ 提取失败: {e}")
        return {}


def step2_generate_letter(info):
    """步骤二：基于提取的信息，生成正式的投标函"""
    print(f"   ✍️ [Step 2] 正在撰写投标函...")

    # 如果提取失败，使用占位符，防止生成中断
    p_name = info.get("project_name", "[项目名称]")
    p_code = info.get("project_code", "[项目编号]")
    p_buyer = info.get("purchaser", "[采购人名称]")
    p_budget = info.get("budget_str", "0")

    system_prompt = "你是一位专业的投标经理。请根据提供的信息，撰写一份正式、严谨的《投标函》。"
    user_prompt = f"""
    请为以下项目撰写一份标准的《投标函》。

    【项目信息】
    - 致：{p_buyer}
    - 项目名称：{p_name}
    - 项目编号：{p_code}
    - 预算金额：{p_budget}

    【写作要求】
    1. **格式**：符合中国政府采购标准格式。
    2. **报价策略**：请在投标函中给出一个具体的投标总报价。策略是：比预算金额降低 1%~2% 左右，取一个吉利的数字。
    3. **承诺**：包含“完全响应招标文件”、“不参与围标串标”、“服务承诺”等标准条款。
    4. **落款**：虚拟一个公司名“AI 智能投标有限公司”，日期写今天。

    请直接输出《投标函》正文，不需要Markdown代码块标记。
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7  # 生成任务温度稍高，增加自然度
    )
    return response.choices[0].message.content


# ================= 🚀 主程序 =================

if __name__ == "__main__":
    print(f"🚀 启动 AI 投标函生成引擎 (Model: {MODEL_NAME})\n")

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]

    if not files:
        print(f"❌ 目录 {INPUT_DIR} 为空，请先运行数据清洗脚本！")
        exit()

    for i, fname in enumerate(files):
        print(f"📄 [{i + 1}/{len(files)}] 处理文件: {fname}")

        # 读取文本
        with open(os.path.join(INPUT_DIR, fname), 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 提取 (Extract)
        info = step1_extract_info(fname, content)

        # 2. 生成 (Generate)
        # 只有当提取到了哪怕一部分信息时才生成，全是N/A就不生成了
        if info and info.get("project_name") not in ["N/A", None]:
            bid_letter = step2_generate_letter(info)

            # 3. 保存 (Save)
            save_name = f"投标函_{fname.replace('.txt', '.md')}"
            save_path = os.path.join(OUTPUT_DIR, save_name)

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# 项目提取信息\n```json\n{json.dumps(info, ensure_ascii=False, indent=2)}\n```\n\n")
                f.write(f"# 自动生成的投标函\n\n{bid_letter}")

            print(f"   ✅ 已生成: {save_name}\n")
        else:
            print(f"   ⚠️ 信息提取不足，跳过生成。\n")

    print(f"🎉 所有生成任务完成！请查看目录: {OUTPUT_DIR}")