import sqlite3

conn = sqlite3.connect('swt_fleet.db')
cursor = conn.cursor()
cursor.execute('SELECT driver_name, company_name, phone, email FROM drivers')
print('Drivers table contents:')
for row in cursor.fetchall():
    print(f'  {row[0]}: Company={row[1]}, Phone={row[2]}, Email={row[3]}')
conn.close()