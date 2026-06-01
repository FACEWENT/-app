const request = require('../../utils/request');

Page({
  data: {
    schoolList: [],
    schoolIndex: -1,
    majorList: [],
    majorIndex: -1,
    yearList: ['2025', '2026', '2027'],
    yearIndex: 1,
    submitting: false,
    targetSchoolId: null
  },

  onLoad() {
    this.loadSchools();
    this.loadCurrentTarget();
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

  // 加载当前目标院校
  async loadCurrentTarget() {
    const userId = wx.getStorageSync('userId');
    if (!userId) return;

    try {
      const res = await request.get('/tutoring/target-school', { user_id: userId });
      
      if (res.data) {
        // 找到对应的学校索引
        const schoolIndex = this.data.schoolList.findIndex(
          s => s.id === res.data.school_id
        );
        
        this.setData({
          schoolIndex: schoolIndex >= 0 ? schoolIndex : -1,
          targetSchoolId: res.data.school_id
        });
      }
    } catch (e) {
      console.error('加载目标院校失败:', e);
    }
  },

  onSchoolChange(e) {
    this.setData({ schoolIndex: e.detail.value });
  },

  onMajorChange(e) {
    this.setData({ majorIndex: e.detail.value });
  },

  onYearChange(e) {
    this.setData({ yearIndex: e.detail.value });
  },

  // 提交
  async onSubmit() {
    if (this.data.schoolIndex < 0) {
      wx.showToast({ title: '请选择学校', icon: 'none' });
      return;
    }

    const userId = wx.getStorageSync('userId');
    const school = this.data.schoolList[this.data.schoolIndex];
    const major = this.data.majorIndex >= 0 ? this.data.majorList[this.data.majorIndex] : null;
    const year = parseInt(this.data.yearList[this.data.yearIndex]);

    this.setData({ submitting: true });

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

      wx.showToast({ title: '设置成功', icon: 'success' });

      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (e) {
      console.error('设置目标院校失败:', e);
      wx.showToast({ title: '设置失败', icon: 'none' });
    } finally {
      this.setData({ submitting: false });
    }
  },

  onCancel() {
    wx.navigateBack();
  }
});
