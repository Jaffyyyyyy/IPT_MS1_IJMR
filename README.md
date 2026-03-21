# Connectly Project - Django REST API

A Django REST Framework API with Token Authentication, Role-Based Access Control (RBAC), Privacy Settings, Caching, Pagination, Factory Pattern, Singleton design patterns, OAuth support, and User Interaction features (Likes & Comments).

> **🤖 AI Disclosure:** This README file was created using AI assistance. The rest of the codebase was developed without AI assistance.

## ✨ Features

### Core Functionality
- ✅ **User Management** - Custom user model with role-based access control (`admin`, `user`, `guest`)
- ✅ **Post Creation** - Create text, image, and video posts
- ✅ **Post Privacy** - Posts can be `public` (visible to all) or `private` (visible to author only)
- ✅ **Factory Pattern** - Type-specific post creation with validation
- ✅ **Token Authentication** - Secure API access with Django REST Framework tokens
- ✅ **OAuth Integration** - Google OAuth via django-allauth

### User Interactions
- ✅ **Like/Unlike Posts** - Users can like and unlike posts
- ✅ **Comment on Posts** - Add comments to posts with validation
- ✅ **Paginated Comments** - Efficient retrieval of large comment datasets (10 per page, configurable)
- ✅ **Like & Comment Counts** - DB-level aggregated counts on post details and feed
- ✅ **Duplicate Prevention** - Users can only like a post once
- ✅ **News Feed** - Paginated, cached feed of posts (newest first, privacy-filtered)

### Security & Access Control (RBAC)
- ✅ **Admin role** - Full access: list/create users, edit/delete any post, delete any comment
- ✅ **User role** - Read/write access to own content; can read all public posts
- ✅ **Guest role** - Read-only; blocked from creating posts, comments, or likes
- ✅ **Object-level permissions** - Only the post author (or admin) can edit/delete a post
- ✅ **Privacy enforcement** - Private posts return 404 (not 403) to non-owners to obscure existence

### Performance
- ✅ **Feed caching** - `GET /feed/` results cached per user+page with version-based invalidation
- ✅ **Post detail caching** - `GET /posts/{id}/` cached individually; invalidated on write
- ✅ **Cache invalidation** - Cache automatically busted when posts are created or deleted
- ✅ **N+1 prevention** - `select_related` / `prefetch_related` / DB `COUNT` annotations throughout
- ✅ **Pagination** - Feed (10/page, max 100) and comments (10/page, max 100) both paginated

### Design Patterns
- ✅ **Factory Pattern** - PostFactory for creating posts with type-specific validation
- ✅ **Singleton Pattern** - LoggerSingleton and ConfigManager for centralized services

## 🚀 Quick Setup

### Automated Setup (Recommended)

**Windows:**
```bash
setup.bat
```

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Create a virtual environment
2. Install all dependencies
3. Run database migrations
4. Generate an authentication token

### Manual Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd IPT_MS1_IJMR-1
   ```

2. **Create and activate virtual environment:**
   
   **Windows:**
   ```bash
   python -m venv env
   env\Scripts\activate
   ```
   
   **Mac/Linux:**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   cd connectly_project
   pip install -r dependencies.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create the admin user (required for Postman tests):**
   ```bash
   python manage.py shell -c "
   from posts.models import User
   u, created = User.objects.get_or_create(username='admin')
   u.set_password('adminpass123')
   u.role = 'admin'
   u.is_staff = True
   u.is_superuser = True
   u.save()
   print('Done – id:', u.id)
   "
   ```

## 🖥️ Running the Server

### Development Server (HTTP)
```bash
python manage.py runserver
```
Server will be available at: `http://127.0.0.1:8000`

### HTTPS Server (with SSL certificates)

Run from inside the `connectly_project/` directory:

```bash
# Windows (full path to the venv Python)
cd connectly_project ; ..\.venv\Scripts\python.exe manage.py runserver_plus 127.0.0.1:8000 --cert-file cert.pem --key-file key.pem

# Mac/Linux
python manage.py runserver_plus 127.0.0.1:8000 --cert-file cert.pem --key-file key.pem
```

Server will be available at: `https://127.0.0.1:8000`

