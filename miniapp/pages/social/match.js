const request = require('../../utils/request');

Page({
  data: {
    userId: null,
    
    // 瀑布流数据
    leftColumn: [],
    rightColumn: [],
    allMoments: [],
    
    // 加载状态
    loading: false,
    refreshing: false,
    momentsHasMore: true,
    momentsPage: 1,
    momentsPageSize: 20
  },

  onLoad() {
    const userId = wx.getStorageSync('userId');
    if (userId) {
      this.setData({ userId });
      this.loadMoments();
    } else {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      setTimeout(() => {
        wx.switchTab({ url: '/pages/me/index' });
      }, 1500);
    }
  },

  onShow() {
    if (this.data.userId) {
      this.refreshMoments();
    }
  },

  // 功能模块点击
  onFeatureTap(e) {
    const type = e.currentTarget.dataset.type;
    
    const routeMap = {
      'study_buddy': '/pages/soul-matching/index',
      'material_share': '/pages/study/list',
      'question_help': '/pages/tutoring/index',
      'experience_share': '/pages/experience/list'
    };

    if (routeMap[type]) {
      wx.navigateTo({ url: routeMap[type] });
    }
  },

  // ========================================
  // 树洞瞬间 - 小红书风格
  // ========================================

  // 下拉刷新
  async onRefresh() {
    this.setData({ refreshing: true });
    await this.refreshMoments();
    this.setData({ refreshing: false });
  },

  // 刷新数据
  async refreshMoments() {
    this.setData({
      momentsPage: 1,
      leftColumn: [],
      rightColumn: [],
      allMoments: [],
      momentsHasMore: true
    });
    await this.loadMoments();
  },

  // 加载瞬间列表
  async loadMoments() {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const res = await request.get('/moments', {
        page: this.data.momentsPage,
        page_size: this.data.momentsPageSize
      });

      if (res.data && res.data.items) {
        const newMoments = res.data.items;
        const allMoments = [...this.data.allMoments, ...newMoments];
        
        // 分配到左右两列（交替分配）
        const { leftColumn, rightColumn } = this.distributeToColumns(allMoments);
        
        this.setData({
          allMoments,
          leftColumn,
          rightColumn,
          momentsPage: this.data.momentsPage + 1,
          momentsHasMore: newMoments.length === this.data.momentsPageSize
        });
      }
    } catch (e) {
      console.error('加载瞬间失败:', e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 分配到左右两列
  distributeToColumns(moments) {
    const leftColumn = [];
    const rightColumn = [];
    
    moments.forEach((moment, index) => {
      if (index % 2 === 0) {
        leftColumn.push(moment);
      } else {
        rightColumn.push(moment);
      }
    });
    
    return { leftColumn, rightColumn };
  },

  // 上拉加载更多
  onLoadMore() {
    if (this.data.momentsHasMore && !this.data.loading) {
      this.loadMoments();
    }
  },

  // 发布瞬间
  onPublishMoment() {
    wx.navigateTo({
      url: '/pages/social/publish-moment'
    });
  },

  // 查看瞬间详情
  viewMomentDetail(e) {
    const momentId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/social/moment-detail?id=${momentId}`
    });
  },

  // 预览图片
  onPreviewImage(e) {
    const images = e.currentTarget.dataset.images;
    const index = e.currentTarget.dataset.index;
    
    wx.previewImage({
      current: images[index],
      urls: images
    });
  },

  // 点赞瞬间
  async onLikeMoment(e) {
    if (!this.data.userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    const momentId = e.currentTarget.dataset.id;
    
    try {
      const res = await request.post(
        `/moments/${momentId}/like`,
        {},
        { user_id: this.data.userId }
      );

      if (res.data) {
        // 更新本地数据
        const updateMomentInColumn = (column) => {
          return column.map(m => {
            if (m.id === momentId) {
              return {
                ...m,
                is_liked: res.data.is_liked,
                like_count: m.like_count + (res.data.is_liked ? 1 : -1)
              };
            }
            return m;
          });
        };

        this.setData({
          leftColumn: updateMomentInColumn(this.data.leftColumn),
          rightColumn: updateMomentInColumn(this.data.rightColumn)
        });
      }
    } catch (e) {
      console.error('点赞失败:', e);
    }
  },

  // 评论瞬间
  onCommentMoment(e) {
    const momentId = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '评论',
      editable: true,
      placeholderText: '请输入评论内容',
      success: async (res) => {
        if (res.confirm && res.content) {
          try {
            await request.post(
              `/moments/${momentId}/comments`,
              {},
              {
                user_id: this.data.userId,
                content: res.content
              }
            );

            wx.showToast({ title: '评论成功', icon: 'success' });
            this.refreshMoments();
          } catch (e) {
            console.error('评论失败:', e);
            wx.showToast({ title: '评论失败', icon: 'none' });
          }
        }
      }
    });
  }
});
