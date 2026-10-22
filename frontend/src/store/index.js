import { createStore } from 'vuex'

export default createStore({
  state: {
    user: null,
    chatInfo:{
      chatId:'', // 测试用 helen
      content:'', // 测试用 helen
      mode:'',
      imgList:[] // 上传的图片路径
    }
  },
  mutations: {
    setUser(state, user) {
      state.user = user
    },
    // 新增 mutations 
    setChatInfo(state, chatInfo) {
      state.chatInfo.chatId = chatInfo.chatId||'';
      state.chatInfo.content = chatInfo.content||'';
      state.chatInfo.mode = chatInfo.mode||1;
      state.chatInfo.imgList=chatInfo.imgList||[];
    }
  },
  actions: {
    login({ commit }, userData) {
      commit('setUser', userData)
    },
    logout({ commit }) {
      commit('setUser', null)
    },
    // 修正后的 actions

  },
  getters: {
    getUser: state => state.user,
    getChatInfo: state => state.chatInfo
  }
})