> **Important:** If port 8000 is already in use (e.g., a stale HTTP `runserver` process), kill it first — see the Troubleshooting section below.

**Postman / API client:** Disable SSL certificate verification (Postman → Settings → General → SSL certificate verification → OFF) because the bundled certificates are self-signed.

## 📁 Project Structure

```
connectly_project/
├── manage.py                  # Django management script
├── db.sqlite3                # SQLite database
├── dependencies.txt             # Python dependencies
├── cert.pem / key.pem        # SSL certificates for HTTPS
├── connectly_project/        # Main Django settings
│   ├── settings.py           # Project configuration
│   ├── urls.py               # Root URL routing
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── posts/                    # Main application
│   ├── models.py            # User, Post, Comment, Like models
│   ├── views.py             # API views (class-based and function-based)
│   ├── serializers.py       # DRF serializers
│   ├── permissions.py       # Custom permissions
│   ├── urls.py              # URL routing for posts app
│   ├── tests.py             # Comprehensive unit tests
│   ├── admin.py             # Django admin configuration
│   ├── apps.py              # App configuration
│   └── migrations/          # Database migrations
├── factories/               # Factory Pattern implementation
│   └── post_factory.py     # PostFactory for creating posts
└── singletons/             # Singleton Pattern implementation
    ├── config_manager.py   # Configuration singleton
    └── logger_singleton.py # Logger singleton
```

## 🎯 Design Patterns Implemented

### 1. Factory Pattern (`factories/post_factory.py`)
Creates posts with type-specific validation:

**Supported Post Types:**
- **Text posts**: Default type, no special requirements
- **Image posts**: Requires `file_size` in metadata
  ```python
  metadata={'file_size': 1024000, 'dimensions': '1920x1080'}
  ```
- **Video posts**: Requires `duration` in metadata
  ```python
  metadata={'duration': 120, 'resolution': '1080p'}
  ```

**Features:**
- Validates post type
- Enforces type-specific metadata requirements
- Validates title length (max 255 characters)
- Ensures metadata is a valid JSON object

**Usage Example:**
```python
from factories.post_factory import PostFactory

post = PostFactory.create_post(
    post_type='image',
    title='My Photo',
    content='Beautiful sunset',
    metadata={'file_size': 2048000, 'dimensions': '4K'},
    author=user
)
```

### 2. Singleton Pattern

#### LoggerSingleton (`singletons/logger_singleton.py`)
- Single logger instance across the entire application
- Consistent logging format with timestamps
- Logs all API operations (user creation, post creation, likes, comments, errors)

**Usage:**
```python
from singletons.logger_singleton import LoggerSingleton

logger = LoggerSingleton().get_logger()
logger.info("Operation successful")
logger.error("Something went wrong")
```

#### ConfigManager (`singletons/config_manager.py`)
- Centralized configuration management
- Default settings: `DEFAULT_PAGE_SIZE=20`, `ENABLE_ANALYTICS=True`, `RATE_LIMIT=100`
- Single configuration instance across the application

**Usage:**
```python
from singletons.config_manager import ConfigManager

config = ConfigManager()
page_size = config.get_setting('DEFAULT_PAGE_SIZE')
config.set_setting('RATE_LIMIT', 150)
```

## 🔐 API Endpoints

All authenticated endpoints require: `Authorization: Token <your-token>`

### Authentication
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `POST` | `/posts/get-token/` | Obtain auth token (username + password) | — |
| `POST` | `/posts/authenticate/` | Verify authentication status | Any authenticated |

### Users
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `GET` | `/posts/users/` | List all users | `admin` only |
| `POST` | `/posts/users/` | Create new user | — (public) |
| `GET` | `/posts/users/me/` | Get current user profile | Any authenticated |

### Posts
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `GET` | `/posts/` | List all posts | Any authenticated |
| `POST` | `/posts/` | Create post (serializer path) | `user` or `admin` (not `guest`) |
| `POST` | `/posts/create/` | Create post via Factory Pattern | `user` or `admin` (not `guest`) |
| `GET` | `/posts/{id}/` | Get post detail (cached) | Any authenticated; `private` → author or admin |
| `PUT/PATCH` | `/posts/{id}/` | Edit post | Author or `admin` |
| `DELETE` | `/posts/{id}/` | Delete post | Author or `admin` |

