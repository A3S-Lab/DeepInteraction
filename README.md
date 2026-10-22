# cotChatWithAI

CoT（思维链）对话与精炼系统：Vue3 前端 + Flask 后端。

## 功能

- 多模态对话：图片上传 + 流式回答，支持 `<思考>` 标签折叠展示思维链
- 思维链编辑与 diff：用户可编辑 AI 思维链，保存时红绿高亮显示改动
- **CoT 精炼**（`POST /refine`，两种模式）：
  - `mode=rule`：规则 + Embedding 算法（源自 ACL_Human_CoT 论文实现）
    Emphasis Pruning（去冗余强调）→ 20% 语义过滤（DashScope text-embedding-v4，不可用时降级为关键词过滤）→ NumericalMask（数字掩码 `[NUM]`），
    同时返回 `abc*GH*` 格式的改动强调高亮。输入 `original_text` + `edited_text` + `question`
  - `mode=llm`：大模型 C1→C2 精炼专家提示词，把详细解题思路抽象为方法论摘要。输入 `human_cot` + `question`（或 `message_history`）

前端在"编辑思维链"模式中提供两个精炼按钮（漏斗图标 = 规则精炼，魔法棒图标 = AI 精炼），结果填回编辑框供确认后保存。

## 后端

```bash
cd backend
pip install -r requirements.txt

export DASHSCOPE_API_KEY=sk-xxx        # 必填（DashScope/阿里百炼）
export UPLOAD_FOLDER=./imgs            # 图片保存目录
export MODEL_NAME=qwen3-vl-plus        # 对话模型
export REFINE_LLM_MODEL=qwen-vl-max    # LLM 精炼模型
export COT_FORWARD_URL=http://...      # user_cot 外部思考链路（可选）
export PORT=5019
python main.py
```

## 前端

```bash
cd frontend
npm install
npm run dev        # 默认 http://localhost:8088，/api 代理到 localhost:5019
```

代理目标可通过 `VITE_PROXY_TARGET` 覆盖：`VITE_PROXY_TARGET=http://120.26.174.121 npm run dev`

## 生产部署注意

- 生产请用 gunicorn：`gunicorn -w 2 -b 0.0.0.0:5019 main:app`（不要用 `python main.py` 自带的 dev server）
- 所有密钥走环境变量，代码中不保存任何 API key
