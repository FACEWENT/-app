const app = getApp()
const { request } = require('../../utils/request')

Page({
  data: {
    recordId: '',
    matchData: null
  },

  onLoad(options) {
    this.setData({ recordId: options.recordId })
    this.loadMatchResult()
  },

  async loadMatchResult() {
    wx.showLoading({ title: '加载中...' })
    
    try {
      const res = await request({
        url: `/api/v1/soul-matching/records`,
        method: 'GET'
      })

      // 找到最新的匹配记录
      const record = res.data.find(r => r.id == this.data.recordId)
      
      if (record) {
        this.setData({
          matchData: {
            score: record.match_score,
            avatar: record.matched_user_avatar || '/images/default-avatar.png',
            nickname: record.matched_user_nickname,
            major: record.matched_user_major,
            school: record.matched_user_school,
            exam_year: record.matched_exam_year,
            target_major: record.matched_target_major,
            degree_type: record.matched_degree_type,
            learning_style: record.matched_learning_style,
            personality: record.matched_personality,
            bio: record.matched_user_bio
          }
        })
      }
    } catch (err) {
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  async handleAccept() {
    wx.showLoading({ title: '处理中...' })
    
    try {
      await request({
        url: `/api/v1/soul-matching/records/${this.data.recordId}/accept`,
        method: 'POST'
      })

      wx.hideLoading()
      wx.showToast({ title: '已接受匹配', icon: 'success' })

      // 跳转到聊天页面或返回列表
      setTimeout(() => {
        wx.navigateBack({ delta: 2 })
      }, 1500)
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '操作失败', icon: 'none' })
    }
  },

  async handleReject() {
    wx.showLoading({ title: '处理中...' })
    
    try {
      await request({
        url: `/api/v1/soul-matching/records/${this.data.recordId}/reject`,
        method: 'POST'
      })

      wx.hideLoading()
      
      // 创建新订单并重新匹配
      try {
        const order = await request({
          url: '/api/v1/soul-matching/orders',
          method: 'POST',
          data: { price: 9.9 }
        })

        wx.navigateTo({
          url: `/pages/soul-matching/payment?orderId=${order.id}`
        })
      } catch (err) {
        wx.showToast({ title: '创建订单失败', icon: 'none' })
      }
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message || '操作失败', icon: 'none' })
    }
  }
})