### News Feed
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `GET` | `/posts/feed/` | Paginated feed, newest first, privacy-filtered, cached | Any authenticated |

Query params: `?page=<n>&page_size=<n>` (default 10, max 100)

### Likes
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `POST` | `/posts/{id}/like/` | Like a post | `user` or `admin` (not `guest`) |
| `DELETE` | `/posts/{id}/like/` | Unlike a post | `user` or `admin` (not `guest`) |

### Comments
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `POST` | `/posts/{id}/comment/` | Add a comment | `user` or `admin` (not `guest`) |
| `GET` | `/posts/{id}/comments/` | Get paginated comments for a post | Any authenticated |
| `DELETE` | `/posts/{id}/comment/` | Delete any comment on a post | `admin` only |
| `GET` | `/posts/comments/` | List all comments | Any authenticated |

Query params for comment pagination: `?page=<n>&page_size=<n>` (default 10, max 100)

### OAuth
- `/accounts/*` — Django-allauth endpoints for Google OAuth
## 📊 Models & Database

### User Model (Custom)
Extends Django's `AbstractUser`:

| Field | Type | Notes |
|-------|------|-------|
| `username` | CharField | Unique |
| `email` | EmailField | Optional |
| `password` | CharField | Hashed (PBKDF2/Argon2/BCrypt) |
| `role` | CharField | `admin` / `user` / `guest`; default `user` |
| `created_at` | DateTimeField | Auto-set on creation |

### Post Model

| Field | Type | Notes |
|-------|------|-------|
| `title` | CharField | Max 255 chars |
| `content` | TextField | Post body |
| `post_type` | CharField | `text` / `image` / `video` |
| `privacy` | CharField | `public` / `private`; default `public` |
| `metadata` | JSONField | Type-specific data (file_size, duration, …) |
| `author` | ForeignKey | → User |
| `created_at` | DateTimeField | Auto-set on creation |

Annotated properties (DB level): `like_count`, `comment_count`

### Comment Model

| Field | Type | Notes |
|-------|------|-------|
| `text` | TextField | Comment body |
| `author` | ForeignKey | → User |
| `post` | ForeignKey | → Post |
| `created_at` | DateTimeField | Auto-set; ordering newest-first |

### Like Model

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey | → User |
| `post` | ForeignKey | → Post |
| `created_at` | DateTimeField | Auto-set |

Unique constraint on `(user, post)` — one like per user per post.

## 🛡️ RBAC & Permissions

### Roles

| Role | Description |
|------|-------------|
| `admin` | Full access: manage all users, edit/delete any post or comment |
| `user` | Default role: read/write own content, read all public content |
| `guest` | Read-only: cannot create posts, comments, or likes |

### Custom Permission Classes (`posts/permissions.py`)

| Class | Rule |
|-------|------|
| `IsAdminRole` | Requires `request.user.role == 'admin'` |
| `IsStaffUser` | Requires `request.user.is_staff` (Django staff flag) |
| `IsNotGuest` | Blocks users with `role == 'guest'` |
| `IsAdminOrAuthor` | Allows if admin role **or** the object's author |
| `IsPostAuthor` | Allows only the post author |

### Permission Matrix

| Action | Guest | User | Admin |
|--------|-------|------|-------|
| List users | ✗ | ✗ | ✓ |
| Read public post | ✓ | ✓ | ✓ |
| Read own private post | — | ✓ | ✓ |
| Read other's private post | ✗ (404) | ✗ (404) | ✗ (404) |
| Create post | ✗ | ✓ | ✓ |
| Edit own post | ✗ | ✓ | ✓ |
| Edit any post | ✗ | ✗ | ✓ |
| Delete own post | ✗ | ✓ | ✓ |
| Delete any post | ✗ | ✗ | ✓ |
| Like / comment | ✗ | ✓ | ✓ |
| Delete any comment | ✗ | ✗ | ✓ |

> **Privacy note:** Private posts return `404 Not Found` (not `403 Forbidden`) to non-owners to avoid revealing that the post exists.

