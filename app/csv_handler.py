# app/csv_handler.py
import csv
import os
import shutil
from fastapi import APIRouter, HTTPException, Depends
from filelock import FileLock
from typing import List
from app.models import CSVRecord, CSVRecordUpdate
from app.auth import get_current_user

router = APIRouter()

# Define CSV file paths
CSV_FILE = "backend_table.csv"
CSV_BACKUP = "backend_table_backup.csv"
LOCK_FILE = "backend_table.csv.lock"
lock = FileLock(LOCK_FILE, timeout=10)

# Define the exact CSV headers
HEADERS = ["user", "broker", "API key", "API secret", "pnl", "margin", "max_risk"]

# Sample data (as a list of dictionaries)
SAMPLE_DATA = [
    {"user": "user_1", "broker": "BrokerA", "API key": "APIKEY_1294", "API secret": "APISECRET_83978", "pnl": "3911.21", "margin": "32134.43", "max_risk": "2.63"},
    {"user": "user_2", "broker": "BrokerB", "API key": "APIKEY_2481", "API secret": "APISECRET_48637", "pnl": "-3670.28", "margin": "39863.92", "max_risk": "9.79"},
    {"user": "user_3", "broker": "BrokerB", "API key": "APIKEY_7580", "API secret": "APISECRET_92061", "pnl": "-1349.18", "margin": "37607.74", "max_risk": "0.36"},
    {"user": "user_4", "broker": "BrokerC", "API key": "APIKEY_1819", "API secret": "APISECRET_66637", "pnl": "1114.96", "margin": "42650.44", "max_risk": "2.59"},
    {"user": "user_5", "broker": "BrokerA", "API key": "APIKEY_9241", "API secret": "APISECRET_77485", "pnl": "1779.82", "margin": "36279.78", "max_risk": "4.47"},
    {"user": "user_6", "broker": "BrokerB", "API key": "APIKEY_3843", "API secret": "APISECRET_67949", "pnl": "677.96", "margin": "2226.61", "max_risk": "6.31"},
    {"user": "user_7", "broker": "BrokerA", "API key": "APIKEY_4889", "API secret": "APISECRET_50033", "pnl": "-3227.61", "margin": "43271.03", "max_risk": "9.89"},
    {"user": "user_8", "broker": "BrokerB", "API key": "APIKEY_2998", "API secret": "APISECRET_64865", "pnl": "513.78", "margin": "5138.49", "max_risk": "0.98"},
    {"user": "user_9", "broker": "BrokerB", "API key": "APIKEY_5588", "API secret": "APISECRET_29626", "pnl": "-2203.73", "margin": "12033.94", "max_risk": "6.42"},
    {"user": "user_10", "broker": "BrokerC", "API key": "APIKEY_8492", "API secret": "APISECRET_68319", "pnl": "212.89", "margin": "40958.06", "max_risk": "5.69"},
    {"user": "user_11", "broker": "BrokerB", "API key": "APIKEY_9496", "API secret": "APISECRET_51317", "pnl": "1567.69", "margin": "6536.02", "max_risk": "8.64"},
    {"user": "user_12", "broker": "BrokerA", "API key": "APIKEY_6808", "API secret": "APISECRET_74291", "pnl": "-4358.3", "margin": "24420.21", "max_risk": "5.7"},
]

def init_csv():
    """Initialize the CSV file with headers and sample data if it does not exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
            writer.writeheader()
            for row in SAMPLE_DATA:
                writer.writerow(row)

# Call init_csv() at module load time (or you can call it in startup)
init_csv()

def read_csv() -> List[dict]:
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def write_csv(records: List[dict]):
    # Backup the existing file if it exists
    if os.path.exists(CSV_FILE):
        shutil.copy(CSV_FILE, CSV_BACKUP)
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(records)

@router.get("/csv", dependencies=[Depends(get_current_user)])
def get_csv():
    try:
        with lock:
            records = read_csv()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/csv", dependencies=[Depends(get_current_user)])
def create_csv_record(record: CSVRecord):
    try:
        with lock:
            records = read_csv()
            # Check if record with the same "user" already exists
            for rec in records:
                if rec["user"] == record.user:
                    raise HTTPException(status_code=400, detail="Record with this user already exists")
            # Convert record to dictionary with keys matching CSV headers (using alias)
            record_dict = record.dict(by_alias=True)
            records.append(record_dict)
            write_csv(records)
        return {"message": "Record added", "record": record_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/csv", dependencies=[Depends(get_current_user)])
def update_csv_record(record: CSVRecordUpdate):
    try:
        with lock:
            records = read_csv()
            updated = False
            for rec in records:
                if rec["user"] == record.user:
                    if record.broker is not None:
                        rec["broker"] = record.broker
                    if record.api_key is not None:
                        rec["API key"] = record.api_key
                    if record.api_secret is not None:
                        rec["API secret"] = record.api_secret
                    if record.pnl is not None:
                        rec["pnl"] = record.pnl
                    if record.margin is not None:
                        rec["margin"] = record.margin
                    if record.max_risk is not None:
                        rec["max_risk"] = record.max_risk
                    updated = True
                    break
            if not updated:
                raise HTTPException(status_code=404, detail="Record not found")
            write_csv(records)
        return {"message": "Record updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/csv", dependencies=[Depends(get_current_user)])
def delete_csv_record(user: str):
    try:
        with lock:
            records = read_csv()
            new_records = [rec for rec in records if rec["user"] != user]
            if len(new_records) == len(records):
                raise HTTPException(status_code=404, detail="Record not found")
            write_csv(new_records)
        return {"message": "Record deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/csv/restore", dependencies=[Depends(get_current_user)])
def restore_csv():
    try:
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        backup_path = os.path.join(base_dir, "..", CSV_BACKUP)
        csv_path = os.path.join(base_dir, "..", CSV_FILE)
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="No backup found")
        shutil.copy(backup_path, csv_path)
        return {"message": "CSV restored from backup"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
