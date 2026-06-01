const request = require('../../utils/request');

Page({
  data: {
    title: '',
    content: '',
    subjectType: 'math',
    subjectName: '',
    subjectScore: '',
    currentSchool: '',
    currentMajor: '',
    teachingMode: 'online',
    price: '',
    contactInfo: '',
    submitting: false,
    targetSchool: null
  },

  onLoad() {
    this.loadTargetSchool();
  },

  // 加载目标院校信息
  async loadTargetSchool() {
    const userId = wx.getStorageSync('userId');
    if (!userId) return;

    try {
      const res = await request.get('/tutoring/target-school', { user_id: userId });
      if (res.data) {
        this.setData({ targetSchool: res.data });
      }
    } catch (e) {
      console.error('加载目标院校失败:', e);
    }
  },

  onInputTitle(e) {
    this.setData({ title: e.detail.value });
  },

  onInputContent(e) {
    this.setData({ content: e.detail.value });
  },

  onInputSubjectScore(e) {
    this.setData({ subjectScore: e.detail.value });
  },

  onInputSchool(e) {
    this.setData({ currentSchool: e.detail.value });
  },

  onInputMajor(e) {
    this.setData({ currentMajor: e.detail.value });
  },

  onInputPrice(e) {
    this.setData({ price: e.detail.value });
  },

  onInputContact(e) {
    this.setData({ contactInfo: e.detail.value });
  },

  onSelectSubject(e) {
    const type = e.currentTarget.dataset.type;
    const nameMap = {
      'math': '数学',
      'english': '英语',
      'politics': '政治',
      'professional': '专业课'
    };
    this.setData({ 
      subjectType: type,
      subjectName: nameMap[type]
    });
  },

  onSelectMode(e) {
    this.setData({ teachingMode: e.currentTarget.dataset.mode });
  },

  // 提交发布
  async onSubmit() {
    const { title, content, subjectType, subjectName, price, currentSchool, currentMajor, targetSchool } = this.data;

    if (!title.trim()) {
      wx.showToast({ title: '请输入标题', icon: 'none' });
      return;
    }

    if (!content.trim()) {
      wx.showToast({ title: '请输入个人介绍', icon: 'none' });
      return;
    }

    if (!currentSchool.trim()) {
      wx.showToast({ title: '请输入就读学校', icon: 'none' });
      return;
    }

    if (!price) {
      wx.showToast({ title: '请输入价格', icon: 'none' });
      return;
    }

    if (!targetSchool) {
      wx.showToast({ title: '请先设置目标院校', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });

    try {
      const userId = wx.getStorageSync('userId');
      
      await request.post('/tutoring/posts', {}, {
        user_id: userId,
        school_id: targetSchool.school_id,
        major_id: targetSchool.major_id || 0,
        title: title,
        content: content,
        subject_type: subjectType,
        subject_name: subjectName,
        subject_score: this.data.subjectScore ? parseFloat(this.data.subjectScore) : null,
        current_school: currentSchool,
        current_major: currentMajor,
        teaching_mode: this.data.teachingMode,
        price: parseFloat(price),
        contact_info: this.data.contactInfo,
        bio: content
      });

      wx.showToast({
        title: '发布成功',
        icon: 'success'
      });

      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } catch (e) {
      console.error('发布失败:', e);
      wx.showToast({
        title: '发布失败',
        icon: 'none'
      });
    } finally {
      this.setData({ submitting: false });
    }
  }
});
