const request = require('../../utils/request');

Page({
  data: {
    posts: [],
    loading: false,
    hasMore: true,
    page: 1,
    pageSize: 20,
    filterType: '',
    keyword: ''
  },

  onLoad() {
    this.loadPosts();
  },

  onShow() {
    // 每次显示时刷新
    this.setData({ page: 1, posts: [] });
    this.loadPosts();
  },

  // 加载帖子列表
  async loadPosts() {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const params = {
        page: this.data.page,
        page_size: this.data.pageSize
      };

      if (this.data.filterType) {
        params.post_type = this.data.filterType;
      }

      if (this.data.keyword) {
        params.keyword = this.data.keyword;
      }

      const res = await request.get('/study/posts', params);

      if (res.data) {
        const newPosts = res.data.items.map(post => ({
          ...post,
          created_at: this.formatTime(post.created_at)
        }));

        this.setData({
          posts: this.data.page === 1 ? newPosts : [...this.data.posts, ...newPosts],
          hasMore: newPosts.length === this.data.pageSize,
          page: this.data.page + 1
        });
      }
    } catch (e) {
      console.error('加载帖子失败:', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  // 加载更多
  onLoadMore() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadPosts();
    }
  },

  // 筛选类型
  onFilterType(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({
      filterType: type,
      page: 1,
      posts: []
    });
    this.loadPosts();
  },

  // 搜索
  onSearch() {
    wx.showModal({
      title: '搜索',
      editable: true,
      placeholderText: '输入关键词搜索',
      success: (res) => {
        if (res.confirm && res.content) {
          this.setData({
            keyword: res.content,
            page: 1,
            posts: []
          });
          this.loadPosts();
        }
      }
    });
  },

  // 发布
  onPublish() {
    wx.navigateTo({
      url: '/pages/study/publish'
    });
  },

  // 帖子详情
  onPostTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/study/detail?id=${id}`
    });
  },

  // 格式化时间
  formatTime(timeStr) {
    if (!timeStr) return '';
    const time = new Date(timeStr);
    const now = new Date();
    const diff = now - time;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
    
    return `${time.getMonth() + 1}-${time.getDate()}`;
  }
});
