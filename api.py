from flask import Flask, request, jsonify, render_template, session
import re
import unicodedata
import json
import os

app = Flask(__name__)
app.secret_key = "super-secret-key"

# ================= LOAD JSON =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE_DIR, "data", "chatbot.json")

with open(RULES_PATH, encoding="utf-8") as f:
    DATA = json.load(f)

# ================= NORMALIZE =================
def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ================= DETECT MAJOR =================
def detect_major(user_input):
    for major_name, keywords in DATA["majors"].items():
        for kw in keywords:
            kw_norm = normalize_text(kw)
            pattern = r"\b" + re.escape(kw_norm) + r"\b"

            if re.search(pattern, user_input):
                return major_name
    return None
# ================= DETECT INTENT =================
def detect_intent(user_input):

    for rule in DATA["rules"]:
        for kw in rule["keywords"]:
            kw_norm = normalize_text(kw)

            # Match theo từ hoàn chỉnh
            pattern = r"\b" + re.escape(kw_norm) + r"\b"

            if re.search(pattern, user_input):
                return rule

    return None
# ================= GET RESPONSE =================
def get_response(intent_field, major=None):

    if major:
        major_data = DATA["data"].get(major)
        if major_data:
            answer = major_data.get(intent_field)
            if answer:
                return answer

    answer = DATA["data"].get(intent_field)
    if answer:
        return answer

    return None

# ================= INFER =================
def infer_answer(raw_input):

    user_input = normalize_text(raw_input)

    intent = detect_intent(user_input)
    major = detect_major(user_input)

    # Nếu user chỉ nhập ngành sau khi bot hỏi
    if not intent and major and session.get("pending_intent"):
        intent_field = session.pop("pending_intent")
        session["current_major"] = major
        answer = get_response(intent_field, major)
        return answer if answer else "Hiện chưa có dữ liệu cho ngành này."

    if not intent:
        return "Xin lỗi, tôi chưa hiểu câu hỏi. Ví dụ: 'học phí CNTT'."

    field = intent["field"]

    # Nếu cần ngành
    if intent.get("requires_major"):

        if not major:
            major = session.get("current_major")

        if not major:
            session["pending_intent"] = field
            return "Bạn muốn hỏi ngành nào?"

        session["current_major"] = major

        answer = get_response(field, major)
        return answer if answer else "Hiện chưa có dữ liệu cho ngành này."

    # Không cần ngành
    answer = get_response(field)
    return answer if answer else "Xin lỗi, tôi chưa có dữ liệu cho câu hỏi này."

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    reply = infer_answer(message)
    return jsonify({"reply": reply})

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)