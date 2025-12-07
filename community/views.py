import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseNotAllowed, HttpResponseForbidden, JsonResponse
from .models import Post, Reply
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateformat import format
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import pytz

# --- HELPER FUNCTION: Format tanggal ke WIB ---
def format_datetime_wib(dt):
    """Convert datetime ke WIB (GMT+8) dan format ke string"""
    wib = pytz.timezone('Asia/Jakarta')  # WIB timezone
    dt_wib = dt.astimezone(wib)
    return format(dt_wib, "d M Y, H:i")

# View UTAMA (Updated for Flutter JSON Support)
@login_required
@csrf_exempt
def community_index(request):
    if request.method == "POST":
        # Logic untuk menangani input dari JSON (Flutter) atau Form (Website)
        try:
            data = json.loads(request.body)
            # Input dari Flutter (JSON)
            title = data.get('title')
            description = data.get('description')
            image_url = data.get('image_url')
            is_json = True
        except:
            # Input dari Website (Form Data)
            title = request.POST.get('title')
            description = request.POST.get('description')
            image_url = request.POST.get('image_url')
            is_json = False

        if title and description:
            post = Post.objects.create(
                author=request.user, 
                title=title, 
                description=description,
                image_url=image_url,          
            )
            
            # Jika request JSON (Flutter), kembalikan response JSON
            if is_json or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    "status": "success", 
                    "message": "Post berhasil dibuat!",
                    "id": post.id
                })
                
            return redirect('community:community_home') 
        else:
            if is_json or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({"status": "error", "message": "Title dan Description harus diisi!"}, status=400)

    posts = Post.objects.all().order_by('-created_at')
    # Ambil hanya reply top-level untuk halaman utama
    for post in posts:
        post.top_level_replies = post.replies.filter(parent=None).order_by('created_at')

    return render(request, 'community/index.html', {'posts': posts})

