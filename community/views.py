# community/views.py

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseNotAllowed, HttpResponseForbidden, JsonResponse 
from .models import Post, Reply
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# --- TAMBAHKAN IMPORT INI UNTUK FORMAT TANGGAL ---
from django.utils.dateformat import format
from django.urls import reverse
# -----------------------------------------------

# View UTAMA (Tetap sama)
@login_required
def community_index(request):
    if request.method == "POST":
        # ... (logika buat post baru tetap sama) ...
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
    # Ambil hanya reply top-level untuk halaman utama
    for post in posts:
        post.top_level_replies = post.replies.filter(parent=None).order_by('created_at')

    return render(request, 'community/index.html', {'posts': posts})


# --- VIEW ADD_REPLY (DIUBAH JADI AJAX) ---
@login_required
@require_POST
def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content') 

    if not content:
        return JsonResponse({'success': False, 'message': 'Balasan tidak boleh kosong.'}, status=400)

    try:
        reply = Reply.objects.create(
            post=post, 
            author=request.user, 
            content=content,
            parent=None  # Ini adalah balasan top-level
        )

        # Kembalikan data reply baru dalam format JSON
        return JsonResponse({
            'success': True,
            'message': 'Balasan terkirim!',
            'reply': {
                'id': reply.id,
                'author_username': reply.author.username,
                'content': reply.content,
                'created_at': format(reply.created_at, "d M Y, H:i"),
                'parent_id': None,
                'post_id': post.id,
                # URL untuk membalas reply BARU ini
                'new_reply_url': reverse('community:add_nested_reply', args=[reply.id])
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# --- VIEW ADD_NESTED_REPLY (DIUBAH JADI AJAX) ---
@login_required
@require_POST
def add_nested_reply(request, reply_id):
    parent_reply = get_object_or_404(Reply, id=reply_id)
    post = parent_reply.post
    content = request.POST.get('content') 

    if not content:
        return JsonResponse({'success': False, 'message': 'Balasan tidak boleh kosong.'}, status=400)

    try:
        reply = Reply.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent=parent_reply # Tautkan ke induknya
        )

        # Kembalikan data reply baru dalam format JSON
        return JsonResponse({
            'success': True,
            'message': 'Balasan terkirim!',
            'reply': {
                'id': reply.id,
                'author_username': reply.author.username,
                'content': reply.content,
                'created_at': format(reply.created_at, "d M Y, H:i"),
                'parent_id': parent_reply.id, # ID induknya
                'post_id': post.id,
                # URL untuk membalas reply BARU ini
                'new_reply_url': reverse('community:add_nested_reply', args=[reply.id])
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# --- VIEW EDIT POST (Tetap sama, versi AJAX) ---
@login_required
@require_POST
def edit_post(request, post_id):
    # ... (Logika edit_post AJAX kamu tetap sama) ...
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to edit this post.")
    try:
        data = json.loads(request.body)
        post.title = data.get('title', post.title)
        post.description = data.get('description', post.description)
        post.image_url = data.get('image_url', post.image_url)
        post.save()
        return JsonResponse({
            'success': True, 'message': 'Post berhasil diupdate!',
            'post': {
                'id': post.id, 'title': post.title,
                'description': post.description, 'image_url': post.image_url,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# --- VIEW DELETE POST (Tetap sama) ---
@login_required
def delete_post(request, post_id):
    # ... (Logika delete_post kamu tetap sama) ...
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this post.")
    if request.method == "POST":
        post.delete()
        return redirect('community:community_home')
    return HttpResponseNotAllowed(['POST'])