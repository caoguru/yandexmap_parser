import sqlite3
conn = sqlite3.connect("yandex_leads.db")
cur = conn.cursor()
cur.execute("ALTER TABLE leads RENAME TO leads_old")
cur.execute("""
    CREATE TABLE leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        title TEXT,
        address TEXT,
        phone TEXT,
        website TEXT,
        rating TEXT,
        UNIQUE(keyword, title, address)
    )
""")
cur.execute("""
    INSERT OR IGNORE INTO leads (keyword, title, address, phone, website, rating)
    SELECT keyword, title, address, phone, website, rating FROM leads_old
""")
cur.execute("DROP TABLE leads_old")
conn.commit()
conn.close()
print("마이그레이션 완료")