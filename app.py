from flask import Flask,render_template,request,g,redirect,url_for,flash,Response
import sqlite3,os,csv,io
from functools import wraps
from flask import session
app=Flask(__name__);app.secret_key=os.environ.get('PORTAL_SECRET','centrocar-nuno-local');ADMIN_PASSWORD=os.environ.get('PORTAL_ADMIN_PASSWORD','centrocar');DB=os.path.join(os.path.dirname(__file__),'maintenance.db')
def db():
 if 'db' not in g:g.db=sqlite3.connect(DB);g.db.row_factory=sqlite3.Row
 return g.db
@app.teardown_appcontext
def close(e=None):
 d=g.pop('db',None)
 if d:d.close()
def stats():
 return db().execute('SELECT COUNT(*) machines,(SELECT COUNT(*) FROM maintenance) rows FROM machines').fetchone()
@app.route('/')
def home():
 brands=['Develon','Bobcat','Haulotte','McCloskey','Comacchio','EvoQuip']
 cards=[]
 for b in brands:
  n=db().execute('SELECT COUNT(*) n FROM machines WHERE lower(brand)=lower(?)',(b,)).fetchone()['n']
  fam=db().execute('SELECT COUNT(DISTINCT family) n FROM machines WHERE lower(brand)=lower(?)',(b,)).fetchone()['n']
  cards.append({'brand':b,'n':n,'families':fam})
 return render_template('home_brands.html',cards=cards,s=stats())

@app.route('/brand/<brand>')
def brand_page(brand):
 allowed=['Develon','Bobcat','Haulotte','McCloskey','Comacchio','EvoQuip']
 canonical=next((b for b in allowed if b.lower()==brand.lower()),None)
 if not canonical:return 'Marca não encontrada',404
 q=request.args.get('q','').strip();family=request.args.get('family','').strip();p='%'+q+'%'
 sql='SELECT * FROM machines WHERE lower(brand)=lower(?) AND model LIKE ?';a=[canonical,p]
 if family:sql+=' AND family=?';a.append(family)
 machines=db().execute(sql+' ORDER BY model',a).fetchall()
 families=db().execute('SELECT family,COUNT(*) n FROM machines WHERE lower(brand)=lower(?) GROUP BY family ORDER BY family',(canonical,)).fetchall()
 plans=set(r['machine_id'] for r in db().execute('SELECT DISTINCT machine_id FROM maintenance').fetchall())
 return render_template('brand.html',brand=canonical,machines=machines,families=families,q=q,family=family,plans=plans)

@app.route('/machine/<int:mid>')
def machine(mid):
 m=db().execute('SELECT * FROM machines WHERE id=?',(mid,)).fetchone()
 if not m:return 'Máquina não encontrada',404
 hs=[x['hours'] for x in db().execute('SELECT DISTINCT hours FROM maintenance WHERE machine_id=? ORDER BY hours',(mid,))];h=request.args.get('hours',type=int) or (hs[0] if hs else None);items=db().execute('SELECT * FROM maintenance WHERE machine_id=? AND hours=? ORDER BY item',(mid,h)).fetchall()
 return render_template('machine.html',m=m,hs=hs,h=h,items=items)
@app.route('/search')
def search():
 q=request.args.get('q','').strip();rows=[]
 if q:
  p='%'+q+'%';rows=db().execute("SELECT m.id mid,m.brand,m.model,x.* FROM maintenance x JOIN machines m ON m.id=x.machine_id WHERE m.model LIKE ? OR x.item LIKE ? OR COALESCE(x.reference_oem,'') LIKE ? OR COALESCE(x.reference_alt,'') LIKE ? ORDER BY m.model,x.hours LIMIT 500",(p,p,p,p)).fetchall()
 return render_template('search.html',q=q,rows=rows)

def login_required(f):
 @wraps(f)
 def wrapped(*a,**k):
  if not session.get('admin'):return redirect(url_for('login',next=request.path))
  return f(*a,**k)
 return wrapped
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  if request.form.get('password','')==ADMIN_PASSWORD:
   session['admin']=True;return redirect(request.args.get('next') or url_for('admin'))
  flash('Palavra-passe incorreta.')
 return render_template('login.html')
@app.route('/logout')
def logout():
 session.clear();return redirect(url_for('home'))

@app.route('/admin',methods=['GET','POST'])
@login_required
def admin():
 if request.method=='POST':
  mode=request.form.get('mode','edit')
  if mode=='edit':
   rid=request.form.get('id',type=int);v=[request.form.get(x,'').strip() or None for x in ['reference_oem','qty','specification','reference_alt','notes']]
   try:v[1]=float(v[1].replace(',','.')) if v[1] else None
   except:v[1]=None
   db().execute('UPDATE maintenance SET reference_oem=?,qty=?,specification=?,reference_alt=?,notes=? WHERE id=?',(*v,rid));flash('Dados técnicos guardados.')
  elif mode=='machine':
   b=request.form.get('brand','').strip();m=request.form.get('model','').strip()
   if b and m:db().execute('INSERT OR IGNORE INTO machines(brand,model) VALUES(?,?)',(b,m));flash('Máquina adicionada.')
  elif mode=='item':
   mid=request.form.get('machine_id',type=int);h=request.form.get('hours',type=int);item=request.form.get('item','').strip();action=request.form.get('action','').strip()
   if mid and h and item:db().execute('INSERT OR IGNORE INTO maintenance(machine_id,hours,item,action) VALUES(?,?,?,?)',(mid,h,item,action));flash('Item/revisão adicionado.')
  db().commit();return redirect(url_for('admin',q=request.args.get('q','')))
 q=request.args.get('q','').strip();rows=[]
 if q:
  p='%'+q+'%';rows=db().execute('SELECT m.brand,m.model,x.* FROM maintenance x JOIN machines m ON m.id=x.machine_id WHERE m.model LIKE ? OR x.item LIKE ? ORDER BY m.model,x.hours LIMIT 250',(p,p)).fetchall()
 machines=db().execute('SELECT * FROM machines ORDER BY brand,model').fetchall();return render_template('admin.html',q=q,rows=rows,machines=machines)
@app.route('/delete_item/<int:rid>',methods=['POST'])
@login_required
def delete_item(rid):
 db().execute('DELETE FROM maintenance WHERE id=?',(rid,));db().commit();flash('Registo eliminado.');return redirect(url_for('admin',q=request.args.get('q','')))

@app.route('/export/<int:mid>/<int:h>')
def export(mid,h):
 m=db().execute('SELECT * FROM machines WHERE id=?',(mid,)).fetchone();rows=db().execute('SELECT * FROM maintenance WHERE machine_id=? AND hours=? ORDER BY item',(mid,h)).fetchall();o=io.StringIO();w=csv.writer(o,delimiter=';');w.writerow(['Marca','Modelo','Revisão (h)','Material','Ação','Referência OEM','Qtd.','Especificação','Alternativa','Observações'])
 for x in rows:w.writerow([m['brand'],m['model'],h,x['item'],x['action'],x['reference_oem'] or '',x['qty'] or '',x['specification'] or '',x['reference_alt'] or '',x['notes'] or ''])
 data='\ufeff'+o.getvalue();return Response(data,mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename={m["model"].replace("/","-")}_{h}h.csv'})
if __name__=='__main__':app.run(debug=True,host='127.0.0.1',port=5000)
