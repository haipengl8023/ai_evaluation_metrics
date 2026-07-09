import os
import cv2
import numpy as np
from docx import Document
import pdfplumber  # <--- 替换了 pdf2image
import shutil


class BidBenchCleaner:
    def __init__(self, output_dir="bidbench_data_output/cleaned_data"):
        self.output_dir = output_dir
        self.text_dir = os.path.join(output_dir, "texts")

        # 创建输出目录
        os.makedirs(self.text_dir, exist_ok=True)

    def process_file(self, file_path):
        """核心调度逻辑"""
        filename = os.path.basename(file_path)
        print(f"🔄 正在处理: {filename}...")

        if filename.endswith(".docx"):
            self._clean_docx(file_path, filename)
        elif filename.endswith(".pdf"):
            self._clean_pdf(file_path, filename)  # 新的 PDF 处理逻辑
        elif filename.endswith(".doc"):
            print(f"   ⚠️ 跳过 .doc (请手动另存为docx): {filename}")
        else:
            print(f"   ⚠️ 未知格式: {filename}")

    def _clean_docx(self, file_path, filename):
        """策略 A: Word 文档提取"""
        try:
            doc = Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if len(text) > 1:
                    full_text.append(text)

            save_name = filename.replace(".docx", ".txt")
            self._save_text(save_name, "\n".join(full_text))
            print(f"   ✅ [Word] 文本提取成功")
        except Exception as e:
            print(f"   ❌ [Word] 解析失败: {e}")

    def _clean_pdf(self, file_path, filename):
        """策略 B: PDF 纯文本提取 (无需 Poppler)"""
        try:
            full_text = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # 提取文字
                    text = page.extract_text()
                    if text:
                        full_text.append(text)

                    # (可选) 这里其实也可以提取表格
                    # tables = page.extract_tables()

            if full_text:
                save_name = filename.replace(".pdf", ".txt")
                self._save_text(save_name, "\n".join(full_text))
                print(f"   ✅ [PDF] 文本提取成功 (数字版)")
            else:
                print(f"   ⚠️ [PDF] 提取为空，可能是纯图片扫描件")

        except Exception as e:
            print(f"   ❌ [PDF] 解析失败: {e}")

    def _save_text(self, filename, content):
        path = os.path.join(self.text_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


# --- 运行入口 ---
if __name__ == "__main__":
    # 请确认你的文件在这个目录下
    input_folder = "/Users/lianghaipeng/Desktop/evaluation_metrics/bidbench_data_output/raw_docs"

    # 自动创建 cleaning 实例
    cleaner = BidBenchCleaner()

    if not os.path.exists(input_folder):
        print(f"❌ 找不到文件夹: {input_folder}")
        # 如果你是在当前目录下运行，可以尝试:
        input_folder = "."

    files = [f for f in os.listdir(input_folder) if f.endswith(('.pdf', '.docx', '.doc'))]
    print(f"📂 扫描到 {len(files)} 个文件，开始新一轮提取...\n")

    for f in files:
        cleaner.process_file(os.path.join(input_folder, f))