# --- VIEW ADD_REPLY (Updated for Flutter JSON Support) ---
@login_required
@require_POST
@csrf_exempt 
def add_reply(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Logic Handle input JSON vs Form
    try:
        data = json.loads(request.body)
        content = data.get('content')
    except:
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

        return JsonResponse({
            'success': True,
            'message': 'Balasan terkirim!',
            'reply': {
                'id': reply.id,
                'author_username': reply.author.username,
                'content': reply.content,
                'created_at': format_datetime_wib(reply.created_at),
                'parent_id': None,
                'post_id': post.id,
                'new_reply_url': reverse('community:add_nested_reply', args=[reply.id])
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# --- VIEW ADD_NESTED_REPLY (Updated for Flutter JSON Support) ---
@login_required
@require_POST
@csrf_exempt
def add_nested_reply(request, reply_id):
    parent_reply = get_object_or_404(Reply, id=reply_id)
    post = parent_reply.post
    
    # Logic Handle input JSON vs Form
    try:
        data = json.loads(request.body)
        content = data.get('content')
    except:
        content = request.POST.get('content') 

    if not content:
        return JsonResponse({'success': False, 'message': 'Balasan tidak boleh kosong.'}, status=400)

    try:
        reply = Reply.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent=parent_reply  # Tautkan ke induknya
        )

        return JsonResponse({
            'success': True,
            'message': 'Balasan terkirim!',
            'reply': {
                'id': reply.id,
                'author_username': reply.author.username,
                'content': reply.content,
                'created_at': format_datetime_wib(reply.created_at),
                'parent_id': parent_reply.id,
                'post_id': post.id,
                'new_reply_url': reverse('community:add_nested_reply', args=[reply.id])
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# --- VIEW EDIT POST (Tetap sama, karena sudah JSON aware) ---
@login_required
@require_POST
@csrf_exempt
def edit_post(request, post_id):
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

# --- VIEW DELETE POST (Updated JSON response for Flutter) ---
@login_required
@csrf_exempt
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return HttpResponseForbidden("You are not allowed to delete this post.")
    
    if request.method == "POST":
        post.delete()
        # Jika dari web, redirect. Jika dari Flutter/JSON, return success.
        # Kita cek header atau body, tapi simple-nya kita redirect aja buat web
        # Flutter biasanya handle redirect sebagai sukses, atau bisa kita tambah logic:
        # if request.headers.get('Content-Type') == 'application/json': ...
        return redirect('community:community_home')
        
    return HttpResponseNotAllowed(['POST'])

# --- VIEW Show JSON (NEW) ---
def show_json(request):
    posts = Post.objects.all().order_by('-created_at')
    data = []
    for post in posts:
        data.append({
            "id": post.id,
            "author_username": post.author.username,
            "title": post.title,
            "description": post.description,
            "image_url": post.image_url,
            "created_at": post.created_at.isoformat() if post.created_at else None,
        })
    return JsonResponse(data, safe=False)

# --- VIEW Show JSON by ID (NEW) ---
def show_json_by_id(request, id):
    post = get_object_or_404(Post, id=id)
    data = {
        "id": post.id,
        "author_username": post.author.username,
        "title": post.title,
        "description": post.description,
        "image_url": post.image_url,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }
# --- VIEW ADD POST (Separated for clarity/URL match) ---
@login_required
@csrf_exempt
def add_post(request):
    if request.method == 'POST':
        form_data = request.POST
        title = form_data.get('title')
        description = form_data.get('description')
        image_url = form_data.get('image_url')

        if title and description:
            post = Post.objects.create(
                author=request.user,
                title=title,
                description=description,
                image_url=image_url,
            )
            return redirect('community:community_home')
        return HttpResponseForbidden("Title and Description are required")

    return render(request, 'community/add_post.html') # Assuming a template exists or just for structure

# --- FLUTTER SPECIFIC VIEWS (Missing in original) ---

@csrf_exempt
def add_post_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_post = Post.objects.create(
                author=request.user,
                title=data["title"],
                description=data["description"],
                image_url=data.get("image_url", ""), # Handle potential missing image
            )
            return JsonResponse({"status": "success", "message": "Post added successfully!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)


@csrf_exempt
def edit_post_flutter(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Verify ownership if needed, but for now trusting the flutter logic or adding check
            if post.author != request.user:
                 return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

            post.title = data.get("title", post.title)
            post.description = data.get("description", post.description)
            post.image_url = data.get("image_url", post.image_url)
            post.save()
            return JsonResponse({"status": "success", "message": "Post updated!"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)


@csrf_exempt
def delete_post_flutter(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST': # Flutter might use POST for delete
        if post.author != request.user:
             return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)
        post.delete()
        return JsonResponse({"status": "success", "message": "Post deleted!"}, status=200)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

@csrf_exempt
def add_reply_flutter(request, post_id):
    print(f"DEBUG: add_reply_flutter called for post_id {post_id}") # DEBUG
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
         try:
            if not request.user.is_authenticated:
                print("DEBUG: User is NOT authenticated") # DEBUG
                return JsonResponse({"status": "error", "message": "User not authenticated"}, status=401)
            
            data = json.loads(request.body)
            print(f"DEBUG: Received data: {data}") # DEBUG
            
            Reply.objects.create(
                author=request.user, 
                post=post,
                content=data['content'],
                parent=None
            )
            print("DEBUG: Reply created successfully") # DEBUG
            return JsonResponse({"status": "success", "message": "Reply added!"}, status=200)
         except Exception as e:
            print(f"DEBUG: Error in add_reply_flutter: {e}") # DEBUG
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

@csrf_exempt
def add_nested_reply_flutter(request, reply_id):
    print(f"DEBUG: add_nested_reply_flutter called for reply_id {reply_id}") # DEBUG
    parent = get_object_or_404(Reply, id=reply_id)
    if request.method == 'POST':
         try:
            if not request.user.is_authenticated:
                 print("DEBUG: User is NOT authenticated") # DEBUG
                 return JsonResponse({"status": "error", "message": "User not authenticated"}, status=401)

            data = json.loads(request.body)
            print(f"DEBUG: Received data: {data}") # DEBUG
            
            Reply.objects.create(
                author=request.user,
                post=parent.post,
                content=data['content'],
                parent=parent
            )
            print("DEBUG: Nested reply created successfully") # DEBUG
            return JsonResponse({"status": "success", "message": "Nested reply added!"}, status=200)
         except Exception as e:
            print(f"DEBUG: Error in add_nested_reply_flutter: {e}") # DEBUG
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=401)

def show_json_flutter(request):
    data = Post.objects.all().order_by('-created_at')
    # Use existing show_json logic or custom serializer
    return show_json(request)

def show_json_by_id_flutter(request, id):
    return show_json_by_id(request, id)

def serialize_reply_tree(reply):
    """Helper recursive untuk serialize reply beserta child-nya"""
    return {
        "id": reply.id,
        "author": reply.author.username,
        "content": reply.content,
        "created_at": reply.created_at.isoformat(),
        "parent_id": reply.parent.id if reply.parent else None,
        "replies": [serialize_reply_tree(child) for child in reply.child_replies.all().order_by('created_at')]
    }

def show_replies_json_flutter(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Ambil hanya top-level replies, tapi serialize secara rekursif sampai ke cucu-cucunya
    replies = Reply.objects.filter(post=post, parent=None).order_by('created_at')
    data = [serialize_reply_tree(reply) for reply in replies]
    return JsonResponse(data, safe=False)

def show_nested_replies_json_flutter(request, reply_id):
    # Endpoint ini mungkin jadi redundant kalau pakai tree, 
    # tapi tetap kita sediakan dengan format tree juga untuk konsistensi
    reply = get_object_or_404(Reply, id=reply_id)
    nested = reply.child_replies.all().order_by('created_at')
    data = [serialize_reply_tree(r) for r in nested]
    return JsonResponse(data, safe=False)

