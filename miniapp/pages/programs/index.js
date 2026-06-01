const api = require('../../utils/request')

Page({
  data: {
    keyword: '',
    programs: []
  },

  onLoad() {
    this.fetchPrograms()
  },

  onKeywordChange(event) {
    this.setData({ keyword: event.detail.value })
  },

  async fetchPrograms() {
    try {
      const response = await api.get('/programs', {
        keyword: this.data.keyword
      })
      this.setData({ programs: response.data.items })
    } catch (error) {
      wx.showToast({ title: '加载专业失败', icon: 'none' })
    }
  },

  onSearch() {
    this.fetchPrograms()
  }
})
