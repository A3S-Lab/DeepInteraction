<template>
  <div class="container">
    <!-- <textarea v-model="inputText" placeholder="输入你的问题..." rows="5"></textarea> -->
    <!-- 对话历史内容显示 -->
    <div class="chat-container">
      <div class="chat-item" v-for="item in chatParams.chatHistories" :key="item.id">
        <div class="chat-item-content">
          <div class="chat-item-user" v-if="item.request">
            <div class="chat-item-content-request">
              <div>
                <el-tag class="uploaded-file-item-tag" v-for="(item, index) in item.imgList" :key="index"
                  :disable-transitions="false">
                  <div class="uploaded-file-item">
                    <img :src="item"></img>
                  </div>
                </el-tag>

              </div>
              <div class="pre-line-content">{{ item.request }}</div>
            </div>
            <!-- <div class="chat-item-content-human_cot">{{ item.human_cot }}</div> -->
          </div>
          <div class="chat-item-assistant">
            <div class="chat-item-content-response" v-for="response in item.response" :key="response.id">
              <div class="chat-item-content-response-think" v-if="response.cotContent">
                <div class="think-label">
                  <img src="@/image/thinkLink.svg" alt="思维链" class="think-label-icon">
                  思维链
                </div>
                <div class="think-content" v-html="response.cotContent"></div>
              </div>
              <div class="chat-item-content-response-think" v-else-if="response.thinkContent">
                <div class="think-label">
                  <img src="@/image/thinkLink.svg" alt="思维链" class="think-label-icon">
                  思维链
                </div>
                <div class="think-content" v-html="response.thinkContent"></div>
              </div>
              <div class="chat-item-content-response-answer">
                <div class="answer-content" v-html="getMarkdownThink(response.answerContent)">
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
    <!-- 当前对话内容显示 -->
    <div class="output-container">
      <div class="output-container-status" v-if="isGenerating && !isFinished">分析中<span class="output-container-status-dot"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span></div>
      <div ref="outputDisplay" class="output-display" v-if="displayedText && displayedText.length > 0">
        <div class="chat-item-assistant">
          <div class="chat-item-content-response">
            <div class="chat-item-content-response-think output-response-think"
              v-if="getResponseThink(displayedText).thinkContent">
              <div class="think-label">
                <img src="@/image/thinkLink.svg" alt="思维链" class="think-label-icon">
                思维链
              </div>
              <!-- <div class="think-content" v-if="!chatParams.showEditContainer">{{
                getResponseThink(displayedText).thinkContent }}</div> -->
              <div class="think-content" v-if="!chatParams.showEditContainer"
                v-html="getMarkdownContent(getResponseThink(displayedText).thinkContent ||'')"></div>
              <el-input v-else type="textarea" v-model="chatParams.humanCot" :autosize="{ minRows: 2, maxRows: 8 }"
                resize="none" class="no-border-input"></el-input>

              <div class="think-edit-content" v-if="!isGenerating && !chatParams.showEditContainer">
                <el-button @click="handleEditThink(displayedText)">
                  <el-icon>
                    <Edit />
                  </el-icon>
                </el-button>
              </div>
              <div class="think-save-content" v-else-if="!isGenerating">
                <el-button @click="handleRefineThink('rule')" :disabled="isRefining" title="规则+Embedding精炼">
                  <el-icon>
                    <Filter />
                  </el-icon>
                </el-button>
                <el-button @click="handleRefineThink('llm')" :disabled="isRefining" title="大模型C1->C2精炼">
                  <el-icon>
                    <MagicStick />
                  </el-icon>
                </el-button>
                <el-button @click="handleSaveThink" :disabled="isSaveThinking">
                  <el-icon>
                    <Promotion />
                  </el-icon>
                </el-button>
              </div>
            </div>
            <div class="chat-item-content-response-answer" style="display: flex; align-items: center;">
              <div class="answer-content" v-html="getResponseMarkdownThink(displayedText)">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <ContentInput v-if="chatParams.showInput" ref="contentInputRef" :is-auto-send="true" :is-generate="isGenerating"
      @on-stop-loading="handleStopLoading" @on-send-msg="handleInputSendMessage"></ContentInput>

  </div>
