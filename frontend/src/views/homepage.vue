<template>
    <div class="container main-container-wrapper">
        <div class="flex mb-10 select-list-container">
            <el-select style="width:200px;" v-model="modeParams.currmode">
                <el-option v-for="item in modeParams.modeList" :value="item.value" :label="item.name">{{ item.name
                    }}</el-option>
            </el-select>
        </div>
        <ContentInput ref="contentInputRef" :is-auto-send="false" @on-stop-loading="handleStopLoading"
            @on-send-msg="handleSendMessage"></ContentInput>
    </div>
</template>

<script setup>
import { useStore } from "vuex";
import { useRouter } from "vue-router";
import ContentInput from "@/components/contentInput.vue";
import { reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from 'element-plus';
import { createChat } from '@/api/chatapi'

const store = useStore();
const router = useRouter();
const contentInputRef = ref()

const modeParams = reactive({
    modeList: [ // 模型列表
        { value: 1, name: "R1大模型" },
        { value: 2, name: "Deepseek R1" },
    ],
    currmode: 1,
    imgList: []
})

const handleStopLoading = () => {
   // alert("handle Stop Loading")

}
const handleSendMessage = async (msgInfo) => {
    // alert("handle Send Message")
    let msg = msgInfo.msg;
    console.log("问题内容：", msgInfo)
    // const resp = await createChat(modeParams.currmode);
    // console.log("resp----", resp)
    // if (resp.success) {
    //     const chatInfo = {
    //         chatId: resp.data.chat_id,
    //         content: msg,
    //         mode: modeParams.currmode,
    //         imgList:msgInfo.imgList
    //     }
    //     store.commit("setChatInfo", chatInfo);
    //     // store.commit("setChatContent", msg);
    //     // store.commit('setMode', modeParams.currmode)
    //     console.log("chatInfo----", store.getters.getChatInfo)
    //     router.push('/chatdetail')
    // } else {
    //     ElMessage.error(resp.msg || resp.data.msg)
    // }

    const chatInfo = {
        chatId: generateRandomString(8),
        content: msg,
        mode: modeParams.currmode,
        imgList: msgInfo.imgList
    }
    store.commit("setChatInfo", chatInfo);
    // store.commit("setChatContent", msg);
    // store.commit('setMode', modeParams.currmode)
    console.log("chatInfo----", store.getters.getChatInfo)
    router.push('/chatdetail')
}

const generateRandomString = () => {
    return Array.from({ length: 8 }, () =>
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'[
        Math.floor(Math.random() * 62)
        ]
    ).join('');
}
</script>

<style scoped>
.main-container-wrapper {
    width: 80%;
    max-width: 1200px;
    margin: auto;
}

.select-list-container {
    justify-content: right;
}
</style>