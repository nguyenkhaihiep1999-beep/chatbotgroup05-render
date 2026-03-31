from flask import Flask, request, jsonify, render_template, session
import re
import unicodedata
import json
import os
from fuzzywuzzy import fuzz

app = Flask(__name__)
app.secret_key = "super-secret-key"

# ================= LOAD JSON =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE_DIR, "data", "chatbot.json")

with open(RULES_PATH, encoding="utf-8") as f:
    DATA = json.load(f)

# ================= NORMALIZE =================
def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    # Loại bỏ dấu tiếng Việt
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    # Loại bỏ ký tự đặc biệt
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ================= DETECT INTENT =================
def detect_intent(user_input):
    best_rule = None
    best_score = 0
    user_input_norm = normalize_text(user_input)
    
    for rule in DATA["rules"]:
        for kw in rule["keywords"]:
            kw_norm = normalize_text(kw)
            # Dùng token_set_ratio để tìm keyword bất chấp thứ tự từ hoặc từ thừa
            score = fuzz.token_set_ratio(kw_norm, user_input_norm)
            if score > best_score:
                best_score = score
                best_rule = rule
                
    if best_score >= 80:  # Ngưỡng chấp nhận
        return best_rule
    return None

# ================= DETECT MAJOR =================
# ================= DETECT MAJOR =================
def detect_major(user_input):
    best_major = None
    best_score = 0
    user_input_norm = normalize_text(user_input)
    
    # 1. BỘ LỌC TỪ THỪA: Xóa chữ "ngành" để độ dài chuỗi gần với tên gốc nhất
    # (Giúp thuật toán fuzzy không bị nhiễu bởi các từ không quan trọng)
    user_clean = re.sub(r'\b(nganh|nganh hoc)\b', '', user_input_norm).strip()
    words = user_clean.split()
    
    for major, kws in DATA["majors"].items():
        for kw in kws:
            kw_norm = normalize_text(kw)
            
            # Ưu tiên tuyệt đối cho các từ viết tắt (vd: qtkd, it)
            if kw_norm in words:
                return major
                
            # 2. ÁP DỤNG ĐA THUẬT TOÁN FUZZY
            # - token_set_ratio: Tốt cho trường hợp gõ dư từ, lộn xộn thứ tự
            score_token = fuzz.token_set_ratio(kw_norm, user_clean)
            
            # - ratio: Tốt nhất cho trường hợp sai lỗi chính tả (khao -> khoa, liu -> lieu)
            score_ratio = fuzz.ratio(kw_norm, user_clean)
            
            # - WRatio: Thuật toán tổng hợp mạnh mẽ nhất của thư viện fuzzywuzzy
            score_w = fuzz.WRatio(kw_norm, user_clean)
            
            # Lấy điểm cao nhất mà các thuật toán bắt được
            score = max(score_token, score_ratio, score_w)
            
            if score > best_score:
                best_score = score
                best_major = major
                
    # 3. HẠ NGƯỠNG (THRESHOLD): Chấp nhận sai số từ 75% trở lên thay vì 80%
    if best_score >= 75:
        return best_major
    return None

# ================= GET RESPONSE =================
def get_response(intent_field, major=None):
    try:
        field_data = DATA["data"].get(intent_field)
        if not field_data:
            return None

        # Nếu field chứa dict các ngành học
        if major and isinstance(field_data, dict):
            answer = field_data.get(major)
            if answer:
                return str(answer)

        # Nếu field là text chung (chào hỏi, cơ sở, liên hệ...)
        if isinstance(field_data, str):
            return field_data

        return None
    except Exception as e:
        print("GET_RESPONSE ERROR:", e)
        return None

# ================= INFER =================
def infer_answer(raw_input):
    try:
        intent = detect_intent(raw_input)
        major = detect_major(raw_input)

        print(f"INPUT: {raw_input}")
        print(f"INTENT: {intent['field'] if intent else None}")
        print(f"MAJOR: {major}")

        # TH1: Người dùng KHÔNG nhập intent, NHƯNG có nhập major (Ví dụ: "NAGNFH QTKD")
        # => Lấy lại câu hỏi trước đó (Ví dụ: đang hỏi học phí)
        if not intent and major and session.get("last_intent"):
            intent_field = session.get("last_intent")
            session["current_major"] = major
            answer = get_response(intent_field, major)
            return answer if answer else "Hiện chưa có dữ liệu cho ngành này."

        # TH2: Đang nợ một intent từ câu trước và bây giờ user nhập major bổ sung
        if not intent and major and session.get("pending_intent"):
            intent_field = session.pop("pending_intent")
            session["current_major"] = major
            answer = get_response(intent_field, major)
            return answer if answer else "Hiện chưa có dữ liệu cho ngành này."

        # TH3: Không nhận diện được ý định gì cả
        if not intent:
            return "Xin lỗi, tôi chưa hiểu rõ ý bạn. Bạn có thể hỏi về học phí, điểm chuẩn hoặc thông tin ngành học nhé!"

        field = intent["field"]
        session["last_intent"] = field

        # TH4: Nhận ra Intent, và Intent này YÊU CẦU phải có ngành học
        if intent.get("requires_major"):
            if not major:
                major = session.get("current_major")

            if not major:
                session["pending_intent"] = field
                return intent.get("fallback_message", "Bạn muốn hỏi thông tin này cho ngành nào?")

            session["current_major"] = major
            answer = get_response(field, major)
            return answer if answer else "Hiện chưa có dữ liệu cho ngành này."

        # TH5: Intent chung (chào hỏi, tạm biệt, địa chỉ...) không cần ngành
        answer = get_response(field)
        return answer if answer else "Chưa có dữ liệu."

    except Exception as e:
        print("ERROR:", e)
        return "Lỗi server!"

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