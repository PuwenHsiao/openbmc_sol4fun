import json
import socket
import asyncio
import logging
import websockets
import multiprocessing
from multiprocessing import Process
from flask import Flask, render_template, request

IP = '127.0.0.1'
PORT_WEB = 1234
PORT_CHAT = 4321

# 此方法利用UDP協議，生成一個UDP包，將自己的IP放入UDP協議頭中，然後再從中獲取本機的IP。此方法雖然不會真實向外發包，但仍然會申請一個UDP的連接埠
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    IP = s.getsockname()[0]
finally:
    s.close()


# 保存字典 名字:websockets
USERS = {}

# 提供html
app = Flask(__name__)


@app.route('/')
def index_chat():
    return render_template("index.html", ip=IP, port=PORT_CHAT)


def web():
    app.run(host='0.0.0.0', port=PORT_WEB)


# 提供聊天的後台
async def chat(websocket, path):
    logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                        filename="chat.log",
                        level=logging.INFO)
    # 握手
    await websocket.send(json.dumps({"type": "handshake"}))
    async for message in websocket:
        data = json.loads(message)
        message = ''
        # 使用者發資訊
        if data["type"] == 'send':
            name = '404'
            for k, v in USERS.items():
                if v == websocket:
                    name = k
            data["from"] = name
            if len(USERS) != 0:  # asyncio.wait doesn't accept an empty list
                message = json.dumps(
                    {"type": "user", "content": data["content"], "from": name})
        # 使用者登錄
        elif data["type"] == 'login':
            USERS[data["content"]] = websocket
            if len(USERS) != 0:  # asyncio.wait doesn't accept an empty list
                message = json.dumps(
                    {"type": "login", "content": data["content"], "user_list": list(USERS.keys())})
        # 使用者退出
        elif data["type"] == 'logout':
            del USERS[data["content"]]
            if len(USERS) != 0:  # asyncio.wait doesn't accept an empty list
                message = json.dumps(
                    {"type": "logout", "content": data["content"], "user_list": list(USERS.keys())})
        # 列印聊天資訊到日誌
        logging.info(data)
        # 群發
        await asyncio.wait([user.send(message) for user in USERS.values()])


def chat_server():
    start_server = websockets.serve(chat, '0.0.0.0', PORT_CHAT)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    p_web = Process(target=web, daemon=True)
    p_web.start()
    p_chat_server = Process(target=chat_server, daemon=True)
    p_chat_server.start()

    print("按下ctrl + c 結束程序。聊天記錄將保存在chat.log")
    print("聊天室地址" + IP + ':' + str(PORT_WEB))
    p_web.join()
    p_chat_server.terminate()
