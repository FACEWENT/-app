const request = require('../../utils/request');

Page({
  data: {
    targetSchool: null,
    showSetTarget: false,
    schoolList: [],
    schoolIndex: -1,
    majorList: [],
    majorIndex: -1,
    yearList: ['2025', '2026', '2027'],
    yearIndex: 1,
    subjectType: '',
    posts: [],
    loading: false,
    hasMore: true,
    page: 1,
    pageSize: 20
  },

  onLoad() {
    this.checkTargetSchool();
  },

  onShow() {
    if (this.data.targetSchool) {
      this.loadPosts();
    }
  },

  // 检查是否已设置目标院校
  async checkTargetSchool() {
    const userId = wx.getStorageSync('userId');
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    try {
      const res = await request.get('/tutoring/target-school', { user_id: userId });
      
      if (res.data) {
        this.setData({ targetSchool: res.data });
        this.loadPosts();
      } else {
        // 首次进入，显示设置弹窗
        this.setData({ showSetTarget: true });
        this.loadSchools();
      }
    } catch (e) {
      console.error('检查目标院校失败:', e);
    }
  },

  // 加载学校列表
  async loadSchools() {
    try {
      const res = await request.get('/institutions', { page: 1, page_size: 100 });
      if (res.data) {
        this.setData({ schoolList: res.data.items });
      }
    } catch (e) {
      console.error('加载学校失败:', e);
    }
  },

  // 加载专业列表
  async loadMajors(schoolId) {
    try {
      const res = await request.get('/programs', { page: 1, page_size: 100 });
      if (res.data) {
        this.setData({ majorList: res.data.items });
      }
    } catch (e) {
      console.error('加载专业失败:', e);
    }
  },

  onSchoolChange(e) {
    const index = e.detail.value;
    this.setData({ schoolIndex: index });
    // 加载该学校的专业
    const school = this.data.schoolList[index];
    if (school) {
      this.loadMajors(school.id);
    }
  },

  onMajorChange(e) {
    this.setData({ majorIndex: e.detail.value });
  },

  onYearChange(e) {
    this.setData({ yearIndex: e.detail.value });
  },

  // 提交目标院校
  async onSubmitTarget() {
    if (this.data.schoolIndex < 0) {
      wx.showToast({ title: '请选择学校', icon: 'none' });
      return;
    }

    const userId = wx.getStorageSync('userId');
    const school = this.data.schoolList[this.data.schoolIndex];
    const major = this.data.majorIndex >= 0 ? this.data.majorList[this.data.majorIndex] : null;
    const year = parseInt(this.data.yearList[this.data.yearIndex]);

    try {
      await request.post('/tutoring/target-school', {}, {
        user_id: userId,
        school_id: school.id,
        school_name: school.name,
        exam_year: year,
        major_id: major?.id || null,
        major_code: major?.code || null,
        major_name: major?.name || null
      });

      this.setData({
        targetSchool: {
          school_id: school.id,
          school_name: school.name,
          major_id: major?.id,
          major_name: major?.name,
          exam_year: year
        },
        showSetTarget: false
      });

      wx.showToast({ title: '设置成功', icon: 'success' });
      this.loadPosts();
    } catch (e) {
      console.error('设置目标院校失败:', e);
      wx.showToast({ title: '设置失败', icon: 'none' });
    }
  },

  // 更换目标院校
  onChangeTarget() {
    wx.showModal({
      title: '更换目标院校',
      content: '确定要更换目标院校吗？',
      success: (res) => {
        if (res.confirm) {
          this.setData({ showSetTarget: true });
        }
      }
    });
  },

  // 切换科目
  onSubjectChange(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({
      subjectType: type,
      page: 1,
      posts: []
    });
    this.loadPosts();
  },

  // 加载教学信息
  async loadPosts() {
    if (this.data.loading || !this.data.targetSchool) return;
    
    this.setData({ loading: true });
    
    try {
      const params = {
        school_id: this.data.targetSchool.school_id,
        major_id: this.data.targetSchool.major_id || 0,
        subject_type: this.data.subjectType,
        page: this.data.page,
        page_size: this.data.pageSize
      };

      const res = await request.get('/tutoring/posts', params);

      if (res.data) {
        const newPosts = res.data.items;
        this.setData({
          posts: this.data.page === 1 ? newPosts : [...this.data.posts, ...newPosts],
          hasMore: newPosts.length === this.data.pageSize,
          page: this.data.page + 1
        });
      }
    } catch (e) {
      console.error('加载教学信息失败:', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  onLoadMore() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadPosts();
    }
  },

  // 发布教学信息
  onPublish() {
    wx.navigateTo({
      url: '/pages/tutoring/publish'
    });
  },

  // 帖子详情
  onPostTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/tutoring/detail?id=${id}`
    });
  }
});
