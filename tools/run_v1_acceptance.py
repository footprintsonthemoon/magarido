#!/usr/bin/env python3
import csv,json,math,os,threading,time,urllib.parse,urllib.request,webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
URL=os.environ.get('BROUTER_URL','http://127.0.0.1:17777/brouter'); OUT=Path('output/v1-acceptance'); ROUTES=OUT/'routes'
PROFILES=[('moto-fast','Fast'),('moto-curvy','Curvy'),('moto-very-curvy','Very Curvy')]
CASES=[
('biel-neuchatel','Biel/Bienne -> Neuchatel','mixed/topographical',(7.2468,47.1368),(6.9293,46.9896),'Geography may limit differentiation.'),
('bern-luzern','Bern -> Luzern','high-choice',(7.4474,46.9480),(8.3093,47.0502),'Strong character separation expected; key Very Curvy case.'),
('thun-andermatt','Thun -> Andermatt','mixed/alpine',(7.6292,46.7571),(8.5948,46.6356),'Differences where choice exists; alpine convergence is valid.'),
('interlaken-brienz','Interlaken -> Brienz','high-choice/local',(7.8632,46.6863),(8.0385,46.7541),'Fast corridor vs attractive northern-shore Curvy corridor.'),
('brienz-andermatt','Brienz -> Andermatt','constrained/alpine',(8.0385,46.7541),(8.5948,46.6356),'Profile convergence is acceptable.'),
('zurich-davos','Zurich -> Davos','long-distance/alpine',(8.5417,47.3769),(9.8398,46.8027),'Plausible long-distance Fast/Curvy differentiation.'),
('aigle-martigny','Aigle -> Martigny','motorway-vs-secondary',(6.9706,46.3185),(7.0732,46.1020),'Efficient corridor vs motorcycle-oriented alternatives.'),
('fribourg-altdorf','Fribourg -> Altdorf','long-distance/mixed',(7.1513,46.8065),(8.6444,46.8804),'Overall character must remain plausible; no local tuning.')]
def fetch(c,p):
 q=urllib.parse.urlencode({'lonlats':f'{c[3][0]},{c[3][1]}|{c[4][0]},{c[4][1]}','profile':p,'alternativeidx':0,'format':'geojson'})
 with urllib.request.urlopen(URL+'?'+q,timeout=180) as r:return json.loads(r.read())
def line(d):
 for f in d['features']:
  if (f.get('geometry') or {}).get('type')=='LineString':return f
 raise RuntimeError('No LineString')
def coords(d):return [[float(x[0]),float(x[1])] for x in line(d)['geometry']['coordinates']]
def hav(a,b):
 x1,y1=map(math.radians,a[:2]);x2,y2=map(math.radians,b[:2]);h=math.sin((y2-y1)/2)**2+math.cos(y1)*math.cos(y2)*math.sin((x2-x1)/2)**2
 return 12742000*math.asin(math.sqrt(h))
def dist(d):
 c=coords(d);return sum(hav(a,b) for a,b in zip(c,c[1:]))/1000
def prop(d,*names):
 p={str(k).lower():v for k,v in (line(d).get('properties') or {}).items()}
 for n in names:
  try:return float(p[n.lower()])
  except (KeyError,TypeError,ValueError):pass
def same(a,b,tol=8):
 A,B=coords(a),coords(b)
 return len(A)==len(B) and max((hav(x,y) for x,y in zip(A,B)),default=999)<=tol
