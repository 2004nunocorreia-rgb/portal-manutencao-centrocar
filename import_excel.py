import sqlite3,openpyxl,os
BASE=os.path.dirname(__file__); SRC=os.path.join(BASE,'Plano de Manutencao.xlsm'); DB=os.path.join(BASE,'maintenance.db')
w=openpyxl.load_workbook(SRC,data_only=True,keep_vba=True)
c=sqlite3.connect(DB); c.executescript('DROP TABLE IF EXISTS maintenance;DROP TABLE IF EXISTS machines;CREATE TABLE machines(id INTEGER PRIMARY KEY,brand TEXT,model TEXT,UNIQUE(brand,model));CREATE TABLE maintenance(id INTEGER PRIMARY KEY,machine_id INTEGER,hours INTEGER,item TEXT,action TEXT,reference_oem TEXT,qty REAL,specification TEXT,reference_alt TEXT,notes TEXT,UNIQUE(machine_id,hours,item));CREATE INDEX idx_model ON machines(model);CREATE INDEX idx_item ON maintenance(item);')
def add(brand,model,hours,item,action):
 if not model or not item or hours is None:return
 model=str(model).strip().replace('\\_','-'); item=str(item).strip(); action='' if action is None else str(action).strip()
 c.execute('INSERT OR IGNORE INTO machines(brand,model) VALUES(?,?)',(brand,model)); mid=c.execute('SELECT id FROM machines WHERE brand=? AND model=?',(brand,model)).fetchone()[0]
 c.execute('INSERT OR IGNORE INTO maintenance(machine_id,hours,item,action) VALUES(?,?,?,?)',(mid,int(hours),item,action))
# Develon normalized list
for row in w['Lista '].iter_rows(min_row=2,values_only=True):
 b,m,h,i,a=(list(row)+[None]*5)[:5]
 try:h=int(float(h))
 except:continue
 if b and m and i:add(str(b).strip(),m,h,i,a)
# Bobcat sheet: blocks identified by model row followed by "horas revisão".
ws=w['Bbcat']; model_rows=[]
for r in range(1,ws.max_row+1):
 if str(ws.cell(r,1).value or '').strip().lower()=='horas revisão':
  candidates=[ws.cell(r-1,col).value for col in range(2,ws.max_column+1) if ws.cell(r-1,col).value]
  # visible named model at start of each block; first block contains S550/S630
  if r==2: models=['S550','S630']
  else: models=[str(candidates[0]).strip()] if candidates else []
  model_rows.append((r,models))
for idx,(hr,models) in enumerate(model_rows):
 end=(model_rows[idx+1][0]-1) if idx+1<len(model_rows) else ws.max_row
 hours=[ws.cell(hr,col).value for col in range(2,ws.max_column+1)]
 for mi,model in enumerate(models):
  # Standard 5-hour group. First column in each block is a legacy 1000h summary; use the 50-2000 groups.
  start=3+mi*5 if hr==2 else 3
  for col in range(start,min(start+5,ws.max_column+1)):
   h=ws.cell(hr,col).value
   if not isinstance(h,(int,float)):continue
   for rr in range(hr+1,end+1):
    item=ws.cell(rr,1).value; action=ws.cell(rr,col).value
    if item and action not in (None,''):add('Bobcat',model,h,item,action)
c.commit(); print('Machines',c.execute('select count(*) from machines').fetchone()[0]);print(c.execute('select brand,count(*) from machines group by brand').fetchall());print('Maintenance',c.execute('select count(*) from maintenance').fetchone()[0]);c.close()
