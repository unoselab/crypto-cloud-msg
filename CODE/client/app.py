import os
import json
import base64
import asyncio
import websockets

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization


def b64e(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def b64d(x: str) -> bytes:
    return base64.b64decode(x.encode("ascii"))


def hkdf(x: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"chat",
    ).derive(x)


def encrypt(key: bytes, data: bytes) -> bytes:
    nonce = os.urandom(12)
    ct = ChaCha20Poly1305(key).encrypt(nonce, data, None)
    return nonce + ct


def decrypt(key: bytes, blob: bytes) -> bytes:
    nonce = blob[:12]
    ct = blob[12:]
    return ChaCha20Poly1305(key).decrypt(nonce, ct, None)


def pub_bytes(pub: x25519.X25519PublicKey) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


class Client:
    def __init__(self, name: str, peer: str):
        self.name = name
        self.peer = peer

        self.init_priv = x25519.X25519PrivateKey.generate()
        self.init_pub = self.init_priv.public_key()

        self.chat_priv = x25519.X25519PrivateKey.generate()
        self.chat_pub = self.chat_priv.public_key()

        self.k1 = None
        self.session_key = None
        self.sent_chatkey = False

    async def run(self):
        uri = f"ws://127.0.0.1:9000/ws/{self.name}"

        async with websockets.connect(uri) as ws:
            self.ws = ws

            await self.ws.send(json.dumps({
                "type": "init",
                "pubkey": b64e(pub_bytes(self.init_pub)),
            }))

            print("connected")
            print("commands: /handshake, /quit")

            listener = asyncio.create_task(self.listen())

            while True:
                text = await asyncio.to_thread(input, "> ")
                text = text.strip()

                if text == "/quit":
                    listener.cancel()
                    break

                if text == "/handshake":
                    await self.ws.send(json.dumps({
                        "type": "get_peer_key",
                        "peer": self.peer,
                    }))
                    continue

                if not self.session_key:
                    print("no secure session")
                    continue

                blob = encrypt(self.session_key, text.encode("utf-8"))

                await self.ws.send(json.dumps({
                    "type": "msg",
                    "peer": self.peer,
                    "blob": b64e(blob),
                }))

    async def send_chatkey(self):
        if self.sent_chatkey:
            return

        inner = pub_bytes(self.chat_pub)

        blob = encrypt(self.k1, inner)

        await self.ws.send(json.dumps({
            "type": "chatkey",
            "peer": self.peer,
            "blob": b64e(blob),
        }))

        self.sent_chatkey = True
        print("chatkey sent")

    async def listen(self):
        async for raw in self.ws:
            data = json.loads(raw)
            msg_type = data["type"]

            if msg_type == "peer_key":
                peer_init_pub = x25519.X25519PublicKey.from_public_bytes(
                    b64d(data["pubkey"])
                )
                self.k1 = hkdf(self.init_priv.exchange(peer_init_pub))
                await self.send_chatkey()

            elif msg_type == "chatkey":
                sender_init_pub = x25519.X25519PublicKey.from_public_bytes(
                    b64d(data["sender_init_pub"])
                )

                self.k1 = hkdf(self.init_priv.exchange(sender_init_pub))

                peer_chat_pub = x25519.X25519PublicKey.from_public_bytes(
                    decrypt(self.k1, b64d(data["blob"]))
                )

                if not self.sent_chatkey:
                    blob = encrypt(self.k1, pub_bytes(self.chat_pub))
                    await self.ws.send(json.dumps({
                        "type": "chatkey",
                        "peer": data["sender"],
                        "blob": b64e(blob),
                    }))
                    self.sent_chatkey = True
                    print("chatkey replied")

                self.session_key = hkdf(self.chat_priv.exchange(peer_chat_pub))
                print("secure session ready")

            elif msg_type == "msg":
                if not self.session_key:
                    continue

                text = decrypt(self.session_key, b64d(data["blob"])).decode("utf-8")
                print(f"\n[{data['sender']}] {text}")


async def main():
    name = input("username: ").strip()
    peer = input("peer: ").strip()

    client = Client(name, peer)
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
