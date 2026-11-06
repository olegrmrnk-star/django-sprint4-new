from django.contrib import admin

from .models import Category, Comment, Location, Post


admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Location)
