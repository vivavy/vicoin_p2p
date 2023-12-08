import socket
import threading
import time
import types
import uuid as _uuid
from vip2p._base_ import *


def threaded(fn) -> types.FunctionType:
    def _wrapper(*a, **k):
        thread = threading.Thread(target=fn, args=a, kwargs=k)
        thread.daemon = True
        thread.start()
        return thread

    return _wrapper


class vip2p(vip2p):
    NAME = b"VIP2P"
    VERSION = b"1.0"

    INIT = b"INIT"
    OK = b"OK"
    DISCONN = b"DISCONN"
    SEND = b"SEND"

    @staticmethod
    def request(conn:socket.socket, cmd:bytes,
                data:str|bytes=b"")->bytes:
        if isinstance(data, str):
            data = data.encode()
        conn.sendall(r:=(vip2p.NAME + b"\r\n" + vip2p.VERSION +
                     b"\r\n" + cmd + b"\r\n" + data))
        return r
    
    @staticmethod
    def parse(data: bytes) -> list[bytes]:
        return data.split(b"\r\n", 3)[2:]


class Server(Server):
    '''server class'''

    def __init__(self, bindary: tuple[str,int], debug: bool = False):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.debug = debug
        self.bind = bindary
    
    def init(self):
        if self.debug:
            print("[DEBUG][SERVER] Binding socket... ", end="")
        self.sock.bind(self.bind)
        print("Done")
    
    def start(self):
        self.users = {}
        self.sock.listen(1024)
        while True:
            self.handledm(SNode(self, *self.sock.accept(), self.debug))
    
    @threaded
    def handledm(self, node: SNode):
        while True:
            node.handle()
            time.sleep(2)
    
    def disconn(self, node: SNode, data: bytes):
        if self.debug:
            print("[DEBUG][SERVER] User {%s} disconnecting:\n\t%s" %
                  (str(node.uuid), data.decode()))
        node.conn.close()
        del self.users[node.uuid]
        if self.debug:
            print("[DEBUG][SERVER] User {%s} disconnected"
                  % str(node.uuid))


class CNode(CNode):
    '''client-side user class'''

    uuid: _uuid.UUID
    conn: socket.socket
    stat: str
    send: bool

    def __init__(self, serv: tuple[str,int], debug: bool = False):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(serv)
        self.uuid = None
        self.stat = "NOINIT"
        self.debug = debug
        self.send = False
        self.recv = None
    
    def __del__(self):
        if self.debug:
            print("[DEBUG][CLIENT] Closing connection... ", end="")
        self.conn.close()
        if self.debug:
            print("Done")
    
    def wait_for_send(self):
        while not self.send:
            ...
    
    @threaded
    def recvdm(self):
        while True:
            recv = self.conn.recv(1024)
            if vip2p.parse(recv)[0] == vip2p.SEND:
                self.send = True
            else:
                self.recv = recv
    
    def init(self):
        if self.debug:
            print("[DEBUG][CLIENT] Initializing... ", end="")
        self.recvdmt = self.recvdm()
        self.wait_for_send()
        vip2p.request(self.conn, vip2p.INIT)
        self.send = False
        while not self.recv: ...
        a = self.recv
        if self.debug:
            print("[DEBUG][CLIENT] UUID recieved:", repr(a))
        self.uuid = _uuid.UUID(vip2p.parse(a)[1].decode())
        if self.debug:
            print("Done with UUID = {%s}" % str(self.uuid))
    
    def disconn(self):
        if self.debug:
            print("[DEBUG][CLIENT] Disconnecting... ", end="")
        self.wait_for_send()
        vip2p.request(self.conn, vip2p.DISCONN)
        self.send = False
        while not self.recv: ...
        a = vip2p.parse(self.recv)[0].decode()
        if self.debug:
            print("Done with status", a)
        del self.recvdmt


class SNode(SNode):
    '''
    server-side user class
    '''

    serv: Server

    def __init__(self, server: Server,
                 conn: socket.socket,
                 addr: tuple[str,int],
                 debug: bool = False):
        self.serv = server
        self.uuid = _uuid.uuid4()
        self.conn = conn
        self.addr = addr
        self.stat = "NOINIT"
        self.wait = True
        self.debug = debug
        self.recv = None
        self.recvdmt = self.recvdm()
    
    def __del__(self):
        if self.debug:
            print("[DEBUG][SERNOD] Closing connection... ", end="")
        self.conn.close()
        if self.debug:
            print("Done")
    
    @threaded
    def recvdm(self):
        while True:
            while not self.wait:
                ...
            vip2p.request(self.conn, vip2p.SEND)
            self.recv = self.conn.recv(1024)
            self.wait = False
    
    def handle(self):
        if not self.recv:
            if self.debug:
                print("[DEBUG][SERNOD] Result not received")
            return
        
        cmd, data = vip2p.parse(self.recv)
        
        if cmd == vip2p.INIT:
            self.init()
        
        if cmd == vip2p.DISCONN:
            self.disconn(data)
        
        self.recv = None
    
    def disconn(self, data):
        if self.debug:
            print("[DEBUG][SERNOD] Disconnecting... ", end="")
        vip2p.request(self.conn, vip2p.OK)
        self.serv.disconn(self, data)
        if self.debug:
            print("Done")
        del self.recvdmt
    
    def init(self):
        if self.debug:
            print("[DEBUG][SERNOD] Initializing... ", end="")
        r = vip2p.request(self.conn, vip2p.OK, self.uuid.hex)
        self.serv.users[self.uuid] = self
        if self.debug:
            print("Done")
        self.wait = True
