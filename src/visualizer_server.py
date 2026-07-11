import os
import json
import glob
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class VisualizerHTTPHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for API requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == '/api/events':
            self.handle_api_events(parsed_url)
        elif path in ('', '/', '/index.html'):
            self.serve_index_html()
        else:
            # Fallback to default handler for static files if needed
            super().do_GET()

    def serve_index_html(self):
        src_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(src_dir, 'index.html')
        
        if not os.path.exists(index_path):
            self.send_error(404, "index.html not found")
            return

        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error reading index.html: {e}")

    def handle_api_events(self, parsed_url):
        query = parse_qs(parsed_url.query)
        since = 0.0
        try:
            if 'since' in query:
                since = float(query['since'][0])
        except (ValueError, IndexError):
            pass

        src_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(src_dir)
        
        patterns = [
            os.path.join(src_dir, 'Locals', 'Rank *', 'visual_events.jsonl'),
            os.path.join(root_dir, 'output', 'Rank *', 'visual_events.jsonl'),
            os.path.join(root_dir, 'test-output', 'Rank *', 'visual_events.jsonl')
        ]

        event_files = []
        for pattern in patterns:
            event_files.extend(glob.glob(pattern))

        all_events = []
        for file_path in event_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            evt = json.loads(line)
                            # Only include events after the specified timestamp
                            if evt.get('time', 0.0) > since:
                                all_events.append(evt)
                        except json.JSONDecodeError:
                            # Skip incomplete lines written during concurrent execution
                            continue
            except Exception:
                continue

        # Sort all events chronologically by timestamp
        all_events.sort(key=lambda x: x.get('time', 0.0))

        # Respond with JSON
        try:
            response_data = json.dumps({"events": all_events})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response_data.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error building response: {e}")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, VisualizerHTTPHandler)
    print(f"[Visualizer Server] Running on http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Visualizer Server] Stopping...")
        httpd.server_close()

if __name__ == '__main__':
    import sys
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
