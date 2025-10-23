# community/views.py

from django.shortcuts import render, get_object_or_404, redirect
# Tambahin import ini
from django.http import HttpResponseNotAllowed, HttpResponseForbidden 
from .models import Post, Reply
from django.contrib.auth.decorators import login_required

# View UTAMA untuk /community/
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
            # Redirect ke halaman ini lagi setelah sukses
            return redirect('community:community_home') 

    # Tampilkan semua post
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'community/index.html', {'posts': posts})

# View untuk nambah reply (udah bener)
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

# --- VIEW BARU UNTUK EDIT POST ---
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Cek Kepemilikan: Cuma author yang boleh edit
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == "POST":
        # Ambil data baru dari form
        post.title = request.POST.get('title', post.title)
        post.description = request.POST.get('description', post.description)
        post.image_url = request.POST.get('image_url', post.image_url)
        
        # Simpan perubahan
        post.save()
        # Balik ke halaman forum
        return redirect('community:community_home')
    
    # Kalau method GET: Tampilkan form edit yang udah diisi data lama
    context = {'post': post}
    # Kita perlu bikin template baru: 'community/edit_post.html'
    return render(request, 'community/edit_post.html', context)

# --- VIEW BARU UNTUK DELETE POST ---
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Cek Kepemilikan: Cuma author yang boleh delete
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    # Hapus hanya jika method POST (lebih aman)
    if request.method == "POST":
        post.delete()
        # Balik ke halaman forum
        return redirect('community:community_home')
    
    # Kalau bukan POST, tolak
    return HttpResponseNotAllowed(['POST'])