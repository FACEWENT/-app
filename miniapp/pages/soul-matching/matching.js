const request = require('../../utils/request');

Page({
  data: {
    matchType: 'free', // free 或 premium
    orderId: '',
    statusText: '正在寻找合适的研友...',
    subText: '匹配算法正在运行',
    tipText: '请耐心等待，正在为您匹配最佳研友',
    progress: 0,
    dimensions: [
      { name: '考研年份', icon: '📅', status: 'pending' },
      { name: '目标专业', icon: '📚', status: 'pending' },
      { name: '学位类型', icon: '🎓', status: 'pending' },
      { name: '学习风格', icon: '💡', status: 'pending' },
      { name: '性格偏好', icon: '😊', status: 'pending' }
    ],
    phase: 'searching' // searching, connecting, found
  },

  onLoad(options) {
    const type = options.type || 'free';
    const orderId = options.orderId || '';
    this.setData({ matchType: type, orderId });
    
    if (type === 'premium') {
      this.startPremiumMatching();
    } else {
      this.startFreeMatching();
    }
  },

  // 免费快速匹配
  async startFreeMatching() {
    this.setData({
      statusText: '正在搜索在线研友...',
      subText: '随机匹配中',
      tipText: '正在为您寻找合适的考研伙伴'
    });

    // 模拟快速匹配动画
    await this.animateProgress(0, 30, 1000);
    this.setData({ statusText: '发现潜在匹配...', subText: '正在建立连接' });
    
    await this.animateProgress(30, 60, 1000);
    this.setData({ statusText: '匹配成功！', subText: '正在加载用户信息' });
    
    await this.animateProgress(60, 100, 800);

    // 调用后端免费匹配API
    try {
      const userId = wx.getStorageSync('userId');
      const result = await request.post('/soul-matching/match', {
        user_id: userId,
        type: 'free'
      });

      setTimeout(() => {
        wx.navigateTo({
          url: `/pages/soul-matching/result?recordId=${result.record_id}&type=free`
        });
      }, 500);
    } catch (err) {
      wx.showToast({ title: err.message || '匹配失败', icon: 'none' });
      setTimeout(() => {
        wx.navigateBack();
      }, 2000);
    }
  },

  // 付费高级匹配
  async startPremiumMatching() {
    // 模拟匹配动画过程
    await this.animateProgress(0, 20, 1500, '正在分析考研年份偏好...', 0, 'matching');
    this.setData({ subText: '维度 1/5' });
    
    await this.animateProgress(20, 40, 1500, '正在匹配目标专业...', 1, 'done');
    this.setData({ subText: '维度 2/5' });
    
    await this.animateProgress(40, 60, 1500, '正在匹配学位类型...', 2, 'matching');
    this.setData({ subText: '维度 3/5' });
    
    await this.animateProgress(60, 80, 1500, '正在分析学习风格...', 3, 'done');
    this.setData({ subText: '维度 4/5' });
    
    await this.animateProgress(80, 100, 1500, '正在匹配性格偏好...', 4, 'matching');
    this.setData({ subText: '维度 5/5' });
    
    // 所有维度完成
    this.updateDimension(4, 'done');
    this.setData({
      statusText: '✨ 匹配完成！',
      subText: '找到最佳匹配',
      tipText: '正在为你展示最合适的研友...'
    });

    // 调用后端匹配API
    try {
      const result = await request.post('/soul-matching/match', {
        order_id: this.data.orderId
      });

      setTimeout(() => {
        wx.navigateTo({
          url: `/pages/soul-matching/result?recordId=${result.record_id}&type=premium`
        });
      }, 1000);
    } catch (err) {
      wx.showToast({ title: err.message || '匹配失败', icon: 'none' });
      setTimeout(() => {
        wx.navigateBack();
      }, 2000);
    }
  },

  animateProgress(from, to, duration, tip, dimensionIndex, status) {
    return new Promise((resolve) => {
      const step = (to - from) / 20;
      let current = from;
      const interval = setInterval(() => {
        current += step;
        if (current >= to) {
          current = to;
          clearInterval(interval);
          const data = { progress: Math.round(current) };
          if (tip) data.tipText = tip;
          this.setData(data);
          if (dimensionIndex >= 0) {
            this.updateDimension(dimensionIndex, status);
          }
          resolve();
        } else {
          this.setData({ progress: Math.round(current) });
        }
      }, duration / 20);
    });
  },

  updateDimension(index, status) {
    const dimensions = [...this.data.dimensions];
    dimensions[index].status = status;
    this.setData({ dimensions });
  },

  // 取消匹配
  onCancel() {
    wx.showModal({
      title: '提示',
      content: '确定要取消匹配吗？',
      success: (res) => {
        if (res.confirm) {
          wx.navigateBack();
        }
      }
    });
  }
});
