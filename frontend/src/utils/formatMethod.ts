import MarkdownIt from "markdown-it";
const md = new MarkdownIt({ html: true });

const getMarkdownHtml = (content: string) => {
    if (!content) return '';
    let result = ""
    try {
        result = md.render(content)

    } catch (err) {
        console.log("md失败---", content)
        result = content
    }
    return result;
}

/**
* 参数处理
* @param {*} params  参数
*/
const tansParams = (params:any) => {
    let result = ''
    for (const propName of Object.keys(params)) {
        const value = params[propName];
        var part = encodeURIComponent(propName) + "=";
        if (value !== null && value !== "" && typeof (value) !== "undefined") {
            if (typeof value === 'object') {
                for (const key of Object.keys(value)) {
                    if (value[key] !== null && value[key] !== "" && typeof (value[key]) !== 'undefined') {
                        let params = propName + '[' + key + ']';
                        var subPart = encodeURIComponent(params) + "=";
                        result += subPart + encodeURIComponent(value[key]) + "&";
                    }
                }
            } else {
                result += part + encodeURIComponent(value) + "&";
            }
        }
    }
    return result
}

export {
    getMarkdownHtml,tansParams
}