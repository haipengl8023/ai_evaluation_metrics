import csv
import json
import os
import random
from collections import Counter

# ================= ⚙️ 瘦身配置区域 =================

# 1. 核心学科锁定
TARGET_FILES = {
    "business_ethics.csv": ("商业伦理", "Business_Ethics"),
    "professional_accounting.csv": ("会计学", "Accounting"),
    "economics.csv": ("经济学", "Economics"),
    "chinese_civil_service_exam.csv": ("公务员行测", "Civil_Service_Exam"),
    "professional_law.csv": ("法律法规", "Professional_Law"),
    "international_law.csv": ("国际法", "International_Law")
}

# 2. 采样上限：每个学科只测 50 题 (总计 300 题)
MAX_SAMPLES_PER_SUBJECT = 10


def convert_cmmlu_lite(output_file="cmmlu.json"):
    """
    生成 CMMLU 核心学科的精简评测集。
    """
    print(f"🚀 开始转换 CMMLU (极速瘦身版)，目标文件: {output_file}")

    beitou_payloads = []

    for filename, (mode_name, type_id) in TARGET_FILES.items():
        if not os.path.exists(filename):
            print(f"⚠️ 跳过缺失文件: {filename}")
            continue

        print(f"   📖 处理学科: {mode_name} ({filename})...")

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                total_rows = len(rows)

                # --- 随机采样逻辑 ---
                if total_rows > MAX_SAMPLES_PER_SUBJECT:
                    selected_rows = random.sample(rows, MAX_SAMPLES_PER_SUBJECT)
                    print(f"      - 采样: {total_rows} 条 -> {MAX_SAMPLES_PER_SUBJECT} 条")
                else:
                    selected_rows = rows
                    print(f"      - 保留全量: {total_rows} 条")

                for idx, row in enumerate(selected_rows):
                    # 字段清洗
                    question = row.get('Question', row.get('question', '')).strip()
                    answer = row.get('Answer', row.get('answer', '')).strip()

                    if not question or not answer:
                        continue

                    # 构造选项
                    options_text = ""
                    for char in ['A', 'B', 'C', 'D']:
                        opt_val = row.get(char, row.get(char.lower(), '')).strip()
                        options_text += f"{char}. {opt_val}\n"

                    # 构造 Prompt
                    full_prompt = f"""[任务] 请作为相关领域的专家，回答以下单项选择题。

[题目]
{question}

[选项]
{options_text}
[要求] 仅输出正确选项的字母（如 A、B、C 或 D），不需要解释。"""

                    # 封装数据
                    new_entry = {
                        "id": f"CMMLU_LITE_{type_id}_{idx}",  # 标记为 LITE
                        "category": mode_name,
                        "prompt": full_prompt,
                        "ground_truth": answer,
                        "risk_type": f"Knowledge_{type_id}",
                        "original_file": filename
                    }
                    beitou_payloads.append(new_entry)

        except Exception as e:
            print(f"❌ 处理 {filename} 时出错: {e}")

    # 保存结果
    final_output = {
        "dataset_info": {
            "source": "CMMLU (GXBTXC Core Subset - Lite)",
            "description": f"Randomly sampled {MAX_SAMPLES_PER_SUBJECT} items per subject.",
            "total_count": len(beitou_payloads)
        },
        "data": beitou_payloads
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 瘦身完成！总计生成 {len(beitou_payloads)} 条数据。")

    # 打印分布
    stats = Counter([d['category'] for d in beitou_payloads])
    for cat, count in stats.items():
        print(f"   - {cat}: {count}")


if __name__ == "__main__":
    convert_cmmlu_lite()
