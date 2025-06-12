from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading # To run the server in a background thread if needed from Python itself
                 # but for this subtask, it will be run as a background process by the shell.

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode('utf-8'))
            print("\n--- Mock Server Received Data ---")
            print(json.dumps(data, indent=2))
            print("---------------------------------\n")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_message = {"status": "success", "message": "Data received successfully"}
            self.wfile.write(json.dumps(response_message).encode('utf-8'))
        except json.JSONDecodeError:
            print("\n--- Mock Server Received Invalid JSON ---")
            print(body.decode('utf-8', errors='ignore')) # Print raw body if not JSON
            print("---------------------------------------\n")
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_message = {"status": "error", "message": "Invalid JSON received"}
            self.wfile.write(json.dumps(response_message).encode('utf-8'))
        except Exception as e:
            print(f"\n--- Mock Server Error ---")
            print(f"Error processing request: {e}")
            print(f"Raw body: {body.decode('utf-8', errors='ignore')}")
            print("-------------------------\n")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_message = {"status": "error", "message": "Internal server error"}
            self.wfile.write(json.dumps(response_message).encode('utf-8'))

def run_server(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000, address='localhost'):
    server_address = (address, port)
    httpd = server_class(server_address, handler_class)
    print(f"Mock server starting on http://{address}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nMock server shutting down...")
    finally:
        httpd.server_close()
        print("Mock server stopped.")

if __name__ == '__main__':
    # To run this server standalone: python mock_server.py
    # It will be started as a background process in the main execution script for the subtask.
    run_server()
