import json
import os
import random


def convert_wild_final(input_file="HaluEval_Wild_6types.json", output_file="payloads_wild_fixed.json"):
    print(f"🚀 正在处理 HaluEval Wild 数据集: {input_file}")

    if not os.path.exists(input_file):
        print("❌ 文件不存在")
        return

    # 1. 读取数据
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        print(f"📊 原始数据总量: {len(raw_data)} 条")
    except:
        print("❌ JSON 格式错误，尝试作为 jsonl 读取...")
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = [json.loads(line) for line in f if line.strip()]

    # ==========================================
    # 🎯 策略: 重点类别分层采样
    # ==========================================

    # 定义我们关注的类别及其采样目标
    # 重点关注：复杂推理、越界信息、混淆指令
    target_strategy = {
        'complex reasoning': 10,  # 逻辑陷阱，最难
        'out-of-scope information': 10,  # 知识盲区，测拒答
        'confused / erroneous queries': 10,  # 错误前提，测纠错
        'inappropriate content': 10,  # 安全红线
        'other types': 5,  # 其他补充
        'beyond-modality interaction': 5  # 多模态交互（通常纯文本模型处理不好，测鲁棒性）
    }

    # 将数据按类型桶装
    buckets = {k: [] for k in target_strategy.keys()}

    for item in raw_data:
        q_type = item.get('query_type', 'other types')
        if q_type in buckets:
            buckets[q_type].append(item)

    beitou_payloads = []
    case_id = 1

    print("------------------------------------------------")
    print(f"{'幻觉类型 (Query Type)':<30} | {'采样数':<5}")
    print("------------------------------------------------")

    for q_type, target_count in target_strategy.items():
        items = buckets.get(q_type, [])
        if not items:
            continue

        # 随机采样
        selected = random.sample(items, min(len(items), target_count))

        for item in selected:
            question = item.get('query', '')
            ref_ans = item.get('ref_answer', '')

            # 构造 Prompt
            prompt_text = f"【用户问题】\n{question}"

            # 风险标签映射
            risk_map = {
                'complex reasoning': 'Risk_Logic_Hallucination',
                'out-of-scope information': 'Risk_Knowledge_Boundary',
                'inappropriate content': 'Risk_Safety_Compliance',
                'confused / erroneous queries': 'Risk_Fact_Correction'
            }
            risk_tag = risk_map.get(q_type, 'Risk_General_Hallucination')

            new_entry = {
                "id": f"WILD_FINAL_{case_id}",
                "mode_type": f"🦁 野生幻觉测试 ({q_type})",
                "risk_type": risk_tag,
                "prompt": prompt_text,
                "expected_behavior": "Should avoid hallucination and provide accurate or refusal response.",
                "reference": f"Standard Answer:\n{ref_ans}"
            }
            beitou_payloads.append(new_entry)
            case_id += 1

        print(f"{q_type:<30} | {len(selected):<5}")

    print("------------------------------------------------")
    print(f"📊 最终评测集总量: {len(beitou_payloads)} 条")

    # 3. 保存
    final_output = {
        "dataset_info": {"desc": "Fixed HaluEval-Wild (Stratified Sample)"},
        "data": beitou_payloads
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"✅ 转换完成！已生成 {output_file}")


if __name__ == "__main__":
    convert_wild_final()