from fastapi import FastAPI ,WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from typing import Dict, List
import uuid
import asyncio

app = FastAPI()

#等待配對的使用者: {遊戲名稱(ex:apex,LOL): [WebSocket, ...]}
waiting_users: Dict[str, List[WebSocket]] = {}

#活耀中的聊天室房間: {room_id(uuid): [WebSocket,WebSocket]}
active_rooms: Dict[str, List[WebSocket]] = {}

#雙方聊天室中收發訊息
async def handle_chat(myself: WebSocket, partner: WebSocket):
    try:
        while True:
            data = await myself.receive_text()
            await partner.send_text(f"對方說：{data}")
            await myself.send_text(f"你：{data}")
        
    except WebSocketDisconnect:
        #避免一人離開後，剩下那一人離開後發了"對方已離開聊天室"到對方的聊天室
        try:
            await partner.send_text("對方已離開聊天室")
        except:
            pass

#首頁
@app.get("/")
async def get():
    #這樣瀏覽器每次都會重新抓最新的 web2.html
    return FileResponse("main_web.html", headers={"Cache-Control": "no-store"})

@app.websocket("/ws/{game}")
async def websocket_endpoint(websocket:WebSocket ,game: str ):
    await websocket.accept() #接受 WebSocket 的握手請求

    # 加入遊戲等待佇列 （若遊戲尚未出現）
    if game not in waiting_users:
        waiting_users[game] = []

    #嘗試配對
    queue = waiting_users[game]

    if queue:
        partner = queue.pop(0)
        room_id = str(uuid.uuid4()) #使用 uuid 生成唯一 ID
        active_rooms[room_id] = [websocket, partner] # 儲存聊天室的兩個人

        await websocket.send_text(f"✅ 配對成功！房號：{room_id}")
        await partner.send_text(f"✅ 配對成功！房號：{room_id}")
        
        # ✅ 雙人聊天直到任一人離線
        await asyncio.gather(
            handle_chat(websocket, partner),
            handle_chat(partner, websocket)
        )

    #沒人等 進入排隊
    else:
        queue.append(websocket)
        await websocket.send_text(f"配對中....")
        
        # 改為等待配對事件，而不是自己 receive
        try:
            # 等待配對，停在這裡什麼都不做
            try:
                await asyncio.Event().wait()  # 模擬「等待另一人加入」，但實際會被 gather 取代
            except asyncio.CancelledError:
                 pass  # 當伺服器結束時，不印出錯誤

        #假如使用者不等了選擇關閉， 將使用者移出等待池
        except WebSocketDisconnect:
            if websocket in queue:
                queue.remove(websocket)










