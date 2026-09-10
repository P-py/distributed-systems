import argparse

HOST = 'localhost'
PORT = 50007

def client():
  import xmlrpc.client
  with xmlrpc.client.ServerProxy(f'http://{HOST}:{PORT}/') as proxy:
    print("call pow(2,9) %s" % str(proxy.pow(2,9)))
    print("call add(1,2) %s" % str(proxy.add(1,2)))
    print("call mul(-5,20) %s" % str(proxy.mul(-5,20)))

def server():
  from xmlrpc.server import SimpleXMLRPCServer
  with SimpleXMLRPCServer((HOST, PORT)) as server:
    server.register_introspection_functions()
    server.register_function(pow)
    @server.register_function(name='add')
    def adder_function(x, y): return x + y
    @server.register_function
    def mul(x, y):
        return x * y
    try:
      server.serve_forever()
    except KeyboardInterrupt:
      print("Exiting")

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', action='store_true')
args = parser.parse_args()
if args.server: server()
else: client()
