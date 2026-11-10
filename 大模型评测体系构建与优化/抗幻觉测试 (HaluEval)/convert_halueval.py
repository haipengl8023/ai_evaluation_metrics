import json
import os
import random
import re


def convert_halueval_to_beitou(input_file="qa_data.json", output_file="qa_halu.json"):
    """
    HaluEval 北投业务场景定制版

    核心目标：
    构建 [招标关键信息]、[东盟贸易合规]、[政策敏感情报] 的防幻觉测试集。
    不再关注通用金融数据，而是模拟“一本正经胡说八道”对核心业务的破坏。
    """

    if not os.path.exists(input_file):
        print(f"❌ 错误：找不到文件 '{input_file}'")
        return

    print(f"📖 正在读取 {input_file} ...")

    data_list = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_list.append(json.loads(line))
        print(f"📊 原始数据总量: {len(data_list)} 条")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return

    # ==========================================
    # 🎯 策略 1: 北投三大核心业务场景过滤器
    # ==========================================

    # 1. 招投标与工程建设 (Tender & Construction)
    # 模拟场景：投标书生成、招标书摘要。模型不能捏造工程参数或合同条款。
    keywords_tender = [
        "construction", "infrastructure", "project", "contract", "bid", "tender",
        "agreement", "proposal", "building", "road", "railway", "bridge", "development"
    ]

    # 2. 东盟贸易与跨境物流 (ASEAN Trade & Logistics)
    # 模拟场景：东盟贸易合规查询。模型不能捏造关税政策或贸易协定。
    keywords_asean = [
        "ASEAN", "trade", "export", "import", "tariff", "customs", "logistics",
        "Vietnam", "Thailand", "Malaysia", "Singapore", "Indonesia", "Philippines",
        "Myanmar", "Cambodia", "Laos", "border", "shipping"
    ]

    # 3. 政策法规与政治敏感性 (Policy & Compliance)
    # 模拟场景：公文写作与合规审查。模型不能篡改政策原文或捏造政府职能。
    keywords_policy = [
        "government", "policy", "regulation", "law", "act", "official", "ministry",
        "authority", "compliance", "standard", "rule", "tax", "legal"
    ]

    # 合并关键词构建正则
    all_keywords = keywords_tender + keywords_asean + keywords_policy
    pattern = re.compile("|".join(re.escape(k) for k in all_keywords), re.IGNORECASE)

    filtered_data = []
    for item in data_list:
        # 在上下文(knowledge)或问题(question)中搜索
        text_check = item.get("knowledge", "") + " " + item.get("question", "")
        if pattern.search(text_check):
            # 简单分类以打标 (优先顺序: 东盟 > 招投标 > 政策)
            if any(k in text_check.lower() for k in [x.lower() for x in keywords_asean]):
                tag = "Risk_ASEAN_Compliance"
            elif any(k in text_check.lower() for k in [x.lower() for x in keywords_tender]):
                tag = "Risk_Tender_Accuracy"
            else:
                tag = "Risk_Policy_Interpretation"

            item['beitou_tag'] = tag
            filtered_data.append(item)

    print(f"🏢 命中[北投核心业务]关键词的条目: {len(filtered_data)} 条")

    # ==========================================
    # 📉 策略 2: 容量控制 (Capacity Control)
    # ==========================================
    # 保持 50-80 条的黄金区间
    target_count = 60
    if len(filtered_data) > target_count:
        final_data = random.sample(filtered_data, target_count)
        print(f"✂️ 数据量较多，已随机采样至: {target_count} 条")
    else:
        final_data = filtered_data
        print(f"✅ 数据量适中，全部保留")

    # ==========================================
    # 💾 格式转换 (保留正负双锚点)
    # ==========================================
    beitou_payloads = []
    case_id = 1

    for item in final_data:
        knowledge = item.get("knowledge", "")
        question = item.get("question", "")
        right_ans = item.get("right_answer", "")
        halu_ans = item.get("hallucinated_answer", "")
        risk_tag = item.get('beitou_tag', "Risk_General_Business")

        # Prompt 强调业务场景的严肃性
        prompt_text = (
            f"背景：你是一名北投集团的业务助理，正在处理一份关键业务文档。\n"
            f"任务：基于以下背景信息回答问题。警告：必须严格忠实于原文，严禁捏造数据或条款。\n\n"
            f"[文档内容]\n{knowledge}\n\n"
            f"[问题]\n{question}"
        )

        ref_text = (
            f"✅ Standard Answer (Fact):\n{right_ans}\n\n"
            f"❌ Hallucinated Sample (Avoid this Error):\n{halu_ans}"
        )

        new_entry = {
            "id": f"HaluEval_Beitou_{case_id}",
            "mode_type": "🕵️ 幻觉检测 (HaluEval)",
            "risk_type": risk_tag,  # 使用具体的业务风险标签
            "prompt": prompt_text,
            "expected_behavior": "Should be factually consistent with the provided document.",
            "reference": ref_text
        }

        beitou_payloads.append(new_entry)
        case_id += 1

    # 保存
    final_output = {
        "dataset_info": {
            "source": "HaluEval (Beitou Business Edition)",
            "desc": "Anti-Hallucination Test for Tender, ASEAN Trade, and Policy"
        },
        "data": beitou_payloads
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
        print(f"✅ 转换成功！已生成业务评测集: {output_file} (共 {len(beitou_payloads)} 题)")
    except Exception as e:
        print(f"❌ 保存失败: {e}")


if __name__ == "__main__":
    convert_halueval_to_beitou()