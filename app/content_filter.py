import openai #使用 OpenAI 的 ChatGPT API
import os #讀取環境變數（例如 API 金鑰）

openai.api_key = os.getenv("OPENAI_API_KEY")

async def is_illegal_content(text:str) -> bool:
    #加入chatgpt指令 讓他去判斷text是否有違規
    prompt = f"""
        你是一個用來識別聊天室違規語句的 AI。

        以下是一段使用者最近幾句話，請判斷是否包含性暗示、性邀約、色情、或以年齡+性別開場等不當行為：
        「{text}」

        只回 YES 或 NO。
    """

    try:
        #非同步版的 ChatCompletion.create()（可與 FastAPI 配合）
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo", #使用最便宜、快速的 ChatGPT 模型
            messages=[{"role" : "user", "content" : prompt}], #系統與使用者對話紀錄（這裡只有一條使用者提問）
            temperature=0 #設定為 0 表示回覆穩定、不亂跑（只會選最可能的答案）
        )
        
        result = response.choices[0].message.content.strip().upper() #response.choices[0].message.content → 是 ChatGPT 回覆的文字
        return result == "YES"
    
    #如果 API 發生錯誤（例如：金鑰錯誤、連線失敗）
    except Exception as e:
        print("ChatGPT 濾詞錯誤：", e)
        return False #預設傳回 False（讓聊天室不中斷，但不封鎖內容）

