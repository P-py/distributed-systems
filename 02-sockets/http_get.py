from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = 'localhost'
PORT = 50007

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

httpd = HTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
print(f'Servindo em http://{HOST}:{PORT}/ (Ctrl-C para encerrar)')
httpd.serve_forever()
