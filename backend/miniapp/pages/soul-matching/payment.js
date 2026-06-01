const app = getApp()
const { request } = require('../../utils/request')

Page({
  data: {
    orderId: '',
    loading: false
  },

  onLoad(options) {
    this.setData({ orderId: options.orderId })
  },

  async handlePay() {
    if (this.data.loading) return
    
    this.setData({ loading: true })
    wx.showLoading({ title: '支付中...' })

    try {
      // 模拟支付
      await request({
        url: `/api/v1/soul-matching/orders/${this.data.orderId}/pay`,
        method: 'POST'
      })

      wx.hideLoading()
      wx.showToast({ title: '支付成功', icon: 'success' })

      // 跳转到匹配动画页面
      setTimeout(() => {
        wx.navigateTo({
          url: `/pages/soul-matching/matching?orderId=${this.data.orderId}`
        })
      }, 1000)
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '支付失败', icon: 'none' })
      this.setData({ loading: false })
    }
  }
})
