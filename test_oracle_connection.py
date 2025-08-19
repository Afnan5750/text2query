import cx_Oracle

DB_CONFIG = {
    'host': 'localhost',
    'port': 1521,
    'sid': 'orcl',        
    'user': 'AFNAN',      
    'password': 'AFNAN'   
}

def get_dsn():
    return cx_Oracle.makedsn(
        DB_CONFIG['host'],
        DB_CONFIG['port'],
        sid=DB_CONFIG['sid']  
    )

try:
    dsn = get_dsn()
    print("DSN:", dsn)

    conn = cx_Oracle.connect(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        dsn=dsn
    )

    print("✅ Connection successful!")
    print("Database version:", conn.version)

    conn.close()

except Exception as e:
    print("❌ Connection failed:", e)
