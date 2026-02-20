from flask import Flask, request, jsonify, render_template
import re
import unicodedata
import json
import os

app = Flask(__name__)

# ===== LOAD RULES FROM JSON =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE_DIR, "data", "chatbot.json")

with open(RULES_PATH, encoding="utf-8") as f:
    rules = json.load(f)

# ===== NLP: TIỀN XỬ LÝ =====
def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ===== SUY DIỄN IF - THEN =====
def infer_answer(user_input):
    results = []

    for rule in rules:
        for kw in rule.get("keywords", []):
            if kw in user_input:
                ans = rule.get("answer", "")
                if isinstance(ans, list):
                    results.extend(ans)
                else:
                    results.append(ans)
                break

    # Xóa trùng – giữ thứ tự
    results = list(dict.fromkeys(results))

    if results:
        return "<br>".join(results)

    return "Xin lỗi, chủ nhân chưa thêm thông tin về vấn đề này cho tôi, bạn có thể hỏi câu hỏi khác tôi sẽ cố gắng giúp bạn."

# ===== ROUTES =====
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = normalize_text(data.get("message", ""))
    reply = infer_answer(user_input)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=False)

