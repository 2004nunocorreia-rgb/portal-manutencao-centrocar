@echo off
cd /d "%~dp0"
echo PORTAL V6 FINAL
python -c "import sqlite3; c=sqlite3.connect('maintenance.db'); print('TOTAL MODELOS:',c.execute('select count(*) from machines').fetchone()[0]); print('BOBCAT:',c.execute(\"select count(*) from machines where brand='Bobcat'\").fetchone()[0]); print('DEVELON:',c.execute(\"select count(*) from machines where brand='Develon'\").fetchone()[0]); print('PLANOS:',c.execute('select count(*) from maintenance').fetchone()[0])"
pause
