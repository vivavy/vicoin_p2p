import vip2p.client as vip2p


client = vip2p.Client(("localhost", 9999), debug=True)

client.init()
client.disconn()
