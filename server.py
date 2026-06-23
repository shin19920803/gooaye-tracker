import http.server
import socketserver
import json
import subprocess
import os
import sys

PORT = 8000
DIRECTORY = "docs"

class LocalServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static files from the 'docs' directory
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == '/api/run-scraper':
            print("Received request to run scraper...")
            try:
                # Resolve local Python virtualenv executable path
                python_bin = os.path.join('.venv', 'bin', 'python3')
                if not os.path.exists(python_bin):
                    python_bin = 'python3'
                
                print(f"Running scraper using {python_bin}...")
                result = subprocess.run([python_bin, 'scraper.py'], capture_output=True, text=True, timeout=180)
                
                if result.returncode == 0:
                    print("Scraper completed successfully.")
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "message": "Scraper completed successfully."}).encode('utf-8'))
                else:
                    print(f"Scraper failed with exit code {result.returncode}. Stderr: {result.stderr}")
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": result.stderr or result.stdout}).encode('utf-8'))
            except Exception as e:
                print(f"Error running scraper: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                
        elif self.path == '/api/save-portfolio':
            print("Received request to save portfolio...")
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                portfolio_data = json.loads(post_data.decode('utf-8'))
                
                # Format to save to portfolio.json
                clean_portfolio = []
                for item in portfolio_data:
                    clean_portfolio.append({
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "buy_price": float(item.get("buy_price", 0.0)),
                        "shares": float(item.get("shares", 0.0)),
                        "buy_date": item.get("buy_date", "")
                    })
                
                # Write to root portfolio.json
                with open('portfolio.json', 'w', encoding='utf-8') as f:
                    json.dump(clean_portfolio, f, ensure_ascii=False, indent=4)
                
                print(f"Successfully saved {len(clean_portfolio)} stocks to portfolio.json.")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Portfolio saved successfully."}).encode('utf-8'))
            except Exception as e:
                print(f"Error saving portfolio: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run():
    # Make sure docs directory exists
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)
        
    # Standard socketserver initialization
    # Allow address reuse to avoid "Address already in use" on fast restarts
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LocalServerHandler) as httpd:
        print(f"Gooaye Tracker local server started at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            httpd.server_close()
            sys.exit(0)

if __name__ == "__main__":
    run()
