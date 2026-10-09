import json, os, urllib.request, urllib.error, threading, time
BASE=os.environ.get("BASE","http://api:8000"); DAY="2026-10-10"
ORIGIN="http://booking.localhost:8088"
def call(m,p,b=None,cookie=None,csrf=None):
    h={"Content-Type":"application/json","Origin":ORIGIN}
    if cookie:h["Cookie"]=cookie
    if csrf:h["X-CSRF-Token"]=csrf
    d=json.dumps(b).encode() if b is not None else None
    r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    try:
        x=urllib.request.urlopen(r,timeout=30); return x.status,x.headers,x.read().decode()
    except urllib.error.HTTPError as e: return e.code,e.headers,e.read().decode()
def login(mob):
    s,_,b=call("POST","/api/v1/auth/otp/request",{"mobile":mob})
    if s!=200: raise RuntimeError(f"otp req {s} {b[:80]}")
    code=json.loads(b)["dev_code"]
    s,h,b=call("POST","/api/v1/auth/otp/verify",{"mobile":mob,"code":code})
    if s!=200: raise RuntimeError(f"verify {s} {b[:80]}")
    return h.get_all("Set-Cookie")[0].split(";")[0], json.loads(b)["csrf_token"]

def rush(label, session_time, singles, doubles, mobiles):
    creds=[login(m) for m in mobiles]
    n=len(creds); results=[None]*n; lats=[0.0]*n; barrier=threading.Barrier(n)
    def worker(i,cookie,csrf):
        barrier.wait()
        t0=time.monotonic()
        s,_,_=call("POST","/api/v1/reservations",{"date":DAY,"time":session_time,"single_count":singles,"double_count":doubles,"contact_name":"L"},cookie=cookie,csrf=csrf)
        lats[i]=time.monotonic()-t0; results[i]=s
    ths=[threading.Thread(target=worker,args=(i,c[0],c[1])) for i,c in enumerate(creds)]
    for t in ths:t.start()
    for t in ths:t.join()
    ok=results.count(201); full=results.count(409); other=[r for r in results if r not in(201,409)]
    sl=sorted(lats); pct=lambda q: sl[min(len(sl)-1,int(len(sl)*q))]*1000
    print(f"[{label}] {n} users rush {session_time} (req s={singles} d={doubles})")
    print(f"   201={ok}  409_full={full}  other={len(other)} {sorted(set(other)) if other else ''}")
    print(f"   lat p50={pct(.5):.0f}ms p95={pct(.95):.0f}ms p99={pct(.99):.0f}ms max={max(lats)*1000:.0f}ms")
    return ok
a=rush("SINGLES","15:00",1,0,[f"09121{i:06d}" for i in range(50)])
b=rush("DOUBLE","15:15",0,1,[f"09122{i:06d}" for i in range(30)])
print(f"\nRESULT singles_created={a} (cap 6)   double_created={b} (cap 1)")
