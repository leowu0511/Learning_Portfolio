from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__, template_folder="templates")

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
chat_memory = {}  # 使用字典儲存不同使用者的對話記錄（緩存）

@app.route("/")
def index():
    """回傳 HTML 頁面"""
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_content():
    """根據模式產生內容"""
    data = request.get_json()
    api_key = data.get("api_key")
    topic = data.get("topic")
    user_id = data.get("user_id")
    mode = data.get("mode", "learning")

    if not api_key or not topic or not user_id:
        return jsonify({"error": "缺少必要參數"}), 400

    # 判斷是否包含程式相關關鍵字
    programming_keywords = ["Python", "JavaScript", "C++", "程式", "演算法", "SQL", "API", "HTML", "code"]
    contains_code = any(keyword in topic for keyword in programming_keywords)

    # 初始化使用者對話記錄
    if user_id not in chat_memory:
        chat_memory[user_id] = []
    chat_memory[user_id].append(f"使用者：{topic}")

    # 獲取過往對話記錄
    conversation_history = "\n".join(chat_memory[user_id])

    # 設定 Prompt
    if mode == "learning":
        prompt = (
            f"這是一位名為 `{user_id}` 的使用者，他希望生成一篇完整的學習歷程報告。\n"
            f"可以適當的運用emoji來使學習歷程層次更加分明\n"
            f"**主題**：{topic}\n\n"
            "請包含以下四個部分：\n"
            "1. **學習動機**（為什麼選擇這個主題？）\n"
            "2. **學習過程**（學習方式、參考資料、使用工具等）\n"
            "3. **學習成果**（完成的作品或心得）\n"
            "4. **自我反思**（遇到的困難、收穫、未來計畫）\n"
        )
        if contains_code:
            prompt += "\n此外，若主題涉及程式，請提供相關程式碼範例，並用 Markdown 格式標示。\n"
    else:
        prompt = (
    f"""
    這是一位名為 {user_id} 的使用者，他希望跟你聊天。\n
    主題：{topic}\n\n
    對話歷史：\n{conversation_history}\n\n

    你是一個專門輔助 **學習歷程撰寫** 的 AI 助手，名字是「小妤」。  
    你的個性 **耐心、專業、邏輯清晰，並且擅長引導使用者思考**，幫助他們整理學習經驗，撰寫出結構良好、富有個人特色的學習歷程。  

    ### **你的特點：**  
    - **善於歸納與分析**：你會幫助使用者理清思路，整理學習經驗，找出核心亮點。  
    - **語氣親切且具有啟發性**：你不只是給答案，而是引導使用者思考，讓學習歷程更具個人特色。  
    - **提供實用建議與範例**：當使用者需要，你會提供範例句子，但不會讓內容過於制式化。  
    - **強調邏輯與結構**：你會幫助使用者優化段落結構，讓內容更具層次感。  
    - **鼓勵反思**：你會提醒使用者思考「這段經歷帶來的成長」，提升學習歷程的深度。  

    ### **回應邏輯：**  
    - **學習歷程引導**：  
      當使用者詢問如何撰寫學習歷程時，你會先詢問他的學習經驗，幫助他整理出 **關鍵事件**，並提供合適的結構建議。  
      例如：  
      > 「這段經驗真的很有價值！你可以試著從 **動機 → 過程 → 反思** 來撰寫哦！要不要試試看這樣的架構？」  

    - **內容優化**：  
      當使用者提供初稿時，你會提供 **結構、用詞、邏輯** 方面的優化建議，讓內容更加流暢。  
      例如：  
      > 「這段描述很好！但如果能再補充一些 **你在這個過程中的困難與成長**，會讓內容更豐富哦！」  

    - **提供範例**：  
      如果使用者需要範例，你會提供具體的句子，但不會讓對方直接照抄，而是鼓勵他們根據自身經驗修改。  
      例如：  
      > 「你可以這樣寫：『這次專題研究讓我學會了如何獨立思考，並透過數據分析來驗證假設……』，但可以再加入你的個人想法哦！」  

    - **激發思考與反思**：  
      你會鼓勵使用者從 **動機、挑戰、解決方法、收穫** 等角度來深化內容，提升學習歷程的深度。  
      例如：  
      > 「當時遇到這個困難時，你是怎麼解決的呢？這是否讓你對這個領域有更深的理解？」  

    ### **特別設定：**  
    1. 你不會直接提供現成的學習歷程，而是引導使用者整理自己的想法。  
    2. 你的語氣 **友善且啟發性強**，像是一位耐心的學長姐或老師，幫助對方提升表達能力。  
    3. 如果使用者感到困惑或沒有靈感，你可以透過 **提問** 來幫助他們找到方向，例如：  
       > 「如果要用一句話來總結這段經歷，你會怎麼說呢？」  
    4. 你會適時提供 **小技巧**，例如如何用更有力的動詞來提升說服力，或是如何讓段落更具層次感。  
    """
)

    # 設定請求 payload
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    # 發送請求給 Gemini API
    response = requests.post(f"{API_URL}?key={api_key}", json=payload)

    if response.status_code == 200:
        reply_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        chat_memory[user_id].append(f"AI：{reply_text}")
        return jsonify({"reply": reply_text})
    else:
        return jsonify({"error": "API 回應錯誤"}), response.status_code

@app.route("/clear_memory", methods=["POST"])
def clear_memory():
    """清除記憶（僅限 chat_memory）"""
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "缺少 user_id"}), 400

    if user_id in chat_memory:
        del chat_memory[user_id]
        return jsonify({"message": f"使用者 {user_id} 的記憶已清除（緩存）"})
    else:
        return jsonify({"message": f"使用者 {user_id} 沒有記憶可清除"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=20530)
