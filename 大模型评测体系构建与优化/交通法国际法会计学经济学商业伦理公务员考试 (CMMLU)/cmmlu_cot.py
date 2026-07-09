import json


def upgrade_cmmlu_to_cot(input_file='cmmlu.json', output_file='cmmlu_cot.json'):
    print(f"🚀 正在升级数据集: {input_file} -> {output_file} ...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cot_count = 0
        new_data = []

        # 锁定需要 CoT 的高智力学科
        TARGET_SUBJECTS = ['经济学', '公务员行测']

        for item in data['data']:
            # 如果属于目标学科，进行 CoT 改造
            if item['category'] in TARGET_SUBJECTS:
                original_prompt = item['prompt']
                # 去除旧的“仅输出字母”的限制
                base_prompt = original_prompt.split('[要求]')[0].strip()

                # 注入强力的 CoT 指令
                cot_instruction = (
                    "\n[要求] 请采用思维链 (Chain-of-Thought) 策略进行回答。\n"
                    "1. 首先，深入分析题干与选项的逻辑关系。\n"
                    "2. 然后，一步步推导正确答案（Step-by-step Reasoning）。\n"
                    "3. 最后，在独立的一行明确输出：答案：X (X为选项字母)。"
                )

                item['prompt'] = base_prompt + cot_instruction
                # 标记 Risk Type 以便裁判识别
                item['risk_type'] = item['risk_type'].replace('Knowledge_', 'Knowledge_CoT_')
                item['id'] = item['id'].replace('CMMLU_LITE_', 'CMMLU_CoT_')
                cot_count += 1

            new_data.append(item)

        data['data'] = new_data
        data['dataset_info']['description'] += " (With CoT Enforcement)"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 升级完成！已将 {cot_count} 条逻辑题改造为 CoT 模式。")
        print(f"   新文件已保存至: {output_file}")

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    upgrade_cmmlu_to_cot()