const api = require('../../utils/request')

Page({
  data: {
    schoolId: '',
    school: null,
    loading: true,
    expandedPrograms: {}
  },

  onLoad(options) {
    this.setData({ schoolId: options.id })
    this.loadSchoolDetail()
  },

  async loadSchoolDetail() {
    this.setData({ loading: true })
    
    try {
      const res = await api.get(`/institutions/${this.data.schoolId}/detail`)
      if (res.data) {
        this.setData({ school: res.data })
      }
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 展开/收起专业
  toggleProgram(e) {
    const programId = e.currentTarget.dataset.id
    const expanded = { ...this.data.expandedPrograms }
    expanded[programId] = !expanded[programId]
    this.setData({ expandedPrograms: expanded })
  },

  // 打开链接
  openLink(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      wx.setClipboardData({
        data: url,
        success: () => {
          wx.showModal({
            title: '链接已复制',
            content: '请在浏览器中粘贴打开',
            showCancel: false
          })
        }
      })
    }
  }
})
