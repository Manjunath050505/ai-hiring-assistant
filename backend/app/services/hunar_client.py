import httpx
from app.core.config import settings

class HunarError(Exception):
    def __init__(self, status_code:int, detail:str): self.status_code=status_code; self.detail=detail; super().__init__(detail)

class HunarClient:
    def __init__(self): self.base=settings.hunar_base_url.rstrip("/")
    def _headers(self): return {"X-API-Key": settings.hunar_api_key or ""}
    async def _request(self, method, path, **kwargs):
        if settings.hunar_mock_mode: return self._mock(method, path, kwargs.get("json"))
        if not settings.hunar_api_key: raise HunarError(500,"Hunar API key is not configured")
        try:
            async with httpx.AsyncClient(timeout=25) as c:
                r=await c.request(method, self.base+path, headers=self._headers(), **kwargs)
            if r.status_code >= 400: raise HunarError(r.status_code, r.text[:1000])
            return r.json() if r.content else {}
        except httpx.HTTPError as e: raise HunarError(503, f"Hunar unavailable: {e}")
    async def create_agent(self, payload): return await self._request("POST","/agents/",json=payload)
    async def create_call(self,payload): return await self._request("POST","/calls/",json=payload)
    async def get_call(self,call_id): return await self._request("GET",f"/calls/{call_id}/")
    def _mock(self, method, path, payload):
        import uuid
        if path.startswith("/agents"): return {"id":"mock-agent-"+uuid.uuid4().hex[:8],"status":"ACTIVE"}
        if path.startswith("/calls"):
            return {"id":"mock-call-"+uuid.uuid4().hex[:8],"lifecycle_status":"SCHEDULED","status":"SCHEDULED"}
        return {}
