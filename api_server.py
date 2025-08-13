"""
REST API Server for Trailer Move Tracker
Provides endpoints for external applications (VB.NET, mobile apps, etc.)
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import hashlib
from datetime import datetime, timedelta
import secrets

# Initialize FastAPI app
app = FastAPI(
    title="Smith & Williams Trucking API",
    description="REST API for Trailer Move Management System",
    version="1.0.0"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your VB.NET app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

# Database connection
def get_db():
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    conn.row_factory = sqlite3.Row
    return conn

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify user credentials"""
    conn = get_db()
    cursor = conn.cursor()
    
    hashed_pw = hash_password(credentials.password)
    cursor.execute(
        "SELECT username, role FROM users WHERE username = ? AND password = ? AND active = 1",
        (credentials.username, hashed_pw)
    )
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return {"username": user["username"], "role": user["role"]}

# ===== MODELS =====
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    username: str
    role: str
    message: str

class TrailerRequest(BaseModel):
    trailer_number: str
    trailer_type: str
    status: str = "available"
    condition: str = "good"
    current_location: str
    customer_owner: Optional[str] = None
    notes: Optional[str] = None

class MoveRequest(BaseModel):
    order_number: str
    customer_name: str
    origin_city: str
    origin_state: str
    destination_city: str
    destination_state: str
    pickup_date: str
    delivery_date: str
    amount: float
    driver_name: Optional[str] = None
    status: str = "pending"

class StatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

# ===== AUTHENTICATION ENDPOINTS =====
@app.post("/api/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Login endpoint for authentication"""
    conn = get_db()
    cursor = conn.cursor()
    
    hashed_pw = hash_password(request.password)
    cursor.execute(
        "SELECT username, role, name FROM users WHERE username = ? AND password = ? AND active = 1",
        (request.username, hashed_pw)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return LoginResponse(
            success=True,
            username=user["username"],
            role=user["role"],
            message=f"Welcome {user['name'] if user['name'] else user['username']}!"
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get("/api/verify")
def verify_token(current_user: dict = Depends(verify_user)):
    """Verify authentication token"""
    return {
        "authenticated": True,
        "user": current_user
    }

# ===== TRAILER ENDPOINTS =====
@app.get("/api/trailers")
def get_trailers(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(verify_user)
):
    """Get all trailers or filter by status"""
    conn = get_db()
    cursor = conn.cursor()
    
    if status:
        cursor.execute(
            "SELECT * FROM trailer_inventory WHERE status = ? LIMIT ?",
            (status, limit)
        )
    else:
        cursor.execute("SELECT * FROM trailer_inventory LIMIT ?", (limit,))
    
    trailers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "count": len(trailers),
        "trailers": trailers
    }

@app.get("/api/trailers/{trailer_number}")
def get_trailer(trailer_number: str, current_user: dict = Depends(verify_user)):
    """Get specific trailer by number"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM trailer_inventory WHERE trailer_number = ?",
        (trailer_number,)
    )
    trailer = cursor.fetchone()
    conn.close()
    
    if trailer:
        return dict(trailer)
    else:
        raise HTTPException(status_code=404, detail="Trailer not found")

@app.post("/api/trailers")
def create_trailer(
    trailer: TrailerRequest,
    current_user: dict = Depends(verify_user)
):
    """Create new trailer"""
    if current_user["role"] not in ["business_administrator", "admin", "data_entry"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO trailer_inventory 
            (trailer_number, trailer_type, status, condition, current_location, 
             customer_owner, notes, updated_by, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trailer.trailer_number, trailer.trailer_type, trailer.status,
            trailer.condition, trailer.current_location, trailer.customer_owner,
            trailer.notes, current_user["username"], datetime.now()
        ))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Trailer {trailer.trailer_number} created successfully"
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Trailer already exists")

@app.put("/api/trailers/{trailer_number}/status")
def update_trailer_status(
    trailer_number: str,
    update: StatusUpdate,
    current_user: dict = Depends(verify_user)
):
    """Update trailer status"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE trailer_inventory SET status = ?, notes = ?, updated_by = ?, last_updated = ? WHERE trailer_number = ?",
        (update.status, update.notes, current_user["username"], datetime.now(), trailer_number)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Trailer not found")
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Trailer {trailer_number} status updated to {update.status}"
    }

# ===== MOVE ENDPOINTS =====
@app.get("/api/moves")
def get_moves(
    status: Optional[str] = None,
    driver: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(verify_user)
):
    """Get all moves or filter by status/driver"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM moves WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if driver:
        query += " AND driver_name = ?"
        params.append(driver)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    moves = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "count": len(moves),
        "moves": moves
    }

@app.get("/api/moves/{order_number}")
def get_move(order_number: str, current_user: dict = Depends(verify_user)):
    """Get specific move by order number"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM moves WHERE order_number = ?",
        (order_number,)
    )
    move = cursor.fetchone()
    conn.close()
    
    if move:
        return dict(move)
    else:
        raise HTTPException(status_code=404, detail="Move not found")

