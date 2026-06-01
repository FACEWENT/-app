const request = require('../../utils/request');

Page({
  data: {
    chatId: null,
    userId: null,
    myAvatar: '',
    messages: [],
    otherUser: {},
    inputText: '',
    scrollToId: '',
    pollTimer: null
  },

  onLoad(options) {
    const chatId = options.chatId;
    const userId = wx.getStorageSync('userId');
    const myAvatar = wx.getStorageSync('avatarUrl') || '';

    if (chatId && userId) {
      this.setData({ chatId, userId, myAvatar });
      this.loadMessages();
      // 开始轮询新消息
      this.startPolling();
    }
  },

  onUnload() {
    // 停止轮询
    if (this.data.pollTimer) {
      clearInterval(this.data.pollTimer);
    }
  },

  async loadMessages() {
    try {
      const res = await request.get(`/social/chats/${this.data.chatId}/messages`, {
        user_id: this.data.userId,
        limit: 50,
        offset: 0
      });

      if (res.data) {
        this.setData({
          messages: res.data.messages,
          otherUser: res.data.other_user
        });

        // 滚动到底部
        if (res.data.messages.length > 0) {
          const lastMsg = res.data.messages[res.data.messages.length - 1];
          this.setData({ scrollToId: `msg-${lastMsg.id}` });
        }
      }
    } catch (e) {
      console.error('加载消息失败:', e);
    }
  },

  startPolling() {
    // 每2秒轮询一次新消息
    const timer = setInterval(() => {
      this.loadMessages();
    }, 2000);

    this.setData({ pollTimer: timer });
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value });
  },

  async onSend() {
    const content = this.data.inputText.trim();
    if (!content) return;

    try {
      await request.post(
        `/social/chats/${this.data.chatId}/messages`,
        {},
        {
          user_id: this.data.userId,
          content: content,
          message_type: 'text'
        }
      );

      // 清空输入框
      this.setData({ inputText: '' });

      // 立即加载新消息
      this.loadMessages();
    } catch (e) {
      console.error('发送消息失败:', e);
      wx.showToast({
        title: '发送失败',
        icon: 'none'
      });
    }
  }
});
