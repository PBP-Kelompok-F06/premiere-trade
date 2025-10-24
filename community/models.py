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
    
    # 🆕 FITUR BARU: Reply bisa punya parent (reply ke reply)
    parent = models.ForeignKey(
        'self',  # Self-referencing: Reply bisa nge-reply Reply lain
        on_delete=models.CASCADE,
        null=True,  # Null = ini reply langsung ke Post
        blank=True,
        related_name='child_replies'  # Untuk akses balasan dari balasan
    )

    class Meta:
        ordering = ['created_at']  # Urutkan berdasarkan waktu
        verbose_name_plural = 'Replies'

    def __str__(self):
        if self.parent:
            return f'Reply by {self.author} on {self.parent.author}\'s comment'
        return f'Reply by {self.author} on {self.post.title}'
    
    # 🆕 Helper method: Cek apakah ini top-level reply (langsung ke post)
    def is_top_level(self):
        return self.parent is None
    
    # 🆕 Helper method: Ambil semua nested replies
    def get_nested_replies(self):
        """Rekursif ambil semua child replies"""
        return self.child_replies.all()