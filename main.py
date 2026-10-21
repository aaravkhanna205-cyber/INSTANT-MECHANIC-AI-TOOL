import json, os, re, sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
ROOT=Path(__file__).parent
DB=Path(os.getenv('DB_PATH',str(ROOT/'diagnosis.db')))
app=FastAPI(title='Instant Mechanic AI Diagnosis API',version='0.1.0')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','*').split(','),allow_credentials=False,allow_methods=['*'],allow_headers=['*'])
def connect():
 DB.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def setup():
 with connect() as c:
  c.execute('CREATE TABLE IF NOT EXISTS faults(id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,subcategory TEXT NOT NULL,symptoms TEXT NOT NULL,questions TEXT NOT NULL,checks TEXT NOT NULL,action TEXT NOT NULL,urgency TEXT NOT NULL,parts TEXT NOT NULL,price_min INTEGER,price_max INTEGER,labour_min INTEGER,labour_max INTEGER,repair_minutes INTEGER)')
  if c.execute('SELECT COUNT(*) FROM faults').fetchone()[0]==0:
   for row in SEED:c.execute('INSERT INTO faults(category,subcategory,symptoms,questions,checks,action,urgency,parts,price_min,price_max,labour_min,labour_max,repair_minutes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',row)
SEED=[
 ('Battery','Discharged battery','no crank dashboard dim clicking slow start battery dead','Are the dashboard lights dim?|Do you hear clicking?|Has the car been parked for days?','Check battery voltage and terminal connections; test charging system.','Turn off accessories. Request battery testing or professional jump-start assistance.','medium','Battery / terminal service',0,0,0,0,30),
 ('Starting','Starter motor fault','car not starting no crank single click starter self motor','Does the engine crank?|Is there one click when turning the key?|Are dashboard lights bright?','Test battery first, then starter relay, wiring and starter current draw.','Do not repeatedly crank. Arrange technician inspection.','medium','Starter relay / starter motor (only if confirmed)',0,0,0,0,90),
 ('Clutch','Clutch release bearing or hydraulic fault','clutch pedal pressed noise gear not engaging grinding whirring','Does the noise occur only when the clutch is pressed?|Can you select gears with engine off?|Is clutch fluid low?','Inspect clutch hydraulics, release bearing, clutch assembly and gearbox input; verify before replacement.','Stop forcing gears; request towing or workshop inspection.','high','Release bearing / clutch hydraulic components (after testing)',0,0,0,0,180),
 ('Tyres','Flat tyre or puncture','flat tyre puncture low pressure air leaking wheel','Is the tyre visibly flat?|Is there sidewall damage?|Is a spare tyre available?','Inspect tread and sidewall; locate leak; confirm repairability.','Park safely away from traffic; use roadside assistance for wheel change.','medium','Puncture repair / tyre (as needed)',0,0,0,0,45),
 ('Cooling','Engine overheating','temperature high overheating steam coolant leak radiator fan','Is the temperature warning red?|Is steam visible?|Is coolant leaking?','Allow engine to cool; pressure-test cooling system; inspect fan, coolant level and thermostat.','Pull over safely, turn engine off. Never open a hot radiator cap. Request towing if overheating.','critical','Coolant / fan / thermostat (after diagnosis)',0,0,0,0,120),
 ('Brakes','Brake system fault','brake pedal soft brake failure stopping squeal grinding abs','Is the brake pedal sinking?|Is braking reduced?|Is brake fluid leaking?','Inspect brake fluid, lines, pads, discs, hydraulic pressure and ABS codes.','Do not drive if braking performance is reduced. Arrange towing.','critical','Brake components (after inspection)',0,0,0,0,120),
 ('Electrical','Charging or alternator fault','battery warning light car stalls electrical power alternator','Does the battery light stay on while driving?|Did the car stall?|Are lights dimming?','Test alternator output, belt, wiring and battery condition.','Switch off unnecessary loads and stop safely; request assistance.','high','Alternator / belt / wiring (after testing)',0,0,0,0,90),
 ('AC','Air conditioning not cooling','ac not cooling warm air compressor blower refrigerant','Does the blower move air?|Is cooling poor only while idling?|Do you hear compressor noise?','Check cabin filter, condenser airflow, system pressures and leak evidence.','Use ventilation; book AC inspection rather than adding refrigerant blindly.','low','Filter / refrigerant / compressor (after testing)',0,0,0,0,90),
 ('Transmission','Gearbox or gear selection fault','gear stuck not shifting automatic transmission gear lock','Is the vehicle automatic?|Is the brake light working?|Does the gear lever move?','Check brake switch, selector cable, transmission fault codes and fluid leaks.','Do not force selector or drive with slipping transmission. Request assistance.','high','Selector / transmission components (after testing)',0,0,0,0,120),
 ('EV and Hybrid','EV charging failure','ev not charging charger connector charging port hybrid high voltage','Does another charger work?|Is there a charging error code?|Is the connector damaged?','Check charger compatibility, connector seating, 12V system and manufacturer error codes.','Do not touch orange high-voltage cables. Contact qualified EV service personnel.','high','Charging connector / 12V / onboard charger (after testing)',0,0,0,0,120)
]
setup()
class Vehicle(BaseModel):
 make:str='';model:str='';year:str='';fuel:str='';variant:str='';mileage_km:int|None=None
