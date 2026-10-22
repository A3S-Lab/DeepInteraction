<template>
  <div class="">
    <div class="relative">
      <!-- 整体容器 -->
      <div class="border input-container-wrapper">
        <div id="uploadedFileList" style="display:flex;">
          <el-tag class="uploaded-file-item-tag" v-for="(item, index) in uploadParams.fileUrls" :key="index" closable :disable-transitions="false"
            @close="handleClose(index)">
            <div class="uploaded-file-item">
              <img :src="item"></img>
            </div>
          </el-tag>

        </div>

        <!-- 可编辑的文本区域 -->
        <div class="relative">
          <textarea rows="3" ref="textareaRef" v-model="contentText" placeholder="" @keydown="handleKeyDown"
            @input="handleKeyInput" @cut="handleCut" class="w100 text-area-custom border-none"></textarea>
          <!-- 模拟placeholder -->
          <div v-if="shouldShowPlaceholder && !contentText"
            class="absolute placeholder-container top-0 flex items-center pointer-events-none">
            <img class="text-img-icon" src="@/image/inputIcon.png" />
            <span class="text-placeholder">请输入你的问题</span>
          </div>
        </div>

        <!-- 底部区域 -->
        <div class="flex items-center justify-between border-none">
          <div class="flex"></div>
          <div class="flex gap-8">
            <!-- 单文件上传按钮 -->
            <!-- <el-upload v-model:file-list="uploadParams.fileList" :action="uploadParams.action"
              :on-change="handleFileChange" :on-success="handleUploadSuccess" :on-error="handleUploadError"
              :accept="imageTypes" :before-upload="beforeUpload" :show-file-list="false"
              :multiple="false">
              <el-button class="input-btn border-none" title="单文件上传"><el-icon>
                  <Picture />
                </el-icon></el-button>
            </el-upload> -->
            <!-- 多文件上传按钮 -->
            <el-upload v-model:file-list="multiUploadParams.fileList" :action="multiUploadParams.action"
              :on-change="handleFileChange" :on-success="handleUploadSuccess" :on-error="handleUploadError"
              :accept="imageTypes" :before-upload="beforeUpload" :show-file-list="false"
              :multiple="true" :limit="10">
              <el-button class="input-btn border-none" title="多文件上传"><el-icon>
                  <FolderAdd />
                </el-icon></el-button>
            </el-upload>
            <!-- 右下角发送按钮 -->
            <!-- 对话生成中 -->
            <el-button class="input-btn send-message-btn loading-send-icon border-none" v-if="isLoading"
              @click="handleCloseSend">
              <el-icon>
                <VideoPause />
              </el-icon>
              <div class="tooltip">停止生成</div>
            </el-button>
            <!-- 空白不可发送 -->
            <el-button class="input-btn send-message-btn wait-input-icon border-none" v-else-if="props.isGenerate||!hasSelection"
              :disabled="true">
              <el-icon>
                <el-icon>
                  <Position />
                </el-icon>
              </el-icon>
            </el-button>
            <!-- 激活可发送 -->
            <el-button class="input-btn send-message-btn active-send-icon border-none" v-else
              @click="handleSendMessage">
              <el-icon>
                <Promotion />
              </el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useStore } from "vuex";
import { ref, computed, onMounted, reactive } from "vue";
import { Position, Promotion, VideoPause, Picture, FolderAdd } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
const store = useStore();
// const chatimageUrl='/chatimage-api/upload'
const chatimageUrl='/api/upload'

// 更新emits定义
const emit = defineEmits(["on-send-msg", "on-stop-loading"]);

// 定义入参
const props = defineProps({
  isAutoSend: {
    type: Boolean,
    default: () => false,
  },
  isGenerate:{
    type: Boolean,
    default: () => false,
  }
});

// 使用 computed 获取响应式数据
const textareaRef = ref()
const contentText = ref("");

// 状态控制
const isLoading = ref(false);
const shouldShowPlaceholder = ref(true);

const uploadParams = reactive({
  fileList: [],
  action: chatimageUrl, // 单文件上传路径，通过代理转发到 localhost:8000
  fileUrls: [],
})

const multiUploadParams = reactive({
  fileList: [],
  action: chatimageUrl, // 多文件上传路径，通过代理转发到 localhost:8000
})

// 允许的图片类型
const imageTypes = 'image/jpeg,image/jpg,image/png,image/gif,image/bmp,image/webp,image/svg+xml'

// 计算是否有选择值
const hasSelection = computed(() => {
  return contentText.value && (contentText.value.trim() !== "");
});

