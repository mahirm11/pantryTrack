import sqlite3
from datetime import datetime, timedelta
import json

def init_db():
    con = sqlite3.connect("pantry.db")
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS foods(
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id,
        name,
        qty,
        storage_location,
        expire_date
                )"""
                )
    con.commit()
    con.close()


def add_item(user_id: str, item_data: dict, storage_suggestions: dict):
    con = sqlite3.connect("pantry.db")
    cur = con.cursor()
    jsoned = storage_suggestions
    cur.execute("INSERT INTO foods(user_id, name, qty, storage_location) VALUES(?, ?, ?, ?)", (user_id, item_data['name'], item_data['qty'], jsoned,))
    con.commit()
    con.close()

def get_items(user_id:str):
    con = sqlite3.connect("pantry.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM foods WHERE user_id = ? ", (user_id,))
    output = res.fetchall()
    con.commit()
    con.close()
    return output

def update_item_storage(item_id: int, new_storage: str, new_expiration: int):
    con = sqlite3.connect("pantry.db")
    cur = con.cursor()
    cur.execute("UPDATE foods SET storage_location = ?, expire_date = ?  WHERE item_id = ?", (new_storage, new_expiration, item_id,))
    con.commit()
    con.close()

def get_expiration_timestamp(item_id: int, selected_storage: str) -> datetime:
    conn = sqlite3.connect("pantry.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT storage_location FROM foods WHERE item_id = ?", (item_id,))
        row = cursor.fetchone()

        if not row:
            return datetime.now() + timedelta(days=7)

        suggestions = json.loads(row[0])
        days = suggestions[selected_storage]

        cursor.execute("UPDATE foods SET storage_location = ?, expire_date = ?  WHERE item_id = ?", (item_id, selected_storage, days))

        return datetime.now() + timedelta(days = days)
    finally:
        conn.close()