---

## ⚡ Caching

### Backend
`django.core.cache.backends.locmem.LocMemCache` (in-memory, single-process). Configured in `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'connectly-cache',
    }
}
CACHE_TTL = 60 * 5  # 5 minutes
```

### Cached Endpoints

| Endpoint | Cache Key Pattern | TTL |
|----------|------------------|-----|
| `GET /posts/{id}/` | `post_detail_{pk}` | 5 min |
| `GET /posts/feed/` | `news_feed_{uid}_v{ver}_p{page}_s{page_size}` | 5 min |

### Cache Invalidation

Feed caches use a **version counter** per user (`feed_ver_{uid}` key, TTL = 24 h). When a post is created or deleted the version is incremented — all previously cached feed pages for that user become stale automatically without needing to enumerate individual keys.

Invalidation is triggered by:
- `POST /posts/` — new post created
- `POST /posts/create/` — new post created via factory
- `DELETE /posts/{id}/` — post deleted

Post-detail cache is invalidated on every write to that post object.

---

## 📄 Pagination

Both the news feed and comment lists are paginated.

### Classes

| Class | Endpoint | Default page size | Max page size |
|-------|----------|-------------------|---------------|
| `NewsFeedPagination` | `GET /posts/feed/` | 10 | 100 |
| `CommentPagination` | `GET /posts/{id}/comments/` | 10 | 100 |

### Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `page` | Page number (1-indexed) | `?page=2` |
| `page_size` | Results per page (≤ max) | `?page_size=25` |

### Response Structure

```json
{
  "count": 42,
  "next": "https://127.0.0.1:8000/posts/feed/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

## 🧪 Postman Test Suite

The `postman/` directory contains a ready-to-import collection and environment that cover all major features.

### Files

| File | Description |
|------|-------------|
| `postman/Connectly_API_Collection.json` | 48 requests across 6 test folders |
| `postman/Connectly_Environment.json` | Environment variables (base URL, credentials, captured IDs) |

### How to Import

1. Open Postman → **Import** → drag both JSON files in.
2. Select the **Connectly Environment** in the environment dropdown (top-right).
3. If using HTTPS: Postman → **Settings → General → SSL certificate verification → OFF**.

### Folder Structure

| Folder | Requests | Purpose |
|--------|----------|---------|
| `0. Setup (Run First, In Order)` | 12 | Creates admin/user/user2/guest accounts, obtains tokens, creates seed posts and comments |
| `1. Authentication` | 2 | Valid credentials → token; invalid credentials → 400 |
| `2. RBAC` | 15 | Sub-folders: unauthenticated, guest, non-owner, owner, admin — verifies each permission boundary |
| `3. Privacy Settings` | 5 | Owner sees private post; non-owner gets 404; feed filters private posts |
| `4. Caching` | 7 | Cold vs warm feed response, cache bust on post detail write, feed invalidation after create |
| `5. Pagination` | 7 | Default/custom page_size, page 2, out-of-range page, comment pagination |

### Prerequisites

- Django server must be running (see **Running the Server** above).
- Run the **`0. Setup`** folder **first and in order** before any other folder.
- The Setup folder uses timestamp-suffixed usernames so it is safe to re-run without conflicts.

---

## 🧪 Unit Tests

The project includes comprehensive test coverage in [posts/tests.py](connectly_project/posts/tests.py):

### Run Tests
```bash
python manage.py test
```

### Test Coverage
- **Factory Pattern Tests**: 10+ test cases
  - Text, image, video post creation
  - Metadata validation
  - Invalid post type handling
  - Edge cases (empty content, long titles)
- **API Tests**: Covers all endpoints
  - Authentication
  - Post CRUD operations
  - Like/Unlike functionality
  - Comment creation and pagination
  - Authorization checks

## 🔧 Configuration & Settings

### Key Settings ([connectly_project/settings.py](connectly_project/connectly_project/settings.py))
- `DEBUG = True` - Development mode
- `ALLOWED_HOSTS = ['127.0.0.1', 'localhost']`
- Database: SQLite (development)
- Custom User Model: `posts.User`
- Authentication: Token-based (DRF)

### Installed Apps
- Django core apps
- `rest_framework` - API framework
- `rest_framework.authtoken` - Token authentication
- `django_extensions` - Enhanced management commands
- `posts` - Main application
- `allauth` - OAuth authentication
- `crispy_forms` & `crispy_bootstrap5` - Form rendering

### Password Hashers
- PBKDF2 (default)
- Argon2
- BCrypt

## 📦 Dependencies

Dependencies are listed in [dependencies.txt](connectly_project/dependencies.txt):

**Core:**
- Django 6.0.1
- djangorestframework 3.16.1
- django-extensions 4.1

**Authentication:**
- djangorestframework_simplejwt 5.5.1
- django-allauth 0.62.0

**Security:**
- cryptography 46.0.5
- pyOpenSSL 25.3.0

**Utilities:**
- python-decouple 3.8
- django-cors-headers 4.9.0
- Werkzeug 3.1.5 (for runserver_plus)

**Forms:**
- django-crispy-forms 2.3
- crispy_bootstrap5 2026.3

## 📝 Environment Variables

For Google OAuth, create a `.env` file in the project root:
```
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
```

## 🔧 Troubleshooting

### Issue: "Module not found" errors
**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
# Activate virtual environment first
# Windows: env\Scripts\activate
# Mac/Linux: source env/bin/activate

pip install -r dependencies.txt
```

