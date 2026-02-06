# Quick Reference - Test Credentials & Tokens

## Generated Test Users

### 1. Admin User (Full Access)
- **Username:** `admin_user`
- **Password:** `AdminPass123!`
- **Token:** `e0a3b4268a26e8aeb02441c7a701613179c4edc9`
- **Group:** Admin
- **Email:** admin@test.com

### 2. Regular User (Limited Access)
- **Username:** `regular_user`
- **Password:** `RegularPass123!`
- **Token:** `179077d7023e53acb4afd1a70b3587653cbcc756`
- **Group:** Viewer
- **Email:** regular@test.com

### 3. Author User (Content Creator)
- **Username:** `author_user`
- **Password:** `AuthorPass123!`
- **Token:** `51609aa9d842569be5af31a9bcb3cce233c6d6fb`
- **Group:** (none)
- **Email:** author@test.com

---

## Postman Variable Configuration

Copy these values into your Postman collection variables:

| Variable Name | Value |
|--------------|-------|
| `base_url` | `https://127.0.0.1:8000/api` |
| `admin_token` | `e0a3b4268a26e8aeb02441c7a701613179c4edc9` |
| `regular_token` | `179077d7023e53acb4afd1a70b3587653cbcc756` |
| `author_token` | `51609aa9d842569be5af31a9bcb3cce233c6d6fb` |

---

## Test Scenarios

### Scenario 1: Test Password Encryption
1. Register user via `/register/` endpoint
2. Check database - password should be hashed with Argon2
3. Login with correct password - should succeed (200 OK)
4. Login with wrong password - should fail (401 Unauthorized)

### Scenario 2: Test Token Authentication
1. Access `/protected/` without token → 401 Unauthorized
2. Access `/protected/` with valid token → 200 OK
3. Use token format: `Authorization: Token <token>`

### Scenario 3: Test RBAC (Role-Based Access Control)
1. **As admin_user:**
   - Can access `/posts/3/` (admin's own post) → 200 OK
   
2. **As regular_user:**
   - Cannot access `/posts/3/` (admin's post) → 403 Forbidden
   - Can only access own posts

### Scenario 4: Test HTTPS Security
1. All requests use `https://` protocol
2. Check response headers for `Strict-Transport-Security`
3. Verify cookies have `Secure` and `HttpOnly` flags

### Scenario 5: Test Sensitive Data Protection
1. GET `/users/` endpoint
2. Verify response does NOT contain `password` field
3. Only `username`, `email`, `created_at` should be present

---

## Sample Test Data

### Posts in Database:
- **Post ID 1:** By author_user - "First post by author_user..."
- **Post ID 2:** By author_user - "Second post by author_user..."
- **Post ID 3:** By admin_user - "Post by admin_user..."

### Expected Access Control:
| User | Can Access Post 1? | Can Access Post 2? | Can Access Post 3? |
|------|-------|-------|-------|
| author_user | ✅ Yes | ✅ Yes | ❌ No (403) |
| admin_user | ❌ No (403) | ❌ No (403) | ✅ Yes |
| regular_user | ❌ No (403) | ❌ No (403) | ❌ No (403) |

---

## API Endpoints Reference

### Public Endpoints (no auth required):
- `GET /api/posts/` - List all posts
- `GET /api/users/` - List all users (no passwords)
- `GET /api/comments/` - List all comments
- `POST /api/register/` - Register new user
- `POST /api/login/` - Login (verify credentials)

### Protected Endpoints (require token):
- `GET /api/protected/` - Test authentication
- `GET /api/posts/<id>/` - View post (must be author)

### Create Endpoints:
- `POST /api/posts/` - Create post
- `POST /api/comments/` - Create comment

---

## How to Use Tokens in Postman

### Add Token to Request Header:
1. Open request in Postman
2. Go to **Headers** tab
3. Add header:
   - **Key:** `Authorization`
   - **Value:** `Token e0a3b4268a26e8aeb02441c7a701613179c4edc9`
   - (Or use variable: `Token {{admin_token}}`)

### Or Use Authorization Tab:
1. Go to **Authorization** tab
2. Type: Select **API Key**
3. Key: `Authorization`
4. Value: `Token {{admin_token}}`
5. Add to: **Header**

---

## Start HTTPS Server

Run this command before testing:

```powershell
cd c:\IPT-HW--1\connectly_project
c:\IPT-HW--1\env\Scripts\python.exe manage.py runserver_plus --cert-file cert.pem --key-file key.pem
```

Server will start at: **https://127.0.0.1:8000**

---

## Verify Password Hashing

### Check in Database:
1. Open `db.sqlite3` in DB Browser
2. Go to `auth_user` table
3. Look at `password` column
4. Should see: `argon2$argon2id$v=19$m=65536,t=3,p=4$...` (hashed!)

### Check in Django Shell:
```python
python manage.py shell

>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='admin_user')
>>> print(user.password)
# Output: argon2$argon2id$v=19$m=65536,t=3,p=4$...
```

---

## Important Notes

⚠️ **SSL Certificate Warning:** Browsers/Postman will warn about self-signed certificate - this is expected. Disable SSL verification in Postman settings.

⚠️ **Token Format:** Must be `Token <key>` NOT `Bearer <key>`

⚠️ **Custom vs Auth Users:** App uses two user models:
- `django.contrib.auth.models.User` - for authentication
- `posts.models.User` - for post authorship
- They are linked by username

✅ **All passwords are hashed** - Never stored in plain text
✅ **All endpoints support HTTPS** - HTTP will redirect to HTTPS
✅ **Tokens don't expire** - Valid until manually deleted

---

## Test Checklist

Before uploading results to Google Drive, ensure you've tested:

- [ ] HTTPS connection works (🔒 icon visible)
- [ ] User registration creates hashed passwords
- [ ] Login validates credentials correctly
- [ ] Invalid login returns 401
- [ ] Protected endpoint requires token
- [ ] Valid token grants access
- [ ] Author can access own post
- [ ] Non-author gets 403 on others' posts
- [ ] HSTS header present in responses
- [ ] Cookies have Secure flag
- [ ] User list doesn't expose passwords
- [ ] All responses saved in Postman collection

---

**Ready to test! Follow the POSTMAN_TESTING_GUIDE.md for step-by-step instructions.** 🚀
