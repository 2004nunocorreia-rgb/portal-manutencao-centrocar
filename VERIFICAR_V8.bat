@echo off
cd /d "%~dp0"
echo PORTAL V8 - 5 MARCAS
python -c "import sqlite3; c=sqlite3.connect('maintenance.db'); brands=['Develon','Bobcat','Haulotte','McCloskey','Comacchio']; [print(b+':',c.execute('select count(*) from machines where lower(brand)=lower(?)',(b,)).fetchone()[0]) for b in brands]; print('TOTAL:',c.execute('select count(*) from machines').fetchone()[0]); print('PLANOS:',c.execute('select count(*) from maintenance').fetchone()[0])"
pause