### Issue: "Port 8000 already in use"
**Solution:** 
```bash
# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Windows (CMD)
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Issue: "SSL certificate verification" error
**Solution:** 
- In Postman: Settings → General → Turn OFF "SSL certificate verification"
- In browsers: Accept the security warning for self-signed certificates
- For production, use proper SSL certificates

### Issue: Token authentication not working
**Solution:** 
1. Ensure token is correctly generated:
   ```python
   python manage.py shell
   >>> from rest_framework.authtoken.models import Token
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> user = User.objects.get(username='your_username')
   >>> token, created = Token.objects.get_or_create(user=user)
   >>> print(token.key)
   ```
2. Verify header format: `Authorization: Token <your-token-key>`

### Issue: Database migration errors
**Solution:** 
```bash
# Reset migrations (WARNING: This deletes all data)
python manage.py migrate posts zero
python manage.py migrate
```

### Issue: "Table doesn't exist" errors
**Solution:** Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

## 💡 API Usage Examples

### Creating a Post (Factory Pattern)
```bash
curl -X POST https://127.0.0.1:8000/posts/create/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "post_type": "image",
    "title": "Sunset Photo",
    "content": "Beautiful sunset at the beach",
    "metadata": {
      "file_size": 2048000,
      "dimensions": "1920x1080"
    }
  }'
```

### Liking a Post
```bash
curl -X POST https://127.0.0.1:8000/posts/1/like/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### Adding a Comment
```bash
curl -X POST https://127.0.0.1:8000/posts/1/comment/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Great post!"
  }'
```

### Getting News Feed
```bash
curl -X GET https://127.0.0.1:8000/posts/feed/?page=1 \
  -H "Authorization: Token YOUR_TOKEN"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## � Technologies Used

- **Django** 6.0.1 - Web framework
- **Django REST Framework** 3.16.1 - API framework
- **django-extensions** 4.1 - Enhanced management commands
- **django-allauth** 0.62.0 - OAuth authentication
- **Werkzeug** 3.1.5 - HTTPS development server
- **pyOpenSSL** 25.3.0 - SSL support
- **SQLite** - Database (development)

## 👥 Authors

- RALPH R-NOLD NOCUM
- Michael Angelo Bernardo
- Jafphet Grengia
- Immaculate De Guzman


## 📄 License

This project is for educational purposes as part of IPT coursework.

---

**Note:** This is a development project. Do not use in production without proper security hardening, environment variable management, and SSL certificate configuration.

## 🤝 Contributing

This is a coursework project. For peer review:
1. Clone the repository
2. Follow setup instructions above
3. Test all Postman requests
4. Report any issues

---

**Note:** The `env/` folder is NOT included in the repository (it's in `.gitignore`). Each user must create their own virtual environment as shown in the setup instructions.
