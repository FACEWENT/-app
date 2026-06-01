const request = require('../../utils/request');

Page({
  data: {
    note: null,
    loading: false,
    noteId: null,
    userId: null,
    isAuthor: false
  },

  onLoad(options) {
    const noteId = options.id;
    const userId = wx.getStorageSync('userId');
    
    if (noteId) {
      this.setData({ noteId, userId });
      this.loadNoteDetail();
    }
  },

  async loadNoteDetail() {
    this.setData({ loading: true });
    
    try {
      const params = {};
      if (this.data.userId) {
        params.user_id = this.data.userId;
      }

      const res = await request.get(`/experience/notes/${this.data.noteId}`, params);

      if (res.data) {
        this.setData({ 
          note: res.data,
          isAuthor: res.data.user_id === this.data.userId
        });
        wx.setNavigationBarTitle({ title: res.data.title });
      }
    } catch (e) {
      console.error('加载笔记失败:', e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 预览图片
  onPreviewImage(e) {
    const images = e.currentTarget.dataset.images;
    const index = e.currentTarget.dataset.index;
    
    wx.previewImage({
      current: images[index],
      urls: images
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
        `/experience/notes/${this.data.noteId}/like`,
        { user_id: this.data.userId }
      );

      if (res.data) {
        const note = this.data.note;
        note.is_liked = res.data.is_liked;
        note.like_count += res.data.is_liked ? 1 : -1;
        this.setData({ note });
      }
    } catch (e) {
      console.error('点赞失败:', e);
    }
  },

  // 收藏
  async onCollect() {
    if (!this.data.userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    try {
      const res = await request.post(
        `/experience/notes/${this.data.noteId}/collect`,
        { user_id: this.data.userId }
      );

      if (res.data) {
        const note = this.data.note;
        note.is_collected = res.data.is_collected;
        note.collect_count += res.data.is_collected ? 1 : -1;
        this.setData({ note });
        
        wx.showToast({ 
          title: res.data.is_collected ? '收藏成功' : '取消收藏', 
          icon: 'success' 
        });
      }
    } catch (e) {
      console.error('收藏失败:', e);
    }
  },

  // 评论
  onComment() {
    wx.showModal({
      title: '评论',
      editable: true,
      placeholderText: '请输入评论内容',
      success: async (res) => {
        if (res.confirm && res.content) {
          try {
            await request.post(
              `/experience/notes/${this.data.noteId}/comments`,
              {
                user_id: this.data.userId,
                content: res.content
              }
            );

            wx.showToast({ title: '评论成功', icon: 'success' });
            this.loadNoteDetail();
          } catch (e) {
            console.error('评论失败:', e);
            wx.showToast({ title: '评论失败', icon: 'none' });
          }
        }
      }
    });
  }
});
