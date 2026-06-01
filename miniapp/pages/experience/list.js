const request = require('../../utils/request');

Page({
  data: {
    notes: [],
    loading: false,
    hasMore: true,
    page: 1,
    pageSize: 10,
    category: '',
    sortBy: 'newest',
    userId: null
  },

  onLoad() {
    this.setData({
      userId: wx.getStorageSync('userId')
    });
    this.loadNotes();
  },

  onShow() {
    this.loadNotes();
  },

  // 加载笔记列表
  async loadNotes() {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const params = {
        page: this.data.page,
        page_size: this.data.pageSize,
        sort_by: this.data.sortBy
      };
      
      if (this.data.category) {
        params.category = this.data.category;
      }
      
      if (this.data.userId) {
        params.user_id = this.data.userId;
      }

      const res = await request.get('/experience/notes', params);

      if (res.data) {
        const newNotes = res.data.items;
        this.setData({
          notes: this.data.page === 1 ? newNotes : [...this.data.notes, ...newNotes],
          hasMore: newNotes.length === this.data.pageSize,
          page: this.data.page + 1
        });
      }
    } catch (e) {
      console.error('加载笔记失败:', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadNotes();
    }
  },

  // 切换分类
  onCategoryChange(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      category: category,
      page: 1,
      notes: []
    });
    this.loadNotes();
  },

  // 切换排序
  onSortChange(e) {
    const sortBy = e.currentTarget.dataset.sort;
    this.setData({
      sortBy: sortBy,
      page: 1,
      notes: []
    });
    this.loadNotes();
  },

  // 搜索
  onSearch() {
    wx.showToast({ title: '搜索功能开发中', icon: 'none' });
  },

  // 发布笔记
  onPublish() {
    wx.navigateTo({
      url: '/pages/experience/publish'
    });
  },

  // 点击笔记
  onNoteTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/experience/detail?id=${id}`
    });
  }
});
