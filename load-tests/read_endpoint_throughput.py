import json,os,time,threading,urllib.request,urllib.error
BASE=os.environ["BASE"]; DUR=float(os.environ.get("DUR","30")); N=int(os.environ.get("VU","64"))
EPS=json.loads(os.environ.get("EPS",'["/api/v1/reservations/info","/api/v1/reservations/calendar","/api/v1/reservations/availability?date=2026-10-10"]'))
HOST=os.environ.get("HOSTHDR","")
lat={e:[] for e in EPS}; status={}; lock=threading.Lock(); stop=time.monotonic()+DUR
def hit(e):
    h={}
    if HOST:h["Host"]=HOST
    r=urllib.request.Request(BASE+e,headers=h)
    t0=time.monotonic()
    try:
        x=urllib.request.urlopen(r,timeout=30); c=x.status; x.read()
    except urllib.error.HTTPError as ex: c=ex.code
    except Exception: c="ERR"
    dt=time.monotonic()-t0
    with lock:
        lat[e].append(dt); status[c]=status.get(c,0)+1
def worker():
    i=0
    while time.monotonic()<stop:
        hit(EPS[i%len(EPS)]); i+=1
ths=[threading.Thread(target=worker) for _ in range(N)]
t0=time.monotonic()
for t in ths:t.start()
for t in ths:t.join()
elapsed=time.monotonic()-t0
total=sum(len(v) for v in lat.values())
print(f"BASE={BASE} VU={N} dur={elapsed:.1f}s  total_req={total}  RPS={total/elapsed:.0f}")
print("status:", dict(sorted(status.items(), key=lambda x:str(x[0]))))
for e,v in lat.items():
    if not v: continue
    s=sorted(v); pct=lambda q:s[min(len(s)-1,int(len(s)*q))]*1000
    print(f"  {e[:46]:46} n={len(v):5} p50={pct(.5):6.1f} p95={pct(.95):7.1f} p99={pct(.99):7.1f} max={max(v)*1000:7.1f} ms")
