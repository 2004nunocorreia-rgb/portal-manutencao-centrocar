@echo off
cd /d "%~dp0"
echo PORTAL V9 - 6 MARCAS
python -c "import sqlite3; c=sqlite3.connect('maintenance.db'); bs=['Develon','Bobcat','Haulotte','McCloskey','Comacchio','EvoQuip']; [print(b+':',c.execute('select count(*) from machines where lower(brand)=lower(?)',(b,)).fetchone()[0]) for b in bs]; print('TOTAL:',c.execute('select count(*) from machines').fetchone()[0]); print('PLANOS:',c.execute('select count(*) from maintenance').fetchone()[0])"
pause
