# community/views.py

import json # <--- TAMBAHKAN IMPORT INI
from django.shortcuts import render, get_object_or_404, redirect
# Ganti HttpResponseNotAllowed dengan JsonResponse
from django.http import HttpResponseNotAllowed, HttpResponseForbidden, JsonResponse 
from .models import Post, Reply
from django.contrib.auth.decorators import login_required
# TAMBAHKAN DECORATOR INI
from django.views.decorators.http import require_POST

# View UTAMA (Tetap sama)
@login_required
def community_index(request):
    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description') 
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

# View reply (Tetap sama)
@login_required
def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        content = request.POST.get('content') 
        if content:
            Reply.objects.create(
                post=post, 
                author=request.user, 
                content=content
            )
        return redirect('community:community_home')
    return HttpResponseNotAllowed(['POST'])

# --- VIEW EDIT POST (VERSI AJAX) ---
@login_required
@require_POST  # <-- HANYA izinkan method POST
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Cek Kepemilikan
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    try:
        # Ambil data dari body request (JSON)
        data = json.loads(request.body)
        
        # Ambil data baru dari JSON
        post.title = data.get('title', post.title)
        post.description = data.get('description', post.description)
        post.image_url = data.get('image_url', post.image_url)
        
        # Simpan perubahan
        post.save()
        
        # Kembalikan data post yang sudah di-update
        return JsonResponse({
            'success': True,
            'message': 'Post berhasil diupdate!',
            'post': {
                'id': post.id,
                'title': post.title,
                'description': post.description,
                'image_url': post.image_url,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# --- VIEW DELETE POST (Tetap sama) ---
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    if request.method == "POST":
        post.delete()
        return redirect('community:community_home')
    
    return HttpResponseNotAllowed(['POST'])