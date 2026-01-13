<template>
	<view class="container">
		<view class="card">
			<view class="header">
				<text class="title">📚 书籍识别</text>
				<text class="subtitle">拍摄书脊，自动识别信息</text>
			</view>
			
			<!-- 学号输入框 (必填，放在最上方) -->
			<view class="contact-box required-box">
				<text class="contact-label">你的学号 <text class="required-star">*</text></text>
				<input class="contact-input" type="text" v-model="studentId" placeholder="请先填写学号" @blur="saveStudentId" />
			</view>
			
			<!-- QQ 输入框 -->
			<view class="contact-box">
				<text class="contact-label">你的 QQ 号 (选填):</text>
				<input class="contact-input" type="number" v-model="qq" placeholder="方便买家联系你" @blur="saveQQ" />
			</view>
			
			<view class="preview-area" @click="chooseImage">
				<view v-if="!imagePath" class="placeholder">
					<text class="icon">📷</text>
					<text>点击拍摄/选择图片</text>
				</view>
				<image v-else :src="imagePath" mode="aspectFit" class="preview-image"></image>
				<view v-if="imagePath" class="clear-btn" @click.stop="clearImage">✕</view>
			</view>
			
			<view class="status-text">{{ statusText }}</view>
			
			<button class="btn btn-primary" :disabled="!imagePath || loading || !studentId" @click="analyzeImage">
				{{ loading ? '识别中...' : '🔍 开始识别' }}
			</button>
		</view>
		
		<view v-if="result" class="result-section">
			<view class="header">
				<text class="title sm">识别完成 ✨</text>
				<text class="subtitle">已自动保存到书库</text>
			</view>
			
			<view class="book-card" v-for="book in result.books" :key="book.id">
				<view class="category-badge" :style="{ backgroundColor: getCategoryColor(book.category) }">
					{{ book.category || '其他' }}
				</view>
				<view class="book-title">{{ book.title }}</view>
				<view class="book-meta">
					<view v-if="book.author" class="meta-item">👤 {{ book.author }}</view>
					<view v-if="book.publisher" class="meta-item">🏢 {{ book.publisher }}</view>
					<view v-if="book.price" class="book-price">¥{{ book.price }}</view>
					<view v-if="book.contact" class="meta-item contact-info">📞 卖家 QQ: {{ book.contact }}</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { config } from '../../utils/config.js';
	import { request, uploadFile } from '../../utils/request.js';

	export default {
		data() {
			return {
				imagePath: '',
				loading: false,
				statusText: '',
				result: null,
				qq: '',
				studentId: '',
				categoryColors: {
					'高等数学': '#FF6B6B', '线性代数': '#4ECDC4', '其他': '#BDC3C7'
				}
			}
		},
		onLoad() {
			// 读取保存的学号和 QQ
			this.studentId = uni.getStorageSync('user_student_id') || '';
			this.qq = uni.getStorageSync('user_qq') || '';
		},
		methods: {
			saveStudentId() {
				// 保存学号到本地
				if (this.studentId) {
					uni.setStorageSync('user_student_id', this.studentId);
				}
			},
			
			saveQQ() {
				// 保存 QQ 到本地，并在请求工具中自动带上
				if (this.qq) {
					uni.setStorageSync('user_qq', this.qq);
				}
			},
			
			chooseImage() {
				// 必须先填写学号才能选择图片
				if (!this.studentId) {
					uni.showToast({
						title: '请先填写学号',
						icon: 'none'
					});
					return;
				}
				// 保存学号
				this.saveStudentId();
				
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					success: (res) => {
						this.imagePath = res.tempFilePaths[0];
						this.statusText = '图片已选择';
						this.result = null;
					}
				});
			},
			
			clearImage() {
				this.imagePath = '';
				this.statusText = '';
				this.result = null;
			},
			
			async analyzeImage() {
				if (!this.imagePath) return;
				
				// 确保学号已填写
				if (!this.studentId) {
					uni.showToast({
						title: '请先填写学号',
						icon: 'none'
					});
					return;
				}
				
				// 保存学号和 QQ
				this.saveStudentId();
				this.saveQQ();
				
				this.loading = true;
				this.statusText = '正在上传并识别...';
				
				try {
					const uploadRes = await uploadFile(this.imagePath);
					if (!uploadRes.success) throw new Error(uploadRes.message);
					
					const analyzeRes = await request({
						url: `/api/analyze/${uploadRes.file_id}?save=true`,
						method: 'POST'
					});
					
					if (analyzeRes.success && analyzeRes.books.length > 0) {
						this.result = analyzeRes;
						this.statusText = '✅ 识别成功';
					} else {
						this.statusText = analyzeRes.message || '未识别到书籍';
					}
				} catch (e) {
					console.error(e);
					this.statusText = '识别失败: ' + (e.errMsg || '网络错误');
				} finally {
					this.loading = false;
				}
			},
			
			getCategoryColor(cat) { return this.categoryColors[cat] || '#BDC3C7'; }
		}
	}
</script>

<style>
	.container { padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
	.card { background: rgba(255,255,255,0.95); border-radius: 16px; padding: 20px; margin-bottom: 20px; }
	.header { text-align: center; margin-bottom: 20px; }
	.title { font-size: 24px; font-weight: bold; color: #333; display: block; }
	.title.sm { font-size: 20px; color: #fff; }
	.subtitle { font-size: 14px; color: #666; margin-top: 5px; display: block; }
	.result-section .subtitle { color: rgba(255,255,255,0.8); }
	
	.contact-box { background: #f0f4ff; padding: 10px; border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; }
	.contact-box.required-box { background: #fff0f0; border: 1px solid #ffcccc; }
	.contact-label { font-size: 14px; color: #666; margin-right: 10px; white-space: nowrap; }
	.required-star { color: #e74c3c; font-weight: bold; }
	.contact-input { flex: 1; font-size: 14px; height: 30px; }
	
	.preview-area { background: #f5f5f5; border-radius: 12px; height: 250px; display: flex; align-items: center; justify-content: center; position: relative; }
	.preview-image { width: 100%; height: 100%; }
	.placeholder { text-align: center; color: #999; }
	.icon { font-size: 40px; display: block; margin-bottom: 10px; }
	.clear-btn { position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.5); color: #fff; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; }
	
	.btn { margin-top: 15px; border-radius: 25px; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; }
	
	.book-card { background: #fff; border-radius: 12px; padding: 15px; margin-bottom: 10px; position: relative; }
	.category-badge { position: absolute; top: 0; right: 0; padding: 2px 10px; font-size: 11px; color: #fff; border-radius: 0 12px 0 12px; }
	.book-title { font-weight: bold; font-size: 16px; margin-bottom: 5px; }
	.book-meta { font-size: 13px; color: #666; }
	.book-price { color: #e74c3c; font-weight: bold; margin-top: 5px; }
	.contact-info { color: #667eea; font-weight: 500; margin-top: 5px; }
</style>
