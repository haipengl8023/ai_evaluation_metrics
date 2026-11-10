import json
import os
import random


def fix_wild_dataset(input_file="HaluEval_Wild_6types.json", output_file="payloads_wild_fixed.json"):
    print(f"🕵️‍♂️ 正在诊断文件: {input_file}")

    if not os.path.exists(input_file):
        print("❌ 文件不存在！")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        # 尝试读取
        try:
            raw_data = json.load(f)
        except:
            # 如果是 jsonl
            f.seek(0)
            raw_data = [json.loads(line) for line in f if line.strip()]

    if not raw_data:
        print("❌ 数据为空")
        return

    # 🔍 打印第一条数据的所有 Key，人工核对！
    first_item = raw_data[0]
    print(f"🔍 第一条数据的 Keys: {list(first_item.keys())}")
    print(f"👀 数据预览: {str(first_item)[:200]}...")

    # ----------------------------------------------------
    # 🛠️ 智能映射逻辑 (根据常见变体自动匹配)
    # ----------------------------------------------------
    keys = first_item.keys()

    # 找“问题”字段
    q_key = next((k for k in ['instruction', 'question', 'prompt', 'input'] if k in keys), None)
    # 找“文档”字段
    doc_key = next((k for k in ['context', 'knowledge', 'document', 'evidence'] if k in keys), None)
    # 找“类型”字段
    type_key = next((k for k in ['type', 'category', 'task'] if k in keys), None)
    # 找“答案”字段
    ans_key = next((k for k in ['output', 'answer', 'response'] if k in keys), None)

    print(f"✅ 自动映射字段: 问题=[{q_key}], 文档=[{doc_key}], 类型=[{type_key}]")

    if not q_key:
        print("❌ 无法识别问题字段，请手动修改脚本！")
        return

    # 开始转换
    beitou_payloads = []
    # 采样 50 条
    sampled = random.sample(raw_data, min(50, len(raw_data)))

    for i, item in enumerate(sampled):
        instruction = item.get(q_key, "")
        context = item.get(doc_key, "") if doc_key else ""
        halu_type = item.get(type_key, "General") if type_key else "General"
        ref_ans = item.get(ans_key, "") if ans_key else ""

        # 构造 Prompt
        if context:
            prompt = f"请基于以下参考资料回答问题：\n\n【参考资料】\n{context}\n\n【问题】\n{instruction}"
        else:
            prompt = f"【问题】\n{instruction}"

        beitou_payloads.append({
            "id": f"WILD_FIX_{i + 1}",
            "mode_type": f"🦁 野生幻觉测试 ({halu_type})",  # 这样才能匹配到裁判
            "risk_type": f"Hallucination_{halu_type}",
            "prompt": prompt,
            "expected_behavior": "Faithful answer.",
            "reference": ref_ans
        })

    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"dataset_info": {"desc": "Fixed Wild Data"}, "data": beitou_payloads}, f, ensure_ascii=False,
                  indent=2)

    print(f"🎉 修复完成！已生成 {output_file}，包含类型: {[x['mode_type'] for x in beitou_payloads[:3]]}")


if __name__ == "__main__":
    fix_wild_dataset()