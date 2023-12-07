import socket
import uuid as _uuid
import threading
import types


def threaded(fn) -> types.FunctionType:return


class vip2p(object):
    NAME: bytes
    VERSION: bytes
    INIT: bytes
    OK: bytes
    DISCONN: bytes

    @staticmethod
    def request(conn:socket.socket,cmd:bytes,data:str|bytes=""):return

    @staticmethod
    def parse(data:bytes)->list[bytes]:return


class SNode(object):
    '''server-side user class'''

    serv: object
    uuid: _uuid.UUID
    conn: socket.socket
    addr: tuple[str, int]
    stat: str
    wait: bool
    recvdmt: threading.Thread
    debug: bool

    def __init__(self,debug:bool=False):...

    @threaded
    def recvdm(self):...

    def handle(self):...

    def disconn(self,data:bytes):...

    def init(self):...


class CNode(object):
    '''client-side user class'''

    uuid: _uuid.UUID
    conn: socket.socket
    stat: str
    recvdmt: threading.Thread
    debug: bool

    def __init__(self,serv:tuple[str,int],debug:bool=False):...
    
    def init(self):...

    @threaded
    def recvdm(self):...

    def disconn(self):...


class Server:
    '''server class'''

    sock: socket.socket
    debug: bool
    users: dict[_uuid.UUID,SNode]

    def __init__(self,boundary:tuple[str,int],debug:bool=True):...

    def init(self):...

    def start(self):...

    def disconn(self,node:SNode,data:bytes):...
