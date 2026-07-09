import json
import os

# 定义要合并的文件列表
files_to_merge = [
    "/Users/lianghaipeng/Desktop/evaluation_metrics/大模型评测体系构建与优化/通用安全 (SafetyBench)/safetybench.json", # 通用安全
    "/Users/lianghaipeng/Desktop/evaluation_metrics/大模型评测体系构建与优化/极端压力测试 (BeaverTails)/beavertails.json", # 极端压力测试
    "/Users/lianghaipeng/Desktop/evaluation_metrics/大模型评测体系构建与优化/交通法国际法会计学经济学商业伦理公务员考试 (CMMLU)/cmmlu_cot.json",  # 交通法国际法会计学经济学商业伦理公务员考试
    "/Users/lianghaipeng/Desktop/evaluation_metrics/大模型评测体系构建与优化/逻辑计算 (GSM8K)/gsm8k_math.json",  # 数学
    "/Users/lianghaipeng/Desktop/evaluation_metrics/大模型评测体系构建与优化/抗幻觉测试 (HaluEval)/qa_halu.json", # 抗幻觉
    "/Users/lianghaipeng/Desktop/evaluation_metrics/大模型评测体系构建与优化/野生幻觉测试 (General)/payloads_wild_fixed.json", #野生幻觉测试
    "/Users/lianghaipeng/Desktop/evaluation_metrics/大模型评测体系构建与优化/真相探究 (TruthfulQA)/QA_truth.json" # 真相探究
]

all_data = []
print("🧹 正在清理并合并数据...")

for filename in files_to_merge:
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = json.load(f)
                # 兼容处理：有些脚本生成的是 {"data": []}，有些可能是直接 []
                if isinstance(content, dict):
                    data = content.get('data', [])
                elif isinstance(content, list):
                    data = content
                else:
                    data = []

                print(f"   ✅ 读取 {filename}: +{len(data)} 条")
                all_data.extend(data)
        except json.JSONDecodeError:
            print(f"   ❌ 跳过 {filename}: 文件格式损坏 (JSON Decode Error)")
        except Exception as e:
            print(f"   ❌ 读取 {filename} 失败: {e}")
    else:
        print(f"   ⚠️ 跳过 {filename} (文件不存在)")

# 输出文件
output_file = "merger_all.json"

final_output = {
    "dataset_info": {"desc": "Merged Dataset (Clean Build)"},
    "data": all_data
}

# 🔥 关键：使用 'w' 模式强制覆盖
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

print(f"\n🎉 修复完成！新文件已生成: {output_file}")
print(f"📊 总题量: {len(all_data)}")