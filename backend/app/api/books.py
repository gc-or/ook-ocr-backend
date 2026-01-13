"""
书籍识别 API 路由
提供图片上传、书籍识别、搜索、编辑等接口
"""
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body, Header
from pydantic import BaseModel
from typing import Optional

from ..services.ocr_service import get_ocr_service
from ..services.llm_service import get_llm_service
from ..services.db_service import get_db_service


router = APIRouter(prefix="/api", tags=["书籍识别"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ============ 辅助函数 ============

def fuzzy_match_title(title1: str, title2: str) -> float:
    """
    计算两个书名的相似度（0.0-1.0）
    使用 difflib.SequenceMatcher 进行模糊匹配
    """
    from difflib import SequenceMatcher
    return SequenceMatcher(None, title1, title2).ratio()


def enhance_with_db_matching(books_data: list[dict], db_service) -> list[dict]:
    """
    使用数据库中已有记录来增强识别结果
    
    Args:
        books_data: LLM 识别的书籍列表
        db_service: 数据库服务实例
        
    Returns:
        增强后的书籍列表（修正书名、提升置信度）
    """
    # 获取数据库中所有书籍（用于匹配）
    all_books = db_service.search_books(limit=1000)  # 获取足够多的记录用于匹配
    
    enhanced_books = []
    for book in books_data:
        original_title = book.get("title", "")
        best_match = None
        best_similarity = 0.0
        
        # 与数据库中的每本书比对
        for db_book in all_books:
            db_title = db_book.get("title", "")
            similarity = fuzzy_match_title(original_title, db_title)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = db_book
        
        # 如果找到高相似度匹配（>0.8），使用数据库中的正确信息
        if best_similarity >= 0.8 and best_match:
            print(f"📚 匹配成功: '{original_title}' -> '{best_match['title']}' (相似度: {best_similarity:.2%})")
            
            # 使用数据库中的准确信息替换
            book["title"] = best_match["title"]
            if best_match.get("author"):
                book["author"] = best_match["author"]
            if best_match.get("publisher"):
                book["publisher"] = best_match["publisher"]
            if best_match.get("edition"):
                book["edition"] = best_match["edition"]
            if best_match.get("category"):
                book["category"] = best_match["category"]
            
            # 提升置信度（表示这是经过验证的正确结果）
            original_conf = book.get("confidence", 0.5)
            book["confidence"] = max(0.95, original_conf)  # 至少 0.95
            book["_matched_from_db"] = True  # 标记来源
        
        enhanced_books.append(book)
    
    return enhanced_books


# ============ 数据模型 ============

class BookInfo(BaseModel):
    """书籍信息（含价格）"""
    id: Optional[int] = None
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    condition: Optional[str] = "良好"
    description: Optional[str] = None
    contact: Optional[str] = None   # QQ/微信
    owner_id: Optional[str] = None  # 用户 ID
    status: Optional[int] = 0       # 0:在售, 1:已售


class BookUpdate(BaseModel):
    """书籍更新请求"""
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    contact: Optional[str] = None
    status: Optional[int] = None


class AnalyzeResponse(BaseModel):
    success: bool
    message: str
    ocr_text: str = ""
    books: list[BookInfo] = []
    saved_ids: list[int] = []


class UploadResponse(BaseModel):
    success: bool
    message: str
    file_id: str = ""
    filename: str = ""


class SearchResponse(BaseModel):
    success: bool
    total: int
    books: list[BookInfo]


class StatsResponse(BaseModel):
    total: int
    by_category: dict


# ============ 上传与识别 ============

@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """上传书脊图片"""
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
    
    file_id = str(uuid.uuid4())
    extension = Path(file.filename).suffix or ".jpg"
    filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / filename
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    return UploadResponse(success=True, message="图片上传成功", file_id=file_id, filename=filename)


import asyncio

# 并发控制：限制只有 1 个 OCR 任务同时进行，防止内存溢出
ocr_semaphore = asyncio.Semaphore(1)

@router.post("/analyze/{file_id}", response_model=AnalyzeResponse)
async def analyze_image(
    file_id: str, 
    save: bool = True,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_contact: Optional[str] = Header(None, alias="X-Contact"),
    x_delivery_method: Optional[str] = Header(None, alias="X-Delivery-Method"),
    x_pickup_location: Optional[str] = Header(None, alias="X-Pickup-Location"),
    x_delivery_fee: Optional[str] = Header(None, alias="X-Delivery-Fee")
):
    """
    分析书脊图片，提取书籍信息
    
    Header X-User-ID: 当前用户 ID
    Header X-Contact: 当前用户联系方式
    Header X-Delivery-Method: 交易方式
    Header X-Pickup-Location: 自提地点
    Header X-Delivery-Fee: 配送费用
    """
    import time
    start_total = time.time()
    
    matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_id}")
    
    file_path = matching_files[0]
    
    try:
        # OCR (CPU 密集型任务，放入线程池并加锁)
        t0 = time.time()
        ocr_service = get_ocr_service()
        
        # 1. 抢锁 (如果有人在用，这里会排队等待，但不会阻塞主线程)
        async with ocr_semaphore:
            # 2. 扔到后台线程跑 (释放主线程去处理别人的 HTTP 请求)
            ocr_text = await asyncio.to_thread(ocr_service.extract_text, str(file_path))
            
        t1 = time.time()
        print(f"⏱️ [Perf] OCR Engine took: {t1 - t0:.2f}s")
        
        if not ocr_text.strip():
            return AnalyzeResponse(success=False, message="未能从图片中识别出文字", ocr_text="")
        
        # LLM
        t2 = time.time()
        llm_service = get_llm_service()
        books_data = await llm_service.extract_book_info(ocr_text)
        t3 = time.time()
        print(f"⏱️ [Perf] LLM Service took: {t3 - t2:.2f}s")
        
        # 🧠 智能学习：从数据库匹配相似书籍，提升准确率
        if books_data:
            db_service = get_db_service()
            books_data = enhance_with_db_matching(books_data, db_service)
        
        # 补充用户信息和交易方式
        if books_data and x_user_id:
            for book in books_data:
                book["owner_id"] = x_user_id
                if x_contact:
                    book["contact"] = x_contact
                if x_delivery_method:
                    book["delivery_method"] = x_delivery_method
                if x_pickup_location:
                    book["pickup_location"] = x_pickup_location
                if x_delivery_fee:
                    book["delivery_fee"] = x_delivery_fee
        
        # 保存到数据库
        saved_ids = []
        if save and books_data:
            db_service = get_db_service()
            saved_ids = db_service.save_books(books_data, str(file_path), ocr_text)
        
        books = []
        for i, book in enumerate(books_data):
            book_obj = BookInfo(**book)
            if i < len(saved_ids):
                book_obj.id = saved_ids[i]
            books.append(book_obj)
        
        end_total = time.time()
        print(f"⏱️ [Perf] Total Request took: {end_total - start_total:.2f}s")
        
        return AnalyzeResponse(
            success=True,
            message=f"成功识别 {len(books)} 本书籍" + (f"，已保存到数据库" if saved_ids else ""),
            ocr_text=ocr_text,
            books=books,
            saved_ids=saved_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/analyze-direct", response_model=AnalyzeResponse)
async def analyze_direct(
    file: UploadFile = File(...), 
    save: bool = True,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_contact: Optional[str] = Header(None, alias="X-Contact"),
    x_delivery_method: Optional[str] = Header(None, alias="X-Delivery-Method"),
    x_pickup_location: Optional[str] = Header(None, alias="X-Pickup-Location"),
    x_delivery_fee: Optional[str] = Header(None, alias="X-Delivery-Fee")
):
    """一键分析：上传图片并直接返回分析结果"""
    # 这里直接复用 analyze_image 的逻辑，但为了简单，先不支持 header 穿透到 upload，
    # 而是先 upload 再 fake 调用 analyze_image 逻辑
    # 更好的做法是在 analyze_direct 里自己组装逻辑
    
    # 1. Upload
    upload_result = await upload_image(file)
    
    # 2. Analyze (passing user info and delivery info)
    return await analyze_image(
        upload_result.file_id, 
        save=save, 
        x_user_id=x_user_id, 
        x_contact=x_contact,
        x_delivery_method=x_delivery_method,
        x_pickup_location=x_pickup_location,
        x_delivery_fee=x_delivery_fee
    )


# ============ 书籍管理 ============

@router.get("/books", response_model=list[BookInfo])
async def get_books(
    keyword: str = None, 
    category: str = None,
    owner_id: str = None,
    status: int = None,
    limit: int = 50, 
    offset: int = 0
):
    """搜索书籍 (支持分页、筛选)"""
    db_service = get_db_service()
    return db_service.search_books(keyword, category, owner_id, status, limit, offset)


@router.get("/books/{book_id}", response_model=BookInfo)
async def get_book(book_id: int):
    """获取单本书籍详情"""
    db_service = get_db_service()
    book = db_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return BookInfo(**book)


@router.put("/books/{book_id}")
async def update_book(
    book_id: int, 
    book_update: BookUpdate,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """更新书籍信息（需要权限验证）"""
    db_service = get_db_service()
    
    # 检查书籍是否存在
    existing = db_service.get_book_by_id(book_id)
    if not existing:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 【权限检查】如果书籍有 owner_id，则必须匹配
    if existing.get("owner_id") and existing["owner_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="没有权限修改此书籍，只能修改自己发布的书籍")
    
    # 更新
    update_data = book_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供更新内容")
    
    # 如果没变 owner_id，不需要在这里补，db_service 会处理
    
    success = db_service.update_book(book_id, update_data)
    if success:
        updated_book = db_service.get_book_by_id(book_id)
        return {"success": True, "message": "更新成功", "book": BookInfo(**updated_book)}
    else:
        raise HTTPException(status_code=500, detail="更新失败")


@router.delete("/books/{book_id}")
async def delete_book(
    book_id: int,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """删除书籍（需要权限验证）"""
    db_service = get_db_service()
    
    existing = db_service.get_book_by_id(book_id)
    if not existing:
        raise HTTPException(status_code=404, detail="书籍不存在")
    
    # 【权限检查】
    if existing.get("owner_id") and existing["owner_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="没有权限删除此书籍")
        
    success = db_service.delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return {"success": True, "message": "删除成功"}


@router.post("/books/batch/delete")
async def batch_delete_books(
    book_ids: list[int] = Body(...),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """批量删除书籍（需要权限验证）"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="未提供用户ID")
    
    if not book_ids:
        raise HTTPException(status_code=400, detail="未提供书籍ID列表")
    
    db_service = get_db_service()
    deleted_count = db_service.batch_delete_books(book_ids, x_user_id)
    
    return {
        "success": True, 
        "message": f"成功删除 {deleted_count} 本书籍",
        "deleted_count": deleted_count
    }


@router.post("/books/batch/price")
async def batch_update_price(
    book_ids: list[int] = Body(...),
    price: float = Body(...),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """批量修改价格（需要权限验证）"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="未提供用户ID")
    
    if not book_ids:
        raise HTTPException(status_code=400, detail="未提供书籍ID列表")
    
    if price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负数")
    
    db_service = get_db_service()
    updated_count = db_service.batch_update_price(book_ids, price, x_user_id)
    
    return {
        "success": True,
        "message": f"成功修改 {updated_count} 本书籍的价格",
        "updated_count": updated_count
    }



@router.get("/categories")
async def get_categories():
    """获取所有分类列表"""
    db_service = get_db_service()
    categories = db_service.get_all_categories()
    return {"categories": ["全部"] + categories}


@router.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """获取统计信息"""
    db_service = get_db_service()
    return StatsResponse(**db_service.get_statistics())
