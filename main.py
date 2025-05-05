
from fastapi import FastAPI, HTTPException, Query
import ibm_db
from typing import List

app = FastAPI()

# IBM Cloud DB2 connection string
DB2_CONNECTION_STRING = (
    "DATABASE=bludb;"
    "HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;"
    "PORT=31321;"
    "PROTOCOL=TCPIP;"
    "UID=zcf94894;"
    "PWD=NAaw00LZ6oJJ5Uio;"
    "SECURITY=SSL;"
 )

# Expected columns in 'users' table
EMAIL_COLUMN = "emailid"
POLICY_COLUMN = "policies"

def get_db_connection():
    try:
        conn = ibm_db.connect(DB2_CONNECTION_STRING, "", "")
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB2 Connection Failed: {e}")

def validate_columns(conn):
    discover_sql = """
    SELECT COLNAME
    FROM SYSCAT.COLUMNS
    WHERE TABNAME = 'USERS'
    """
    stmt = ibm_db.exec_immediate(conn, discover_sql)

    available_columns = []
    row = ibm_db.fetch_assoc(stmt)
    while row:
        available_columns.append(row["COLNAME"].strip())
        row = ibm_db.fetch_assoc(stmt)

    if EMAIL_COLUMN.upper() not in available_columns:
        raise HTTPException(status_code=500, detail=f"Missing expected column: {EMAIL_COLUMN}")

    if POLICY_COLUMN.upper() not in available_columns:
        raise HTTPException(status_code=500, detail=f"Missing expected column: {POLICY_COLUMN}")

@app.get("/get-policies", response_model=List[str])
async def get_policies(email: str = Query(..., description="User's email ID")):
    conn = None
    try:
        conn = get_db_connection()
        validate_columns(conn)

        # Build query dynamically with correct column names
        query_sql = f"""
        SELECT {POLICY_COLUMN}
        FROM users
        WHERE {EMAIL_COLUMN} = ?
        """

        stmt = ibm_db.prepare(conn, query_sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.execute(stmt)

        policies = []
        result = ibm_db.fetch_assoc(stmt)
        while result:
            policies.append(result[POLICY_COLUMN.upper()])
            result = ibm_db.fetch_assoc(stmt)

        if not policies:
            raise HTTPException(status_code=404, detail=f"No policies found for {email}")

        return policies

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    finally:
        if conn:
            ibm_db.close(conn)
if __name__ == "__main__":
    #uvicorn.run(app, host="0.0.0.0", port=8000, log_level="trace")
    pass            