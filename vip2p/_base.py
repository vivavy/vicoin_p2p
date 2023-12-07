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
    def request(conn:socket.socket, cmd:bytes, data:str|bytes=b""):
        conn.sendall(vip2p.NAME + b"\r\n" + vip2p.VERSION +
                     b"\r\n" + cmd + b"\r\n" +
                     (data if type(data) == bytes else data.encode()))
    
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
            while not self.send:
                ...
            self.send = True
    
    def init(self):
        if self.debug:
            print("[DEBUG][CLIENT] Initializing... ", end="")
        self.recvdmt = self.recvdm()
        self.wait_for_send()
        vip2p.request(self.conn, vip2p.INIT)
        self.send = False
        self.uuid = _uuid.UUID(bytes=vip2p.parse(self.conn.recv(1024))[1])
        if self.debug:
            print("Done with UUID = {%s}" % str(self.uuid))
    
    def disconn(self):
        if self.debug:
            print("[DEBUG][CLIENT] Disconnecting... ", end="")
        self.wait_for_send()
        vip2p.request(self.conn, vip2p.DISCONN)
        self.send = False
        if self.debug:
            print("Done with status",
              vip2p.parse(self.conn.recv(4096))[0].decode())


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
            self.disconn(self, data)
    
    def disconn(self, data):
        if self.debug:
            print("[DEBUG][SERNOD] Disconnecting... ", end="")
        vip2p.request(self.conn, vip2p.OK)
        self.serv.disconn(data)
        if self.debug:
            print("Done")
    
    def init(self):
        if self.debug:
            print("[DEBUG][SERNOD] Initializing... ", end="")
        self.recvdmt = self.recvdm()
        vip2p.request(self.conn, vip2p.OK, bytes(self.uuid))
        self.serv.users[self.uuid] = self
        if self.debug:
            print("Done")
