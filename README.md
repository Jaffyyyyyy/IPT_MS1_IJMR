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

## �️ Architecture & Design Decisions

This section documents the key architectural choices made during development, the alternatives considered, and why each decision was taken.

### Module Decomposition

The application is split into focused, single-responsibility modules rather than a single large file:

| Module | Responsibility |
|--------|----------------|
| `models.py` | Data layer — User, Post, Comment, Like ORM definitions |
| `serializers.py` | Data shape — three context-specific serialiser classes (see below) |
| `permissions.py` | Access control — four reusable permission classes used across every view |
| `views.py` | Request handling — class-based views consuming the above |
| `urls.py` | Routing only — no logic |
| `factories/post_factory.py` | Post-creation logic isolated from views |
| `singletons/` | App-wide services (logger, config) with controlled instantiation |

Shared permission classes (`IsAdminRole`, `IsAdminOrAuthor`, `IsNotGuest`) eliminate duplicated access-control checks across views. Shared `StandardPagination` is subclassed rather than re-configured per endpoint.

### Three Serialiser Classes (Not One)

A single serialiser was initially considered but would have caused over-fetching on list endpoints. Three context-specific serialisers are used instead:

| Class | Used by | Why |
|-------|---------|-----|
| `PostSerializer` | Create / list (`POST /posts/`, `GET /posts/`) | Full write surface + nested comment strings |
| `PostDetailSerializer` | Cached detail (`GET /posts/{id}/`) | Reads from DB-level `Count` annotations; no extra queries |
| `PostFeedSerializer` | News feed (`GET /posts/feed/`) | Omits the nested comment list to avoid serialising hundreds of comments per post |

### ORM Query Strategy

All list and detail endpoints use Django ORM optimisations to avoid N+1 query problems:

- **`select_related('author')`** on every queryset that serialises `author_username` — prevents one `SELECT` per post.
- **`Count('likes', distinct=True)` / `Count('comments', distinct=True)` annotations** replace the model-level `@property` counts. The properties issue a `COUNT(*)` per object; annotations resolve both counts in a single aggregated query alongside the main queryset.
- **`Q(privacy='public') | Q(author=request.user)`** pushes the privacy filter to the database rather than filtering a Python list.
- **`unique_together = ('user', 'post')` on `Like`** enforces the one-like-per-user rule at the database constraint level, making duplicate-prevention reliable under concurrent requests.

### Cache Invalidation Strategy

The initial cache design used a simple per-user key (`news_feed_{uid}`). This was insufficient: if user A creates a public post, user B's cached feed would remain stale.

The final design uses a **compound versioned key**:

```
news_feed_{user_id}_v{global_ver}_{user_ver}_p{page}_s{page_size}
```

Two counters are maintained:
- `global_feed_ver` — incremented on **any** public post write; busts cached feeds for **all** users.
- `feed_ver_{uid}` — incremented on the specific user's private-post writes; busts only that user's feed.

This means creating, updating, or deleting a post invalidates stale feed pages across the entire user base without needing to enumerate individual cache keys.

### Privacy Enforcement — Four Layers

Privacy is enforced at four independent points so that a bug in any single layer does not expose private content:

1. **Model field** — `Post.privacy` with `choices` validation.
2. **ORM queryset** — `Q(privacy='public') | Q(author=request.user)` in `PostListCreate` and `NewsFeedView`.
3. **Object-level check** — explicit `post.privacy == 'private' and post.author != request.user` in `PostDetailView`.
4. **Response masking** — returns `404 Not Found` (not `403 Forbidden`) so that the existence of the post is not revealed to non-owners.

### Authentication — Two Independent Paths

Both authentication mechanisms issue the same DRF `Token`, so all downstream endpoints work identically regardless of how the user signed in:

- **Token auth** — `POST /auth/token/` (DRF built-in `obtain_auth_token`).
- **Google OAuth** — `POST /auth/google/login/` validates the Google ID token via Google's `tokeninfo` endpoint, then calls `User.objects.get_or_create(email=…)` to find or provision a local account, and returns a standard DRF token.

