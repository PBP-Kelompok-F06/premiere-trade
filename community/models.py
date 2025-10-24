# community/models.py

from django.db import models
from django.conf import settings  

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField() 
    image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Reply(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # --- PERUBAHAN UTAMA DI SINI ---
    # Menambahkan 'parent' yang menunjuk ke Reply lain.
    # 'null=True' berarti ini adalah balasan level atas (top-level).
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='child_replies'
    )
    # --------------------------------

    def __str__(self):
        # Memperbarui __str__ agar lebih deskriptif
        if self.parent:
            return f'Reply by {self.author} to {self.parent.author} on {self.post.title}'
        return f'Reply by {self.author} on {self.post.title}'