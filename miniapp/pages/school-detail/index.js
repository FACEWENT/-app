const api = require('../../utils/request')

Page({
  data: {
    detail: null
  },

  onLoad(options) {
    if (options.id) {
      this.fetchDetail(options.id)
    }
  },

  async fetchDetail(id) {
    try {
      const response = await api.get(`/institutions/${id}`)
      const detail = response.data
      detail.offerings = detail.offerings.map((item) => ({
        ...item,
        subject_text: item.subject_codes.join(' / ')
      }))
      this.setData({ detail })
      wx.setNavigationBarTitle({
        title: detail.name
      })
    } catch (error) {
      wx.showToast({ title: '加载详情失败', icon: 'none' })
    }
  }
})
