const request = require('../../utils/request');

Page({
  data: {
    genderPreference: 'any',
    examYearIndex: 1,
    yearList: ['2025', '2026', '2027'],
    targetMajor: '',
    targetDegreeType: '',
    studyStyle: '',
    personalityType: '',
    studyIntensity: ''
  },

  onLoad() {
    this.loadPreferences();
  },

  async loadPreferences() {
    const userId = wx.getStorageSync('userId');
    if (!userId) return;

    try {
      const res = await request.get('/soul-matching/preferences', { user_id: userId });
      if (res.data) {
        const pref = res.data;
        const examYear = pref.exam_year || 2026;
        const yearIndex = this.data.yearList.indexOf(String(examYear));
        
        this.setData({
          genderPreference: pref.gender_preference || 'any',
          examYearIndex: yearIndex >= 0 ? yearIndex : 1,
          targetMajor: pref.target_major || '',
          targetDegreeType: pref.target_degree_type || '',
          studyStyle: pref.study_style || '',
          personalityType: pref.personality_type || '',
          studyIntensity: pref.study_intensity || ''
        });
      }
    } catch (e) {
      console.error('加载偏好失败:', e);
    }
  },

  onSelectGender(e) {
    this.setData({ genderPreference: e.currentTarget.dataset.value });
  },

  onExamYearChange(e) {
    this.setData({ examYearIndex: e.detail.value });
  },

  onInputMajor(e) {
    this.setData({ targetMajor: e.detail.value });
  },

  onSelectDegree(e) {
    this.setData({ targetDegreeType: e.currentTarget.dataset.value });
  },

  onSelectStudyStyle(e) {
    this.setData({ studyStyle: e.currentTarget.dataset.value });
  },

  onSelectPersonality(e) {
    this.setData({ personalityType: e.currentTarget.dataset.value });
  },

  onSelectIntensity(e) {
    this.setData({ studyIntensity: e.currentTarget.dataset.value });
  },

  async onSubmit() {
    const userId = wx.getStorageSync('userId');
    if (!userId) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '保存中...' });

    try {
      // 保存偏好
      await request.post('/soul-matching/preferences', {
        user_id: userId,
        gender_preference: this.data.genderPreference,
        exam_year: parseInt(this.data.yearList[this.data.examYearIndex]),
        target_major: this.data.targetMajor || null,
        target_degree_type: this.data.targetDegreeType || null,
        study_style: this.data.studyStyle || null,
        personality_type: this.data.personalityType || null,
        study_intensity: this.data.studyIntensity || null
      });

      // 创建订单
      const orderRes = await request.post('/soul-matching/orders', {
        user_id: userId,
        price: 9.9
      });

      wx.hideLoading();

      // 跳转到支付页面
      wx.navigateTo({
        url: `/pages/soul-matching/payment?orderId=${orderRes.id}`
      });
    } catch (e) {
      wx.hideLoading();
      console.error('保存偏好失败:', e);
      wx.showToast({ title: '保存失败', icon: 'none' });
    }
  }
});
