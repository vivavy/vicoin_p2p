import vip2p.server as vip2p


server = vip2p.Server(("localhost", 9999), debug=True)

server.init()
server.start()
