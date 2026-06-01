const request = require('../../utils/request');

Page({
  data: {
    targetSchool: null
  },

  onShow() {
    this.loadTargetSchool();
  },

  // 加载目标院校信息
  async loadTargetSchool() {
    const userId = wx.getStorageSync('userId');
    if (!userId) return;

    try {
      const res = await request.get('/tutoring/target-school', { user_id: userId });
      
      if (res.data) {
        this.setData({ targetSchool: res.data });
      }
    } catch (e) {
      console.error('加载目标院校失败:', e);
    }
  },

  // 跳转到目标院校设置
  onTargetSchool() {
    wx.navigateTo({
      url: '/pages/tutoring/target-school'
    });
  }
})
