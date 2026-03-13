from fastapi import FastAPI, WebSocket
import json

app = FastAPI()

connections = {}
init_keys = {}


@app.websocket("/ws/{user}")
async def ws_endpoint(ws: WebSocket, user: str):
    await ws.accept()
    connections[user] = ws

    try:
        while True:
            data = json.loads(await ws.receive_text())
            msg_type = data["type"]

            if msg_type == "init":
                init_keys[user] = data["pubkey"]

            elif msg_type == "get_peer_key":
                peer = data["peer"]
                if peer in init_keys:
                    await connections[user].send_text(json.dumps({
                        "type": "peer_key",
                        "pubkey": init_keys[peer]
                    }))

            elif msg_type == "chatkey":
                peer = data["peer"]
                if peer in connections and user in init_keys:
                    await connections[peer].send_text(json.dumps({
                        "type": "chatkey",
                        "sender": user,
                        "sender_init_pub": init_keys[user],
                        "blob": data["blob"],
                    }))

            elif msg_type == "msg":
                peer = data["peer"]
                if peer in connections:
                    await connections[peer].send_text(json.dumps({
                        "type": "msg",
                        "sender": user,
                        "blob": data["blob"],
                    }))

    except Exception:
        pass
    finally:
        connections.pop(user, None)