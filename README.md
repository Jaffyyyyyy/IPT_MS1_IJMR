# Connectly Project - Django REST API

A Django REST Framework API with Token Authentication, Factory Pattern, Singleton design patterns, and User Interaction features (Likes & Comments).

> **🤖 AI Disclosure:** This project was developed with assistance from Claude Sonnet 4.5 (Anthropic AI). AI was used for debugging, testing, and documentation.

## ✨ NEW FEATURES

### User Interactions (v2.0)
- ✅ **Like/Unlike Posts** - Users can like and unlike posts
- ✅ **Comment on Posts** - Add comments to posts with validation
- ✅ **Paginated Comments** - Efficient retrieval of large comment datasets
- ✅ **Like & Comment Counts** - Real-time counts on post details
- ✅ **Duplicate Prevention** - Users can only like a post once

📚 **See [LIKES_COMMENTS_API.md](LIKES_COMMENTS_API.md) for full documentation**

## 🚀 Quick Setup for Your Peers

### Prerequisites
- Python 3.8+ installed
- Git installed
- Postman (for API testing)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd IPT_MS1_IJMR
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
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Generate authentication token:**
   ```bash
   python create_token.py
   ```
   Copy the displayed token - you'll need it for Postman.

6. **Start the HTTPS server:**
   ```bash
   python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
   ```
   
   Server will run at: `https://127.0.0.1:8000`

## 📮 Postman Setup

1. **Import the collection:**
   - Open Postman
   - Click "Import" → Select `connectly_project/Connectly_API.postman_collection.json`

2. **Configure SSL for self-signed certificates:**
   - Go to Settings (⚙️) → General
   - Turn **OFF** "SSL certificate verification"

3. **Update the token (if needed):**
   - Click "Connectly API" collection → Variables tab
   - The `auth_token` should already be set to: `8162911afba3fc49964ecfd83802c92d1b2d376d`
   - If you generated a new token, paste it here

4. **Test the API:**
   - Start with "Authenticate User" request to verify everything works
   - All 22 requests are ready to test

## 📁 Project Structure

```
connectly_project/
├── manage.py                 # Django management script
├── create_token.py          # Token generation utility
├── db.sqlite3              # SQLite database
├── cert.pem / key.pem      # SSL certificates for HTTPS
├── requirements.txt        # Python dependencies
├── Connectly_API.postman_collection.json  # Postman test collection
├── connectly_project/      # Main Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── posts/                  # Main app
│   ├── models.py          # User, Post, Comment models
│   ├── views.py           # API views
│   ├── serializers.py     # DRF serializers
│   ├── permissions.py     # Custom permissions
│   ├── urls.py            # URL routing
│   └── tests.py           # Unit tests
├── factories/             # Factory Pattern implementation
│   └── post_factory.py   # PostFactory for creating posts
└── singletons/           # Singleton Pattern implementation
    ├── config_manager.py  # Configuration singleton
    └── logger_singleton.py # Logger singleton
```

## 🎯 Design Patterns Implemented

### 1. Factory Pattern (`factories/post_factory.py`)
Creates posts with type-specific validation:
- **Text posts**: Default type
- **Image posts**: Requires `file_size` in metadata
- **Video posts**: Requires `duration` in metadata

### 2. Singleton Pattern
- **LoggerSingleton** (`singletons/logger_singleton.py`): Single logger instance across the app
- **ConfigManager** (`singletons/config_manager.py`): Centralized configuration management

## 🔐 API Endpoints

All authenticated endpoints require: `Authorization: Token <your-token>`

### Authentication (No auth required)
- `POST /posts/authenticate/` - Authenticate user

### Users (Token auth required)
- `GET /posts/users/` - List all users
- `POST /posts/users/` - Create new user

### Posts (Token auth required)
- `GET /posts/` - List all posts
- `POST /posts/` - Create post (via serializer)
- `GET /posts/{id}/` - Get post detail (with like_count & comment_count)
- `POST /posts/create/` - Create post (via Factory Pattern)

### User Interactions - NEW! 🎉 (Token auth required)
- `POST /posts/{id}/like/` - Like a post
- `DELETE /posts/{id}/like/` - Unlike a post
- `POST /posts/{id}/comment/` - Add a comment to a post
- `GET /posts/{id}/comments/` - Get all comments for a post (paginated)

### Comments (Token auth required)
- `GET /posts/comments/` - List all comments
- `POST /posts/comments/` - Create comment



## 📝 Environment Variables

Key settings in `connectly_project/settings.py`:
- `DEBUG = True` - Development mode
- `ALLOWED_HOSTS = ['127.0.0.1', 'localhost']`
- Database: SQLite (included in repo)

## 🔧 Troubleshooting

### Issue: "SSL certificate verification" error in Postman
**Solution:** Disable SSL verification in Postman Settings → General

### Issue: "Port 8000 already in use"
**Solution:** 
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Mac/Linux
lsof -ti:8000 | xargs kill
```

### Issue: Token not working
**Solution:** Regenerate token:
```bash
python create_token.py
```
Update the token in Postman collection variables.

### Issue: Module not found
**Solution:** Ensure virtual environment is activated and dependencies installed:
```bash
pip install -r requirements.txt
```

## 👥 Default Test User

- **Username:** testuser
- **Password:** secure_pass123
- **Token:** 862bff975353833c417ef008836d063aab3f9f30
- **User ID:** 1

## 📚 Technologies Used

- Django 6.0.2
- Django REST Framework 3.16.1
- djangorestframework-simplejwt 5.5.1
- django-extensions 4.1
- Werkzeug 3.1.5 (for HTTPS server)
- pyOpenSSL 25.3.0 (for SSL support)

## 🤖 AI Development Acknowledgment

This project was developed with significant assistance from **Claude Sonnet 4.5** (Anthropic). The AI assisted with:

- **Testing**: Creating comprehensive unit tests and 84 Postman API tests including edge cases
- **Debugging**: Resolving SSL redirect issues, validation logic, and pagination errors
- **Documentation**: Writing this README and API documentation
- **Best Practices**: Ensuring Django/DRF conventions and security practices

All code was MANUALLY reviewed, tested, and validated to ensure functionality and understanding.

## 📄 License

Educational project for IPT coursework.

## 🤝 Contributing

This is a coursework project. For peer review:
1. Clone the repository
2. Follow setup instructions above
3. Test all Postman requests
4. Report any issues

---

**Note:** The `env/` folder is NOT included in the repository (it's in `.gitignore`). Each user must create their own virtual environment as shown in the setup instructions.