// 处理输入事件
const handleKeyInput = (event) => {
  if (event.data) {
    shouldShowPlaceholder.value = false;
  }
}
// 处理按键
const handleKeyDown = (event) => {
  // 处理特殊按键 Enter
  if (event.key === 'Enter') {
    if (!props.isGenerate&&!isLoading.value && hasSelection) {
      event.preventDefault(); // 阻止默认的换行行为
      handleSendMessage();
    }
  }
  // 处理退格键
  if (event.key === 'Backspace' && contentText.value.length >= 0) {
    shouldShowPlaceholder.value = true
  }
  if (event.key === 'Delete') {
    if (event.target.selectionEnd - event.target.selectionStart == contentText.value.length) {
      shouldShowPlaceholder.value = true
    } else if (event.target.selectionStart == 0 && contentText.value.length == 1) {
      shouldShowPlaceholder.value = true
    }

  }
}
const handleCut = (event) => {
  console.log("cut----", event)
  if (event.target.selectionEnd - event.target.selectionStart == contentText.value.length) {
    shouldShowPlaceholder.value = true
  }
}

const handleFileChange = (file, fileList) => {
  console.log("fileChange----", file, fileList)
  
  // 单文件上传，检查是否超过已上传文件数量限制
  if (uploadParams.fileUrls.length >= 10) {
    ElMessage.warning('最多只能上传10个文件');
    return false;
  }
}

// 上传前验证
const beforeUpload = (file) => {
  console.log("上传前验证----", file)
  
  // 检查文件类型 - 更严格的图片类型检查
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml'];
  const isImage = allowedTypes.includes(file.type);
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件！支持格式：JPG、PNG、GIF、BMP、WEBP、SVG');
    return false;
  }
  
  // 检查文件大小 (限制为10MB)
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB！');
    return false;
  }
  
  // 检查文件名
  const fileName = file.name.toLowerCase();
  const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'];
  const hasValidExtension = imageExtensions.some(ext => fileName.endsWith(ext));
  
  if (!hasValidExtension) {
    ElMessage.error('文件扩展名必须是图片格式！');
    return false;
  }
  
  return true;
}

// 上传成功处理
const handleUploadSuccess = (response, file, fileList) => {
  // 判断上传结果 - 适配单文件上传响应格式
  if (response) {
    // 上传成功，将文件URL添加到fileUrls中
    console.log("---------",response)
    if (response.url) {
      uploadParams.fileUrls.push(response.url);
      console.log("文件上传成功，URL已添加:", response.url);
      ElMessage.success('文件上传成功');
    } else {
      console.warn("上传成功但未返回文件URL");
      ElMessage.warning('上传成功但未获取到文件地址');
    }
  } else {
    // 上传失败
    console.error("上传失败:", response);
    ElMessage.error(response.message || '上传失败，请再重试');
  }
}

// 上传失败处理
const handleUploadError = (error, file, fileList) => {
  console.error("上传出错----", error, file, fileList);
  
  // 检查是否是网络错误或服务器错误
  if (error && error.response) {
    const status = error.response.status;
    if (status >= 500) {
      ElMessage.error('服务器错误，请稍后重试');
    } else if (status === 413) {
      ElMessage.error('文件过大，请选择较小的文件');
    } else if (status === 400) {
      ElMessage.error('文件格式不支持或参数错误');
    } else {
      ElMessage.error('上传失败，请重试');
    }
  } else {
    ElMessage.error('网络错误，请检查网络连接后重试');
  }
  
  // 移除测试代码，不再添加测试图片
  // let i = Math.floor(Math.random() * 2) + 1;
  // uploadParams.fileUrls.push("/testData/testImage/icon"+i+".png");
}

// 停止生成-发送
const handleCloseSend = () => {
  if (isLoading.value) {
    isLoading.value = false;
    console.log("停止发送。。。")
    emit("on-stop-loading")
    return;
  }
}

// 处理发送请求
const handleSendMessage = () => {
  if (isLoading.value) {
    isLoading.value = false;
    console.log("停止发送。。。")
    emit("on-stop-loading")
    return;
  }

  if (!hasSelection.value) return;
  emit("on-send-msg", {
    msg: contentText.value.trim(),
    imgList: uploadParams.fileUrls
  });
  shouldShowPlaceholder.value = true
};

// 返回输入的文本
const getMessageInfo = () => {
  return {
    msg: contentText.value || "",
    files: uploadParams.fileUrls
  }
};

