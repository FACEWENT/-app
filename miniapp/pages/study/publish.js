const request = require('../../utils/request');

Page({
  data: {
    title: '',
    content: '',
    postType: 'book',
    category: '',
    categoryIndex: 0,
    categories: ['数学', '英语', '政治', '专业课', '其他'],
    price: '',
    originalPrice: '',
    condition: 'like_new',
    province: '',
    city: '',
    detailAddress: '',
    latitude: null,
    longitude: null,
    contactInfo: '',
    submitting: false
  },

  onInputTitle(e) {
    this.setData({ title: e.detail.value });
  },

  onInputContent(e) {
    this.setData({ content: e.detail.value });
  },

  onInputPrice(e) {
    this.setData({ price: e.detail.value });
  },

  onInputOriginalPrice(e) {
    this.setData({ originalPrice: e.detail.value });
  },

  onInputContact(e) {
    this.setData({ contactInfo: e.detail.value });
  },

  onSelectType(e) {
    this.setData({ postType: e.currentTarget.dataset.type });
  },

  onCategoryChange(e) {
    this.setData({
      categoryIndex: e.detail.value,
      category: this.data.categories[e.detail.value]
    });
  },

  onSelectCondition(e) {
    this.setData({ condition: e.currentTarget.dataset.condition });
  },

  // 选择位置
  onChooseLocation() {
    const that = this;
    wx.chooseLocation({
      success(res) {
        that.setData({
          province: '',  // 需要从地址解析
          city: res.address.split(' ')[1] || res.name,
          detailAddress: res.name,
          latitude: res.latitude,
          longitude: res.longitude
        });
      }
    });
  },

  // 提交发布
  async onSubmit() {
    const { title, content, postType, price } = this.data;

    if (!title.trim()) {
      wx.showToast({ title: '请输入标题', icon: 'none' });
      return;
    }

    if (!content.trim()) {
      wx.showToast({ title: '请输入详细介绍', icon: 'none' });
      return;
    }

    if (!price) {
      wx.showToast({ title: '请输入价格', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });

    try {
      const userId = wx.getStorageSync('userId');
      
      await request.post('/study/posts', {}, {
        user_id: userId,
        title: title,
        content: content,
        post_type: postType,
        price: parseFloat(price),
        original_price: this.data.originalPrice ? parseFloat(this.data.originalPrice) : null,
        condition_level: this.data.condition,
        province: this.data.province,
        city: this.data.city,
        detail_address: this.data.detailAddress,
        latitude: this.data.latitude,
        longitude: this.data.longitude,
        category: this.data.category,
        contact_info: this.data.contactInfo
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
        title: '发布失败',
        icon: 'none'
      });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
