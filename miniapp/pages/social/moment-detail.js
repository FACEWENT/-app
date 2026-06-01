const request = require('../../utils/request');

Page({
  data: {
    momentId: '',
    userId: null,
    moment: null,
    comments: [],
    commentContent: '',
    inputFocus: false
  },

  onLoad(options) {
    this.setData({ 
      momentId: options.id,
      userId: wx.getStorageSync('userId')
    });
    this.loadMomentDetail();
    this.loadComments();
  },

  // 加载瞬间详情
  async loadMomentDetail() {
    try {
      const res = await request.get(`/moments/${this.data.momentId}`);
      if (res.data) {
        this.setData({ moment: res.data });
      }
    } catch (e) {
      console.error('加载瞬间详情失败:', e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  // 加载评论列表
  async loadComments() {
    try {
      const res = await request.get(`/moments/${this.data.momentId}/comments`, {
        page: 1,
        page_size: 50
      });

      if (res.data && res.data.items) {
        this.setData({ comments: res.data.items });
      }
    } catch (e) {
      console.error('加载评论失败:', e);
    }
  },

  // 预览图片
  previewImage(e) {
    const index = e.currentTarget.dataset.index;
    wx.previewImage({
      current: this.data.moment.images[index],
      urls: this.data.moment.images
    });
  },

  // 点赞
  async onLike() {
    if (!this.data.userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    try {
      const res = await request.post(
        `/moments/${this.data.momentId}/like`,
        {},
        { user_id: this.data.userId }
      );

      if (res.data) {
        const moment = { ...this.data.moment };
        moment.is_liked = res.data.is_liked;
        moment.like_count += res.data.is_liked ? 1 : -1;
        this.setData({ moment });
      }
    } catch (e) {
      console.error('点赞失败:', e);
    }
  },

  // 聚焦评论框
  focusComment() {
    this.setData({ inputFocus: true });
  },

  // 评论输入
  onCommentInput(e) {
    this.setData({ commentContent: e.detail.value });
  },

  // 提交评论
  async submitComment() {
    if (!this.data.userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    const content = this.data.commentContent.trim();
    if (!content) {
      wx.showToast({ title: '请输入评论内容', icon: 'none' });
      return;
    }

    try {
      await request.post(
        `/moments/${this.data.momentId}/comments`,
        {},
        {
          user_id: this.data.userId,
          content: content
        }
      );

      wx.showToast({ title: '评论成功', icon: 'success' });
      
      // 清空输入框
      this.setData({ 
        commentContent: '',
        inputFocus: false
      });

      // 重新加载评论
      this.loadComments();
      
      // 更新评论数
      const moment = { ...this.data.moment };
      moment.comment_count += 1;
      this.setData({ moment });
    } catch (e) {
      console.error('评论失败:', e);
      wx.showToast({ title: '评论失败', icon: 'none' });
    }
  }
});
