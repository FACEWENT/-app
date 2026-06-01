const api = require('../../utils/request')

Page({
  data: {
    keyword: '',
    filters: {
      province: '',
      school_level: '',
      school_type: '',
      discipline_code: '',
      discipline_name: ''
    },
    schools: [],
    loading: false,
    page: 1,
    pageSize: 20,
    total: 0,
    hasMore: true,
    hasActiveFilters: false,
    
    // 筛选面板
    showProvincePicker: false,
    showLevelPicker: false,
    showTypePicker: false,
    showDisciplinePicker: false,
    
    // 筛选选项
    filterOptions: {
      provinces: [],
      school_levels: ['985', '211', '双一流'],
      school_types: [],
      disciplines: []
    }
  },

  onLoad() {
    this.syncFilterState()
    this.loadFilters()
    this.loadSchools()
  },

  // 加载筛选选项
  async loadFilters() {
    try {
      const res = await api.get('/institutions/filters')
      if (res.data) {
        this.setData({
          'filterOptions.provinces': res.data.provinces || [],
          'filterOptions.school_types': res.data.school_types || [],
          'filterOptions.disciplines': res.data.disciplines || []
        })
      }
    } catch (e) {
      console.error('加载筛选条件失败:', e)
    }
  },

  // 加载院校列表
  async loadSchools(refresh = false) {
    if (this.data.loading) return
    
    this.setData({ loading: true })
    
    try {
      const page = refresh ? 1 : this.data.page
      const res = await api.get('/institutions', {
        keyword: this.data.keyword,
        province: this.data.filters.province,
        school_level: this.data.filters.school_level,
        school_type: this.data.filters.school_type,
        discipline_code: this.data.filters.discipline_code,
        page: page,
        page_size: this.data.pageSize
      })

      if (res.data) {
        const schools = refresh ? res.data.items : [...this.data.schools, ...res.data.items]
        this.setData({
          schools,
          page: page + 1,
          total: res.data.total,
          hasMore: schools.length < res.data.total
        })
      }
    } catch (e) {
      wx.showToast({ title: '加载院校失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 搜索
  onKeywordChange(e) {
    this.setData({ keyword: e.detail.value })
  },

  onSearch() {
    this.setData({ page: 1 })
    this.loadSchools(true)
  },

  closeAllPickers() {
    this.setData({
      showProvincePicker: false,
      showLevelPicker: false,
      showTypePicker: false,
      showDisciplinePicker: false
    })
  },

  // 筛选面板切换
  toggleProvincePicker() {
    this.setData({
      showProvincePicker: !this.data.showProvincePicker,
      showLevelPicker: false,
      showTypePicker: false,
      showDisciplinePicker: false
    })
  },

  toggleLevelPicker() {
    this.setData({
      showLevelPicker: !this.data.showLevelPicker,
      showProvincePicker: false,
      showTypePicker: false,
      showDisciplinePicker: false
    })
  },

  toggleTypePicker() {
    this.setData({
      showTypePicker: !this.data.showTypePicker,
      showProvincePicker: false,
      showLevelPicker: false,
      showDisciplinePicker: false
    })
  },

  toggleDisciplinePicker() {
    this.setData({
      showDisciplinePicker: !this.data.showDisciplinePicker,
      showProvincePicker: false,
      showLevelPicker: false,
      showTypePicker: false
    })
  },

  // 选择筛选条件
  selectProvince(e) {
    const value = e.currentTarget.dataset.value
    this.setData({
      'filters.province': value,
      page: 1
    })
    this.closeAllPickers()
    this.syncFilterState()
    this.loadSchools(true)
  },

  selectLevel(e) {
    const value = e.currentTarget.dataset.value
    this.setData({
      'filters.school_level': value,
      page: 1
    })
    this.closeAllPickers()
    this.syncFilterState()
    this.loadSchools(true)
  },

  selectType(e) {
    const value = e.currentTarget.dataset.value
    this.setData({
      'filters.school_type': value,
      page: 1
    })
    this.closeAllPickers()
    this.syncFilterState()
    this.loadSchools(true)
  },

  selectDiscipline(e) {
    const code = e.currentTarget.dataset.code
    const name = e.currentTarget.dataset.name
    this.setData({
      'filters.discipline_code': code,
      'filters.discipline_name': name,
      page: 1
    })
    this.closeAllPickers()
    this.syncFilterState()
    this.loadSchools(true)
  },

  // 清除筛选
  clearProvince() {
    this.setData({ 'filters.province': '', page: 1 })
    this.syncFilterState()
    this.loadSchools(true)
  },

  clearLevel() {
    this.setData({ 'filters.school_level': '', page: 1 })
    this.syncFilterState()
    this.loadSchools(true)
  },

  clearType() {
    this.setData({ 'filters.school_type': '', page: 1 })
    this.syncFilterState()
    this.loadSchools(true)
  },

  clearDiscipline() {
    this.setData({ 'filters.discipline_code': '', 'filters.discipline_name': '', page: 1 })
    this.syncFilterState()
    this.loadSchools(true)
  },

  clearAllFilters() {
    this.setData({
      filters: {
        province: '',
        school_level: '',
        school_type: '',
        discipline_code: '',
        discipline_name: ''
      },
      page: 1
    })
    this.closeAllPickers()
    this.syncFilterState()
    this.loadSchools(true)
  },

  // 加载更多
  loadMore() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadSchools()
    }
  },

  // 查看详情
  openDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/schools/detail?id=${id}`
    })
  },

  syncFilterState() {
    const f = this.data.filters
    this.setData({
      hasActiveFilters: !!(f.province || f.school_level || f.school_type || f.discipline_name)
    })
  }
})
