import os
import time
import json
import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent


class BidCrawler:
    def __init__(self, save_dir="bidbench_data_output"):
        self.base_dir = save_dir
        self.doc_dir = os.path.join(save_dir, "../bidbench_data_output/raw_docs")  # 存 PDF/Word
        self.text_dir = os.path.join(save_dir, "../bidbench_data_output/html_text")  # 存网页正文
        self.meta_dir = os.path.join(save_dir, "../bidbench_data_output/metadata")

        # 创建目录
        os.makedirs(self.doc_dir, exist_ok=True)
        os.makedirs(self.text_dir, exist_ok=True)
        os.makedirs(self.meta_dir, exist_ok=True)

        options = Options()
        options.add_argument(f"user-agent={UserAgent().random}")
        options.add_argument("--disable-blink-features=AutomationControlled")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def crawl_ccgp_samples(self, keyword="公开招标 大数据", max_pages=1):
        # 搜索 URL (通用)
        search_url = f"http://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=0&bidType=1&dbselect=bidx&kw={keyword}&start_time=2025%3A01%3A01&end_time=2026%3A12%3A31&timeType=6"

        print(f"🕵️‍♂️ 访问搜索: {search_url}")
        self.driver.get(search_url)
        time.sleep(5)

        links = []
        try:
            results = self.driver.find_elements(By.XPATH, "//ul[contains(@class,'vT-srch-result-list')]//li/a")
            print(f"👀 找到 {len(results)} 个链接")

            if not results:
                input("🔴 未找到结果，请手动检查页面，按回车继续...")

            for a in results[:8]:  # 抓前8个试试
                link = a.get_attribute("href")
                title = a.text
                if link and "http" in link and len(title) > 5:
                    links.append({"url": link, "title": title})

        except Exception as e:
            print(f"⚠️ 列表获取失败: {e}")

        for item in links:
            self.parse_detail_page(item["url"], item["title"])
            time.sleep(3)

    def parse_detail_page(self, url, title):
        print(f"   📄 解析: {title}")
        try:
            self.driver.get(url)
            time.sleep(2)

            # 清洗标题，作为文件名
            clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()

            # === 策略 A: 抓取网页 HTML 正文 (保底) ===
            self.extract_html_content(clean_title, url)

            # === 策略 B: 抓取附件 (PDF/Word) ===
            # 扩展查找范围：不仅找 PDF，也找 Word 和 Zip
            # XPath 寻找 href 包含特定后缀的链接
            attachment_xpath = "//a[contains(@href, '.pdf') or contains(@href, '.doc') or contains(@href, '.zip')]"
            attachments = self.driver.find_elements(By.XPATH, attachment_xpath)

            if attachments:
                print(f"      📎 发现 {len(attachments)} 个附件")
                for idx, att in enumerate(attachments):
                    file_url = att.get_attribute("href")
                    # 获取原始后缀名
                    ext = os.path.splitext(file_url)[-1]
                    if not ext or len(ext) > 5: ext = ".pdf"  # 默认防错

                    file_name = f"{clean_title}_{idx}{ext}"
                    save_path = os.path.join(self.doc_dir, file_name)

                    self.download_file(file_url, save_path)
                    self.save_metadata(file_name, title, url, file_url, has_attachment=True)
            else:
                print("      ⚠️ 无附件，仅保留HTML内容")
                self.save_metadata(f"{clean_title}.txt", title, url, "", has_attachment=False)

        except Exception as e:
            print(f"      ❌ 解析异常: {e}")

    def extract_html_content(self, filename, url):
        """抓取网页正文文本"""
        try:
            # CCGP 的正文通常在这个 class 里
            content_div = self.driver.find_element(By.CLASS_NAME, "vF_detail_content_container")
            text_content = content_div.text

            save_path = os.path.join(self.text_dir, f"{filename}.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(f"Source: {url}\n\n")
                f.write(text_content)
            print(f"      📝 正文已保存: {filename}.txt")
        except:
            # 如果找不到特定 class，尝试抓 body
            try:
                text_content = self.driver.find_element(By.TAG_NAME, "body").text
                save_path = os.path.join(self.text_dir, f"{filename}_full.txt")
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text_content)
                print(f"      📝 (Body)正文已保存")
            except:
                print("      ❌ 无法提取网页正文")

    def download_file(self, url, path):
        try:
            headers = {"User-Agent": UserAgent().random}
            r = requests.get(url, headers=headers, stream=True, timeout=15)  # 超时稍微长点
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"      ✅ 附件下载成功: {os.path.basename(path)}")
            else:
                print(f"      ❌ 附件下载失败: {r.status_code}")
        except Exception as e:
            print(f"      ❌ 下载报错: {e}")

    def save_metadata(self, filename, title, source_url, file_url, has_attachment):
        meta_data = {
            "bid_id": f"AUTO_{int(time.time())}_{random.randint(100, 999)}",
            "title": title,
            "type": "Attachment" if has_attachment else "WebPage",
            "file_path": filename,
            "url": source_url,
            "attachment_url": file_url
        }
        # 简单的保存逻辑，避免覆盖
        json_name = f"{os.path.splitext(filename)[0]}.json"
        json_path = os.path.join(self.meta_dir, json_name)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
    import random

    crawler = BidCrawler()
    try:
        # 技巧：关键词里加上“招标文件”四个字，更容易搜到带附件的！
        crawler.crawl_ccgp_samples(keyword="招标 2025", max_pages=1)
        print("\n✅ 任务完成")
        input("🔴 按回车退出...")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("🔴 Error...")
    finally:
        crawler.close()