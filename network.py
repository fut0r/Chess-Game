import sys
import asyncio
import requests
import json

# Detect if running in Wasm/Pyodide
IS_WEB = sys.platform == 'emscripten'

async def async_request(method, url, **kwargs):
    """Perform a network request safely on both Web and Desktop."""
    if IS_WEB:
        # Use pyfetch for high-performance web requests
        from pyodide.http import pyfetch
        
        # Prepare headers and body
        headers = kwargs.get('headers', {})
        body = kwargs.get('json', None)
        if body:
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json'
        
        try:
            response = await pyfetch(url, method=method, headers=headers, body=body)
            if response.status_code == 200:
                data = await response.json()
                return 200, data
            else:
                try:
                    data = await response.json()
                    return response.status_code, data
                except:
                    return response.status_code, {"detail": "Server Error"}
        except Exception as e:
            return 0, {"detail": f"Network Error: {str(e)}"}
    else:
        # Standard requests for Desktop/EXE
        try:
            loop = asyncio.get_event_loop()
            def sync_req():
                return requests.request(method, url, **kwargs)
            
            resp = await loop.run_in_executor(None, sync_req)
            try:
                return resp.status_code, resp.json()
            except:
                return resp.status_code, {"detail": "Server Error"}
        except Exception as e:
            return 0, {"detail": str(e)}
