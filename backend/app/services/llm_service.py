"""
LLM 服务模块
使用 SiliconCloud API (硅基流动) 将 OCR 文本结构化为书籍信息 JSON
支持 DeepSeek、Qwen 等多种模型
"""
import httpx
import json
import os
import asyncio
from typing import Optional


class LLMService:
    """
    LLM 服务类
    调用 SiliconCloud API 进行智能文本结构化
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 LLM 服务
        
        Args:
            api_key: SiliconCloud API 密钥
        """
        self.api_key = api_key or os.getenv("SILICONCLOUD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "❌ 未找到 SiliconCloud API Key！\n"
                "请设置环境变量: set SILICONCLOUD_API_KEY=你的密钥"
            )
        
        # SiliconCloud API 端点 (兼容 OpenAI 格式)
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        
        # 使用 Qwen2.5-7B 模型 (速度更快，适合结构化提取)
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        
        # System Prompt - 增强版 (支持列分组 + 置信度评分)
        self.system_prompt = """你是一个专业的书籍信息结构化助手。
用户会提供一段 OCR 识别文本（包含大量噪声、错别字、碎片文字）。

📐 **重要：文本格式说明**
- 文本中可能包含 `---BOOK_SEPARATOR---` 分隔符
- **每个分隔符之间的内容代表一本独立的书籍**
- 同一分隔符内的多行文字都属于同一本书，请聚合在一起

⚠️ 你的核心任务：
1. **识别分隔符**：遇到 `---BOOK_SEPARATOR---` 时，将其前后内容视为不同书籍。
2. **去噪**：忽略无关的字符（如 "扫描全能王"、"24元"、单纯的数字、乱码符号）。
3. **纠错**：根据语义修正 OCR 错误（例如 "高等效学" -> "高等数学", "C++程字设计" -> "C++程序设计"）。
4. **聚合**：将原本属于同一本书的碎片信息（书名、作者、出版社）合并。通常书名最长，作者较短。
5. **自评**：评估每本书识别结果的可信度（0.0-1.0）

请提取每本书的以下字段:
- title: 书名 (必填，尽量完整)
- author: 作者 (尽量提取，如"xxx 主编/著/编"，如果没有则 null)
- publisher: 出版社 (常见如"高等教育出版社"、"清华大学出版社"等，没有则 null)
- edition: 版次 (如"第7版"、"第三版"，没有则 null)
- price: 价格 (数字，如果文本中有价格信息，提取出来，否则 null)
- category: 学科分类，必须从以下列表选择最接近的一个:
  ["高等数学", "线性代数", "概率统计", "大学物理", "电子电路", "程序设计", "数据结构", "计算机网络", "考研", "英语", "其他"]
- **confidence: 置信度 (0.0-1.0)**
  - 1.0: 非常确定，书名完整、语义通顺、无明显错误
  - 0.8: 较为确定，书名基本完整，可能有小瑕疵
  - 0.5: 存在疑问，书名不完整或有明显拼接痕迹
  - 0.3: 很不确定，大量乱码或碎片拼接
  - 评分时请严格判断，宁可保守

🔍 示例输入 -> 输出:
输入: "工科数学分析教程\n下册\n28.00\n同济大学数学系编\n---BOOK_SEPARATOR---\n万维社工上\n岗训练"
输出: [
  {"title": "工科数学分析教程 下册", "author": "同济大学数学系", "price": 28.0, "category": "高等数学", "confidence": 0.95},
  {"title": "万维社工上岗训练", "author": null, "category": "其他", "confidence": 0.3}
]

输出格式:
- 必须是纯标准的 JSON 数组 `[...]`
- 不要包含 Markdown (```json) 标记
- 如果无法识别出任何有效的书籍信息，返回空数组 []"""

    async def extract_book_info(self, ocr_text: str, max_retries: int = 3) -> list[dict]:
        """
        从 OCR 文本中提取书籍信息
        
        Args:
            ocr_text: OCR 识别出的原始文本
            max_retries: 最大重试次数
            
        Returns:
            list[dict]: 书籍信息列表
        """
        # OpenAI 兼容格式的请求体
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"请从以下 OCR 文本中提取书籍信息：\n\n{ocr_text}"}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.api_url,
                        json=payload,
                        headers=headers
                    )
                    
                    # 处理速率限制 (429)
                    if response.status_code == 429:
                        wait_time = (attempt + 1) * 2
                        print(f"⏳ API 速率限制，等待 {wait_time} 秒后重试 ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # 解析 OpenAI 格式返回
                    content = result["choices"][0]["message"]["content"]
                    return self._parse_json_response(content)
                    
            except httpx.HTTPStatusError as e:
                print(f"⚠️ HTTP 错误: {e.response.status_code}")
                if attempt < max_retries - 1:
                    print(f"   重试中... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(2)
                else:
                    raise e
            except Exception as e:
                print(f"⚠️ 请求错误: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise e
        
        return []
    
    def _parse_json_response(self, content: str) -> list[dict]:
        """解析 LLM 返回的 JSON"""
        content = content.strip()
        # 清理 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            books = json.loads(content)
            return books if isinstance(books, list) else [books]
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败: {e}")
            print(f"原始返回: {content}")
            return []


# 全局实例
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """获取 LLM 服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service



