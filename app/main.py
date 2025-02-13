# app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app import auth, background, csv_handler, database
from app.database import get_db, init_db
from app.auth import verify_token

app = FastAPI()

# Enable CORS to allow requests from your frontend
origins = [
    "http://localhost:3000",  # Adjust if necessary,
    "https://backrose-task-snowy.vercel.app"
    "https://blackrose-task.vercel.app",    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for auth and CSV operations
app.include_router(auth.router)
app.include_router(csv_handler.router)

@app.on_event("startup")
async def startup_event():
    init_db()
    # CSV file is initialized automatically in csv_handler.py (via init_csv)
    # Start the background random number generator
    asyncio.create_task(background.random_number_generator())

# REST endpoint for retrieving random numbers (protected)
@app.get("/numbers", dependencies=[Depends(auth.get_current_user)])
def get_numbers():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM numbers ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        numbers = [
            {"id": row["id"], "timestamp": row["timestamp"], "value": row["value"]}
            for row in rows
        ]
        return numbers
    except Exception as e:
        raise Exception("Error fetching numbers: " + str(e))

# WebSocket endpoint for real-time random number streaming
@app.websocket("/ws/numbers")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        username = verify_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    last_sent_id = 0
    try:
        while True:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM numbers WHERE id > ? ORDER BY id ASC", (last_sent_id,))
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                data = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "value": row["value"]
                }
                await websocket.send_json(data)
                last_sent_id = row["id"]
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {username}")
    except Exception as e:
        print("WebSocket error:", e)
