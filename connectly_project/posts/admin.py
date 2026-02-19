from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Comment, Like

# Register custom User model with Django admin
admin.site.register(User, UserAdmin)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
