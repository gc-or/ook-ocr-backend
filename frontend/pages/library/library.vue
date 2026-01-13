<template>
	<view class="container">
		<!-- 统计信息 -->
		<view class="stats">
			<view class="stat-item">
				<view class="stat-value">{{ stats.total }}</view>
				<view class="stat-label">书籍总数</view>
			</view>
			<view class="stat-item">
				<view class="stat-value">{{ categoryCount }}</view>
				<view class="stat-label">分类详情</view>
			</view>
		</view>
		
		<!-- 搜索框 -->
		<view class="search-box">
			<input 
				class="search-input" 
				type="text" 
				v-model="keyword" 
				placeholder="搜索书名、作者..." 
				confirm-type="search"
				@confirm="searchBooks"
			/>
			<button class="search-btn" @click="searchBooks">搜索</button>
		</view>
		
		<!-- 分类列表 -->
		<scroll-view scroll-x class="category-scroll" show-scrollbar="false">
			<view class="categories">
				<view 
					v-for="cat in categories" 
					:key="cat"
					:class="['category-tag', currentCategory === cat ? 'active' : '']"
					@click="filterCategory(cat)"
				>
					{{ cat }}
				</view>
			</view>
		</scroll-view>
		
		<!-- 书籍列表 -->
		<view class="book-list">
			<view v-if="loading" class="loading-state">
				<text>加载中...</text>
			</view>
			
			<view v-else-if="books.length === 0" class="empty-state">
				<text class="empty-icon">📭</text>
				<text>没有找到相关书籍</text>
			</view>
			
			<view v-else class="book-card" v-for="book in books" :key="book.id">
				<view class="category-badge" :style="{ backgroundColor: getCategoryColor(book.category) }">
					{{ book.category || '其他' }}
				</view>
				
				<view class="book-title">{{ book.title }}</view>
				
			<view class="book-meta">
				<view v-if="book.author" class="meta-item">👤 {{ book.author }}</view>
				<view v-if="book.publisher" class="meta-item">🏢 {{ book.publisher }}</view>
				<view v-if="book.edition" class="meta-item">📖 {{ book.edition }}</view>
				<view v-if="book.condition" class="meta-item">📦 {{ book.condition }}</view>
				<view v-if="book.delivery_method" class="meta-item">📍 {{ book.delivery_method }}</view>
				<view v-if="book.pickup_location" class="meta-item">📌 {{ book.pickup_location }}</view>
				<view v-if="book.delivery_fee" class="meta-item">🚚 {{ book.delivery_fee }}</view>
				<view v-if="book.contact" class="meta-item contact-info">📞 QQ: {{ book.contact }}</view>
			</view>				<view v-if="book.price" class="book-price">¥{{ book.price }}</view>
				
				<!-- 操作栏 -->
				<view class="book-actions">
					<!-- 如果是自己的书，显示编辑 -->
					<button v-if="isMine(book)" class="action-btn edit-btn" size="mini" @click="openEdit(book)">✏️ 编辑</button>
					
					<!-- 如果是别人的书且有联系方式，显示联系 -->
					<button v-else-if="book.contact" class="action-btn contact-btn" size="mini" @click="contactSeller(book)">💬 联系卖家</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import { request, getCurrentUserId } from '../../utils/request.js';
	
	export default {
		data() {
			return {
				keyword: '',
				currentCategory: '全部',
				categories: ['全部'],
				books: [],
				stats: { total: 0, by_category: {} },
				loading: false,
				currentUserId: '',
				categoryColors: {
					'高等数学': '#FF6B6B', '线性代数': '#4ECDC4', '概率统计': '#45B7D1',
					'大学物理': '#96CEB4', '电子电路': '#FFEAA7', '程序设计': '#DDA0DD',
					'数据结构': '#98D8C8', '计算机网络': '#F7DC6F', '其他': '#BDC3C7'
				}
			}
		},
		computed: {
			categoryCount() {
				return Object.keys(this.stats.by_category).length;
			}
		},
		onShow() {
			this.currentUserId = getCurrentUserId(); // 获取当前用户 ID
			this.loadData();
		},
		methods: {
			isMine(book) {
				// 判断书籍是否属于当前用户
				return book.owner_id === this.currentUserId;
			},
			
			async loadData() {
				await this.fetchCategories();
				await this.fetchStats();
				await this.searchBooks();
			},
			
			async fetchCategories() {
				try {
					const res = await request({ url: '/api/categories' });
					this.categories = res.categories;
				} catch (e) { console.error(e); }
			},
			
			async fetchStats() {
				try {
					const res = await request({ url: '/api/stats' });
					this.stats = res;
				} catch (e) { console.error(e); }
			},
			
			async searchBooks() {
				this.loading = true;
				try {
					const params = {};
					if (this.keyword) params.keyword = this.keyword;
					if (this.currentCategory !== '全部') params.category = this.currentCategory;
					
					const res = await request({ 
						url: '/api/books',
						data: params
					});
					this.books = res.books;
				} catch (e) {
					console.error(e);
				} finally {
					this.loading = false;
				}
			},
			
			filterCategory(cat) {
				this.currentCategory = cat;
				this.searchBooks();
			},
			
			getCategoryColor(cat) {
				return this.categoryColors[cat] || this.categoryColors['其他'];
			},
			
			openEdit(book) {
				uni.navigateTo({
					url: `/pages/edit/edit?id=${book.id}`
				});
			},
			
			contactSeller(book) {
				uni.setClipboardData({
					data: book.contact,
					success: () => {
						uni.showToast({
							title: 'QQ号已复制',
							icon: 'success'
						});
					}
				});
			}
		}
	}
