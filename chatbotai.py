import tkinter as tk
import unicodedata
import re

# ===== NLP: TIEN XU LY VAN BAN =====
def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

# ===== TAP LUAT IF - THEN =====
rules = [
    {"keywords": ["hoc phi", "hocphi"], "answer": "Hoc phi hien tai la 8 trieu moi hoc ky."},
    {"keywords": ["dang ky", "dangky", "dang ky mon"], "answer": "Sinh vien dang ky mon hoc tren cong thong tin sinh vien."},
    {"keywords": ["thoi gian hoc", "gio hoc"], "answer": "Thoi gian hoc tu thu 2 den thu 6."},
    {"keywords": ["dia chi", "o dau"], "answer": "Truong nam tai 140 Le Trong Tan."}
]

# ===== SUY DIEN =====
def infer_answer(user_input):
    for rule in rules:
        for keyword in rule["keywords"]:
            if keyword in user_input:
                return rule["answer"]
    return "Xin loi, toi chua co tri thuc ve cau hoi nay."

# ===== GUI =====
def send_message():
    user_text = entry.get()
    if user_text.strip() == "":
        return

    processed_text = normalize_text(user_text)
    chat_box.insert(tk.END, "Ban: " + user_text + "\n")
    chat_box.insert(tk.END, "Chatbot: " + infer_answer(processed_text) + "\n\n")
    entry.delete(0, tk.END)

root = tk.Tk()
root.title("Chatbot AI - IF THEN + NLP")
root.geometry("500x400")

chat_box = tk.Text(root, height=18, width=58)
chat_box.pack(pady=10)

entry = tk.Entry(root, width=45)
entry.pack(side=tk.LEFT, padx=10)

send_btn = tk.Button(root, text="Gui", command=send_message)
send_btn.pack(side=tk.LEFT)

root.mainloop()