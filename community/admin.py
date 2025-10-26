# community/admin.py

from django.contrib import admin
from .models import Post, Reply # <-- Import model Post dan Reply

# Daftarkan model Post ke admin
admin.site.register(Post)

# Daftarkan model Reply ke admin
admin.site.register(Reply)