class Diagnose(BaseModel):
 vehicle:Vehicle=Field(default_factory=Vehicle);complaint:str=Field(min_length=3,max_length=2000);answers:dict[str,str]=Field(default_factory=dict)
def tokenize(s):return set(re.findall(r'[a-z0-9]+',s.lower()))-{'the','and','is','my','a','car','not','to','it','i','when','on','of'}
@app.get('/api/health')
def health():return {'status':'ok','mode':'rule-based prototype','database':'sqlite'}
@app.get('/api/categories')
def categories():
 with connect() as c:rows=c.execute('SELECT DISTINCT category,subcategory FROM faults ORDER BY category,subcategory').fetchall()
 d={}
 for r in rows:d.setdefault(r['category'],[]).append(r['subcategory'])
 return d
@app.post('/api/diagnose')
def diagnose(req:Diagnose):
 content=req.complaint+' '+' '.join(req.answers.values());words=tokenize(content)
 with connect() as c:rows=[dict(r) for r in c.execute('SELECT * FROM faults').fetchall()]
 ranked=[]
 for r in rows:
  key=tokenize(r['symptoms']);match=len(words&key);score=match/max(1,min(len(words),len(key)))
  if any(t in content.lower() for t in ['clutch','brake','overheat','puncture','battery','starter','ac ','charging','gear']):
   score+=0.12*len(words&tokenize(r['category']+' '+r['subcategory']))
  ranked.append((score,match,r))
 ranked.sort(key=lambda x:x[0],reverse=True)
 matched=[(s,r) for s,m,r in ranked if m>0][:3]
 if not matched:return {'status':'needs_more_information','message':'No reliable match in the current knowledge base. Please describe symptoms, warning lights, sounds and when the issue occurs.','follow_up_questions':['Does the engine start?','What warning lights appear?','What changed just before the problem?'],'candidates':[],'disclaimer':'Prototype information is not a confirmed mechanical diagnosis.'}
 results=[]
 for score,r in matched:
  results.append({'category':r['category'],'subcategory':r['subcategory'],'match_score':round(score,2),'urgency':r['urgency'],'follow_up_questions':r['questions'].split('|'),'mechanic_checks':r['checks'],'recommended_action':r['action'],'parts':r['parts'],'parts_estimate_inr':{'min':r['price_min'],'max':r['price_max']},'labour_estimate_inr':{'min':r['labour_min'],'max':r['labour_max']},'repair_minutes':r['repair_minutes']})
 return {'status':'possible_matches','message':'Possible causes based on keyword matching; not verified or a probability estimate.','candidates':results,'disclaimer':'Do not use this result as a substitute for an inspection. Zero cost means no verified price has been entered.'}
@app.post('/api/admin/import-json')
async def import_json(file:UploadFile=File(...)):
 if os.getenv('ADMIN_IMPORT_ENABLED','false').lower()!='true':raise HTTPException(403,'Admin imports disabled. Enable only behind authentication in a trusted environment.')
 try:data=json.loads((await file.read()).decode());assert isinstance(data,list)
 except Exception:raise HTTPException(400,'Upload a JSON array')
 keys=['category','subcategory','symptoms','questions','checks','action','urgency','parts','price_min','price_max','labour_min','labour_max','repair_minutes']
 with connect() as c:
  for row in data:
   if not all(k in row for k in keys):raise HTTPException(400,'Missing required fields')
   c.execute('INSERT INTO faults('+','.join(keys)+') VALUES('+','.join(['?']*len(keys))+')',[row[k] for k in keys])
 return {'imported':len(data)}
