Here's the **API Endpoints Documentation** for **PantryTrack** backend (Flask server run by Manhir, using Ethan's modular functions).

This doc describes the expected REST endpoints that the Flutter frontend (Eland) will call. All endpoints are relative to the base URL, e.g.:

- Dev: `http://localhost:5000`
- Later (if needed): `http://your-server-ip:5000` or deployed URL

All responses are **JSON**. Use standard HTTP status codes (200 OK, 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Internal Error).

Assume simple auth for MVP: pass `user_id` (from Firebase Auth UID) in every relevant request body or query param. (Later add Firebase ID token verification in headers if time allows.)

### 1. Parse Receipt (Extract Items + Storage Suggestions)

**Endpoint**  
`POST /parse-receipt`

**Purpose**  
Upload receipt image → call Ethan's `parse_receipt(image_bytes)` → Gemini parses items, quantities, and suggests storage options with estimated shelf life (days) for each: room_temp, fridge, freezer.

**Request**  
- Content-Type: `multipart/form-data`
- Body (form fields):
  - `image`: file (JPEG/PNG receipt photo)

**Response** (200 OK)  
```json
{
  "status": "success",
  "items": [
    {
      "name": "Whole Milk",
      "qty": 1,
      "suggestions": {
        "room_temp": { "days": 1, "note": "Short-term only, spoils quickly" },
        "fridge": { "days": 7, "note": "Standard storage" },
        "freezer": { "days": 30, "note": "For longer preservation" }
      }
    },
    {
      "name": "Eggs (dozen)",
      "qty": 1,
      "suggestions": {
        "room_temp": { "days": 0, "note": "Not recommended" },
        "fridge": { "days": 21, "note": "Best storage" },
        "freezer": { "days": 0, "note": "Do not freeze in shell" }
      }
    }
    // ... more items
  ]
}
```

**Error Responses**  
- 400: No image provided → `{ "error": "No image file provided" }`
- 500: Gemini / parsing failed → `{ "error": "Failed to parse receipt", "details": "..." }`

### 2. Add Item(s) to Pantry (After User Selects Storage)

**Endpoint**  
`POST /add-item`  
(or `/add-items` for batch if sending multiple)

**Purpose**  
User selected storage → call Ethan's DB helpers to calculate final expiration + save to SQLite.

**Request** (JSON body)  
```json
{
  "user_id": "firebase-uid-string",
  "items": [
    {
      "name": "Whole Milk",
      "qty": 1,
      "selected_storage": "fridge",          // one of: "fridge" | "freezer" | "room_temp"
      "expiration_days": 7                   // optional: user override from suggestion
    },
    // ... more items for batch
  ]
}
```

**Response** (201 Created or 200 OK)  
```json
{
  "status": "success",
  "added_count": 1,
  "items": [
    {
      "id": "uuid-or-int-from-db",
      "name": "Whole Milk",
      "qty": 1,
      "selected_storage": "fridge",
      "expiration_date": "2026-03-15T00:00:00Z",
      "added_at": "2026-03-08T10:00:00Z"
    }
  ]
}
```

**Error**  
- 400: Missing fields → `{ "error": "Missing user_id or items" }`

### 3. Get User's Pantry Items

**Endpoint**  
`GET /items`

**Query Params**  
- `user_id` (required): string (Firebase UID)

**Response** (200 OK)  
```json
{
  "status": "success",
  "items": [
    {
      "id": "123",
      "name": "Whole Milk",
      "qty": 1,
      "selected_storage": "fridge",
      "expiration_date": "2026-03-15T00:00:00Z",
      "added_at": "2026-03-08T10:00:00Z",
      "days_left": 7                       // computed or stored
    },
    // ...
  ]
}
```

**Error**  
- 404: No items → `{ "items": [] }` (or empty array, your choice)

### 4. Update Item Storage (User Changes Placement)

**Endpoint**  
`POST /update-storage`

**Purpose**  
User edits item → new storage → recalculate expiration via Ethan's function → update DB.

**Request** (JSON)  
```json
{
  "user_id": "firebase-uid-string",
  "item_id": "123",
  "new_storage": "freezer",
  "new_expiration_days": 90              // optional override
}
```

**Response** (200 OK)  
```json
{
  "status": "success",
  "updated_item": {
    "id": "123",
    "name": "Whole Milk",
    "qty": 1,
    "selected_storage": "freezer",
    "expiration_date": "2026-06-06T00:00:00Z",
    "days_left": 90
  }
}
```

**Error**  
- 404: Item not found → `{ "error": "Item not found" }`