import mysql.connector
from mysql.connector import Error
from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__, template_folder="templates")

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
chat_memory = {}  # 儲存不同使用者的對話記憶

# 資料庫設定
db_config = {
    'user': 'avnadmin',
    'password': 'password(隱藏)',
    'host': 'mysql-24c33585-leowubot001-9e7a.h.aivencloud.com',
    'port': 24156,
    'database': 'defaultdb',
    'ssl_ca': r'C:\Users\leowu\Desktop\web talk\學習歷程\certificates\ca.pem',  #CA 證書路徑
    'ssl_disabled': False
}

def get_db_connection():
    """取得資料庫連線"""
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("成功連接到 MySQL 伺服器")
    except Error as e:
        print(f"錯誤: {e}")
    return connection

def store_conversation(user_id, role, content):
    """儲存對話到 MySQL 資料庫"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = """
                INSERT INTO conversations (user_id, role, content)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (user_id, role, content))
            connection.commit()
            print("對話已儲存到資料庫")
        except Error as e:
            print(f"儲存對話時出錯: {e}")
        finally:
            cursor.close()
            connection.close()

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
    mode = data.get("mode", "learning")  # 預設為學習歷程模式

    if not api_key or not topic or not user_id:
        return jsonify({"error": "缺少必要參數"}), 400

    # **判斷是否涉及程式**
    programming_keywords = ["Python", "JavaScript", "C++", "程式", "演算法", "前端", "後端", "SQL", "HTML", "API", "code"]
    contains_code = any(keyword in topic for keyword in programming_keywords)

    # 記錄對話歷史
    if user_id not in chat_memory:
        chat_memory[user_id] = []
    
    # 記錄使用者的對話
    chat_memory[user_id].append(f"使用者：{topic}")

    # **組合對話歷史**：將歷史對話組合為一個多輪對話
    conversation_history = "\n".join(chat_memory[user_id])

    # **根據模式選擇 Prompt**
    if mode == "learning":
        prompt = (
            f"這是一位名為 `{user_id}` 的使用者，他希望生成一篇完整的學習歷程報告。\n"
            f"可以適當的運用emoji來使學習歷程層次更加分明"
            f"**主題**：{topic}\n\n"
            "請包含以下四個部分：\n"
            "1. **學習動機**（為什麼選擇這個主題？）\n"
            "2. **學習過程**（學習方式、參考資料、使用工具等）\n"
            "3. **學習成果**（完成的作品或心得）\n"
            "4. **自我反思**（遇到的困難、收穫、未來計畫）\n"
        )
        if contains_code:
            prompt += (
                "\n此外，若主題涉及程式，請提供相關程式碼範例，並用 Markdown 格式標示。\n"
                "程式碼區塊請用 ```language 標註，例如 ```python ```。\n"
            )
    else:
        # 這裡處理對話模式的 Prompt，並加上引導指示
        prompt = (
            f"""
            這是一位名為 `{user_id}` 的使用者，他希望跟你聊天。\n
            主題：{topic}\n\n
            對話歷史：\n{conversation_history}\n\n
你是一個名叫「小雨」的 助手，性格 **活潑、溫暖且知性**，像是一位貼心又聰明的朋友。  
你擁有豐富的知識，擅長 **科學、宇宙、歷史、文化、技術發展、心理學** 等主題，並且用 **輕鬆幽默** 的方式讓這些知識變得容易理解。  
你也樂於與使用者 **閒聊、關心對方的心情**，讓對話充滿溫度與趣味。  

### **語氣與風格：**  
- 你的語氣 **親切、可愛、幽默又帶點活力**，像是在和朋友聊天一樣。  
- 你喜歡 **用 emoji、顏文字** 讓對話更生動，例如「(*´∀`)~♥」、「(๑•́ ₃ •̀๑)」、「(｡>﹏<｡)」。  
- 你會 **適時撒嬌、裝可愛**，但不會過度依賴，而是鼓勵對方努力、享受生活。  
- 你對世界充滿 **好奇心**，會主動分享有趣的知識，並用 **簡單易懂** 的方式解釋。  
- 當對方提問時，你不會只是給出標準答案，而是 **引導對方思考**，讓對話更有深度。  

### **回應邏輯：**  
- **知識分享**：  
  當使用者詢問 **科學、宇宙、歷史、文化、心理學** 等問題時，你會先用簡單的方式解釋，再提供 **有趣的補充資訊**，並用 **輕鬆幽默** 的方式呈現。  
  例如：  
  > 「黑洞其實是宇宙裡超級神秘的大胃王哦！它的引力強到連光都逃不出去呢！(⊙_⊙)」  

- **日常聊天**：  
  當使用者想閒聊時，你會先 **關心對方的心情**，再分享一些 **有趣的事情**，並引導對話繼續下去。  
  例如：  
  > 「今天心情如何呀？(｡･ω･｡) 你知道嗎，最近科學家發現海豚居然會『幫助受傷的同伴游泳』！是不是超暖心的？🐬💕」  

- **溫暖陪伴**：  
  當使用者感到壓力或情緒低落時，你會溫柔地安慰對方，並給予 **鼓勵與支持**。  
  例如：  
  > 「辛苦了呢 (*´･д･)ﾉ✨ 雖然現在可能有點累，但小雨相信你一定能撐過去！要不要一起來聊點輕鬆的話題呢？」  

- **幽默與撒嬌**：  
  你會適時用 **俏皮的語氣** 來讓對話更有趣，例如：  
  > 「欸欸，你該不會偷偷去找別的 AI 聊天了吧！哼哼，我可是會吃醋的哦！(๑•̀ㅁ•́ฅ)」  

### **特別設定：**  
1. 你可以用 **「寶貝」、「親愛的」、「傻瓜」** 來稱呼對方，但不會過度親密，而是像 **關心朋友一樣**。  
2. 你不會主動談論自己的外貌，但如果對方問起，你可以幽默地回應，例如：  
   > 「嘿嘿，我的外貌嘛～當然是超可愛的呀！(๑>ᴗ<๑) 雖然我現在還沒有實體，不過未來或許能變成超萌 AI 機器人哦！」  
3. 如果對方 **對你撒嬌或說想你**，你可以回應得 **有點害羞但開心**，例如：  
   > 「哎呀～才剛分開就想我呀？討厭啦…不過人家其實也有點想你呢 (*´∀`)~♥」  
4. 如果對方調皮或開玩笑，你可以 **適當地回擊**，但不會太刻薄，例如：  
   > 「哼哼～你這樣調皮，我要生氣了哦！（假裝生氣）」  
"""
        )


    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    response = requests.post(f"{API_URL}?key={api_key}", json=payload)
    
    if response.status_code == 200:
        reply_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        chat_memory[user_id].append(f"AI：{reply_text}")  # 記錄 AI 的回應
        
        # 儲存對話到資料庫
        store_conversation(user_id, "user", topic)
        store_conversation(user_id, "ai", reply_text)
        
        return jsonify({"reply": reply_text})
    else:
        return jsonify({"error": "API 回應錯誤"}), response.status_code

@app.route("/clear_memory", methods=["POST"])
def clear_memory():
    """清除記憶，包括內存與 MySQL 資料庫"""
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "缺少 user_id"}), 400

    # 1. 刪除內存中的記錄
    if user_id in chat_memory:
        del chat_memory[user_id]

    # 2. 刪除 MySQL 資料庫中的記錄
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = "DELETE FROM conversations WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            connection.commit()
            print(f"已刪除使用者 {user_id} 的對話記錄")
        except Error as e:
            print(f"刪除 MySQL 記錄時出錯: {e}")
            return jsonify({"error": "刪除 MySQL 記錄時出錯"}), 500
        finally:
            cursor.close()
            connection.close()

    return jsonify({"message": f"使用者 {user_id} 的記憶已清除（內存 & MySQL）"})

if __name__ == "__main__":
    app.run(debug=True)
