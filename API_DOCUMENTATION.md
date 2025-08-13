# Smith & Williams Trucking REST API Documentation

## Quick Start

### 1. Start the API Server
```bash
python api_server.py
```
The API will run on: http://localhost:8000

### 2. View Interactive Documentation
Open your browser to: http://localhost:8000/docs

### 3. Test with VB.NET
Use the provided `VB_NET_Example.vb` file

## API Endpoints

### Authentication
All endpoints (except login) require Basic Authentication using your username and password.

#### Login
```
POST /api/login
Body: {"username": "Brandon", "password": "owner123"}
Response: {"success": true, "username": "Brandon", "role": "business_administrator"}
```

### Trailers

#### Get All Trailers
```
GET /api/trailers
GET /api/trailers?status=available
```

#### Get Single Trailer
```
GET /api/trailers/TR-001
```

#### Create Trailer
```
POST /api/trailers
Body: {
  "trailer_number": "TR-001",
  "trailer_type": "Dry Van",
  "status": "available",
  "condition": "good",
  "current_location": "Atlanta Depot"
}
```

#### Update Trailer Status
```
PUT /api/trailers/TR-001/status
Body: {"status": "in_use", "notes": "Assigned to move"}
```

### Moves

#### Get All Moves
```
GET /api/moves
GET /api/moves?status=pending
GET /api/moves?driver=Brandon
```

#### Get Single Move
```
GET /api/moves/ORD-001
```

#### Create Move
```
POST /api/moves
Body: {
  "order_number": "ORD-001",
  "customer_name": "ABC Company",
  "origin_city": "Atlanta",
  "origin_state": "GA",
  "destination_city": "Miami",
  "destination_state": "FL",
  "pickup_date": "2025-01-15",
  "delivery_date": "2025-01-17",
  "amount": 1500.00
}
```

#### Assign Driver
```
PUT /api/moves/ORD-001/assign?driver_name=John
```

### Dashboard

#### Get Statistics
```
GET /api/dashboard/stats
Response: {
  "moves": {"pending": 5, "active": 3, "completed": 10},
  "trailers": {"available": 8, "in_use": 4},
  "drivers": {"active": 6}
}
```

#### Get Recent Activity
```
GET /api/dashboard/recent-activity?limit=10
```

## VB.NET Integration

### 1. Install NuGet Package
In Visual Studio Package Manager Console:
```
Install-Package Newtonsoft.Json
```

### 2. Basic Usage
```vb
' Create API client
Dim api = New TrailerTrackerAPI()

' Login
Dim result = Await api.Login("Brandon", "owner123")

' Get trailers
Dim trailers = Await api.GetTrailers()

' Create new trailer
Dim newTrailer = New Trailer With {
    .trailer_number = "TR-999",
    .trailer_type = "Dry Van",
    .status = "available",
    .current_location = "Main Depot"
}
Dim success = Await api.CreateTrailer(newTrailer)
```

### 3. Windows Forms Example
See `VB_NET_Example.vb` for complete Windows Forms application

### 4. Console Application Example
See `VB_NET_Example.vb` for console application example

## Test Credentials

| Username | Password | Role |
|----------|----------|------|
| Brandon | owner123 | business_administrator |
| admin | admin123 | business_administrator |
| DataEntry | data123 | data_entry |
| TestCoordinator | test123 | operations_coordinator |

## Error Codes

- 200: Success
- 401: Unauthorized (bad credentials)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 400: Bad Request (invalid data)

## Security Notes

1. Always use HTTPS in production
2. Store credentials securely in VB.NET (not in code)
3. Implement token-based auth for production
4. Add rate limiting for production

## Support

For issues or questions, contact Vernon - Chief Data Security Officer