# Python Proxy Implementation Alternatives

## Current Issue
aiohttp is not suitable for CONNECT tunneling because it abstracts away raw socket access.

## Solution 1: Use proxy.py library (RECOMMENDED)
Similar to Node.js proxy-chain, but for Python.

```bash
pip install proxy.py
```

**Pros:**
- Battle-tested HTTP/HTTPS proxy
- Built-in CONNECT support
- Clean plugin architecture
- Production-ready

**Implementation:**
```python
from proxy import Proxy
from proxy.http.proxy import HttpProxyBasePlugin

class AluviaProxyPlugin(HttpProxyBasePlugin):
    def before_upstream_connection(self, request):
        hostname = request.host
        if should_proxy(hostname, rules):
            # Route through Aluvia gateway
            return gateway_host, gateway_port, auth
        # Route direct
        return None

proxy = Proxy(['--hostname', '127.0.0.1', '--port', '0', '--plugins', 'AluviaProxyPlugin'])
```

## Solution 2: Raw asyncio TCP proxy (Complex)
Implement from scratch using asyncio.start_server()

**Pros:**
- Full control
- No dependencies

**Cons:**
- 500+ lines of code
- Need to handle HTTP parsing, CONNECT, authentication
- Error-prone

## Solution 3: Use gateway mode (Current Workaround)
Bypass local proxy, use Aluvia gateway directly.

**Limitation:** No rules-based routing (all traffic goes through Aluvia)

```python
client = AluviaClient(api_key="...", local_proxy=False)
```

---

**Recommendation:** Implement Solution 1 (proxy.py) for production-quality HTTPS support.
