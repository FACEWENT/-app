const { get, post } = require('../../utils/request');

// A区和B区划分
const A_PROVINCES = [
  '北京市', '天津市', '河北省', '山西省', '辽宁省', '吉林省', 
  '黑龙江省', '上海市', '江苏省', '浙江省', '安徽省', '福建省', 
  '江西省', '山东省', '河南省', '湖北省', '湖南省', '广东省', 
  '重庆市', '四川省', '陕西省', '海南省'
];

const B_PROVINCES = [
  '内蒙古自治区', '广西壮族自治区', '贵州省', '云南省', 
  '西藏自治区', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区'
];

// 按地区分组
const PROVINCE_GROUPS = [
  {
    name: '华北地区',
    provinces: ['北京市', '天津市', '河北省', '山西省', '内蒙古自治区']
  },
  {
    name: '东北地区',
    provinces: ['辽宁省', '吉林省', '黑龙江省']
  },
  {
    name: '华东地区',
    provinces: ['上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省']
  },
  {
    name: '华中地区',
    provinces: ['河南省', '湖北省', '湖南省']
  },
  {
    name: '华南地区',
    provinces: ['广东省', '广西壮族自治区', '海南省']
  },
  {
    name: '西南地区',
    provinces: ['重庆市', '四川省', '贵州省', '云南省', '西藏自治区']
  },
  {
    name: '西北地区',
    provinces: ['陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区']
  }
];

Page({
  data: {
    score_total: '',
    program_code: '',
    degreeTypes: ['学硕', '专硕'],
    degreeTypeIndex: -1,
    degree_type: '',
    
    // 地区相关
    provinceGroups: PROVINCE_GROUPS.map(group => ({
      ...group,
      provinces: group.provinces.map(name => ({ name, selected: false }))
    })),
    expandedGroups: {},
    selectedProvinces: [],
    areaFilter: '', // A, B, all
    
    loading: false,
    result: null,
    guide: {
      process: [
        '1. 确认自己是否达到国家线',
        '2. 在研招网调剂系统开放后填报调剂志愿',
        '3. 等待学校复试通知',
        '4. 参加复试',
        '5. 等待录取结果',
      ],
      tips: [
        '调剂志愿可同时填报3个平行志愿',
        '48小时后可修改志愿',
        '建议优先选择本科母校或家乡附近的学校',
        '提前联系目标院校的招生办',
      ],
      notes: [
        'A区考生可调剂到B区，但B区考生不能调剂到A区',
        '学硕可以调剂到专硕，但专硕一般不能调剂到学硕',
        '同一学科门类内可以调剂',
      ],
    },
  },

  onScoreInput(e) {
    this.setData({ score_total: e.detail.value });
  },

  onCodeInput(e) {
    this.setData({ program_code: e.detail.value });
  },

  onDegreeTypeChange(e) {
    const index = e.detail.value;
    const types = ['', 'academic', 'professional'];
    this.setData({
      degreeTypeIndex: index,
      degree_type: types[index] || '',
    });
  },

  // A区/B区快捷筛选
  onAreaFilter(e) {
    const area = e.currentTarget.dataset.area;
    const targetProvinces = area === 'A' ? A_PROVINCES : 
                            area === 'B' ? B_PROVINCES : [];
    
    // 更新所有省份的选中状态
    const provinceGroups = this.data.provinceGroups.map(group => ({
      ...group,
      provinces: group.provinces.map(p => ({
        ...p,
        selected: area === 'all' ? false : targetProvinces.includes(p.name)
      }))
    }));

    const selectedProvinces = area === 'all' ? [] : targetProvinces;
    
    this.setData({
      areaFilter: area,
      provinceGroups,
      selectedProvinces
    });
  },

  // 展开/收起地区分组
  toggleGroup(e) {
    const group = e.currentTarget.dataset.group;
    const expanded = { ...this.data.expandedGroups };
    expanded[group] = !expanded[group];
    this.setData({ expandedGroups: expanded });
  },

  // 省份选择
  onProvinceToggle(e) {
    const name = e.currentTarget.dataset.name;
    const provinceGroups = [...this.data.provinceGroups];
    let found = false;
    
    // 更新选中状态
    for (let i = 0; i < provinceGroups.length; i++) {
      const provinces = provinceGroups[i].provinces.map(p => {
        if (p.name === name) {
          found = true;
          return { ...p, selected: !p.selected };
        }
        return p;
      });
      provinceGroups[i] = { ...provinceGroups[i], provinces };
      if (found) break;
    }

    // 更新已选列表
    const selectedProvinces = [];
    provinceGroups.forEach(group => {
      group.provinces.forEach(p => {
        if (p.selected) selectedProvinces.push(p.name);
      });
    });

    this.setData({
      provinceGroups,
      selectedProvinces
    });
  },

  async queryTransfer() {
    const { score_total, program_code } = this.data;

    if (!score_total || !program_code) {
      wx.showToast({ title: '请输入分数和专业代码', icon: 'none' });
      return;
    }

    this.setData({ loading: true });

    try {
      const res = await post('/transfer/opportunities', {
        score_total: parseInt(score_total),
        program_code,
        degree_type: this.data.degree_type,
        preferred_provinces: this.data.selectedProvinces,
      });

      if (res.code === 0) {
        this.setData({ result: res.data });
      } else {
        wx.showToast({ title: res.message || '查询失败', icon: 'none' });
      }
    } catch (err) {
      console.error('查询调剂机会失败:', err);
      wx.showToast({ title: '网络错误，请稍后重试', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  goToSchool(e) {
    const schoolId = e.currentTarget.dataset.id;
    if (schoolId) {
      wx.navigateTo({ url: `/pages/schools/detail?id=${schoolId}` });
    }
  },
});
