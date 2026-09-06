const BASE=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api';
export async function api<T>(path:string, options:RequestInit={}){const r=await fetch(`${BASE}${path}`,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})},cache:'no-store'});const data=await r.json().catch(()=>({}));if(!r.ok)throw new Error(data.detail||'Request failed');return data as T}