</template>

<script setup>
import { useStore } from "vuex";
import { useRouter } from "vue-router";
import { ref, watch, onUnmounted, onMounted, reactive } from 'vue';
import { Edit, Promotion, Filter, MagicStick } from '@element-plus/icons-vue'
import ContentInput from "@/components/contentInput.vue";
import { getStringCompare, refineCot } from '@/api/chatapi';
import MarkdownIt from 'markdown-it'
const md = new MarkdownIt({ html: true });

const store = useStore();
const router = useRouter();

// 注册MarkdownIt组件
const components = {
  MarkdownIt
};

const contentInputRef = ref();
const fullResponse = ref('');
const displayedText = ref('');
const isGenerating = ref(false);
const isFinished = ref(false);
const isSaveThinking = ref(false); // 保存思维链按钮是否正在处理，防止重复点击
const isRefining = ref(false); // 精炼按钮是否正在处理，防止重复点击
const controller = ref(null);
const outputDisplay = ref(null);
let printerInterval = null;
let printerIndex = 0;

const chatParams = reactive({
  showEditContainer: false,
  showInput: true,
  chatId: '',
  mode: '',
  lastQuery: '',
  chatHistories: [],
  mediaprompt: []
})

// 打印机效果函数
const startPrinterEffect = () => {
  printerIndex = 0;
  clearInterval(printerInterval);
  console.log("stop interval --- 4")
  printerInterval = null;
  console.log("start printer effect")
  printerInterval = setInterval(() => {
    if (printerIndex < fullResponse.value.length) {
      displayedText.value = fullResponse.value.substring(0, printerIndex + 1);
      printerIndex++;

      // console.log(displayedText.value)
      // 自动滚动到底部
      if (outputDisplay.value) {
        outputDisplay.value.scrollTop = outputDisplay.value.scrollHeight;
      }
    } else {
      clearInterval(printerInterval);
      console.log("stop interval --- 5")
      printerInterval = null;
      isFinished.value = true;
    }
  }, 50); // 调整速度
};

