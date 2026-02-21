# This is a demo of a safe key exchange between two users
# The server does not know what the keys are
# This code is just a demo and will be reworked

import os
import base64
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def b64(b):
    return base64.b64encode(b).decode("ascii")


def hkdf_32(shared_secret, salt, info):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    ).derive(shared_secret)


def aead_encrypt(key, pt, aad=b""):
    nonce = os.urandom(12)
    return nonce + ChaCha20Poly1305(key).encrypt(nonce, pt, aad)


def aead_decrypt(key, blob, aad=b""):
    return ChaCha20Poly1305(key).decrypt(blob[:12], blob[12:], aad)


def x25519_pub_bytes(pub):
    return pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def x25519_pub_from_bytes(b):
    return x25519.X25519PublicKey.from_public_bytes(b)


@dataclass
class User:
    init_priv: x25519.X25519PrivateKey
    init_pub: x25519.X25519PublicKey
    k1: bytes = None
    k1_salt: bytes = None
    chat_priv: x25519.X25519PrivateKey = None
    chat_pub: x25519.X25519PublicKey = None
    k2: bytes = None

    @classmethod
    def create(cls):
        priv = x25519.X25519PrivateKey.generate()
        return cls(priv, priv.public_key())

    def derive_k1(self, other_pub, salt):
        self.k1_salt = salt
        self.k1 = hkdf_32(self.init_priv.exchange(other_pub), salt, b"messenger:k1")

    def gen_chat_keys(self):
        self.chat_priv = x25519.X25519PrivateKey.generate()
        self.chat_pub = self.chat_priv.public_key()

    def enc_chat_pub(self):
        if self.k1 is None:
            return
        return aead_encrypt(self.k1, x25519_pub_bytes(self.chat_pub), b"chat-pub2")

    def dec_chat_pub(self, blob):
        return x25519_pub_from_bytes(aead_decrypt(self.k1, blob, b"chat-pub2"))

    def derive_k2(self, other_chat_pub):
        if not self.chat_priv:
            return
        salt = self.k1_salt or b"\x00" * 16
        self.k2 = hkdf_32(self.chat_priv.exchange(other_chat_pub), salt, b"messenger:k2")


def main():
    u1, u2 = User.create(), User.create()
    salt = os.urandom(16)

    u1.derive_k1(x25519_pub_from_bytes(x25519_pub_bytes(u2.init_pub)), salt)
    u2.derive_k1(x25519_pub_from_bytes(x25519_pub_bytes(u1.init_pub)), salt)

    assert u1.k1 == u2.k1

    u1.gen_chat_keys()
    u2.gen_chat_keys()

    u1.derive_k2(u1.dec_chat_pub(u2.enc_chat_pub()))
    u2.derive_k2(u2.dec_chat_pub(u1.enc_chat_pub()))

    assert u1.k2 == u2.k2

    msg = b"This is a test message"
    ct = aead_encrypt(u1.k2, msg, b"msg")
    pt = aead_decrypt(u2.k2, ct, b"msg")

    print(pt.decode("utf-8"))


if __name__ == "__main__":
    main()
