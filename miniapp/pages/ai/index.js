const api = require('../../utils/request')

const DEFAULT_USER_ID = 1

Page({
  data: {
    question: '',
    loading: false,
    sessionId: null,
    messages: [],          // 聊天消息列表 {role, content, message_type?, structured_payload?, thinking?, streaming?}
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
    if (this.data.loading) return  // 流式期间不允许重复提交

    const sid = await this.ensureSession()
    if (!sid) {
      wx.showToast({ title: '会话初始化失败，请检查后端', icon: 'none' })
      return
    }

    // 推入用户消息 + AI 占位气泡，用于后续流式 append
    const userMsg = { role: 'user', content: question }
    const aiMsg = {
      role: 'assistant',
      content: '',
      message_type: 'text',
      structured_payload: null,
      thinking: [],
      streaming: true
    }
    const aiIdx = this.data.messages.length + 1   // user 占用 +0，ai 占用 +1
    this.setData({
      messages: [...this.data.messages, userMsg, aiMsg],
      loading: true,
      question: ''
    })

    api.requestStream(
      '/ai/agent/chat/stream',
      { session_id: sid, user_id: DEFAULT_USER_ID, message: question },
      {
        onEvent: (evt) => this.handleStreamEvent(aiIdx, evt),
        onDone: () => {
          // 标记 streaming 结束（关闭闪烁光标）
          this.patchMessage(aiIdx, { streaming: false })
          this.setData({ loading: false })
        },
        onError: (err) => {
          console.error('流式调用失败', err)
          this.patchMessage(aiIdx, {
            streaming: false,
            content: (this.data.messages[aiIdx] && this.data.messages[aiIdx].content)
              ? this.data.messages[aiIdx].content
              : ('调用 AI 失败：' + (err && err.errMsg ? err.errMsg : '请检查后端服务'))
          })
          this.setData({ loading: false })
          wx.showToast({ title: 'AI 调用失败', icon: 'none' })
        }
      }
    )
  },

  handleStreamEvent(aiIdx, evt) {
    if (!evt || !evt.event) return
    const messages = this.data.messages
    const cur = messages[aiIdx]
    if (!cur) return

    if (evt.event === 'session') {
      if (evt.session_id) this.setData({ sessionId: evt.session_id })
      return
    }
    if (evt.event === 'delta') {
      const content = (cur.content || '') + (evt.content || '')
      this.patchMessage(aiIdx, { content })
      return
    }
    if (evt.event === 'tool_call_start') {
      const thinking = [...(cur.thinking || []), {
        name: evt.name,
        arguments: evt.arguments || {},
        status: 'running',
        summary: ''
      }]
      this.patchMessage(aiIdx, { thinking })
      return
    }
    if (evt.event === 'tool_call_end') {
      const thinking = (cur.thinking || []).slice()
      // 找最后一个同名 running 的标记完成
      for (let i = thinking.length - 1; i >= 0; i--) {
        if (thinking[i].name === evt.name && thinking[i].status === 'running') {
          thinking[i] = Object.assign({}, thinking[i], { status: 'done', summary: evt.summary || '完成' })
          break
        }
      }
      this.patchMessage(aiIdx, { thinking })
      return
    }
    if (evt.event === 'done') {
      const patch = {
        content: evt.content || cur.content,
        message_type: evt.message_type || 'text',
        structured_payload: evt.structured_payload || null
      }
      this.patchMessage(aiIdx, patch)
      // 同步老 wxml 的 result
      this.setData({
        result: this.adaptToLegacyResult({
          content: patch.content,
          message_type: patch.message_type,
          structured_payload: patch.structured_payload
        })
      })
      return
    }
    if (evt.event === 'error') {
      this.patchMessage(aiIdx, {
        content: (cur.content || '') + '\n\n[错误] ' + (evt.message || '未知错误'),
        streaming: false
      })
      return
    }
  },

  // 局部更新 messages[aiIdx]
  patchMessage(aiIdx, patch) {
    const messages = this.data.messages.slice()
    if (!messages[aiIdx]) return
    messages[aiIdx] = Object.assign({}, messages[aiIdx], patch)
    this.setData({ messages })
  },

  // 把新接口结构化结果适配回老 wxml 的 result.plan.rush/match/safe
  adaptToLegacyResult(data) {
    if (!data) return null
    const sp = data.structured_payload
    if (!sp || data.message_type !== 'plan') return null
    // 兼容两种结构：直接 plan，或者 {tool, data: {plan}}
    const inner = sp.data || sp
    const plan = inner.plan || inner
    if (!plan || (!plan.rush && !plan.match && !plan.safe)) return null
    return {
      summary: inner.summary || data.content,
      parsed_profile: inner.profile || inner.parsed_profile || { score_total: '-', program_code: '-' },
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
  },

  // 折叠/展开思考过程
  toggleThinking(event) {
    const idx = Number(event.currentTarget.dataset.idx)
    const messages = this.data.messages.slice()
    const m = messages[idx]
    if (!m) return
    messages[idx] = Object.assign({}, m, { thinkingCollapsed: !m.thinkingCollapsed })
    this.setData({ messages })
  }
})
