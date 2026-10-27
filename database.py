import sqlite3


class YandexDB:
    def __init__(self, db_name="yandex_leads.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # UNIQUE(keyword, title, address): 같은 키워드 안에서만 중복 방지
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
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
        self.conn.commit()

    def insert_lead(self, keyword, title, address, phone, website, rating):
        """같은 키워드+상호명+주소가 이미 있으면 갱신(UPSERT), 없으면 삽입"""
        try:
            self.cursor.execute("""
                INSERT INTO leads (keyword, title, address, phone, website, rating)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(keyword, title, address) DO UPDATE SET
                    phone=excluded.phone,
                    website=excluded.website,
                    rating=excluded.rating
            """, (keyword, title, address, phone, website, rating))
            self.conn.commit()
        except Exception as e:
            print(f"[-] DB 저장 실패: {e}")

    def fetch_by_keyword(self, keyword):
        self.cursor.execute(
            "SELECT title, address, phone, website, rating FROM leads WHERE keyword=?",
            (keyword,)
        )
        return self.cursor.fetchall()

    def fetch_all_keywords(self):
        self.cursor.execute("SELECT DISTINCT keyword FROM leads")
        return [row[0] for row in self.cursor.fetchall()]

    def delete_by_keyword(self, keyword):
        """특정 키워드의 데이터만 삭제 (다른 키워드는 보존)"""
        try:
            self.cursor.execute("DELETE FROM leads WHERE keyword=?", (keyword,))
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            print(f"[-] 키워드 삭제 실패: {e}")
            return 0

    def count_by_keyword(self, keyword):
        self.cursor.execute("SELECT COUNT(*) FROM leads WHERE keyword=?", (keyword,))
        return self.cursor.fetchone()[0]