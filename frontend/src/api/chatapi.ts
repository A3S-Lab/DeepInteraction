import request from '@/utils/request';

/**
 * 创建新会话
 */
export function createChat(modeId) {
    let data = {
        "mode": modeId
    }
    return request({
        url: '/create_chat',
        method: 'post',
        data: data
    });
}
/**
 * 获取字符串对比结果
 */
export function getStringCompare(source,target) {
    let data={
        original:source,
        edition:target
    }
    return request({
        // url: '/chatdiff-api/diff',
        url: '/api/diff',
        method: 'post',
        data: data
    });
}
/**
 * CoT 精炼：mode=rule（规则+embedding）/ mode=llm（C1->C2）
 */
export function refineCot(mode, payload) {
    return request({
        url: '/api/refine',
        method: 'post',
        data: { mode, ...payload },
        timeout: 120000
    });
}