// 调用API生成内容
const generate = async (askMsg, isHuman = false) => {
  let chatHistories = '';

  let asklist = [], historyList = []
  if (!isHuman) { // 非人工干预
    chatParams.lastQuery = askMsg.request;
    chatHistories = getMessageHistories();
    asklist.push(askMsg.request)
    historyList = chatHistories;
  } else {
    asklist.push(chatParams.lastQuery)
    asklist.push(askMsg.llm_cot)
    asklist.push(askMsg.human_cot)
  }

  // 重置状态
  fullResponse.value = '';
  displayedText.value = '';
  isGenerating.value = true;
  isFinished.value = false;

  controller.value = new AbortController();

  try {
    const params = {
      message_history: isHuman ? [] : getMessageHistories(),
      user_query: asklist[0], // 用户请求
      llm_cot: asklist[1] || '', //llm思维链
      user_cot: asklist[2] || '', // 用户修改思维链
      mediaprompt: askMsg.imgList || [],
      stream: true
    }

    console.log("🚀 发送请求到 getChatWithAI:", params);
    if (printerInterval) {
      printerInterval = null;
    }

    isGenerating.value = true;
    isFinished.value = false;
    // 请求 getChatWithAI 接口
    const response = await fetch('/api/forward', {
      method: 'post',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
      signal: controller.value.signal,
      stream: true
    });

    if (!response.ok) throw new Error(`请求失败: ${response.status}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let outchunk = '', outstream = '';

    while (true) {
      // 创建超时 Promise，如果 reader.read() 等待超过 15 秒则超时
      const timeoutPromise = new Promise((resolve) => {
        setTimeout(() => {
          resolve({ timeout: true });
        }, 1000 * 15);
      });

      // 使用 Promise.race 来检测 reader.read() 是否超时
      const readPromise = reader.read().then((result) => {
        return { ...result, timeout: false };
      });

      const raceResult = await Promise.race([readPromise, timeoutPromise]);

      // 如果超时，则结束循环
      if (raceResult.timeout) {
        console.warn('reader.read() 等待超过 15 秒，结束循环');
        isGenerating.value = false;
        break;
      }

      const { value, done } = raceResult;
      if (done) break;

      // 处理流式数据
      const chunk = decoder.decode(value, { stream: true });
      try {
        const dataArray = [];
        // const lines = chunk.split('\n');
        const lines = chunk.trim();
        let trimmedLine = '';

        // 处理拆分后的数据数组
        // for (const line of lines) {
        //   let outchunk = line.trim();
        //   if (!outchunk) continue;

        //   console.log("outchunk----", outchunk)
        //   let outtext = '';
        //   if (typeof outchunk === 'string') {
        //     outtext = outchunk.replace(/\n\n/g, '\n');
        //   } else {
        //     outtext = outchunk;
        //   }
        //   fullResponse.value += outtext;
        // }

        let outchunk = lines.trim();
        if (!outchunk) continue;

        console.log("outchunk----", outchunk)
        // let outtext = '';
        // if (typeof outchunk === 'string') {
        //   outtext = outchunk.replace(/\n\n/g, '\n');
        // } else {
        //   outtext = outchunk;
        // }
        // fullResponse.value += outtext;
        fullResponse.value += outchunk;
        // console.log("---------------", fullResponse.value);
        // 启动/更新打印机效果
        if (!printerInterval) {
          startPrinterEffect();
        }
        // outchunk += chunk;
      } catch (err) {
        console.error("出错啦：", err)
        console.log("******", chunk)
      }
    }
    isGenerating.value = false;
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('请求出错:', error);
      fullResponse.value = `错误: ${error.message}`;
      displayedText.value = fullResponse.value;
    }
    isGenerating.value = false;
  } finally {
    controller.value = null;
  }
};

const showMessageHistories = () => {
  console.log("---历史信息-----", chatParams.chatHistories)
  console.log("获取历史消息----", getMessageHistories())
}

const getMessageHistories = () => {
  // console.log("--------", chatParams.chatHistories)
  let result = []

  for (let i = 0; i < chatParams.chatHistories.length - 1; i++) { // 不包括当前对话和第一次对话
    let item = chatParams.chatHistories[i];
    if (item.response && item.response.length > 0) {
      let usercontent = [], imgcontent = [];
      usercontent.push({ // 第一次输入放入请求
        type: 'text',
        text: item.request
      })
      if (item.imgList && item.imgList.length > 0) {
        item.imgList.forEach(img => {
          usercontent.push({
            type: 'image_url',
            // image_url: {
            //   type: 'image_url',
            //   url: img
            // }
            image_url: img
          })
        })
      }
      if (item.response.length > 1) { // 最后一次修改放入请求
        let lastitem = item.response[item.response.length - 2];
        if (lastitem.human_cot) {
          usercontent.push({
            type: 'text',
            text: lastitem.human_cot
          })
        }
      }
      result.push({
        role: 'user',
        content: usercontent
      })
      let assistantcontent = [];
      assistantcontent.push({
        type: 'text',
        text: item.response[item.response.length - 1].answerContent
      })
      result.push({
        role: 'assistant',
        content: assistantcontent
      })
    }
  }

  return result;
}

// 中断生成
const stopGenerate = () => {
  if (controller.value) {
    controller.value.abort();
  }
  isGenerating.value = false;
  clearInterval(printerInterval);
  console.log("stop interval --- 1")
  printerInterval = null;
};
// 对话框输入问题发送
const handleInputSendMessage = async (msgInfo) => {
  // console.log("handleInput SendMessage----", msgInfo)
  let chatHistories = chatParams.chatHistories[chatParams.chatHistories.length - 1];
  const content = getResponseThink(displayedText.value);
  chatHistories.response.push({
    role: 'assistant',
    thinkContent: content.thinkContent,
    answerContent: content.answerContent,
    content: displayedText.value,
    human_cot: ''
  });
  displayedText.value = ""
  contentInputRef.value.clearInput();
  chatParams.showEditContainer = false;

  handleSendMessage(msgInfo);
}
const handleSendMessage = async (msgInfo) => { // 首页进入或者对话框输入问题发送
  let askMsg = {
    request: msgInfo.msg,
    human_cot: '',
    llm_cot: '',
    response: [],
    imgList: msgInfo.imgList
  };
  // console.log("问题内容：", askMsg)
  chatParams.chatHistories.push(askMsg);
  generate(askMsg, false); // ，for test helen
}
const handleStopLoading = () => {
  console.log("loading stoped")
  stopGenerate();
}

const getResponseThink = (content) => {
  let firstStr = '\u003cthink\u003e', lastStr = '\u003c/think\u003e'
  // 查找第一个<think>标签位置
  let firstThinkStart = content.indexOf(firstStr);
  // 查找最后一个</think>标签位置
  let lastThinkEnd = content.lastIndexOf(lastStr);
  // console.log("执行匹配------------------", content)
  if (firstThinkStart >= 0) {
    // console.log("匹配到思维链---", firstStr)
  } else {
    if (firstThinkStart < 0) {
      firstStr = '\u003c思考\u003e', lastStr = '\u003c/思考\u003e'
      firstThinkStart = content.indexOf(firstStr);
      lastThinkEnd = content.lastIndexOf(lastStr);
      if (firstThinkStart >= 0) {
        // console.log("匹配到思维链---", firstStr)
      }
    }
    if (firstThinkStart < 0) {
      firstStr = '\u003cdetails\u003e'
      lastStr = '\u003c/details\u003e'

      firstThinkStart = content.indexOf(firstStr);
      lastThinkEnd = content.lastIndexOf(lastStr);
      if (firstThinkStart >= 0) {
        firstStr = checkSummary(content, firstStr, firstThinkStart);
        // console.log("匹配到思维链---", firstStr)
      }
    }

    if (firstThinkStart < 0) {
      firstStr = '<details>'
      lastStr = '</details>'

      firstThinkStart = content.indexOf(firstStr);
      lastThinkEnd = content.lastIndexOf(lastStr);
      if (firstThinkStart >= 0) {
        firstStr = checkSummary(content, firstStr, firstThinkStart);
        // console.log("匹配到思维链---", firstStr)
      }
    }
    if (firstThinkStart < 0) {
      firstStr = '<\u601d\u8003\u8fc7\u7a0b>'
      lastStr = '</\u601d\u8003\u8fc7\u7a0b>'

      firstThinkStart = content.indexOf(firstStr);
      lastThinkEnd = content.lastIndexOf(lastStr);
      if (firstThinkStart >= 0) {
        // console.log("匹配到思维链---", firstStr)
      }
    }
    if (firstThinkStart < 0) {
      firstStr = '<思考过程>'
      lastStr = '</思考过程>'

      firstThinkStart = content.indexOf(firstStr);
      lastThinkEnd = content.lastIndexOf(lastStr);
      // console.log("匹配思考过程----", content, firstThinkStart, lastThinkEnd)
      if (firstThinkStart >= 0) {
        // console.log("匹配到思维链---", firstStr)
      }
    }
    // if (firstThinkStart < 0) {
    //   console.log("没匹配到----", content)
    // }
  }

  let thinkContent = '';
  let answerContent = '';

  // 如果找到了<think>标签
  if (firstThinkStart !== -1) {
    // 如果没找到</think>标签，则从<think>开始的内容作为thinkContent（去掉<think>标签）
    if (lastThinkEnd === -1) {
      thinkContent = content.substring(firstThinkStart + firstStr.length).trim();
      answerContent = '';
    } else {
      // 从第一个<think>开始到最后一个</think>结束作为thinkContent（去掉头尾标签）
      thinkContent = content.substring(firstThinkStart + firstStr.length, lastThinkEnd).trim();
      // 最后一个</think>之后的内容作为answerContent
      answerContent = content.substring(lastThinkEnd + lastStr.length).trim();
    }
  } else {
    // 如果没有找到<think>标签，则全部内容作为answerContent
    thinkContent = '';
    answerContent = content;
    // console.log("没有找到标签------------------", content)
  }

  return {
    thinkContent,
    answerContent
  };
}

const checkSummary = (content, firstStr, firstThinkStart) => {
  let summaryPattern = '<summary>思考过程</summary>';
  let detailsWithSummary = firstStr + summaryPattern;
  if (content.substring(firstThinkStart, firstThinkStart + detailsWithSummary.length) === detailsWithSummary) {
    // 如果匹配，调整firstStr以跳过<summary>思考过程</summary>部分
    firstStr = detailsWithSummary;
  } else {
    summaryPattern = '\n<summary>思考过程</summary>';
    detailsWithSummary = firstStr + summaryPattern;
    if (content.substring(firstThinkStart, firstThinkStart + detailsWithSummary.length) === detailsWithSummary) {
      // 如果匹配，调整firstStr以跳过<summary>思考过程</summary>部分
      firstStr = detailsWithSummary;
    } else {
      summaryPattern = '\n<summary>图片描述（供参考）</summary>';
      detailsWithSummary = firstStr + summaryPattern;
      if (content.substring(firstThinkStart, firstThinkStart + detailsWithSummary.length) === detailsWithSummary) {
        // 如果匹配，调整firstStr以跳过<summary>思考过程</summary>部分
        firstStr = detailsWithSummary;
      } else {
        summaryPattern = '\n<summary>\ud83d\udd0d \u601d\u8003\u8fc7\u7a0b</summary>';
        detailsWithSummary = firstStr + summaryPattern;
        if (content.substring(firstThinkStart, firstThinkStart + detailsWithSummary.length) === detailsWithSummary) {
          // 如果匹配，调整firstStr以跳过<summary>思考过程</summary>部分
          firstStr = detailsWithSummary;
        }
      }
    }
  }
  return firstStr;
}
const getMarkdownContent = (content) => {
  let result = md.render(content);
  return result;
}
const getMarkdownThink = (content) => {
  let result = md.render(content);
  // console.log("result----", result)
  return result;
}
const getResponseMarkdownThink = (content) => {
  let answerContent = getResponseThink(content).answerContent;
  let result = md.render(answerContent);
  // console.log("result----", result)
  return result;
}
// 编辑思维链按钮
const handleEditThink = (content) => {
  // console.log("handle Edit Think----", content)
  chatParams.showEditContainer = true;
  chatParams.humanCot = getResponseThink(content).thinkContent;
}
// 精炼思维链（'rule' 规则+embedding / 'llm' C1->C2）
const handleRefineThink = async (mode) => {
  const { ElMessage } = await import('element-plus');
  isRefining.value = true;
  try {
    const responseContent = getResponseThink(displayedText.value);
    let payload;
    if (mode === 'llm') {
      payload = {
        human_cot: chatParams.humanCot,
        question: chatParams.lastQuery,
        message_history: getMessageHistories()
      };
    } else {
      payload = {
        original_text: responseContent.thinkContent,
        edited_text: chatParams.humanCot,
        question: chatParams.lastQuery
      };
    }
    const res = await refineCot(mode, payload);
    if (res && res.refined_text) {
      chatParams.humanCot = res.refined_text;
      if (mode === 'rule' && res.emphasized_text) {
        ElMessage.success('规则精炼完成，修改处已应用强调算法');
      } else {
        ElMessage.success('C1->C2 精炼完成');
      }
    } else {
      ElMessage.error('精炼失败：' + ((res && res.error) || '未知错误'));
    }
  } catch (err) {
    ElMessage.error('精炼请求失败：' + (err?.message || err));
  } finally {
    isRefining.value = false;
  }
}
// 保存思维链按钮
const handleSaveThink = async () => {
  // console.log("handle Save Think----", chatParams.humanCot)
  isSaveThinking.value = true;
  const responseContent = getResponseThink(displayedText.value);
  let response = await getStringCompare(responseContent.thinkContent, chatParams.humanCot)
  // console.log("handle Save Think response----", response)
  if (response) {
    let chatHistories = chatParams.chatHistories[chatParams.chatHistories.length - 1];
    chatHistories.response.push({
      role: 'assistant',
      // thinkContent: response,
      thinkContent: responseContent.thinkContent,
      answerContent: responseContent.answerContent,
      content: displayedText.value,
      human_cot: chatParams.humanCot,
      cotContent: response.replaceAll('/n', '')
    });
    displayedText.value = ""
    chatParams.showEditContainer = false;
    let newAskMsg = {
      request: "",
      human_cot: chatParams.humanCot,
      llm_cot: responseContent.thinkContent,
      response: [],
      imgList: []
    }
    generate(newAskMsg, true);
    isSaveThinking.value = false;
  }
}
const handleSaveThink_old = async () => {
  // console.log("handle Save Think----", chatParams.humanCot)
  const llm_cot = getResponseThink(displayedText.value).thinkContent;
  let response = await getStringCompare(getResponseThink(displayedText.value).thinkContent, chatParams.humanCot)
  // console.log("handle Save Think response----", response)
  if (response) {
    let chatHistories = chatParams.chatHistories[chatParams.chatHistories.length - 1];
    const content = getResponseThink(displayedText.value)
    chatHistories.response.push({
      role: 'assistant',
      // thinkContent: response,
      thinkContent: content.thinkContent,
      answerContent: content.answerContent,
      content: displayedText.value,
      human_cot: chatParams.humanCot,
      cotContent: response.replaceAll('/n', '')
    });
    displayedText.value = ""
    chatParams.showEditContainer = false;
    let newAskMsg = {
      request: "",
      human_cot: chatParams.humanCot,
      llm_cot: '',
      response: [],
      imgList: []
    }
    generate(newAskMsg, true);
  }
}

onMounted(() => {
  const chatInfo = store.getters.getChatInfo;
  if (!chatInfo || chatInfo.chatId == '') { // 若没有chatId，则跳转到首页
    router.push('/homepage');
  }
  // console.log("onMounted----", chatInfo)

  chatParams.chatId = chatInfo.chatId;
  chatParams.mode = chatInfo.mode;
  handleSendMessage({ msg: chatInfo.content, imgList: chatInfo.imgList });
  store.commit("setChatInfo", { chatId: '', content: '', mode: chatInfo.mode, imgList: [] });
})
// 组件卸载时清理
onUnmounted(() => {
  if (controller.value) controller.value.abort();
  clearInterval(printerInterval);
  console.log("stop interval --- 2")
  printerInterval = null;
});

// 监听生成状态变化
watch(isGenerating, (newVal) => {
  if (!newVal) {
    clearInterval(printerInterval);
    console.log("stop interval --- 3")
    printerInterval = null;
    // 确保显示完整内容
    if (displayedText.value !== fullResponse.value) {
      displayedText.value = fullResponse.value;
    }
  }
});


</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: sans-serif;
}

textarea {
  width: 100%;
  padding: 12px;
  margin-bottom: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
}

.controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

button {
  padding: 0;
  width: 15px;
  height: 15px;
  background: transparent;
  color: #333;
  border: none;
  cursor: pointer;
  transition: background 0.3s;
}

button:disabled {
  /* background: #cccccc; */
  cursor: not-allowed;
}

button:not(:disabled):hover {
  /* background: #359a6d; */
  /* background: #e0e0e0; */
}

.chat-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 20px;
}

.chat-item {
  width: 100%;
}

.chat-item-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-item-user {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.chat-item-content-request {
  max-width: 100%;
  padding: 5px 12px;
  /* background: #42b983; */
  background: #edf3fe;
  /* color: white; */
  color: #0f1115;
  border-radius: 4px;
  border-top-right-radius: 4px;
  word-wrap: break-word;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: left;
}

.uploaded-file-item-tag {
  width: 30px;
  padding: 0 !important;
}

.chat-item-assistant {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  width: 100%;
}

.pre-line-content {
  white-space: pre-line;
}

.chat-item-content-response {
  max-width: 100%;
  width: 100%;
  text-align: left;
  padding: 12px 16px;
  /* background: #f0f0f0; */
  color: #333;
  border-radius: 12px;
  border-top-left-radius: 4px;
  word-wrap: break-word;
  /* box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); */
  box-sizing: border-box;
}

.chat-item-content-response-role {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
  font-weight: 500;
}

.chat-item-content-response-content {
  line-height: 1.2;
  white-space: pre-wrap;
}

.chat-item-content-response-think {
  margin-bottom: 12px;
  padding: 10px;
  /* background:#f0f0f0; */

  background: rgba(244, 245, 249, 1);
  border-left: 3px solid rgba(215, 216, 221, 1);
  /* background: #fff3cd;
  border-left: 3px solid #ffc107; */
  /* border-radius: 4px; */
  position: relative;
}

.chat-item-content-response-think.output-response-think {
  padding: 10px 15px 30px 15px;
}

.chat-item-content-response-think.output-response-think:hover .think-edit-content {
  display: block;
}

.think-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: bold;
  color: rgba(18, 19, 22, 0.9);
  margin-bottom: 6px;
}

.think-content {
  font-size: 13px;
  color: rgba(18, 19, 22, 0.6);
  line-height: 1.6;
  white-space: normal;
}

.think-save-content {
  position: absolute;
  right: 15px;
  bottom: 10px;
}

.think-edit-content {
  position: absolute;
  right: 15px;
  bottom: 10px;
  display: none;
}

.chat-item-content-response-answer {
  margin-top: 8px;
}

.answer-content {
  line-height: 1.4;
  color: #333;
}

.answer-content :deep(h1),
.answer-content :deep(h2),
.answer-content :deep(h3),
.answer-content :deep(h4),
.answer-content :deep(h5),
.answer-content :deep(h6) {
  margin: 5px 0 5px 0;
  font-weight: bold;
  color: #333;
  margin-block-start: 0px;
  margin-block-end: 0px;
  line-height: 1;
}

.answer-content :deep(p) {
  margin: 8px 0;
  margin-block-end: 0 !important;
  margin-block-start: 0 !important;
  white-space: normal;
  line-height: 1.6;
}

.answer-content :deep(ul),
.answer-content :deep(ol) {
  margin: 0px 0;
  padding-left: 20px;
  padding-inline-start: 15px;
  margin-block-start: 0px;
  margin-block-end: 0px;
  white-space: normal;
}

.answer-content :deep(li) {
  display: list-item;
  margin-top: 2.5px;
  margin-bottom: 2.5px;
  padding-top: 0;
  padding-bottom: 0;
  line-height: 1.2;
}

.answer-content :deep(code) {
  background: #f4f4f4;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.answer-content :deep(pre) {
  background: #f4f4f4;
  padding: 5px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 5px 0;
}

.answer-content :deep(pre code) {
  background: none;
  padding: 0;
}

.answer-content :deep(blockquote) {
  border-left: 4px solid #ddd;
  margin: 5px 0;
  padding-left: 16px;
  color: #666;
}

.answer-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.answer-content :deep(th),
.answer-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.answer-content :deep(th) {
  background: #f5f5f5;
  font-weight: bold;
}

.output-container {
  margin-bottom: 5px;
}
.output-container-status{
  text-align: left;
  margin-bottom: 5px;
}

.output-container-status-dot {
  display: inline-block;
  margin-left: 5px;
}

.output-container-status-dot .dot {
  display: inline-block;
  opacity: 0;
  animation: dotPrinter 3s infinite;
}

.output-container-status-dot .dot:nth-child(1) {
  animation-delay: 0s;
}

.output-container-status-dot .dot:nth-child(2) {
  animation-delay: 1s;
}

.output-container-status-dot .dot:nth-child(3) {
  animation-delay: 2s;
}

@keyframes dotPrinter {
  0% {
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  30% {
    opacity: 1;
  }
  40% {
    opacity: 0;
  }
  100% {
    opacity: 0;
  }
}
.output-display {
  line-height: 1.2;
  white-space: pre-wrap;
  /* max-height: 400px; */
  overflow-y: auto;
}

.cursor {
  animation: blink 1s infinite;
}

@keyframes blink {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0;
  }
}

/* 无边框输入框样式 */
.no-border-input :deep(.el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  /* background: transparent !important; */
  /* padding: 0 !important; */
  resize: none !important;
}

.no-border-input :deep(.el-textarea__inner):focus {
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

.no-border-input :deep(.el-input__wrapper) {
  border: none !important;
  box-shadow: none !important;
  /* background: transparent !important; */
  /* padding: 0 !important; */
}

.no-border-input :deep(.el-input__wrapper):focus {
  border: none !important;
  box-shadow: none !important;
}

/* 文本修改对比样式 */
.deleted {
  text-decoration: line-through;
  color: red;
}

.added {
  color: blue;
}

.unchanged {
  color: black;
}
</style>