import os
import uuid
import requests
from difflib import SequenceMatcher
from flask import (
    Flask,
    Response,
    jsonify,
    request,
    send_from_directory,
)
from openai import OpenAI


app = Flask(__name__)

# ===== 通用配置 =====
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/home/admin/cot_dev/imgs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_NAME = os.environ.get("MODEL_NAME", "qwen3-vl-plus")
REFINE_LLM_MODEL = os.environ.get("REFINE_LLM_MODEL", "qwen-vl-max")
DASHSCOPE_API_KEY = os.environ["DASHSCOPE_API_KEY"]
DASHSCOPE_BASE_URL = os.environ.get(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
COT_FORWARD_URL = os.environ.get(
    "COT_FORWARD_URL", "http://47.100.37.20:5020/forward"
)

# 初始化 DashScope 兼容的 OpenAI 客户端
client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)


# ===== 图片上传与访问 =====
@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # 返回当前服务的访问地址，若部署在外网可通过 PUBLIC_BASE_URL 覆盖
    public_base = os.environ.get("PUBLIC_BASE_URL", request.host_url.rstrip("/"))
    return jsonify({"url": f"{public_base}/api/images/{filename}"})


@app.route("/images/<filename>")
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ===== 文本差异 HTML =====
def single_change_span(old: str, new: str):
    sm = SequenceMatcher(a=old, b=new, autojunk=False)
    opcodes = sm.get_opcodes()

    result = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            result.append(("unchanged", old[i1:i2]))
        elif tag == "delete":
            result.append(("deleted", old[i1:i2]))
        elif tag == "insert":
            result.append(("added", new[j1:j2]))
        elif tag == "replace":
            result.append(("deleted", old[i1:i2]))
            result.append(("added", new[j1:j2]))

    return result


def generate_html(changes):
    html_content = """
        <p>
    """
    for change_type, text in changes:
        if change_type == "unchanged":
            html_content += f'<span class="unchanged">{text}</span>'
        elif change_type == "deleted":
            html_content += f'<span class="deleted">{text}</span>'
        elif change_type == "added":
            html_content += f'<span class="added">{text}</span>'
    html_content += """
        </p>
    """
    return html_content


@app.route("/diff", methods=["POST"])
def diff():
    data = request.json
    if not data or "original" not in data or "edition" not in data:
        return jsonify(
            {"error": 'Invalid input. Please provide "original" and "edition" fields.'}
        ), 400

    original = data["original"]
    edition = data["edition"]

    changes = single_change_span(original, edition)
    html_content = generate_html(changes)

    return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}


# ===== 大模型转发（原 /forward）=====
@app.route("/forward", methods=["POST"])
def forward():
    data = request.get_json(force=True)

    stream = data.get("stream", False)
    message_history = data.get("message_history", [])
    mediaprompt = data.get("mediaprompt", [])
    user_query = data.get("user_query", "")
    user_cot = data.get("user_cot", "")

    # 若提供 user_cot，先走外部链路做思考再反馈
    if user_cot:
        response_from_curl = None
        try:
            payload = {"user_query": user_cot, "mediaprompt": mediaprompt}
            resp = requests.post(
                COT_FORWARD_URL, json=payload, timeout=15
            )
            response_from_curl = resp.text
        except Exception as exc:  # noqa: BLE001
            response_from_curl = f"request_failed: {exc}"

        user_query = response_from_curl

    if mediaprompt or user_query:
        current_msg = {"role": "user", "content": []}

        if mediaprompt:
            for img in mediaprompt:
                current_msg["content"].append(
                    {"type": "image_url", "image_url": {"url": img}}
                )

        if user_query:
            if user_cot:
                user_query = f"{user_query}\n{user_cot}"
            current_msg["content"].append(
                {
                    "type": "text",
                    "text": user_query
                    + "\n"
                    + "回答问题前，请先深入思考并将思考过程用<思考>和</思考>标签包裹",
                }
            )

        message_history.append(current_msg)

    if not stream:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=message_history,
            stream=False,
        )
        return Response(
            completion.choices[0].message.content,
            content_type="text/plain; charset=utf-8",
        )

    def generate():
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=message_history,
            stream=True,
        )

        for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    return Response(generate(), content_type="text/plain; charset=utf-8")


# ===== 文本精炼：rule=规则+embedding，llm=C1->C2 精炼专家 =====
@app.route("/refine", methods=["POST"])
def refine():
    from api_refinement import DeepInteractionAPI
    from refine_prompt import COT_REFINE_SYSTEM_PROMPT, COT_REFINE_USER_TEMPLATE

    data = request.get_json(force=True)
    mode = data.get("mode", "rule")

    if mode == "llm":
        # --- LLM 版：C1 -> C2 ---
        human_cot = data.get("human_cot", "")
        if not human_cot:
            return jsonify({"error": "human_cot is required in llm mode"}), 400

        question = data.get("question", "")
        image_url = data.get("image_url", "")
        message_history = data.get("message_history", [])

        # question 未显式给出时，从消息历史取最近一条用户消息
        if not question:
            for msg in reversed(message_history):
                if msg.get("role") == "user":
                    question = next(
                        (item.get("text", "") for item in msg.get("content", [])
                         if item.get("type") == "text"),
                        "",
                    )
                    if not image_url:
                        image_url = next(
                            (item["image_url"]["url"] for item in msg.get("content", [])
                             if item.get("type") == "image_url" and item.get("image_url")),
                            "",
                        )
                    break

        content = []
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
        content.append({
            "type": "text",
            "text": (
                COT_REFINE_SYSTEM_PROMPT
                + COT_REFINE_USER_TEMPLATE.format(question=question, cot=human_cot)
            ),
        })

        try:
            completion = client.chat.completions.create(
                model=REFINE_LLM_MODEL,
                messages=[{"role": "user", "content": content}],
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": f"LLM refinement failed: {exc}"}), 502
        c2 = completion.choices[0].message.content.strip()

        return jsonify({
            "mode": "llm",
            "question": question,
            "c1": human_cot,
            "refined_text": c2,
        })

    # --- 规则+embedding 版 ---
    original_text = data.get("original_text", "")
    edited_text = data.get("edited_text", "")
    question = data.get("question", "")
    if not edited_text:
        return jsonify({
            "error": "edited_text is required in rule mode"
        }), 400

    api = DeepInteractionAPI()
    try:
        result = api.process_text(original_text, edited_text, question)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"refinement failed: {exc}"}), 500

    return jsonify({
        "mode": "rule",
        "refined_text": result.get("refined_text", ""),
        "emphasized_text": result.get("emphasized_text", ""),
        "changes_detected": result.get("changes_detected", {}),
        "processing_stats": result.get("processing_stats", {}),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5019))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true")
    app.run(host="0.0.0.0", port=port, debug=debug)