// 设置加载状态
const setIsLoading = (value) => {
  isLoading.value = value;
};
// 清空输入框所有内容
const clearInput = () => {
  contentText.value = "";
  uploadParams.fileList = [];
  uploadParams.fileUrls = [];
  multiUploadParams.fileList = [];
};
const handleClose = (index) => {
  uploadParams.fileUrls.splice(index, 1);
};
onMounted(() => {

});

defineExpose({
  setIsLoading,
  clearInput,
  getMessageInfo
});
</script>

<style scoped>
/* 输入框样式 */
textarea {
  line-height: 18px;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f1f5f9;
}

/* 滚动条样式 */
textarea::-webkit-scrollbar {
  width: 2px;
}

textarea::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

textarea::-webkit-scrollbar-thumb {
  background-color: #cbd5e0;
  border-radius: 4px;
}

.text-img-icon {
  width: 18px;
  height: 18px;
}

.text-placeholder {
  font-weight: 400;
  color: rgba(18, 19, 22, 0.35);
  padding-left:5px;
}

/* 布局按钮样式 */
button[class*="text-"] {
  z-index: 10;
}

/* 滑块动画效果 */
.transition-all {
  transition-property: all;
}

.duration-300 {
  transition-duration: 300ms;
}

.ease-in-out {
  transition-timing-function: ease-in-out;
}

/* Tooltip样式 */
.tooltip {
  position: absolute;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  padding: 5px 8px;
  height: 32px;
  line-height: 18px;
  background: #121316;
  color: white;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 400;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s;
  color: rgba(255, 255, 255, 0.95);
  z-index: 20;
}

.tooltip:first-child {
  left: 100%;
}

.tooltip::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 1px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.85);
}

.send-message-btn {
  display: flex;
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  justify-content: center;
  align-items: center;
  transition-property: all;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.send-message-btn:hover {
  border: none !important;
}

.loading-send-icon {
  /* cursor:default; */
  background: transparent;
}

.wait-input-icon {
  /* color: #b4b6bc; */
  color: #464a53;
  background: transparent;
}

.active-send-icon {
  color: #121316;
  background: transparent;
  /* background: #b4b6bc; */
}

.active-send-icon svg path {
  fill: #ffffff !important;
}

.active-send-icon:hover {
  background-color: rgba(180, 190, 220, 0.80);
}

.audio-normal-btn {
  border-radius: 4px;
}

.audio-normal-btn:hover {
  background-color: #F4F5F9;
}

/* .text-send-icon {
  color: white;
} */

.group:hover .tooltip,
.loading-send-icon:hover .tooltip {
  opacity: 1;
}

/* 发送按钮状态过渡效果 */
button {
  transition: background-color 0.3s ease, transform 0.2s ease;
}

button:active:not(:disabled) {
  transform: scale(0.95);
}

.input-container-wrapper {
  padding: 12px 16px 12px 16px;
  border-color: #464a53;
  border-radius: 8px;
  margin: auto;
}

.text-area-custom {
  width: 100%;
  /* 占满父容器宽度 */
  font-size: 14px;
  /* 字体大小，与示例一致 */
  line-height: 1.5;
  /* 行高，可根据字体调整 */
  outline: none;
  /* 移除聚焦边框 */
  resize: none;
  /* 禁止手动调整文本域大小 */
  padding-right: 12px;
  overflow-y: auto;
  /* 垂直方向溢出时显示滚动条 */
  border-radius: 4px;
  color: #121316;
}

.text-area-custom:focus .placeholder-container {
  display: none;
}
#uploadedFileList{
  margin-bottom: 8px;
}



.uploaded-file-item {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}


/* 关闭按钮样式 */
:deep(.uploaded-file-item-tag .el-tag__close) {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 16px;
  height: 16px;
  /* background: #ff4757; */
  color: white;
  /* border-radius: 50%; */
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  /* border: 2px solid white; */
  z-index: 10;
}

:deep(.uploaded-file-item-tag:hover .el-tag__close) {
  background: #ff3742;
}

/* 隐藏upload组件的focus border */
:deep(.el-upload) {
  outline: none !important;
  border: none !important;
}

:deep(.el-upload:focus) {
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}

:deep(.el-upload:focus-within) {
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}

:deep(.el-upload__input) {
  outline: none !important;
  border: none !important;
}

:deep(.el-upload__input:focus) {
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}

/* 覆盖upload组件内button的focus样式 */
:deep(.el-upload button:focus) {
  outline: 0px auto -webkit-focus-ring-color !important;
}

:deep(.el-upload button:focus-visible) {
  outline: 0px auto -webkit-focus-ring-color !important;
}
</style>