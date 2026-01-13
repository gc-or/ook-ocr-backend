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
        
        # System Prompt
        self.system_prompt = """你是一个专业的书籍信息提取助手。
用户会给你一段从书脊图片中 OCR 识别出的原始文本（可能有噪声和错误）。

你的任务是：
1. 从文本中识别出所有书籍
2. 提取每本书的信息并返回 JSON 数组

每本书需要提取以下字段:
- title: 书名 (必填)
- author: 作者 (如果能识别出，否则为 null)
- publisher: 出版社 (如果能识别出，否则为 null)
- edition: 版次，如"第7版" (如果有，否则为 null)
- category: 学科分类，从以下选项中选择:
  ["高等数学", "线性代数", "概率统计", "大学物理", "电子电路", "程序设计", "数据结构", "计算机网络", "其他"]

输出格式要求:
- 必须是合法的 JSON 数组
- 不要输出任何解释文字，只输出纯 JSON
- 如果某个字段无法识别，设为 null"""

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


# ============ 测试代码 ============
if __name__ == "__main__":
    import asyncio
    
    test_ocr_text = """
电子技术基础数字部分（第7版）
主编康华光张林
数字信号处理
第3版
程序设计教程 用CC++语言编程
概率论与数理统计（第三版
"""
    
    async def main():
        print("🤖 测试 SiliconCloud LLM 结构化提取...")
        print(f"输入文本:\n{test_ocr_text}")
        print("-" * 40)
        
        try:
            llm = get_llm_service()
            books = await llm.extract_book_info(test_ocr_text)
            
            print("\n📚 提取结果:")
            print(json.dumps(books, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    asyncio.run(main())
