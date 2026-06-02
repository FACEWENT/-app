const api = require('../../utils/request')

const DEFAULT_USER_ID = 1

Page({
  data: {
    question: '',
    loading: false,
    sessionId: null,
    messages: [],          // 聊天消息列表 {role, content, structured_payload?}
    result: null,          // 兼容老 wxml：最近一次结构化推荐结果
    quickPrompts: [
      '我考340分，085404，帮我做冲稳保',
      '计算机技术 355 分适合报哪些学校',
      '081200 方向有哪些稳妥院校',
      '帮我解读苏州大学计算机技术'
    ]
  },

  async onLoad() {
    await this.ensureSession()
  },

  // 创建（或复用）AI Agent 会话
  async ensureSession() {
    if (this.data.sessionId) return this.data.sessionId
    try {
      const res = await api.post('/ai/sessions', { user_id: DEFAULT_USER_ID })
      const sid = res && res.data && res.data.id
      if (sid) this.setData({ sessionId: sid })
      return sid
    } catch (e) {
      console.error('AI 会话创建失败', e)
      return null
    }
  },

  onInput(event) {
    this.setData({ question: event.detail.value })
  },

  onQuickTap(event) {
    const value = event.currentTarget.dataset.value
    this.setData({ question: value })
  },

  async onSubmit() {
    const question = this.data.question.trim()
    if (!question) {
      wx.showToast({ title: '先输入你的问题', icon: 'none' })
      return
    }

    const sid = await this.ensureSession()
    if (!sid) {
      wx.showToast({ title: '会话初始化失败，请检查后端', icon: 'none' })
      return
    }

    // 推入用户消息，先清空输入框
    const userMsg = { role: 'user', content: question }
    this.setData({
      messages: [...this.data.messages, userMsg],
      loading: true,
      question: ''
    })

    try {
      const response = await api.post('/ai/agent/chat', {
        session_id: sid,
        user_id: DEFAULT_USER_ID,
        message: question
      })
      const data = (response && response.data) || {}
      const aiMsg = {
        role: 'assistant',
        content: data.content || '（AI 暂时没有返回内容）',
        message_type: data.message_type || 'text',
        structured_payload: data.structured_payload || null
      }
      this.setData({
        messages: [...this.data.messages, aiMsg],
        result: this.adaptToLegacyResult(data)
      })
    } catch (error) {
      console.error('AI 对话失败', error)
      this.setData({
        messages: [...this.data.messages, {
          role: 'assistant',
          content: '调用 AI 失败：' + (error && error.message ? error.message : '请检查后端服务')
        }]
      })
      wx.showToast({ title: 'AI 调用失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 把新接口结构化结果适配回老 wxml 的 result.plan.rush/match/safe
  adaptToLegacyResult(data) {
    const payload = data && data.structured_payload
    if (!payload || data.message_type !== 'plan') return null
    const plan = payload.plan || payload
    if (!plan || (!plan.rush && !plan.match && !plan.safe)) return null
    return {
      summary: payload.summary || data.content,
      parsed_profile: payload.profile || payload.parsed_profile || { score_total: '-', program_code: '-' },
      plan: {
        rush: plan.rush || [],
        match: plan.match || [],
        safe: plan.safe || []
      }
    }
  },

  openSchool(event) {
    const id = event.currentTarget.dataset.id
    if (!id) return
    wx.navigateTo({
      url: `/pages/school-detail/index?id=${id}`
    })
  }
})
