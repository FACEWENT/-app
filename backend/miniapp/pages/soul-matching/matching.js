const app = getApp()
const { request } = require('../../utils/request')

Page({
  data: {
    orderId: '',
    loadingIcon: '🔍',
    statusText: '正在寻找合适的研友...',
    progress: 0,
    animationDuration: 2,
    currentTip: '正在分析你的匹配偏好',
    dimensions: [
      { name: '考研年份', icon: '📅', status: 'pending' },
      { name: '目标专业', icon: '📚', status: 'pending' },
      { name: '学位类型', icon: '🎓', status: 'pending' },
      { name: '学习风格', icon: '💡', status: 'pending' },
      { name: '性格偏好', icon: '😊', status: 'pending' }
    ],
    matchResult: null
  },

  onLoad(options) {
    this.setData({ orderId: options.orderId })
    this.startMatching()
  },

  async startMatching() {
    // 模拟匹配动画过程
    await this.animateProgress(0, 20, 1500, '正在分析考研年份偏好...', 0, 'matching')
    await this.animateProgress(20, 40, 1500, '正在匹配目标专业...', 1, 'done')
    await this.animateProgress(40, 60, 1500, '正在匹配学位类型...', 2, 'matching')
    await this.animateProgress(60, 80, 1500, '正在分析学习风格...', 3, 'done')
    await this.animateProgress(80, 100, 1500, '正在匹配性格偏好...', 4, 'matching')
    
    // 所有维度完成
    this.updateDimension(4, 'done')
    this.setData({
      loadingIcon: '✨',
      statusText: '匹配完成！',
      currentTip: '正在为你展示最佳匹配...'
    })

    // 调用后端匹配API
    try {
      const result = await request({
        url: '/api/v1/soul-matching/match',
        method: 'POST',
        data: { order_id: this.data.orderId }
      })

      // 跳转到匹配结果页面
      setTimeout(() => {
        wx.navigateTo({
          url: `/pages/soul-matching/result?recordId=${result.record_id}`
        })
      }, 1000)
    } catch (err) {
      wx.showToast({ title: err.message || '匹配失败', icon: 'none' })
      // 失败返回上一页
      setTimeout(() => {
        wx.navigateBack()
      }, 2000)
    }
  },

  animateProgress(from, to, duration, tip, dimensionIndex, status) {
    return new Promise((resolve) => {
      const step = (to - from) / 20
      let current = from
      const interval = setInterval(() => {
        current += step
        if (current >= to) {
          current = to
          clearInterval(interval)
          this.setData({
            progress: Math.round(current),
            currentTip: tip
          })
          if (dimensionIndex >= 0) {
            this.updateDimension(dimensionIndex, status)
          }
          resolve()
        } else {
          this.setData({
            progress: Math.round(current)
          })
        }
      }, duration / 20)
    })
  },

  updateDimension(index, status) {
    const dimensions = this.data.dimensions
    dimensions[index].status = status
    this.setData({ dimensions })
  }
})
