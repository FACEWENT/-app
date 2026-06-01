const request = require('../../utils/request');

Page({
  data: {
    title: '',
    content: '',
    category: '',
    tagsInput: '',
    images: [],
    submitting: false
  },

  onInputTitle(e) {
    this.setData({ title: e.detail.value });
  },

  onInputContent(e) {
    this.setData({ content: e.detail.value });
  },

  onInputTags(e) {
    this.setData({ tagsInput: e.detail.value });
  },

  onSelectCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({ 
      category: this.data.category === category ? '' : category 
    });
  },

  // 添加图片
  onAddImage() {
    const that = this;
    wx.chooseImage({
      count: 9 - this.data.images.length,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success(res) {
        that.setData({
          images: [...that.data.images, ...res.tempFilePaths]
        });
      }
    });
  },

  // 删除图片
  onDeleteImage(e) {
    const index = e.currentTarget.dataset.index;
    const images = this.data.images;
    images.splice(index, 1);
    this.setData({ images });
  },

  // 提交发布
  async onSubmit() {
    if (!this.data.title.trim()) {
      wx.showToast({ title: '请输入标题', icon: 'none' });
      return;
    }

    if (!this.data.content.trim()) {
      wx.showToast({ title: '请输入正文内容', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });

    try {
      const userId = wx.getStorageSync('userId');
      
      // 解析标签
      let tags = [];
      if (this.data.tagsInput.trim()) {
        tags = this.data.tagsInput.trim().split(/\s+/);
      }

      // 注意：图片需要先上传到服务器获取URL
      // 这里简化处理，实际应该调用图片上传API
      const imagesData = this.data.images.map(url => ({ url }));
      
      await request.post('/experience/notes', {
        user_id: userId,
        title: this.data.title,
        content: this.data.content,
        category: this.data.category || null,
        tags: tags.length > 0 ? tags : null,
        images: imagesData.length > 0 ? imagesData : null
      });

      wx.showToast({
        title: '发布成功',
        icon: 'success'
      });

      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (e) {
      console.error('发布失败:', e);
      wx.showToast({
        title: '发布失败: ' + (e.message || '未知错误'),
        icon: 'none',
        duration: 3000
      });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
