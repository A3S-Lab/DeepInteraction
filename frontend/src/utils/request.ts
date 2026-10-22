import axios from 'axios'
import { tansParams } from '@/utils/formatMethod'
import { ElMessage, ElMessageBox } from 'element-plus'

axios.defaults.headers['Content-Type'] = 'application/json;charset=utf-8'

// 创建axios实例
const service = axios.create({
  // axios中请求配置有baseURL选项，表示请求URL公共部分
  baseURL: import.meta.env.VITE_APP_BASE_API,
  // 超时(毫秒单位,设置为600秒)
  timeout: 6000000
})

// request拦截器
service.interceptors.request.use(config => {
  // get请求映射params参数
  if (config.method === 'get' && config.params) {
    let url = config.url + '?' + tansParams(config.params);
    url = url.slice(0, -1);
    config.params = {};
    config.url = url;
  }

  // 是否需要防止数据重复提交
  const isRepeatSubmit = (config.headers || {}).repeatSubmit === false
  if (!isRepeatSubmit && (config.method === 'post' || config.method === 'put')) {
    const requestObj = {
      url: config.url,
      data: typeof config.data === 'object' ? JSON.stringify(config.data) : config.data,
      time: new Date().getTime()
    }
    const requestSize = Object.keys(JSON.stringify(requestObj)).length; // 请求数据大小
    const limitSize = 5 * 1024 * 1024; // 限制存放数据5M
    if (requestSize >= limitSize) {
      console.warn(`[${config.url}]: ` + '请求数据大小超出允许的5M限制，无法进行防重复提交验证。')
      return config;
    }
  }

  // 设置 token
  const exConfig = Object.assign(config, {});

  return exConfig
}, error => {
  console.log(error)
  Promise.reject(error)
})

// 响应拦截器
service.interceptors.response.use(res => {
  // 二进制数据则直接返回
  if (res.request.responseType === 'blob' || res.request.responseType === 'arraybuffer') {
    return res.data
  }
  console.log("res", res.data)
  if (res.status === 200) {
    const ifFail = res?.data?.code !== undefined ? res.data.code !== 200 : false;
    if (ifFail) {
      if (!res?.config?.forbidMsg) {
        ElMessage.error(res.data?.message); // 注意中英文，如果要用msg，需要后台返回对应语言的msg
      }
      return Promise.resolve(res.data);
    }
    return Promise.resolve(res.data);
  } else {
    try {
      const resp = res.data;
      if (resp && resp.code !== 0) {
        const err = new Error(JSON.stringify(resp));
        console.log("1----", err, res.request.responseURL)
        ElMessage.error("请求失败：" + res.data?.message);
      }
    } catch (err) {
      console.log("2----", err, res.request.responseURL)
      ElMessage.error("请求失败：" + res.data?.message);
    }
  }
  return Promise.resolve(res.data);
},
  err => {
    console.log('err' + err)

    try {
      const error = new Error(JSON.stringify(err?.response?.data));
      console.log("3----", err, err.request.responseURL)
    } catch (error) {
      console.log("err----", err, err.request.responseURL)
    }

    const status = err?.response?.status;

    if (!err?.config?.forbidMsg) {
      if (status === 401 && !err?.config?.forbidCheckLogin) {
        ElMessage.warning("当前用户身份过期，请重新登录");
      } else if (status === 404) {
        ElMessage.warning("资源不存在或已移除");
      } else if (status >= 500) {
        ElMessage.warning("服务器出错，请稍后再试:" + status);
      } else {
        ElMessage.warning(err?.message || "请求失败");
      }
    }

    return Promise.reject(err?.response?.data || err?.message || '请求失败：' + err.request.responseURL)
  }
)

export default service
