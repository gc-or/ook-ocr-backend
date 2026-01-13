"""
数据库服务模块
使用 SQLite 存储书籍信息，支持搜索、编辑、价格等功能
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


# 数据库文件路径 (优先使用环境变量，支持 Railway 持久化)
DB_PATH = os.getenv("DB_PATH") or (Path(__file__).parent.parent.parent / "books.db")


class DatabaseService:
    """数据库服务类 - 管理书籍信息的存储和查询"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表结构（含用户信息、售卖状态）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建书籍表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT,
                    publisher TEXT,
                    edition TEXT,
                    category TEXT,
                    price REAL DEFAULT NULL,
                    condition TEXT DEFAULT '良好',
                    description TEXT,
                    image_path TEXT,
                    ocr_text TEXT,
                    owner_id TEXT, -- 用户唯一标识 (OpenID)
                    contact TEXT,  -- 联系方式 (QQ/微信)
                    status INTEGER DEFAULT 0, -- 0:在售, 1:已售
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 尝试添加新字段
            for col in [
                ("price", "REAL DEFAULT NULL"),
                ("condition", "TEXT DEFAULT '良好'"),
                ("description", "TEXT"),
                ("owner_id", "TEXT"),
                ("contact", "TEXT"),
                ("status", "INTEGER DEFAULT 0")
            ]:
                try:
                    cursor.execute(f"ALTER TABLE books ADD COLUMN {col[0]} {col[1]}")
                except sqlite3.OperationalError:
                    pass
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_category ON books(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_owner ON books(owner_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_status ON books(status)")
            
            conn.commit()
            print("✅ 数据库初始化完成")
    
    def save_book(self, book_info: dict, image_path: str = None, ocr_text: str = None) -> int:
        """保存书籍信息到数据库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO books (title, author, publisher, edition, category, price, condition, description, owner_id, contact, status, image_path, ocr_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                book_info.get("title", "未知书名"),
                book_info.get("author"),
                book_info.get("publisher"),
                book_info.get("edition"),
                book_info.get("category", "其他"),
                book_info.get("price"),
                book_info.get("condition", "良好"),
                book_info.get("description"),
                book_info.get("owner_id"),
                book_info.get("contact"),
                book_info.get("status", 0),
                image_path,
                ocr_text
            ))
            conn.commit()
            book_id = cursor.lastrowid
            print(f"📚 保存书籍: {book_info.get('title')} (ID: {book_id})")
            return book_id
    
    def save_books(self, books: list[dict], image_path: str = None, ocr_text: str = None) -> list[int]:
        """批量保存多本书籍"""
        ids = []
        for book in books:
            book_id = self.save_book(book, image_path, ocr_text)
            ids.append(book_id)
        print(f"✅ 批量保存了 {len(ids)} 本书")
        return ids
    
    def update_book(self, book_id: int, book_info: dict) -> bool:
        """更新书籍信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建更新字段
            update_fields = []
            params = []
            
            # 允许更新的字段
            allowed_fields = ['title', 'author', 'publisher', 'edition', 'category', 'price', 'condition', 'description', 'contact', 'status']
            
            for field in allowed_fields:
                if field in book_info:
                    update_fields.append(f"{field} = ?")
                    params.append(book_info[field])
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # 如果提供了 owner_id，则作为安全校验条件
            sql_check = ""
            if 'owner_id' in book_info:
                sql_check = " AND owner_id = ?"
                params.append(book_info['owner_id'])
            
            # 最后的 ID 参数
            params.append(book_id)
            
            sql = f"UPDATE books SET {', '.join(update_fields)} WHERE id = ?{sql_check}"
            cursor.execute(sql, params)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def search_books(self, keyword: str = None, category: str = None, 
                     owner_id: str = None, status: int = None,
                     limit: int = 50, offset: int = 0) -> list[dict]:
        """搜索书籍 (支持按用户和状态筛选)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if keyword:
                conditions.append("(title LIKE ? OR author LIKE ? OR publisher LIKE ?)")
                keyword_param = f"%{keyword}%"
                params.extend([keyword_param, keyword_param, keyword_param])
            
            if category and category != "全部":
                conditions.append("category = ?")
                params.append(category)
                
            if owner_id:
                conditions.append("owner_id = ?")
                params.append(owner_id)
                
            if status is not None:
                conditions.append("status = ?")
                params.append(status)
            
            sql = "SELECT * FROM books"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_book_by_id(self, book_id: int) -> Optional[dict]:
        """根据 ID 获取书籍"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_categories(self) -> list[str]:
        """获取所有分类"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM books WHERE category IS NOT NULL ORDER BY category")
            return [row[0] for row in cursor.fetchall()]
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM books")
            total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM books WHERE category IS NOT NULL 
                GROUP BY category ORDER BY count DESC
            """)
            by_category = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {"total": total, "by_category": by_category}
    
    def delete_book(self, book_id: int) -> bool:
        """删除书籍"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def batch_delete_books(self, book_ids: list[int], owner_id: str) -> int:
        """批量删除书籍（仅限本人）"""
        if not book_ids:
            return 0
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 使用 IN 子句批量删除，同时验证 owner_id
            placeholders = ','.join('?' * len(book_ids))
            sql = f"DELETE FROM books WHERE id IN ({placeholders}) AND owner_id = ?"
            cursor.execute(sql, book_ids + [owner_id])
            conn.commit()
            deleted_count = cursor.rowcount
            print(f"🗑️ 批量删除了 {deleted_count} 本书")
            return deleted_count
    
    def batch_update_price(self, book_ids: list[int], price: float, owner_id: str) -> int:
        """批量修改价格（仅限本人）"""
        if not book_ids:
            return 0
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 使用 IN 子句批量更新，同时验证 owner_id
            placeholders = ','.join('?' * len(book_ids))
            sql = f"UPDATE books SET price = ?, updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders}) AND owner_id = ?"
            cursor.execute(sql, [price] + book_ids + [owner_id])
            conn.commit()
            updated_count = cursor.rowcount
            print(f"💰 批量修改了 {updated_count} 本书的价格为 {price} 元")
            return updated_count



# 全局实例
_db_service: Optional[DatabaseService] = None

def get_db_service() -> DatabaseService:
    """获取数据库服务实例"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
