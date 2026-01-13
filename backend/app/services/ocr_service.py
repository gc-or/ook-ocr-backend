"""
OCR 服务模块
使用 PaddleOCR 识别书脊图片中的文字
"""
from paddleocr import PaddleOCR
from pathlib import Path


class OCRService:
    """
    OCR 服务类 - 单例模式
    PaddleOCR 初始化较慢，所以我们只初始化一次并复用
    """
    _instance = None
    _ocr = None

    def __new__(cls):
        """单例模式：确保整个应用只创建一个 OCR 实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化 PaddleOCR
            # use_angle_cls=True: 启用文字角度分类，处理倾斜文字
            # lang="ch": 使用中文模型（也支持英文）
            # show_log=False: 关闭调试日志
            print("🔄 正在加载 PaddleOCR 模型（首次加载需要下载，请稍候...）")
            cls._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="ch",
                show_log=False
            )
            print("✅ PaddleOCR 模型加载完成！")
        return cls._instance

    def extract_text(self, image_path: str) -> str:
        """
        从图片中提取文字
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: 识别出的所有文字，用换行符分隔
        """
        # 检查文件是否存在
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        # 调用 PaddleOCR 进行识别
        # result 格式: [[[坐标], (文字, 置信度)], ...]
        result = self._ocr.ocr(image_path, cls=True)

        # 提取所有识别出的文字
        texts = []
        if result and result[0]:  # 确保有识别结果
            for line in result[0]:
                text = line[1][0]      # 提取文字
                confidence = line[1][1]  # 提取置信度
                # 只保留置信度大于 0.6 的结果
                if confidence > 0.6:
                    texts.append(text)

        # 用换行符拼接所有文字
        return "\n".join(texts)


# 创建全局 OCR 服务实例（懒加载，首次调用时才初始化）
def get_ocr_service() -> OCRService:
    """获取 OCR 服务实例"""
    return OCRService()


# ============ 测试代码 ============
if __name__ == "__main__":
    # 这段代码只在直接运行此文件时执行，用于测试
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python ocr_service.py <图片路径>")
        print("示例: python ocr_service.py ../uploads/test.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"📖 正在识别图片: {image_path}")
    
    ocr = get_ocr_service()
    text = ocr.extract_text(image_path)
    
    print("\n========== 识别结果 ==========")
    print(text)
    print("==============================")
