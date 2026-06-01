const request = require('../../utils/request');

Page({
  data: {
    post: null,
    loading: false,
    postId: null,
    userId: null
  },

  onLoad(options) {
    const postId = options.id;
    const userId = wx.getStorageSync('userId');
    
    if (postId) {
      this.setData({ postId, userId });
      this.loadPostDetail();
    }
  },

  async loadPostDetail() {
    this.setData({ loading: true });
    
    try {
      const params = {};
      if (this.data.userId) {
        params.user_id = this.data.userId;
      }

      const res = await request.get(`/tutoring/posts/${this.data.postId}`, params);

      if (res.data) {
        this.setData({ post: res.data });
        wx.setNavigationBarTitle({ title: res.data.title });
      }
    } catch (e) {
      console.error('加载详情失败:', e);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 点赞
  async onLike() {
    if (!this.data.userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    try {
      const res = await request.post(
        `/tutoring/posts/${this.data.postId}/like`,
        {},
        { user_id: this.data.userId }
      );

      if (res.data) {
        // 更新本地状态
        const post = this.data.post;
        post.is_liked = res.data.is_liked;
        post.like_count += res.data.is_liked ? 1 : -1;
        
        this.setData({ post });
      }
    } catch (e) {
      console.error('点赞失败:', e);
    }
  },

  // 联系TA
  onContact() {
    wx.showModal({
      title: '联系方式',
      content: this.data.post.contact_info || '该用户未提供联系方式',
      showCancel: false
    });
  }
});
