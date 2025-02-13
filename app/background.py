# app/background.py
import asyncio
import random
from datetime import datetime
from app.database import get_db

async def random_number_generator():
    while True:
        await asyncio.sleep(1)  # Generate a random number every second
        number = random.random()
        timestamp = datetime.utcnow().isoformat()
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO numbers (timestamp, value) VALUES (?, ?)", (timestamp, number))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error inserting random number:", e)
