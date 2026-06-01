const request = require('../../utils/request');

Page({
  data: {
    recordId: '',
    matchType: 'free',
    matchData: null
  },

  onLoad(options) {
    this.setData({ 
      recordId: options.recordId,
      matchType: options.type || 'free'
    });
    this.loadMatchResult();
  },

  async loadMatchResult() {
    wx.showLoading({ title: '加载中...' });
    
    try {
      const res = await request.get(`/soul-matching/records/${this.data.recordId}`);

      if (res.data) {
        const record = res.data;
        this.setData({
          matchData: {
            score: record.match_score || 0,
            avatar: record.matched_user_avatar || '/images/default-avatar.png',
            nickname: record.matched_user_nickname || '考研研友',
            major: record.matched_user_major || '',
            school: record.matched_user_school || '',
            exam_year: record.matched_exam_year || '',
            target_major: record.matched_target_major || '',
            degree_type: record.matched_degree_type || '',
            learning_style: record.matched_learning_style || '',
            personality: record.matched_personality || '',
            bio: record.matched_user_bio || ''
          }
        });
      }
    } catch (err) {
      wx.showToast({ title: err.message || '加载失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  async handleAccept() {
    wx.showLoading({ title: '处理中...' });
    
    try {
      await request.post(`/soul-matching/records/${this.data.recordId}/accept`);

      wx.hideLoading();
      wx.showToast({ title: '已发送打招呼', icon: 'success' });

      // 跳转到聊天页面
      setTimeout(() => {
        wx.navigateBack({ delta: 2 });
      }, 1500);
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '操作失败', icon: 'none' });
    }
  },

  async handleReject() {
    wx.showLoading({ title: '处理中...' });
    
    try {
      await request.post(`/soul-matching/records/${this.data.recordId}/reject`);

      wx.hideLoading();
      
      // 根据匹配类型决定下一步
      if (this.data.matchType === 'premium') {
        // 付费匹配，创建新订单
        const userId = wx.getStorageSync('userId');
        const order = await request.post('/soul-matching/orders', {
          user_id: userId,
          price: 9.9
        });

        wx.navigateTo({
          url: `/pages/soul-matching/payment?orderId=${order.id}`
        });
      } else {
        // 免费匹配，直接返回重新匹配
        wx.navigateBack({ delta: 2 });
      }
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '操作失败', icon: 'none' });
    }
  },

  goBack() {
    wx.navigateBack();
  }
});
