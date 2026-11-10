import json
import os
import random

# ================= ⚙️ 瘦身配置区域 =================

# 1. 采样上限：每个类别最多留多少条？(建议 50-100)
MAX_SAMPLES_PER_TYPE = 50

# 2. 文本长度下限：太短的不要
MIN_TEXT_LENGTH = 40

# 3. "白领犯罪"关键词白名单
# 只有包含这些词的 financial_crime 才会被保留，过滤掉"偷东西"等物理犯罪
WHITE_COLLAR_KEYWORDS = [
    "laundering", "embezzle", "tax", "insider trading", "ponzi",
    "pyramid scheme", "bank", "credit card", "identity theft",
    "scam", "fraud", "counterfeit", "bribe", "accounting", "audit",
    "financial", "invest", "stock", "currency", "loan"
]

# 4. 欺诈关键词 (用于从 unethical 类别中捞数据)
FRAUD_KEYWORDS = [
    "fraud", "scam", "fake report", "fake document", "forgery",
    "phishing", "social engineering"
]


def convert_beavertails_lite(input_file="test.jsonl", output_file="beavertails.json"):
    print(f"🚀 开始执行【极速瘦身版】提取，目标文件: {output_file}")

    # 临时存储桶
    buckets = {
        "Financial_Crime": [],
        "Privacy_Violation": [],
        "Financial_Fraud": []
    }

    if not os.path.exists(input_file):
        print(f"❌ 错误：找不到文件 {input_file}")
        return

    total_scanned = 0

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            total_scanned += 1

            try:
                item = json.loads(line)

                # --- 基础过滤 ---
                if item.get("is_safe") is not False: continue
                prompt = item.get("prompt", "")
                if len(prompt) < MIN_TEXT_LENGTH: continue  # 太短的不要

                cats = item.get("category", {})
                risk_type = None

                # --- 逻辑分类 ---

                # 1. 隐私泄露 (Privacy) - 直接保留
                if cats.get("privacy_violation") is True:
                    risk_type = "Privacy_Violation"

                # 2. 金融犯罪 (Financial Crime) - 必须通过"白领关键词"检测
                elif cats.get("financial_crime,property_crime,theft") is True:
                    prompt_lower = prompt.lower()
                    # 只有包含"洗钱/税务/银行"等词才算，剔除"偷窃/抢劫"
                    if any(kw in prompt_lower for kw in WHITE_COLLAR_KEYWORDS):
                        risk_type = "Financial_Crime"

                # 3. 欺诈 (Fraud) - 从 unethical 中捞取
                elif cats.get("non_violent_unethical_behavior") is True:
                    prompt_lower = prompt.lower()
                    if any(kw in prompt_lower for kw in FRAUD_KEYWORDS):
                        risk_type = "Financial_Fraud"

                # --- 入桶 ---
                if risk_type:
                    # 构造标准数据格式
                    entry = {
                        "id": f"BT_LITE_{risk_type}_{len(buckets[risk_type])}",
                        "prompt": prompt,
                        "risk_type": risk_type,
                        "source": "BeaverTails_Lite",
                        "expected_behavior": "Refusal"
                    }
                    buckets[risk_type].append(entry)

            except:
                continue

    # --- 采样阶段 (Sampling) ---
    final_data = []
    print(f"\n📊 扫描完成 (共 {total_scanned} 条)，正在进行采样 (上限 {MAX_SAMPLES_PER_TYPE} 条/类)...")

    for r_type, items in buckets.items():
        count = len(items)
        # 如果数据够多，就随机抽；不够就全拿
        if count > MAX_SAMPLES_PER_TYPE:
            selected = random.sample(items, MAX_SAMPLES_PER_TYPE)
        else:
            selected = items

        final_data.extend(selected)
        print(f"   - {r_type}: 原始 {count} 条 -> 保留 {len(selected)} 条")

    # 保存
    output_data = {
        "dataset_info": {
            "source": "BeaverTails Financial Lite",
            "total_count": len(final_data),
            "strategy": f"Max {MAX_SAMPLES_PER_TYPE} per category + Keyword Filter"
        },
        "data": final_data
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 瘦身完成！最终保留: {len(final_data)} 条。")
    print(f"   文件已保存至: {output_file}")


if __name__ == "__main__":
    convert_beavertails_lite()