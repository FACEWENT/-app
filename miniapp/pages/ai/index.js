const api = require('../../utils/request')

Page({
  data: {
    question: '',
    loading: false,
    result: null,
    quickPrompts: [
      '我考340分，085404，帮我做冲稳保',
      '计算机技术 355 分适合报哪些学校',
      '081200 方向有哪些稳妥院校',
      '帮我解读苏州大学计算机技术'
    ]
  },

  onInput(event) {
    this.setData({ question: event.detail.value })
  },

  onQuickTap(event) {
    const value = event.currentTarget.dataset.value
    this.setData({ question: value })
  },

  async onSubmit() {
    if (!this.data.question.trim()) {
      wx.showToast({ title: '先输入你的问题', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    try {
      const response = await api.post('/ai/interpret', {
        question: this.data.question
      })
      this.setData({ result: response.data })
    } catch (error) {
      wx.showToast({ title: '解读失败，请检查后端', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  openSchool(event) {
    const id = event.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/school-detail/index?id=${id}`
    })
  }
})