@app.post("/api/moves")
def create_move(
    move: MoveRequest,
    current_user: dict = Depends(verify_user)
):
    """Create new move"""
    if current_user["role"] not in ["business_administrator", "admin", "operations_coordinator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO moves 
            (order_number, customer_name, origin_city, origin_state,
             destination_city, destination_state, pickup_date, delivery_date,
             amount, driver_name, status, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            move.order_number, move.customer_name, move.origin_city, move.origin_state,
            move.destination_city, move.destination_state, move.pickup_date, 
            move.delivery_date, move.amount, move.driver_name, move.status,
            datetime.now(), current_user["username"]
        ))
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Move {move.order_number} created successfully"
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Move order number already exists")

@app.put("/api/moves/{order_number}/status")
def update_move_status(
    order_number: str,
    update: StatusUpdate,
    current_user: dict = Depends(verify_user)
):
    """Update move status"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE moves SET status = ?, notes = ? WHERE order_number = ?",
        (update.status, update.notes, order_number)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Move not found")
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Move {order_number} status updated to {update.status}"
    }

@app.put("/api/moves/{order_number}/assign")
def assign_driver(
    order_number: str,
    driver_name: str,
    current_user: dict = Depends(verify_user)
):
    """Assign driver to move"""
    if current_user["role"] not in ["business_administrator", "admin", "operations_coordinator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE moves SET driver_name = ?, status = 'assigned' WHERE order_number = ?",
        (driver_name, order_number)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Move not found")
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Driver {driver_name} assigned to move {order_number}"
    }

# ===== DASHBOARD ENDPOINTS =====
@app.get("/api/dashboard/stats")
def get_dashboard_stats(current_user: dict = Depends(verify_user)):
    """Get dashboard statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get move stats
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
    pending_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
    active_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
    completed_moves = cursor.fetchone()[0]
    
    # Get trailer stats
    cursor.execute("SELECT COUNT(*) FROM trailer_inventory WHERE status = 'available'")
    available_trailers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailer_inventory WHERE status = 'in_use'")
    in_use_trailers = cursor.fetchone()[0]
    
    # Get driver stats
    cursor.execute("SELECT COUNT(DISTINCT driver_name) FROM moves WHERE driver_name IS NOT NULL")
    active_drivers = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "moves": {
            "pending": pending_moves,
            "active": active_moves,
            "completed": completed_moves
        },
        "trailers": {
            "available": available_trailers,
            "in_use": in_use_trailers
        },
        "drivers": {
            "active": active_drivers
        }
    }

@app.get("/api/dashboard/recent-activity")
def get_recent_activity(
    limit: int = 10,
    current_user: dict = Depends(verify_user)
):
    """Get recent system activity"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT order_number, customer_name, status, created_at, driver_name
        FROM moves
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    activities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "count": len(activities),
        "activities": activities
    }

# ===== DRIVER ENDPOINTS =====
@app.get("/api/drivers")
def get_drivers(current_user: dict = Depends(verify_user)):
    """Get all drivers"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM drivers WHERE status = 'Active'")
    drivers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "count": len(drivers),
        "drivers": drivers
    }

@app.get("/api/drivers/{driver_name}/moves")
def get_driver_moves(
    driver_name: str,
    current_user: dict = Depends(verify_user)
):
    """Get moves assigned to specific driver"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM moves WHERE driver_name = ? ORDER BY pickup_date DESC",
        (driver_name,)
    )
    moves = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "driver": driver_name,
        "count": len(moves),
        "moves": moves
    }

# ===== ROOT ENDPOINT =====
@app.get("/")
def root():
    """API root endpoint with basic info"""
    return {
        "name": "Smith & Williams Trucking API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "login": "/api/login",
            "trailers": "/api/trailers",
            "moves": "/api/moves",
            "dashboard": "/api/dashboard/stats",
            "drivers": "/api/drivers"
        }
    }

# ===== HEALTH CHECK =====
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)