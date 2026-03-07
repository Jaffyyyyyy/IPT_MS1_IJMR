# Connectly Project - Django REST API

A Django REST Framework API with Token Authentication, Factory Pattern, Singleton design patterns, OAuth support, and User Interaction features (Likes & Comments).

> **🤖 AI Disclosure:** This README file was created using AI assistance. The rest of the codebase was developed without AI assistance.

## ✨ Features

### Core Functionality
- ✅ **User Management** - Custom user model with authentication
- ✅ **Post Creation** - Create text, image, and video posts
- ✅ **Factory Pattern** - Type-specific post creation with validation
- ✅ **Token Authentication** - Secure API access with Django REST Framework tokens
- ✅ **OAuth Integration** - Google OAuth via django-allauth

### User Interactions
- ✅ **Like/Unlike Posts** - Users can like and unlike posts
- ✅ **Comment on Posts** - Add comments to posts with validation
- ✅ **Paginated Comments** - Efficient retrieval of large comment datasets (10 per page)
- ✅ **Like & Comment Counts** - Real-time counts on post details
- ✅ **Duplicate Prevention** - Users can only like a post once
- ✅ **News Feed** - Paginated feed of all posts (newest first)

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

5. **Create a superuser (for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Generate authentication token:**
   ```python
   python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> from rest_framework.authtoken.models import Token
   >>> User = get_user_model()
   >>> user = User.objects.get(username='your_username')
   >>> token = Token.objects.create(user=user)
   >>> print(token.key)
   >>> exit()
   ```

## 🖥️ Running the Server

### Development Server (HTTP)
```bash
python manage.py runserver
```
Server will be available at: `http://127.0.0.1:8000`

### HTTPS Server (with SSL certificates)
```bash
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
```
Server will be available at: `https://127.0.0.1:8000`

**Note:** For HTTPS with self-signed certificates, you'll need to:
- Accept the security warning in your browser
- Disable SSL verification if using Postman or API clients

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
- `POST /posts/authenticate/` - Authenticate user (returns success message)

### Users
- `GET /posts/users/` - List all users (Token auth required)
- `POST /posts/users/` - Create new user (Token auth required)
- `GET /posts/users/me/` - Get current user profile (Token auth required)

### Posts
- `GET /posts/` - List all posts (Token auth required)
- `POST /posts/` - Create post via serializer (Token auth required)
- `POST /posts/create/` - Create post via Factory Pattern (Token auth required)
- `GET /posts/{id}/` - Get post detail with like_count & comment_count (Token auth required)

### News Feed
- `GET /posts/feed/` - Get paginated news feed (newest posts first) (Token auth required)

### Likes
- `POST /posts/{id}/like/` - Like a post (Token auth required)
- `DELETE /posts/{id}/like/` - Unlike a post (Token auth required)

### Comments
- `POST /posts/{id}/comment/` - Add a comment to a post (Token auth required)
- `GET /posts/{id}/comments/` - Get all comments for a post, paginated (Token auth required)
- `GET /posts/comments/` - List all comments (Token auth required)
- `POST /posts/comments/` - Create comment (Token auth required)

### OAuth
- `/accounts/*` - Django-allauth endpoints for Google OAuth
## 📊 Models & Database

### User Model (Custom)
Extends Django's `AbstractUser`:
- `username` - Unique username
- `email` - Email address
- `password` - Hashed password
- `created_at` - Timestamp
- All default Django user fields

### Post Model
- `title` - Post title (max 255 chars)
- `content` - Post content (text)
- `post_type` - Choice: 'text', 'image', 'video'
- `metadata` - JSON field for type-specific data
- `author` - ForeignKey to User
- `created_at` - Timestamp
- Properties: `like_count`, `comment_count`

### Comment Model
- `text` - Comment content
- `author` - ForeignKey to User
- `post` - ForeignKey to Post
- `created_at` - Timestamp
- Ordering: Newest first

### Like Model
- `user` - ForeignKey to User
- `post` - ForeignKey to Post
- `created_at` - Timestamp
- Unique constraint: (`user`, `post`) - prevents duplicate likes

## 🧪 Testing

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
