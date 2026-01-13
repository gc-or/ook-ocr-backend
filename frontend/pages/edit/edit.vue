<template>
	<view class="container">
		<view class="card">
			<view class="form-item">
				<text class="label">书名 *</text>
				<input class="input" v-model="form.title" placeholder="请输入书名" />
			</view>
			
			<view class="form-row">
				<view class="form-item flex-1">
					<text class="label">作者</text>
					<input class="input" v-model="form.author" placeholder="作者名" />
				</view>
				<view class="form-item flex-1 ml-10">
					<text class="label">版次</text>
					<input class="input" v-model="form.edition" placeholder="如: 第3版" />
				</view>
			</view>
			
			<view class="form-item">
				<text class="label">出版社</text>
				<input class="input" v-model="form.publisher" placeholder="出版社名称" />
			</view>
			
			<view class="form-row">
				<view class="form-item flex-1">
					<text class="label">💰 价格 (元)</text>
					<input class="input" type="digit" v-model="form.price" placeholder="0.00" />
				</view>
				<view class="form-item flex-1 ml-10">
					<text class="label">成色</text>
					<picker :range="conditions" @change="onConditionChange" :value="conditionIndex">
						<view class="picker-view">{{ form.condition || '请选择' }}</view>
					</picker>
				</view>
			</view>
			
			<view class="form-item">
				<text class="label">📞 联系 QQ</text>
				<input class="input" type="number" v-model="form.contact" placeholder="联系卖家的 QQ 号" />
			</view>
			
			<view class="form-item">
				<text class="label">分类</text>
				<picker :range="categories" @change="onCategoryChange" :value="categoryIndex">
					<view class="picker-view">{{ form.category || '请选择' }}</view>
				</picker>
			</view>
			
			<view class="form-item">
				<text class="label">备注描述</text>
				<textarea class="textarea" v-model="form.description" placeholder="添加备注信息..." />
			</view>
			
			<button class="btn btn-primary" :loading="saving" @click="save">💾 保存修改</button>
			<button class="btn btn-danger" :loading="deleting" @click="remove">🗑️ 删除书籍</button>
		</view>
	</view>
</template>

<script>
	import { request } from '../../utils/request.js';
	
	export default {
		data() {
			return {
				id: null,
				form: {
					title: '', author: '', edition: '', publisher: '',
					price: '', condition: '良好', category: '其他', description: ''
				},
				conditions: ['全新', '九成新', '良好', '有笔记', '旧书'],
				categories: ['高等数学', '线性代数', '概率统计', '大学物理', '电子电路', '程序设计', '数据结构', '计算机网络', '其他'],
				saving: false,
				deleting: false
			}
		},
		computed: {
			conditionIndex() { return this.conditions.indexOf(this.form.condition) },
			categoryIndex() { return this.categories.indexOf(this.form.category) }
		},
		onLoad(options) {
			if (options.id) {
				this.id = options.id;
				this.loadBook(options.id);
			}
		},
		methods: {
			async loadBook(id) {
				try {
					const res = await request({ url: `/api/books/${id}` });
					this.form = { ...this.form, ...res };
				} catch (e) {
					uni.showToast({ title: '加载失败', icon: 'none' });
				}
			},
			
			onConditionChange(e) { this.form.condition = this.conditions[e.detail.value]; },
			onCategoryChange(e) { this.form.category = this.categories[e.detail.value]; },
			
			async save() {
				if (!this.form.title) return uni.showToast({ title: '请输入书名', icon: 'none' });
				
				this.saving = true;
				try {
					const data = { ...this.form };
					if (data.price) data.price = parseFloat(data.price);
					
					await request({
						url: `/api/books/${this.id}`,
						method: 'PUT',
						data: data
					});
					
					uni.showToast({ title: '保存成功' });
					setTimeout(() => uni.navigateBack(), 1000);
				} catch (e) {
					console.error(e);
				} finally {
					this.saving = false;
				}
			},
			
			async remove() {
				const res = await uni.showModal({ content: '确定要删除这本书吗？' });
				if (res.cancel) return;
				
				this.deleting = true;
				try {
					await request({ url: `/api/books/${this.id}`, method: 'DELETE' });
					uni.showToast({ title: '删除成功' });
					setTimeout(() => uni.navigateBack(), 1000);
				} catch (e) {
					console.error(e);
				} finally {
					this.deleting = false;
				}
			}
		}
	}
</script>

<style>
	.container { padding: 20px; background: #f5f7fa; min-height: 100vh; }
	.card { background: #fff; border-radius: 12px; padding: 20px; }
	
	.form-item { margin-bottom: 20px; }
	.form-row { display: flex; }
	.flex-1 { flex: 1; }
	.ml-10 { margin-left: 10px; }
	
	.label { display: block; font-size: 13px; color: #666; margin-bottom: 8px; }
	.input { border: 1px solid #eee; height: 44px; padding: 0 12px; border-radius: 8px; font-size: 15px; }
	.textarea { border: 1px solid #eee; width: 100%; height: 100px; padding: 10px; border-radius: 8px; font-size: 15px; }
	.picker-view { border: 1px solid #eee; height: 44px; line-height: 44px; padding: 0 12px; border-radius: 8px; font-size: 15px; }
	
	.btn { margin-top: 20px; border-radius: 25px; }
	.btn-primary { background-color: #667eea; color: #fff; }
	.btn-danger { background-color: #fff; color: #e74c3c; border: 1px solid #e74c3c; margin-top: 15px; }
</style>
