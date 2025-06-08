import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import parse_qs, urlparse
import os

def debug_print(*args, **kwargs):
    """Print debug information only if DEBUG environment variable is set to 'true' or '1'"""
    if os.getenv('DEBUG', '').lower() in ['true', '1']:
        print(*args, **kwargs)

class SearchHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
        return

    def do_POST(self):
        # Read the request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Parse the JSON request
            request_data = json.loads(post_data.decode('utf-8'))
            query = request_data.get('query')
            count = request_data.get('count', 5)
            
            if not query:
                self.send_error(400, "Missing query parameter")
                return
            
            # Get search engine from environment variable, default to google
            search_engine = os.getenv('SEARCH_ENGINE', 'google').lower()
            if search_engine not in ['google', 'brave']:
                search_engine = 'google'  # Default to google if invalid engine specified
            
            # Forward request to Mullvad Leta
            leta_url = f"https://leta.mullvad.net/search/__data.json?q={query}&engine={search_engine}"
            response = requests.get(leta_url)
            
            if response.status_code != 200:
                self.send_error(500, "Error from Mullvad Leta service")
                return
            
            # Parse the Leta response
            leta_data = response.json()
            
            # Extract search results from the complex JSON structure
            search_results = []
            if leta_data.get('type') == 'data' and len(leta_data.get('nodes', [])) > 2:
                data_node = leta_data['nodes'][2]['data']
                debug_print("Data node:", json.dumps(data_node, indent=2))
                
                if len(data_node) > 3:
                    items = data_node[3]  # Array of result indices
                    debug_print("Items array:", items)
                    
                    if isinstance(items, list):
                        for i in range(min(len(items), count)):
                            idx = items[i]
                            debug_print(f"Processing index {idx}")
                            
                            if isinstance(idx, int) and idx + 3 < len(data_node):
                                # The data structure is:
                                # data_node[idx] = structure object
                                # data_node[idx + 1] = link
                                # data_node[idx + 2] = title
                                # data_node[idx + 3] = snippet
                                result = {
                                    "link": data_node[idx + 1],
                                    "title": data_node[idx + 2],
                                    "snippet": data_node[idx + 3]
                                }
                                debug_print(f"Result before type check: {result}")
                                
                                # Only add if we have all required fields and they are strings
                                if all(isinstance(v, str) for v in result.values()):
                                    search_results.append(result)
                                    debug_print(f"Added result: {result}")
                                else:
                                    debug_print(f"Skipped result due to type mismatch: {result}")
            
            debug_print("Final search results:", json.dumps(search_results, indent=2))
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(search_results).encode('utf-8'))
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON in request")
        except Exception as e:
            self.send_error(500, f"Internal server error: {str(e)}")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SearchHandler)
    search_engine = os.getenv('SEARCH_ENGINE', 'google').lower()
    debug_mode = os.getenv('DEBUG', '').lower() in ['true', '1']
    print(f"Starting server on port {port} with search engine: {search_engine} (debug: {'enabled' if debug_mode else 'disabled'})...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 