const request = require('../../utils/request');

Page({
  data: {
    chats: [],
    userId: null
  },

  onLoad() {
    const userId = wx.getStorageSync('userId');
    if (userId) {
      this.setData({ userId });
      this.loadChats();
    }
  },

  onShow() {
    if (this.data.userId) {
      this.loadChats();
    }
  },

  async loadChats() {
    try {
      const res = await request.get('/social/chats', {
        user_id: this.data.userId
      });

      if (res.data) {
        // 格式化时间
        const chats = res.data.map(chat => ({
          ...chat,
          last_message_at: this.formatTime(chat.last_message_at)
        }));
        this.setData({ chats });
      }
    } catch (e) {
      console.error('加载聊天列表失败:', e);
    }
  },

  formatTime(timeStr) {
    if (!timeStr) return '';
    
    const time = new Date(timeStr);
    const now = new Date();
    const diff = now - time;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
    
    return `${time.getMonth() + 1}/${time.getDate()}`;
  },

  onChatTap(e) {
    const chatId = e.currentTarget.dataset.chatId;
    wx.navigateTo({
      url: `/pages/social/chat?chatId=${chatId}`
    });
  },

  goToMatch() {
    wx.switchTab({
      url: '/pages/social/match'
    });
  }
});