</script>

<style>
	.container { padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }
	
	.stats { display: flex; gap: 15px; margin-bottom: 20px; }
	.stat-item { flex: 1; text-align: center; padding: 15px; background: rgba(255,255,255,0.8); border-radius: 12px; }
	.stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
	.stat-label { font-size: 12px; color: #666; margin-top: 5px; }
	
	.search-box { display: flex; gap: 10px; margin-bottom: 15px; }
	.search-input { flex: 1; padding: 10px 16px; background: #fff; border-radius: 20px; font-size: 14px; height: 40px; }
	.search-btn { height: 40px; line-height: 40px; background: #667eea; color: #fff; font-size: 14px; border-radius: 20px; padding: 0 20px; }
	
	.category-scroll { white-space: nowrap; margin-bottom: 15px; }
	.categories { display: flex; gap: 8px; padding-bottom: 5px; }
	.category-tag { padding: 6px 14px; border-radius: 16px; background: rgba(255,255,255,0.5); color: #666; font-size: 13px; display: inline-block; }
	.category-tag.active { background: #667eea; color: #fff; }
	
	.book-card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; position: relative; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
	.category-badge { position: absolute; top: 0; right: 0; padding: 4px 12px; font-size: 11px; color: #fff; border-radius: 0 12px 0 12px; }
	.book-title { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 8px; padding-right: 60px; }
	.book-meta { font-size: 13px; color: #666; }
	.meta-item { margin-top: 4px; }
	.book-price { font-size: 18px; font-weight: bold; color: #e74c3c; margin-top: 10px; }
	.contact-info { color: #667eea; font-weight: 500; }
	
	.book-actions { margin-top: 12px; display: flex; justify-content: flex-end; gap: 10px; }
	.action-btn { margin: 0; border: none; font-size: 12px; }
	.edit-btn { background: #f0f0f0; color: #666; }
	.contact-btn { background: #e0f2f1; color: #00897b; }
	
	.loading-state, .empty-state { text-align: center; padding: 40px; color: #999; }
	.empty-icon { font-size: 40px; display: block; margin-bottom: 10px; }
</style>
