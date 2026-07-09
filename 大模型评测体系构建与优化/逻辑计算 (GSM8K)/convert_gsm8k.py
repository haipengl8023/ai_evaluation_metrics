import pandas as pd
import json
import os
import re


def convert_gsm8k_parquet_to_beitou(input_file="tests_gsm8k.parquet", output_file="gsm8k_math.json"):
    """
    GSM8K 智能筛选转换脚本
    功能：从 Parquet 中筛选出与 [金融/投资/成本] 相关的题目，并转换为北投评测格式。
    """

    if not os.path.exists(input_file):
        print(f"❌ 错误：找不到文件 '{input_file}'")
        return

    print(f"📖 正在读取 {input_file} ...")

    try:
        # 读取数据
        df = pd.read_parquet(input_file)
        print(f"📊 原始数据总量: {len(df)} 条")

        # ==========================================
        # 🎯 策略 1: 金融业务关键词筛选 (Domain Filter)
        # ==========================================
        finance_keywords = [
            "$", "dollar", "money", "cost", "price", "profit", "earn",
            "spend", "buy", "sell", "interest", "discount", "salary",
            "rent", "loan", "tax", "invest", "budget", "revenue", "bank",
            "saving", "debt", "pay", "rate"
        ]

        # 使用正则表达式进行不区分大小写的匹配
        keyword_pattern = '|'.join([re.escape(k) for k in finance_keywords])
        df_finance = df[df['question'].str.contains(keyword_pattern, case=False, na=False)]

        print(f"💰 命中[金融/商业]关键词的题目: {len(df_finance)} 条")

        # ==========================================
        # 🧠 策略 2: 推理复杂度筛选 (Complexity Filter)
        # ==========================================
        # 假设：答案越长，推理步骤越多。我们筛选答案长度 > 100 字符的题目
        df_complex = df_finance[df_finance['answer'].str.len() > 100]
        print(f"🧠 其中具备[多步推理]复杂度的题目: {len(df_complex)} 条")

        # ==========================================
        # 📉 策略 3: 容量控制 (Capacity Control) - 优化版
        # ==========================================
        # 建议阈值：不要低于 50，除非原始筛选结果就不够
        min_target = 30
        max_target = 50

        total_complex = len(df_complex)

        if total_complex > max_target:
            # 如果筛选出的好题太多（>100），为了节省时间，随机采样到 100
            final_df = df_complex.sample(max_target, random_state=42)
            print(f"✂️ 高质量题目过多 ({total_complex}条)，已采样至上限: {max_target} 条")
        elif total_complex >= min_target:
            # 如果数量在 50-100 之间，直接全部保留，不进行删减
            final_df = df_complex
            print(f"✅ 题目数量适中 ({total_complex}条)，全部保留")
        else:
            # 如果复杂题少于 50 条，我们需要从普通金融题中补货
            print(f"⚠️ 复杂题仅 {total_complex} 条，正在从普通金融题中补足至 {min_target} 条...")

            # 先把刚才的复杂题选上
            selected_indices = df_complex.index

            # 计算还需要补多少
            needed = min_target - total_complex

            # 从剩下的金融题（df_finance）中，排除掉已经被选中的复杂题
            remaining_finance = df_finance.drop(selected_indices)

            # 如果剩下的够补，就补齐；不够就全拿
            if len(remaining_finance) >= needed:
                supplement = remaining_finance.sample(needed, random_state=42)
            else:
                supplement = remaining_finance

            final_df = pd.concat([df_complex, supplement])
            print(f"📦 补货完成，最终评测集数量: {len(final_df)} 条")

        # ==========================================
        # 💾 格式转换与保存
        # ==========================================
        beitou_payloads = []
        case_id = 1

        for index, row in final_df.iterrows():
            question = row['question']
            answer_raw = row['answer']

            new_entry = {
                "id": f"GSM8K_Finance_{case_id}",  # ID前缀改为 Finance 体现业务属性
                "mode_type": "🧮 逻辑计算 (GSM8K)",
                "risk_type": "Ability_Financial_Reasoning",  # 风险类型细化
                "prompt": f"请解决以下数学应用题，并给出计算过程：\n\n{question}",
                "expected_behavior": "Should calculate correctly and match the final number.",
                "reference": f"Standard Solution:\n{answer_raw}"
            }

            beitou_payloads.append(new_entry)
            case_id += 1

        output_data = {
            "dataset_info": {
                "source": "GSM8K (Finance Filtered)",
                "desc": "Math Reasoning Test focused on Financial/Business scenarios"
            },
            "data": beitou_payloads
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 转换成功！已生成高价值评测集: {output_file} (共 {len(beitou_payloads)} 题)")

    except ImportError:
        print("❌ 缺少依赖库，请运行: pip install pandas pyarrow")
    except Exception as e:
        print(f"❌ 发生错误: {e}")


if __name__ == "__main__":
    convert_gsm8k_parquet_to_beitou()