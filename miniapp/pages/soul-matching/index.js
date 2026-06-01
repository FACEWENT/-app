const request = require('../../utils/request');

Page({
  data: {
    matchRecords: [],
    userId: null
  },

  onLoad() {
    const userId = wx.getStorageSync('userId');
    if (userId) {
      this.setData({ userId });
      this.loadMatchRecords();
    }
  },

  onShow() {
    if (this.data.userId) {
      this.loadMatchRecords();
    }
  },

  // 加载匹配记录
  async loadMatchRecords() {
    try {
      const res = await request.get('/soul-matching/records', {
        user_id: this.data.userId,
        page: 1,
        page_size: 5
      });

      if (res.data && res.data.items) {
        this.setData({ matchRecords: res.data.items });
      }
    } catch (e) {
      console.error('加载匹配记录失败:', e);
    }
  },

  // 免费快速匹配
  onFreeMatch() {
    const userId = wx.getStorageSync('userId');
    if (!userId) {
      wx.showModal({
        title: '提示',
        content: '请先登录',
        success: (res) => {
          if (res.confirm) {
            wx.switchTab({ url: '/pages/me/index' });
          }
        }
      });
      return;
    }

    wx.showModal({
      title: '⚡ 快速匹配',
      content: '将为您随机匹配一位在线研友，是否继续？',
      confirmText: '开始匹配',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: '/pages/soul-matching/matching?type=free'
          });
        }
      }
    });
  },

  // 付费高级匹配
  onPremiumMatch() {
    const userId = wx.getStorageSync('userId');
    if (!userId) {
      wx.showModal({
        title: '提示',
        content: '请先登录',
        success: (res) => {
          if (res.confirm) {
            wx.switchTab({ url: '/pages/me/index' });
          }
        }
      });
      return;
    }

    wx.navigateTo({
      url: '/pages/soul-matching/preferences'
    });
  },

  // 查看匹配记录
  viewMatchRecord(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/soul-matching/result?recordId=${id}`
    });
  }
});
