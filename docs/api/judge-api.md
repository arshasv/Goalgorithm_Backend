# Judge API

Judge Management endpoints are accessible only to users with the **ORGANIZER** role (e.g., admin).

---

## Create Judge
Create a new registered judge with a unique employee ID.

* **Endpoint:** `POST /api/v1/judges`
* **HTTP Method:** `POST`
* **Authorization:** Header `Authorization: Bearer <token>` (ORGANIZER only)

### Request Payload
```json
{
  "name": "Dr. John Doe",
  "employee_id": "EMP001"
}
```

### Response JSON (200 OK)
```json
{
  "id": "8fa838df-bfce-4171-aa34-b258e727e02b",
  "name": "Dr. John Doe",
  "employee_id": "EMP001",
  "created_at": "2026-06-22T06:30:00Z",
  "updated_at": "2026-06-22T06:30:00Z"
}
```

---

## Get Registered Judges
Fetch a list of all permanently registered judges.

* **Endpoint:** `GET /api/v1/judges`
* **HTTP Method:** `GET`
* **Authorization:** Header `Authorization: Bearer <token>` (ORGANIZER only)

### Response JSON (200 OK)
```json
[
  {
    "id": "8fa838df-bfce-4171-aa34-b258e727e02b",
    "name": "Dr. John Doe",
    "employee_id": "EMP001",
    "created_at": "2026-06-22T06:30:00Z",
    "updated_at": "2026-06-22T06:30:00Z"
  }
]
```

---

## Update Judge
Modify a judge's name or employee ID.

* **Endpoint:** `PUT /api/v1/judges/{id}`
* **HTTP Method:** `PUT`
* **Authorization:** Header `Authorization: Bearer <token>` (ORGANIZER only)

### Request Payload
```json
{
  "name": "Dr. John Doe Jr.",
  "employee_id": "EMP001"
}
```

### Response JSON (200 OK)
```json
{
  "id": "8fa838df-bfce-4171-aa34-b258e727e02b",
  "name": "Dr. John Doe Jr.",
  "employee_id": "EMP001",
  "created_at": "2026-06-22T06:30:00Z",
  "updated_at": "2026-06-22T06:31:00Z"
}
```

---

## Delete Judge
Delete a registered judge by ID. Cascades to clear associated scores.

* **Endpoint:** `DELETE /api/v1/judges/{id}`
* **HTTP Method:** `DELETE`
* **Authorization:** Header `Authorization: Bearer <token>` (ORGANIZER only)

### Response (200 OK)
```json
{
  "status": "success",
  "message": "Judge deleted successfully"
}
```
