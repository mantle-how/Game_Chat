from fastapi import FastAPI ,WebSocket,WebSocketDisconnect, Query
from fastapi.responses import FileResponse
from typing import Dict, List
import uuid
import asyncio
from app.content_filter import is_illegal_content

app = FastAPI()

#等待配對的使用者: {遊戲名稱(ex:apex,LOL): [{"id":id,"ws" : websocket,"nickname":nickname},{"id":id,"ws" : websocket,"nickname":nickname}]}
waiting_users: Dict[str, List[Dict[str, WebSocket]]] = {}

#活耀中的聊天室房間: {room_id(uuid): [WebSocket,WebSocket]}
active_rooms: Dict[str, List[WebSocket]] = {}
#雙方聊天室中收發訊息
async def handle_chat(myself: WebSocket, partner: WebSocket,my_name:str):
    try:
        while True:
            data = await myself.receive_text()
            if await is_illegal_content(data):
                await myself.send_text(f"系統判定此訊息含有不當內容，未傳送")
                continue
            await partner.send_text(f"{my_name}說：{data}")
            await myself.send_text(f"你說：{data}")
        
    except WebSocketDisconnect:
        #避免一人離開後，剩下那一人離開後發了"對方已離開聊天室"到對方的聊天室
        try:
            await partner.send_text(f"{my_name}已離開聊天室")
        except:
            pass

#首頁
@app.get("/")
async def get():
    #這樣瀏覽器每次都會重新抓最新的 web2.html
    return FileResponse("app/main_web.html", headers={"Cache-Control": "no-store"})

@app.websocket("/ws/{game}")
async def websocket_endpoint(
    websocket:WebSocket ,
    game: str , 
    id:str = Query(...) ,
    nickname:str=Query(...) ):
    await websocket.accept() #接受 WebSocket 的握手請求
    print(f"🟢 {id} ({nickname}) 已加入遊戲：{game}")

    # 加入遊戲等待佇列 （若遊戲尚未出現）
    if game not in waiting_users:
        waiting_users[game] = []


    #嘗試配對
    queue = waiting_users[game]
    
     # 防止重複加入等待池（例如連點兩次按鈕）
    for user in queue:
        if user["id"]  == id:
            await websocket.send_text(f"你已在配對中，請不要重新加入~")
            return

    if queue:
        partner_data = queue.pop(0)
        partner = partner_data["ws"]
        partner_name = partner_data["nickname"]
        room_id = str(uuid.uuid4()) #使用 uuid 生成唯一 ID
        active_rooms[room_id] = [websocket, partner] # 儲存聊天室的兩個人

        await websocket.send_text(f"✅ 配對成功！對方是:{partner_name},房號：{room_id}")
        await partner.send_text(f"✅ 配對成功！對方是:{nickname},房號：{room_id}")
        print(f"配對完成，當前 queue：{[u['id'] for u in queue]}")
        
        # ✅ 雙人聊天直到任一人離線
        await asyncio.gather(
            handle_chat(websocket, partner, nickname),
            handle_chat(partner, websocket, partner_name)
        )

    #沒人等 進入排隊
    else:
        queue.append({"id":id,"ws" : websocket,"nickname":nickname})
        await websocket.send_text(f"{nickname}配對中....")
        print(f"🕒 {id} 加入等待池，當前 queue：{[u['id'] for u in queue]}")
        
        # 改為等待配對事件0，而不是自己 receive
        try:
            # 等待配對，停在這裡什麼都不做
            try:
                await asyncio.Event().wait()  # 模擬「等待另一人加入」，但實際會被 gather 取代
            except asyncio.CancelledError:
                 pass  # 當伺服器結束時，不印出錯誤

        #假如使用者不等了選擇關閉， 將使用者移出等待池
        except WebSocketDisconnect:
            for user in queue:
                if user["ws"] == websocket:
                    queue.remove(user)
                    print(f"🔴 {id} 離線（等待中斷線），已從等待池中移除")
                    break #因為有for迴圈 所以break掉for迴圈
        #finally:
            










