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
            # 优化：强制使用 CPU，禁用 GPU 和 mkldnn 以节省内存
            # 使用轻量级模型结构
            cls._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="ch",
                show_log=False,
                use_gpu=False,
                enable_mkldnn=False, # 禁用 mkldnn 以降低内存占用
                use_mp=False,        # 禁用多进程
                total_process_num=1  # 限制进程数
            )
            print("✅ PaddleOCR 模型加载完成！")
        return cls._instance

    def extract_text(self, image_path: str) -> str:
        """
        从图片中提取文字，并按列分组（适合书脊识别）
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: 按列分组的文字，用分隔符标记不同列/书籍
        """
        # 检查文件是否存在
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        # 调用 PaddleOCR 进行识别
        # result 格式: [[[坐标], (文字, 置信度)], ...]
        result = self._ocr.ocr(image_path, cls=True)

        if not result or not result[0]:
            return ""

        # 提取文字和坐标信息
        text_blocks = []
        for line in result[0]:
            coords = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = line[1][0]
            confidence = line[1][1]
            
            # 只保留置信度大于 0.6 的结果
            if confidence > 0.6:
                # 计算中心点的 X 坐标（用于列分组）
                center_x = sum([p[0] for p in coords]) / 4
                center_y = sum([p[1] for p in coords]) / 4
                text_blocks.append({
                    'text': text,
                    'x': center_x,
                    'y': center_y,
                    'confidence': confidence
                })

        if not text_blocks:
            return ""

        # 自动检测方向并按最优轴分组
        groups = self._auto_group_books(text_blocks)
        
        # 每组内部按主方向排序
        grouped_text = []
        for group in groups:
            # 判断这一组内部的主要方向（通常是垂直于分组轴的）
            if len(group) > 1:
                # 按 Y 坐标排序（从上到下）
                group_sorted = sorted(group, key=lambda b: b['y'])
            else:
                group_sorted = group
            
            group_text = '\n'.join([b['text'] for b in group_sorted])
            grouped_text.append(group_text)
        
        # 用特殊分隔符区分不同书籍
        return '\n---BOOK_SEPARATOR---\n'.join(grouped_text)

    def _auto_group_books(self, text_blocks):
        """
        自动检测拍摄方向并分组书籍
        
        Args:
            text_blocks: 文字块列表
            
        Returns:
            list: 书籍分组列表
        """
        if not text_blocks:
            return []
        
        # 计算 X 和 Y 坐标的标准差，判断主要排列方向
        x_coords = [b['x'] for b in text_blocks]
        y_coords = [b['y'] for b in text_blocks]
        
        import statistics
        x_std = statistics.stdev(x_coords) if len(x_coords) > 1 else 0
        y_std = statistics.stdev(y_coords) if len(y_coords) > 1 else 0
        
        print(f"📐 坐标分析: X标准差={x_std:.1f}, Y标准差={y_std:.1f}")
        
        # 如果 X 轴分散度更大，说明是横向排列（书脊横着）→ 按 Y 坐标（行）分组
        # 如果 Y 轴分散度更大，说明是纵向排列（书脊竖着）→ 按 X 坐标（列）分组
        if x_std > y_std:
            print("📸 检测到横向拍摄，按行分组")
            return self._group_by_coordinate(text_blocks, axis='y', threshold=50)
        else:
            print("📸 检测到纵向拍摄，按列分组")
            return self._group_by_coordinate(text_blocks, axis='x', threshold=50)

    def _group_by_coordinate(self, text_blocks, axis='x', threshold=50):
        """
        根据指定坐标轴将文字块分组
        
        Args:
            text_blocks: 文字块列表
            axis: 分组轴 ('x' 或 'y')
            threshold: 坐标差距阈值（像素）
            
        Returns:
            list: 分组列表
        """
        if not text_blocks:
            return []
        
        # 按指定轴排序
        sorted_blocks = sorted(text_blocks, key=lambda b: b[axis])
        
        groups = []
        current_group = [sorted_blocks[0]]
        
        for block in sorted_blocks[1:]:
            # 如果与当前组的最后一个块在该轴上接近，归入同一组
            if abs(block[axis] - current_group[-1][axis]) < threshold:
                current_group.append(block)
            else:
                # 否则开始新的一组
                groups.append(current_group)
                current_group = [block]
        
        # 添加最后一组
        if current_group:
            groups.append(current_group)
        
        print(f"✅ 共分成 {len(groups)} 组（本书）")
        return groups



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
