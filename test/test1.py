# 匯入 FastAPI 框架與 WebSocket 類別
from fastapi import FastAPI,WebSocket

# 匯入 FileResponse 回應模組，讓我們可以直接回傳 HTML 畫面
from fastapi.responses import FileResponse

# 建立一個 FastAPI 應用實例
app = FastAPI()

html ="web.html"
# 提供 HTML 首頁的路由，當使用者進入 "/" 就回傳這段 HTML
@app.get("/")
async def get():
    return FileResponse(html) #把前面定義好的 html 字串包裝成「HTML 回應」送回去給使用者

# 提供 WebSocket 的端點，路徑為 /ws
@app.websocket("/ws") #必須用 websocket 不是 get！
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept() # 接受前端的 WebSocket 連線請求

    #代表伺服器會不斷等待使用者傳訊息（進入無限循環）
    while True:
        data= await websocket.receive_text() #從使用者那邊接收訊息（文字）
        await websocket.send_text(f"你說{data}") #現在只是把他自己講的話回送給他（回音測試）