def make_map(R):
 data=[{'case':r['case'][0],'name':r['case'][1],'group':r['case'][2],'expect':r['case'][5],'profile':r['profile'],'label':r['label'],'km':r['km'],'coords':[[lat,lon] for lon,lat in coords(r['data'])]} for r in R]
 html="""<!doctype html><meta charset='utf-8'><title>v1 acceptance</title><link rel='stylesheet' href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'><style>html,body,#map{height:100%;margin:0}.p{position:absolute;z-index:999;top:10px;left:50px;background:#fff;padding:10px;max-width:430px;font:13px system-ui}</style><div class=p><b>v1 acceptance</b><br><select id=s></select><div id=i></div></div><div id=map></div><script src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'></script><script>const D=__DATA__,C={'moto-fast':'#1565c0','moto-curvy':'#ef6c00','moto-very-curvy':'#7b1fa2'};const m=L.map('map');L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(m);let ls=[],ctl;const s=document.getElementById('s'),inf=document.getElementById('i'),cs=[...new Map(D.map(x=>[x.case,[x.case,x.name]])).values()];cs.forEach(x=>{let o=document.createElement('option');o.value=x[0];o.text=x[1];s.add(o)});function show(id){ls.forEach(x=>m.removeLayer(x));ls=[];if(ctl)m.removeControl(ctl);let ov={},b=[],rr=D.filter(x=>x.case==id);rr.forEach(r=>{let l=L.polyline(r.coords,{color:C[r.profile],weight:5,opacity:.78}).addTo(m);l.bindPopup('<b>'+r.label+'</b><br>'+r.km.toFixed(1)+' km');ls.push(l);ov[r.label]=l;b=b.concat(r.coords)});ctl=L.control.layers(null,ov,{collapsed:false}).addTo(m);m.fitBounds(b,{padding:[25,25]});inf.innerHTML='<small>'+rr[0].group+'<br>'+rr[0].expect+'<br>Toggle profiles independently.</small>'}s.onchange=()=>show(s.value);show(cs[0][0]);</script>""".replace('__DATA__',json.dumps(data))
 p=OUT/'v1-acceptance-map.html';p.write_text(html);return p
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
def main():
 print('BRouter motorcycle v1 acceptance\n================================');print('Release characters: Fast / Curvy / Very Curvy');print('No tuning, scoring or route-specific shaping.\n');ROUTES.mkdir(parents=True,exist_ok=True);R=[];fail=[]
 for c in CASES:
  print(f'{c[1]} [{c[2]}]')
  for p,l in PROFILES:
   print(f'  {l}...',end='',flush=True)
   try:
    d=fetch(c,p);km=dist(d);t=prop(d,'total-time','time');a=prop(d,'filtered ascend','ascend','ascent');cost=prop(d,'cost','track-cost');(ROUTES/f'{c[0]}--{p}.geojson').write_text(json.dumps(d));R.append({'case':c,'profile':p,'label':l,'data':d,'km':km,'time':t,'ascent':a,'cost':cost});print(f' {km:.1f} km')
   except Exception as e:fail.append((c[1],p,str(e)));print(' ERROR:',e)
  print()
 with (OUT/'summary.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['case','group','profile','distance_km','time','ascent_m','cost'])
  for r in R:w.writerow([r['case'][1],r['case'][2],r['profile'],f"{r['km']:.3f}",r['time'],r['ascent'],r['cost']])
 print('Acceptance summary\n==================');print(f"{'Case':25} {'Fast':>8} {'Curvy':>8} {'Very':>8}  Geometry");print('-'*72)
 for c in CASES:
  x={r['profile']:r for r in R if r['case'][0]==c[0]}
  if len(x)<3:print(f"{c[1][:25]:25} ERROR");continue
  f,cu,v=x['moto-fast'],x['moto-curvy'],x['moto-very-curvy'];fc,cv=same(f['data'],cu['data']),same(cu['data'],v['data']);g='all same' if fc and cv else 'Fast=Curvy; Very differs' if fc else 'Curvy=Very; Fast differs' if cv else 'three route families';print(f"{c[1][:25]:25} {f['km']:8.1f} {cu['km']:8.1f} {v['km']:8.1f}  {g}")
 print(f'\nSuccessful routes: {len(R)}/{len(CASES)*3}')
 if fail:
  print('Failures:');[print('  '+' / '.join(x)) for x in fail]
 if R:
  p=make_map(R);srv=ThreadingHTTPServer(('127.0.0.1',0),partial(Q,directory=str(OUT.resolve())));threading.Thread(target=srv.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{srv.server_address[1]}/{p.name}';webbrowser.open(url);print(f'Results: {OUT}\nInteractive map: {url}');print('\nReview rule: geometry over distance; separation on high-choice routes; convergence is valid on constrained routes; no named-route tuning.');print('Press Ctrl-C to close.')
  try:
   while True:time.sleep(1)
  except KeyboardInterrupt:srv.shutdown();print('\nViewer stopped.')
if __name__=='__main__':main()
