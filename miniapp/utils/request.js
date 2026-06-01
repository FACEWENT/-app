const BASE_URL = 'http://127.0.0.1:8000/api/v1'

function request(path, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${path}`,
      method,
      data,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        reject(res.data)
      },
      fail: reject
    })
  })
}

module.exports = {
  get(path, data) {
    return request(path, 'GET', data)
  },
  post(path, data) {
    return request(path, 'POST', data)
  }
}
