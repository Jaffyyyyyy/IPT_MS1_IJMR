# API Security Testing Guide - Postman

## Prerequisites
1. Start the HTTPS development server:
   ```bash
   python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
   ```
   Server will be available at: `https://127.0.0.1:8000`

2. **Important:** In Postman settings, disable SSL certificate verification:
   - Go to: File → Settings → General
   - Turn OFF "SSL certificate verification"
   (Required because we're using a self-signed certificate)

---

## Step 1: Test HTTPS Transmission

### 1.1 Verify HTTPS Connection
**Request:**
- Method: `GET`
- URL: `https://127.0.0.1:8000/api/posts/`
- Headers: None required

**Expected Result:**
- Status: 200 OK
- Connection uses HTTPS (check the lock icon in Postman)
- Response body: List of posts (may be empty initially)

**To verify cookies:**
- After making a request, go to Postman's Cookies tab (below the response)
- Look for cookies with `Secure` and `HttpOnly` flags set to `true`

---

## Step 2: Test Password Encryption

### 2.1 Register a New User
**Request:**
- Method: `POST`
- URL: `https://127.0.0.1:8000/api/register/`
- Headers:
  - `Content-Type`: `application/json`
- Body (raw JSON):
```json
{
    "username": "testuser",
    "password": "SecurePass123!",
    "email": "test@example.com"
}
```

**Expected Result:**
- Status: 201 Created
- Response:
```json
{
    "message": "User registered successfully.",
    "username": "testuser"
}
```

### 2.2 Verify Password is Hashed in Database
**Check via Django Shell:**
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.get(username='testuser')
print(user.password)
# Should output something like: argon2$argon2id$v=19$m=102400...
# NOT the plain text password
```

### 2.3 Test Login (Authenticate)
**Request:**
- Method: `POST`
- URL: `https://127.0.0.1:8000/api/login/`
- Body (raw JSON):
```json
{
    "username": "testuser",
    "password": "SecurePass123!"
}
```

**Expected Result:**
- Status: 200 OK
- Response:
```json
{
    "message": "Authentication successful!",
    "username": "testuser"
}
```

### 2.4 Test Login with Wrong Password
**Request:** Same as above but with:
```json
{
    "username": "testuser",
    "password": "WrongPassword"
}
```

**Expected Result:**
- Status: 401 Unauthorized
- Response:
```json
{
    "error": "Invalid credentials."
}
```

---

## Step 3: Test Role-Based Access Control (RBAC)

### 3.1 Create an Authentication Token
**Via Django Shell:**
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create token for testuser
user = User.objects.get(username='testuser')
token = Token.objects.create(user=user)
print(f"Token: {token.key}")
```
**Copy the token key for use in Postman requests.**

### 3.2 Create a Post (Authenticated)
**Request:**
- Method: `POST`
- URL: `https://127.0.0.1:8000/api/posts/`
- Headers:
  - `Content-Type`: `application/json`
  - `Authorization`: `Token YOUR_TOKEN_HERE`
- Body (raw JSON):
```json
{
    "content": "This is a test post",
    "author": 1
}
```

**Note:** You'll need to create a custom User in the posts app first, or you may get an error. For testing, create one via Django admin or shell.

### 3.3 Test Protected Endpoint (Token Required)
**Request:**
- Method: `GET`
- URL: `https://127.0.0.1:8000/api/protected/`
- Headers:
  - `Authorization`: `Token YOUR_TOKEN_HERE`

**Expected Result (with token):**
- Status: 200 OK
- Response:
```json
{
    "message": "Authenticated!"
}
```

**Expected Result (without token):**
- Status: 401 Unauthorized
- Response:
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 3.4 Test Post Detail View (Author-Only Access)
**Setup:** First, you need to:
1. Create a User in Django auth system (already done with testuser)
2. Create a Post with that user as the author
3. The Post model's `author` field references the custom User model, not AuthUser

**Request (as post author):**
- Method: `GET`
- URL: `https://127.0.0.1:8000/api/posts/1/`
- Headers:
  - `Authorization`: `Token YOUR_TOKEN_HERE`

**Expected Result:**
- If you're the author: 200 OK with post content
- If you're not the author: 403 Forbidden
- If not authenticated: 401 Unauthorized

---

## Step 4: Test Sensitive Data Protection

### 4.1 Verify User Serializer Excludes Password
**Request:**
- Method: `GET`
- URL: `https://127.0.0.1:8000/api/users/`

**Expected Result:**
- Response shows only: `id`, `username`, `email`, `created_at`
- **Does NOT include:** `password` or password hash

---

## Common Postman Setup Tips

### Setting Environment Variables
1. Create a new environment in Postman
2. Add variables:
   - `base_url`: `https://127.0.0.1:8000`
   - `token`: (paste your auth token here)
3. Use in requests: `{{base_url}}/api/posts/`

### Organizing Collections
1. Create a collection: "Connectly API Security Tests"
2. Create folders:
   - "01 - HTTPS Tests"
   - "02 - Password Encryption"
   - "03 - RBAC Tests"
   - "04 - Protected Endpoints"

### Saving Responses
**Method 1 - Save within collection:**
- Send request
- Click "Save Response" button (appears near response body)

**Method 2 - Save as file:**
- Click "⋮" (three dots) in response panel
- Select "Save Response to File"
- Name it descriptively (e.g., `register_user_success.json`)

### Exporting Collection
1. Click "⋮" on your collection
2. Select "Export"
3. Choose "Collection v2.1"
4. Save as JSON file

---

## Test Scenarios Checklist

- [ ] HTTPS connection established
- [ ] Session cookies have Secure flag
- [ ] User registration creates hashed password
- [ ] Login with correct credentials succeeds
- [ ] Login with wrong credentials fails
- [ ] Protected endpoint denies unauthenticated requests
- [ ] Protected endpoint allows authenticated requests with token
- [ ] Post detail view denies non-authors
- [ ] Post detail view allows authors
- [ ] User serializer excludes sensitive fields
- [ ] All responses saved in Postman

---

## Troubleshooting

### "SSL certificate problem"
- Disable SSL verification in Postman settings

### "CSRF verification failed"
- For POST requests, either:
  - Add `@csrf_exempt` decorator to view (development only)
  - Or obtain CSRF token first and include in headers

### "Authentication credentials were not provided"
- Check Authorization header format: `Token YOUR_TOKEN_KEY`
- Ensure token exists in database

### Post author permissions failing
- The custom Post model uses the `posts.User` model, not `django.contrib.auth.User`
- You need to link them or modify the permission check
