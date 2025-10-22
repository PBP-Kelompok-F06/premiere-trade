# community/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseNotAllowed
from .models import Post, Reply
from django.contrib.auth.decorators import login_required

# Ini view UTAMA untuk /community/
# Dia nanganin GET (nampilin) dan POST (bikin forum baru)
@login_required
def community_index(request):
    if request.method == "POST":
        title = request.POST.get('title')
        # Ini 'description' (udah bener ngebaca form HTML)
        description = request.POST.get('description') 
        # Ini 'image' (udah bener ngebaca form HTML)
        image_url = request.POST.get('image_url')

        if title and description:
            Post.objects.create(
                author=request.user, 
                title=title, 
                description=description,
                image_url=image_url,          
            )
            return redirect('community:community_home') 

    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'community/index.html', {'posts': posts})

@login_required
def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        content = request.POST.get('content') # Ambil 'content' dari form reply
        
        if content:
            Reply.objects.create(
                post=post, 
                author=request.user, 
                content=content
            )
        # Balikin ke halaman forum
        return redirect('community:community_home')
    
    return HttpResponseNotAllowed(['POST'])

# Hapus view 'forum_home' dan 'add_post' yang lama karena sudah digabung