### Thread-Safe Singletons

Both `LoggerSingleton` and `ConfigManager` use the `__new__` override with `threading.Lock` (double-checked locking). This guarantees a single shared instance under Django's default multi-threaded WSGI server without relying on module-level globals that can be initialised multiple times in certain import orders.

### Security Hardening

Beyond authentication and RBAC, the following security measures are configured in `settings.py`:

- **Password hashing**: PBKDF2 (default), Argon2, BCryptSHA256 — strong algorithms with upgrade path.
- **Password validation**: length, commonality, similarity, and numeric-only checks.
- **Rate throttling**: 30 requests/minute for anonymous users, 100/minute for authenticated users — mitigates brute-force and scraping.
- **HTTPS / HSTS**: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS = 31536000` (1 year) with subdomains and preload.
- **Author spoofing prevention**: `author` is always set from `request.user` on the server; the client cannot supply or override it.
- **Secrets management**: `SECRET_KEY`, `GOOGLE_OAUTH_CLIENT_ID/SECRET` loaded from `.env` via `python-decouple`, never committed.

---

## �🎯 Design Patterns Implemented

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
| `POST` | `/auth/token/` | Obtain auth token (username + password) | — |
| `POST` | `/auth/google/login` | Exchange Google ID token for API token | — |
| `POST` | `/posts/authenticate/` | Legacy authentication check | — |

### Users
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `GET` | `/posts/users/` | List all users | `admin` only |
| `POST` | `/posts/users/` | Create new user with role (username + password required) | `admin` only |
| `GET` | `/posts/users/me/` | Get current user profile | Any authenticated |

### Posts
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `GET` | `/posts/` | List all posts | Any authenticated |
| `POST` | `/posts/` | Create post (serializer path; author always from auth token) | `user` or `admin` (not `guest`) |
| `POST` | `/posts/create/` | Create post via Factory Pattern | `user` or `admin` (not `guest`) |
| `GET` | `/posts/{id}/` | Get post detail (cached) | Any authenticated; `private` → author or admin |
| `PUT/PATCH` | `/posts/{id}/` | Edit post | Author or `admin` |
| `DELETE` | `/posts/{id}/` | Delete post | Author or `admin` |

### News Feed
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `GET` | `/posts/feed/` | Paginated feed, newest first, privacy-filtered, cached | Any authenticated |

Query params: `?page=<n>&page_size=<n>` (default 20, max 100)

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

Query params for comment pagination: `?page=<n>&page_size=<n>` (default 20, max 100)

### OAuth
| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| `POST` | `/auth/google/login` | Exchange Google ID token for DRF auth token; auto-creates user | — |
| `*` | `/accounts/*` | Django-allauth endpoints (browser-based OAuth) | — |
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
| `IsStaffUser` | Requires `request.user.role == 'admin'` |
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
| `postman/Connectly_API_Collection.json` | 98 requests across 13 test folders (includes Google OAuth tests in folder 12) |
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
| `3. Privacy Settings` | 7 | Owner sees private post; non-owner gets 404; feed filters private posts correctly |
| `4. Caching` | 7 | Cold vs warm feed response, cache bust on post detail write, feed invalidation after create |
| `5. Pagination` | 10 | Default/custom page_size, page 2, out-of-range page, feed and comment pagination |
| `6. Likes` | 8 | Like, duplicate prevention, unlike, unlike-not-liked error, unauthenticated, non-existent post |
| `7. Post CRUD` | 9 | List posts, create (direct serializer), PUT full update, DELETE, admin delete any post, guest/unauth blocked |
| `8. Comments (Extended)` | 6 | Global comment list/create, empty text validation, missing comment_id, comment on non-existent post |
| `9. Post Factory` | 8 | Image/video post types, metadata validation (file_size, duration), invalid type, missing title, guest blocked |
| `10. User Profiles` | 6 | Admin/guest/unauthenticated profile access, invalid user creation (missing username, bad role) |
| `11. Legacy Auth` | 2 | `/posts/authenticate/` endpoint — valid and invalid credentials |
| `12. Google OAuth` | 4 | Missing/empty/invalid token errors, manual valid-token test with auto-save |

### Prerequisites

- Django server must be running (see **Running the Server** above).
- Run the **`0. Setup`** folder **first and in order** before any other folder.
- The Setup folder uses timestamp-suffixed usernames so it is safe to re-run without conflicts.

---

## 🧪 Unit Tests

The project includes comprehensive test coverage across two test files: [posts/tests.py](connectly_project/posts/tests.py) and [posts/test_singletons.py](connectly_project/posts/test_singletons.py).

### Run Tests
```bash
python manage.py test
```

### Test Classes & Coverage

| Class | Cases | What is tested |
|-------|-------|----------------|
| `PostFactoryTestCase` | 8 | Text/image/video creation, type-specific metadata validation, missing required fields, invalid type, authorless post |
| `CreatePostViewTestCase` | 8 | Factory-path API endpoint — all three post types, missing title, missing metadata fields, invalid type, unauthenticated access, default type |
| `RBACTestCase` | 14 | Admin/user/guest role boundaries — user listing, post edit/delete (owner vs non-owner vs admin), guest read-only, admin comment deletion |
| `PrivacySettingsTestCase` | 7 | Public post visibility in feed and detail; private post hidden from non-owners (`404`); author always sees own private posts; privacy field in response |
| `CachingTestCase` | 4 | Cache populated on first request; invalidated on `PATCH`; invalidated on `DELETE`; feed cache key present after first feed request |
| `PaginationTestCase` | varies | Default page size, custom `page_size`, second page, out-of-range page, feed and comment pagination |
| `LikeTestCase` | varies | Like success, duplicate like (`400`), unlike, unlike-not-liked error, unauthenticated |
| `ConfigManagerSingletonTestCase` | 2 | Same instance returned; shared state visible across references |
| `LoggerSingletonTestCase` | 2 | Same instance returned; same underlying logger object returned |

All test cases cover both the **happy path** and **failure / edge cases** (invalid input, insufficient permissions, missing fields, out-of-range pages, duplicate operations). Cache tests use `@override_settings` to inject an isolated in-memory cache so they do not interfere with each other.

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

For Google OAuth, create a `.env` file in the `connectly_project/` directory (same folder as `manage.py`):
```
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
```

The project uses `python-decouple` to read these values. They are required for the server to start — if the `.env` file is missing, `settings.py` will raise an `UndefinedValueError`.

---

## 🔑 Google OAuth Setup Guide (Step-by-Step)

This guide walks through everything needed to get Google Sign-In (`POST /auth/google/login`) working end-to-end.

### How the flow works

```
Client (browser / Postman)
  │
  │  1. User authenticates with Google and receives a Google ID token
  ▼
POST /auth/google/login   { "id_token": "<google_id_token>" }
  │
  │  2. Server calls https://oauth2.googleapis.com/tokeninfo?id_token=…
  │     to validate the token and extract email + sub
  │
  │  3. Server finds or creates a local User record (email as key)
  │     and returns a standard DRF auth token
  ▼
{ "token": "…", "user_id": …, "username": "…", "email": "…", "created": true/false }
```

The endpoint requires **no prior login** — authentication happens entirely inside the request. The returned `token` is a normal DRF token that works for all other API endpoints.

---

### Step 1 — Create a Google Cloud project

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/) and sign in.
2. Click the project dropdown (top-left) → **New Project**.
3. Give it a name (e.g. `Connectly Dev`) and click **Create**.
4. Make sure the new project is selected in the dropdown before continuing.

---

### Step 2 — Enable the required API

1. In the left sidebar: **APIs & Services → Library**.
2. Search for **"Google People API"** and click **Enable**.  
   *(Some older guides say "Google+ API" — that is deprecated. People API is the current equivalent.)*

---

### Step 3 — Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**.
2. Choose **External** (for testing with any Google account) → **Create**.
3. Fill in the required fields:
   - **App name**: `Connectly` (or any name)
   - **User support email**: your Google account email
   - **Developer contact email**: your Google account email
4. Click **Save and Continue** through the Scopes and Test Users screens (no changes needed for development).
5. On the **Test users** screen, add the Google account(s) you will use for testing, then **Save and Continue**.

> **Note:** While the app is in "Testing" mode, only the email addresses listed as Test Users can authenticate. This is fine for development.

---

### Step 4 — Create OAuth 2.0 credentials

1. Go to **APIs & Services → Credentials**.
2. Click **+ Create Credentials → OAuth client ID**.
3. For **Application type**, choose **Web application**.
4. Give it a name (e.g. `Connectly Local`).
5. Under **Authorized JavaScript origins**, add:
   ```
   http://localhost:8000
   https://127.0.0.1:8000
   ```
6. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8000/accounts/google/login/callback/
   https://127.0.0.1:8000/accounts/google/login/callback/
   ```
7. Click **Create**.
8. A dialog shows your **Client ID** and **Client Secret** — copy both immediately (you can always retrieve them later from the Credentials page).

---

### Step 5 — Configure the `.env` file

Create a file called `.env` inside `connectly_project/` (same directory as `manage.py`):

```
GOOGLE_OAUTH_CLIENT_ID=123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Replace the values with the **Client ID** and **Client Secret** from Step 4.

> **Security:** Never commit `.env` to version control. It is already listed in `.gitignore`.

---

### Step 6 — Register the Google app in Django admin

The `allauth` library requires a `SocialApp` record in the database that matches the credentials. Run the server and complete this one-time setup:

1. Start the development server (see **Running the Server** above).
2. Open `http://127.0.0.1:8000/admin/` (or `https://127.0.0.1:8000/admin/`).
3. Log in with the `admin` superuser account.
4. Under **Sites**, click **Sites → Add site** (or edit the existing `example.com` entry):
   - **Domain name**: `127.0.0.1:8000`
   - **Display name**: `Connectly Local`
   - Save. Note the **ID** — it should be `1` (matches `SITE_ID = 1` in `settings.py`). If it shows a different ID, update `SITE_ID` in `settings.py` to match.
5. Under **Social Accounts → Social applications**, click **Add social application**:
   - **Provider**: `Google`
   - **Name**: `Google`
   - **Client id**: paste the Client ID from Step 4
   - **Secret key**: paste the Client Secret from Step 4
   - **Sites**: move `127.0.0.1:8000` from "Available sites" to "Chosen sites"
   - Click **Save**.

---

### Step 7 — Get a Google ID token for testing

The `/auth/google/login` endpoint expects a **Google ID token** (a signed JWT issued by Google directly to the client). There are two ways to get one for testing:

#### Option A — Google OAuth 2.0 Playground (easiest)

1. Open [https://developers.google.com/oauthplayground/](https://developers.google.com/oauthplayground/).
2. Click the settings gear (top-right) → check **"Use your own OAuth credentials"**.
3. Enter your **OAuth Client ID** and **OAuth Client Secret** from Step 4 → **Close**.
4. In the left panel under **"Google APIs"**, scroll to **"Google OAuth2 API v2"** and select `https://www.googleapis.com/auth/userinfo.email` and `https://www.googleapis.com/auth/userinfo.profile`.
5. Click **Authorize APIs** → sign in with a Test User account → grant consent.
6. Click **Exchange authorization code for tokens**.
7. In the response, copy the value of **`id_token`** — this is what you POST to `/auth/google/login`.

> **Note:** ID tokens expire after **1 hour**. Repeat this step when the token expires.

#### Option B — Minimal HTML test page

Save the following as a local `.html` file, open it in a browser, sign in, and the ID token will be printed on the page. Replace `YOUR_CLIENT_ID` with the actual value from Step 4.

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://accounts.google.com/gsi/client" async defer></script>
</head>
<body>
  <div id="g_id_onload"
       data-client_id="YOUR_CLIENT_ID"
       data-callback="handleCredentialResponse">
  </div>
  <div class="g_id_signin" data-type="standard"></div>
  <pre id="token"></pre>
  <script>
    function handleCredentialResponse(response) {
      document.getElementById('token').textContent = response.credential;
    }
  </script>
</body>
</html>
```

The `response.credential` value is the Google ID token.

---

### Step 8 — Test with Postman

1. Import `Connectly_API_Collection.json` and `Connectly_Environment.json` into Postman.
2. In the **Connectly Environment**, set the `google_id_token` variable to the ID token obtained in Step 7.
3. Open folder **`12. Google OAuth`** in the collection.
4. Run the **"Valid token → 200 + save DRF token"** request — on success it saves the returned DRF token to `{{google_user_token}}` automatically.
5. You can then use `Authorization: Token {{google_user_token}}` for any subsequent request.

**Example of Expected response (200):**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 5,
  "username": "jsmith_a1b2c3",
  "email": "jsmith@gmail.com",
  "created": true
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success — DRF token returned |
| `400` | `id_token` field missing or empty in request body |
| `401` | Token rejected by Google (expired, wrong audience, or tampered) |
| `409` | Email already exists via password auth — must use `/auth/token/` instead |

---

### Common Google OAuth errors

| Error | Cause | Fix |
|-------|-------|-----|
| `UndefinedValueError: GOOGLE_OAUTH_CLIENT_ID not found` | `.env` file missing or in wrong directory | Create `.env` in `connectly_project/` |
| `Invalid or expired Google token` (401) | Token older than 1 hour | Get a fresh token (Step 7) |
| `No module named 'allauth'` | Missing dependency | Run `pip install -r dependencies.txt` |
| `Site matching query does not exist` | No Site with `SITE_ID=1` in the database | Complete Step 6 (Django admin setup) |
| `Redirect URI mismatch` (Google error) | Callback URL not whitelisted | Add the URI in Google Cloud Console (Step 4) |
| `Access blocked: app is in Testing mode` | Google account not a Test User | Add the email in the OAuth consent screen (Step 3, step 5) |

---

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

---

## 🏗️ Design Decisions & Alternatives Analysis

This section documents the key architectural choices made during development, the alternatives that were considered, and why each decision was made. These trade-offs are recorded here to satisfy the "Solution & Alternatives Identification & Design" rubric criterion.

---

### 1. Authentication — Token Auth vs JWT

**Decision:** DRF `TokenAuthentication` (opaque tokens stored in the database).

**Alternatives considered:**

| Option | Pros | Cons | Why rejected |
|--------|------|------|--------------|
| **JWT (simplejwt)** | Stateless, no DB lookup per request, easy horizontal scaling | Cannot be revoked server-side without a deny-list; payload visible to client; expiry management adds complexity | For a course project with a single-process dev server and no revocation requirement, the extra complexity of refresh tokens and deny-lists outweighs the statelessness benefit |
| **Session auth** | Built into Django, simple | CSRF required; not suitable for API-first design | REST APIs should be stateless between requests; session cookies couple the client to server-side storage in a way that conflicts with the API design |
| **Basic auth** | Zero setup | Sends credentials on every request; not safe without HTTPS everywhere | Credential exposure risk on every call is unacceptable even in development |

**Consequence of chosen approach:** Every authenticated request does one extra DB query (`Token` look-up). Acceptable at this scale; would be revisited if horizontal scaling or token-less sessions became a requirement.

---

### 2. Feed Cache Invalidation — Compound Version Keys vs Full-Flush

**Decision:** A two-level version counter: one global key (`global_feed_ver`) incremented on any public-post write + one per-user key (`feed_ver_{uid}`) incremented on private-post writes.

**Alternatives considered:**

| Option | Pros | Cons | Why rejected |
|--------|------|------|--------------|
| **Full cache flush on every write** (`cache.clear()`) | Simple to implement | Destroys unrelated cached data (post detail, other users' feeds) on every write — defeats caching entirely under moderate write load | Too destructive; one user creating a post would bust every other user's cached page |
| **Per-user cache key only** (`news_feed_{uid}_p{page}`) | Simple; each user has isolated cache | When user A creates a *public* post, user B's cached feed becomes stale — but nothing busts it, so B sees an outdated feed until TTL expires | Correctness failure: public posts must appear in all users' feeds promptly |
| **Enumerate and delete keys on write** | Precise invalidation | `django.core.cache.locmem` does not support key listing/scanning; would require Redis with `SCAN` | Not portable to the configured cache backend |
| **Chosen: compound version counter** | No key scanning needed; global bump correctly busts all users; tiny storage overhead (two integers) | Stale version keys accumulate in cache (harmless, they expire at 24 h TTL) | Chosen because it is correct, portable, and requires no key enumeration |

**Consequence:** Old version-keyed cache entries are orphaned (never explicitly deleted) until their TTL expires. With a 5-minute TTL on feed pages this is at most 5 minutes of wasted memory per orphaned entry — acceptable.

---

### 3. Serializer Design — Multiple Specialised Classes vs One Generic Serializer

**Decision:** Four separate serializer classes: `PostSerializer`, `PostDetailSerializer`, `PostFeedSerializer`, `LikeSerializer`.

**Alternatives considered:**

| Option | Pros | Cons | Why rejected |
|--------|------|------|--------------|
| **One `PostSerializer` with optional fields** (e.g. `fields` kwarg) | DRY | Context-passing makes the serializer stateful and harder to test; logic for "include comments or not" leaks into view code | Violates single-responsibility; harder to understand and maintain |
| **`PostSerializer` + `DynamicFieldsMixin`** | Popular pattern | Requires a third-party mixin or custom base class; still ties field selection to the serializer constructor call-site | Adds a dependency or custom abstraction for limited benefit |
| **Chosen: dedicated serializer per use case** | Each serializer is unambiguous; `PostFeedSerializer` omits the comments list (avoiding N+1 serialisation of hundreds of comments per post in the feed); `PostDetailSerializer` maps `annotated_*` sources for DB-level counts | Slightly more code | Chosen because it makes the performance intent explicit and each class can evolve independently |

**Consequence:** Adding a new field to `Post` may require updating multiple serializers. This is an acceptable maintenance cost given the performance and clarity gains.

---

### 4. Privacy Enforcement — 404 vs 403 for Private Posts

**Decision:** Private posts return `404 Not Found` to non-owners (not `403 Forbidden`).

**Alternative:** Return `403 Forbidden` to make the error type explicit.

**Why 404 was chosen:** Returning `403` on a private post confirms to the caller that the post *exists* but they cannot see it — this is an information leak. `404` prevents enumeration of private content IDs. This pattern is used by GitHub (private repos appear as 404 to non-members) and is the recommended approach in OWASP access-control guidelines.

**Consequence:** API consumers cannot distinguish "post doesn't exist" from "post is private". This is intentional; documentation (Postman collection description, API table above) makes the behaviour explicit.

---

### 5. Post-Count Resolution — DB Annotations vs Python `@property`

**Decision:** `like_count` and `comment_count` are resolved via DB-level `Count` annotations (using `annotate()`) in all list and detail endpoints.

**Alternative:** The `Post` model exposes `@property like_count` / `@property comment_count` that call `self.likes.count()` / `self.comments.count()`. This is convenient for single-object access but does **not** benefit from `prefetch_related` — Django's `QuerySet.count()` always issues a new SQL `COUNT` query regardless of what has been prefetched.

**Why annotations are preferred:** For a list of N posts, counting via `@property` issues 2N extra queries (one per post per count). A `Count` annotation resolves both counts in the same aggregated `SELECT` that fetches the posts — O(1) queries regardless of result-set size.

**How this is implemented:**
- `NewsFeedView`, `PostDetailView`, and `PostListCreate.get` all call `.annotate(annotated_like_count=Count('likes', distinct=True), annotated_comment_count=Count('comments', distinct=True))` on the queryset.
- `PostSerializer` uses `SerializerMethodField` helpers that prefer the annotation when present and fall back to `.count()` for single-object contexts (e.g. a freshly created post returned from `POST /posts/`).
- `PostDetailSerializer` and `PostFeedSerializer` use `source='annotated_like_count'` directly since they are only ever instantiated with annotated querysets.

---

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
