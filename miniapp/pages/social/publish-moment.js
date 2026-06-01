const request = require('../../utils/request');

Page({
  data: {
    content: '',
    moodTag: '',
    images: [],
    locationName: '',
    province: '',
    city: '',
    district: '',
    latitude: null,
    longitude: null,
    submitting: false
  },

  onInputContent(e) {
    this.setData({ content: e.detail.value });
  },

  onSelectMood(e) {
    const mood = e.currentTarget.dataset.mood;
    this.setData({ 
      moodTag: this.data.moodTag === mood ? '' : mood 
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

  // 选择位置
  onChooseLocation() {
    const that = this;
    wx.chooseLocation({
      success(res) {
        // 解析地址信息
        const address = res.address;
        let province = '';
        let city = '';
        let district = '';
        
        // 简单解析地址（实际应该使用更精确的解析）
        const parts = address.split(' ');
        if (parts.length >= 1) province = parts[0];
        if (parts.length >= 2) city = parts[1];
        if (parts.length >= 3) district = parts[2];
        
        that.setData({
          locationName: res.name,
          province: province,
          city: city,
          district: district,
          latitude: res.latitude,
          longitude: res.longitude
        });
      },
      fail(err) {
        console.error('选择位置失败:', err);
      }
    });
  },

  // 提交发布
  async onSubmit() {
    console.log('点击发布按钮');
    console.log('content:', this.data.content);
    console.log('userId:', wx.getStorageSync('userId'));
    
    if (!this.data.content.trim()) {
      wx.showToast({ title: '请输入内容', icon: 'none' });
      return;
    }

    const userId = wx.getStorageSync('userId');
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });

    try {
      // 注意：图片需要先上传到服务器获取URL
      // 这里简化处理，只使用本地路径作为示例
      // 实际应该调用图片上传API
      
      await request.post('/moments', {}, {
        user_id: userId,
        content: this.data.content,
        mood_tag: this.data.moodTag || null,
        location_name: this.data.locationName || null,
        province: this.data.province || null,
        city: this.data.city || null,
        district: this.data.district || null,
        latitude: this.data.latitude || null,
        longitude: this.data.longitude || null,
        images: this.data.images.join(',') || null
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
