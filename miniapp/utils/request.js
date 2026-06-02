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

// ======== 工具：把 ArrayBuffer 解码为 utf-8 字符串 ========
function arrayBufferToUtf8(buffer) {
  // 优先使用 TextDecoder（基础库 2.21+）
  try {
    if (typeof TextDecoder !== 'undefined') {
      return new TextDecoder('utf-8').decode(new Uint8Array(buffer))
    }
  } catch (e) { /* fallback */ }
  // 兜底：手写 utf-8 解码
  const arr = new Uint8Array(buffer)
  let result = ''
  let i = 0
  while (i < arr.length) {
    const b = arr[i]
    if (b < 0x80) { result += String.fromCharCode(b); i++ }
    else if (b < 0xE0) { result += String.fromCharCode(((b & 0x1F) << 6) | (arr[i + 1] & 0x3F)); i += 2 }
    else if (b < 0xF0) { result += String.fromCharCode(((b & 0x0F) << 12) | ((arr[i + 1] & 0x3F) << 6) | (arr[i + 2] & 0x3F)); i += 3 }
    else {
      // 4 字节 surrogate pair
      const cp = ((b & 0x07) << 18) | ((arr[i + 1] & 0x3F) << 12) | ((arr[i + 2] & 0x3F) << 6) | (arr[i + 3] & 0x3F)
      const off = cp - 0x10000
      result += String.fromCharCode(0xD800 + (off >> 10), 0xDC00 + (off & 0x3FF))
      i += 4
    }
  }
  return result
}

/**
 * 流式 POST（SSE）。
 * @param path           相对路径，如 /ai/agent/chat/stream
 * @param data           请求体
 * @param callbacks      { onEvent(evt), onDone(), onError(err) }
 *   - onEvent: 收到一个 SSE 事件时回调，evt 是已解析的 JSON 对象
 *   - onDone:  收到 [DONE] 标记或请求完成
 *   - onError: 失败回调
 * @return requestTask（可调用 abort 取消）
 */
function requestStream(path, data, callbacks = {}) {
  const { onEvent, onDone, onError } = callbacks
  let buffer = ''
  let finished = false

  const task = wx.request({
    url: `${BASE_URL}${path}`,
    method: 'POST',
    data,
    enableChunked: true,
    responseType: 'text',
    header: { 'content-type': 'application/json' },
    success(res) {
      if (!finished && res.statusCode >= 400) {
        onError && onError({ statusCode: res.statusCode, data: res.data })
      }
      // 正常情况下事件已经在 onChunkReceived 中回调，这里仅兜底
      if (!finished) {
        finished = true
        onDone && onDone()
      }
    },
    fail(err) {
      if (!finished) {
        finished = true
        onError && onError(err)
      }
    }
  })

  if (task && typeof task.onChunkReceived === 'function') {
    task.onChunkReceived((chunk) => {
      try {
        const text = arrayBufferToUtf8(chunk.data)
        buffer += text
        let idx
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const block = buffer.slice(0, idx).trim()
          buffer = buffer.slice(idx + 2)
          if (!block) continue
          // 解析 data: xxx
          const lines = block.split('\n')
          for (const line of lines) {
            if (!line.startsWith('data:')) continue
            const payload = line.slice(5).trim()
            if (!payload) continue
            if (payload === '[DONE]') {
              finished = true
              onDone && onDone()
              return
            }
            try {
              const evt = JSON.parse(payload)
              onEvent && onEvent(evt)
            } catch (e) {
              console.error('SSE 解析失败:', payload, e)
            }
          }
        }
      } catch (e) {
        console.error('onChunkReceived 异常:', e)
      }
    })
  } else {
    // 老版本基础库不支持 chunked，立即报错
    onError && onError({ errMsg: '当前微信版本不支持流式响应，请升级开发者工具基础库到 2.20.1+' })
  }

  return task
}

module.exports = {
  get(path, data) {
    return request(path, 'GET', data)
  },
  post(path, data) {
    return request(path, 'POST', data)
  },
  requestStream
}
