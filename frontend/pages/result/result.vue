<script setup>
/**
 * 结果页 - 显示书籍识别结果
 * 功能：展示识别出的书籍卡片列表
 */
import { ref, onLoad } from 'vue'

// ============ 状态 ============
const resultData = ref(null)    // 识别结果数据
const books = ref([])           // 书籍列表
const ocrText = ref('')         // OCR 原始文本

// ============ 生命周期 ============
onLoad((options) => {
  if (options.data) {
    try {
      resultData.value = JSON.parse(decodeURIComponent(options.data))
      books.value = resultData.value.books || []
      ocrText.value = resultData.value.ocr_text || ''
    } catch (e) {
      console.error('解析数据失败:', e)
    }
  }
})

// ============ 方法 ============

/**
 * 获取分类颜色
 */
function getCategoryColor(category) {
  const colors = {
    '高等数学': '#FF6B6B',
    '线性代数': '#4ECDC4',
    '概率统计': '#45B7D1',
    '大学物理': '#96CEB4',
    '电子电路': '#FFEAA7',
    '程序设计': '#DDA0DD',
    '数据结构': '#98D8C8',
    '计算机网络': '#F7DC6F',
    '其他': '#BDC3C7'
  }
  return colors[category] || colors['其他']
}

/**
 * 复制书籍信息
 */
function copyBookInfo(book) {
  const text = `《${book.title}》${book.author ? ' - ' + book.author : ''}${book.edition ? ' ' + book.edition : ''}`
  uni.setClipboardData({
    data: text,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    }
  })
}

/**
 * 返回首页重新识别
 */
function goBack() {
  uni.navigateBack()
}
</script>

<template>
  <view class="container">
    <!-- 顶部统计 -->
    <view class="header">
      <text class="title">识别完成 ✨</text>
      <text class="count">共识别出 {{ books.length }} 本书籍</text>
    </view>

    <!-- 书籍卡片列表 -->
    <view class="book-list">
      <view 
        v-for="(book, index) in books" 
        :key="index" 
        class="book-card"
        @longpress="copyBookInfo(book)"
      >
        <!-- 分类标签 -->
        <view 
          class="category-tag" 
          :style="{ backgroundColor: getCategoryColor(book.category) }"
        >
          {{ book.category || '其他' }}
        </view>
        
        <!-- 书籍信息 -->
        <view class="book-info">
          <text class="book-title">{{ book.title }}</text>
          
          <view class="book-meta">
            <view v-if="book.author" class="meta-item">
              <text class="meta-icon">👤</text>
              <text>{{ book.author }}</text>
            </view>
            <view v-if="book.publisher" class="meta-item">
              <text class="meta-icon">🏢</text>
              <text>{{ book.publisher }}</text>
            </view>
            <view v-if="book.edition" class="meta-item">
              <text class="meta-icon">📖</text>
              <text>{{ book.edition }}</text>
            </view>
          </view>
        </view>

        <!-- 操作按钮 -->
        <view class="book-actions">
          <button class="action-btn" @tap="copyBookInfo(book)">
            📋 复制
          </button>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-if="books.length === 0" class="empty">
      <text class="empty-icon">📭</text>
      <text class="empty-text">未识别到书籍信息</text>
    </view>

    <!-- OCR 原文（可展开） -->
    <view v-if="ocrText" class="ocr-section">
      <view class="ocr-header">
        <text class="ocr-title">📝 OCR 识别原文</text>
      </view>
      <scroll-view class="ocr-content" scroll-y>
        <text>{{ ocrText }}</text>
      </scroll-view>
    </view>

    <!-- 底部操作 -->
    <view class="bottom-actions">
      <button class="btn btn-primary" @tap="goBack">
        📷 继续识别
      </button>
    </view>
  </view>
</template>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  padding-bottom: 180rpx;
  box-sizing: border-box;
}

/* 顶部 */
.header {
  text-align: center;
  margin-bottom: 40rpx;
}

.title {
  font-size: 44rpx;
  font-weight: bold;
  color: #fff;
  display: block;
}

.count {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 10rpx;
  display: block;
}

/* 书籍卡片 */
.book-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.book-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 8rpx 30rpx rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.category-tag {
  position: absolute;
  top: 0;
  right: 0;
  padding: 8rpx 24rpx;
  font-size: 22rpx;
  color: #fff;
  border-radius: 0 20rpx 0 16rpx;
  font-weight: 500;
}

.book-info {
  padding-right: 120rpx;
}

.book-title {
  font-size: 34rpx;
  font-weight: bold;
  color: #333;
  display: block;
  line-height: 1.4;
  margin-bottom: 16rpx;
}

.book-meta {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  color: #666;
}

.meta-icon {
  margin-right: 10rpx;
  font-size: 24rpx;
}

.book-actions {
  position: absolute;
  bottom: 30rpx;
  right: 30rpx;
}

.action-btn {
  font-size: 24rpx;
  padding: 10rpx 24rpx;
  background: #f0f0f0;
  border-radius: 30rpx;
  color: #666;
  border: none;
}

/* 空状态 */
.empty {
  text-align: center;
  padding: 100rpx 0;
}

.empty-icon {
  font-size: 100rpx;
  display: block;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 30rpx;
  color: rgba(255, 255, 255, 0.7);
}

/* OCR 原文 */
.ocr-section {
  margin-top: 40rpx;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16rpx;
  overflow: hidden;
}

.ocr-header {
  padding: 20rpx 24rpx;
  background: rgba(255, 255, 255, 0.1);
}

.ocr-title {
  font-size: 26rpx;
  color: #fff;
  font-weight: 500;
}

.ocr-content {
  max-height: 200rpx;
  padding: 20rpx 24rpx;
}

.ocr-content text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
}

/* 底部操作 */
.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24rpx 40rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: linear-gradient(transparent, rgba(102, 126, 234, 0.95));
}

.btn {
  height: 100rpx;
  line-height: 100rpx;
  border-radius: 50rpx;
  font-size: 34rpx;
  font-weight: 500;
  border: none;
}

.btn-primary {
  background: #fff;
  color: #667eea;
  box-shadow: 0 8rpx 30rpx rgba(0, 0, 0, 0.15);
}
</style>
