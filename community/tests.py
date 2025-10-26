# community/tests.py
# VERSI PERBAIKAN (MENDUKUNG AJAX)

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post, Reply
import json

User = get_user_model()

# --- PostModelTest & ReplyModelTest sudah benar ---
class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(
            author=self.user, title='Test Post', description='This is a test post description')
    
    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Test Post')
    
    def test_post_str_method(self):
        self.assertEqual(str(self.post), 'Test Post')

class ReplyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(author=self.user, title='Test Post', description='Test description')
        self.reply = Reply.objects.create(post=self.post, author=self.user, content='This is a test reply')
    
    def test_reply_creation(self):
        self.assertEqual(self.reply.content, 'This is a test reply')
    
    def test_reply_str_method(self):
        expected = f'Reply by {self.user} on {self.post.title}'
        self.assertEqual(str(self.reply), expected)
    
    # Tes untuk model nested reply
    def test_nested_reply_str(self):
        nested = Reply.objects.create(post=self.post, author=self.user, content='nested', parent=self.reply)
        expected = f'Reply by {self.user} on {self.reply.author}\'s comment'
        self.assertEqual(str(nested), expected)
    
    def test_nested_reply_relationship(self):
        nested = Reply.objects.create(post=self.post, author=self.user, content='nested', parent=self.reply)
        self.assertEqual(self.reply.child_replies.count(), 1)
        self.assertEqual(nested.parent, self.reply)


# --- CommunityViewsTest sudah benar ---
class CommunityViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.post = Post.objects.create(author=self.user1, title='User1 Post', description='This is user1 post')
    
    def test_community_index_requires_login(self):
        response = self.client.get(reverse('community:community_home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_community_index_displays_posts(self):
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('community:community_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User1 Post')
    
    def test_create_post_via_form(self):
        self.client.login(username='user1', password='pass123')
        post_data = {'title': 'New Test Post', 'description': 'This is a new test post'}
        response = self.client.post(reverse('community:community_home'), data=post_data)
        self.assertEqual(response.status_code, 302) # Buat post tetap redirect
        self.assertTrue(Post.objects.filter(title='New Test Post').exists())


# ==== PERBAIKAN BESAR DI SINI ====

class AddReplyViewTest(TestCase):
    """Test cases untuk add_reply view (VERSI AJAX)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(author=self.user, title='Test Post', description='Test')
    
    def test_add_reply_requires_login(self):
        url = reverse('community:add_reply', args=[self.post.id])
        response = self.client.post(url, {'content': 'Test reply'})
        self.assertEqual(response.status_code, 302) # Redirect ke login
    
    def test_add_reply_success_ajax(self):
        """Test menambahkan reply (AJAX) berhasil"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_reply', args=[self.post.id])
        
        response = self.client.post(url, {'content': 'Great post!'})
        
        # 1. HARUSNYA 200 (BUKAN 302)
        self.assertEqual(response.status_code, 200)
        
        # 2. Cek apakah reply dibuat
        self.assertEqual(Reply.objects.count(), 1)
        reply = Reply.objects.first()
        self.assertEqual(reply.content, 'Great post!')
        self.assertIsNone(reply.parent) # Pastikan ini top-level
        
        # 3. Cek konten JSON
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['reply']['content'], 'Great post!')
        self.assertIsNone(data['reply']['parent_id'])
    
    def test_add_reply_empty_content_ajax(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_reply', args=[self.post.id])
        response = self.client.post(url, {'content': ''})
        
        self.assertEqual(response.status_code, 400) # Bad Request
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(Reply.objects.count(), 0)

# ==== TES BARU UNTUK NESTED REPLY ====
class AddNestedReplyViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.post = Post.objects.create(author=self.user, title='Test Post')
        self.parent_reply = Reply.objects.create(
            post=self.post, author=self.user, content='Parent Reply'
        )
    
    def test_add_nested_reply_success_ajax(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_nested_reply', args=[self.parent_reply.id])
        response = self.client.post(url, {'content': 'Nested Reply'})
        
        self.assertEqual(response.status_code, 200) # Cek 200 OK
        
        # Cek reply dibuat
        self.assertEqual(Reply.objects.count(), 2)
        nested = Reply.objects.get(content='Nested Reply')
        self.assertEqual(nested.parent, self.parent_reply) # Cek parent-nya
        
        # Cek JSON
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['reply']['parent_id'], self.parent_reply.id)

    def test_add_nested_reply_invalid_parent(self):
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_nested_reply', args=[999]) # ID 999 tidak ada
        response = self.client.post(url, {'content': 'Nested Reply'})
        self.assertEqual(response.status_code, 404) # Not Found
        self.assertEqual(Reply.objects.count(), 1)


# --- EditPostViewTest & DeletePostViewTest sudah benar ---
class EditPostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass456')
        self.post = Post.objects.create(
            author=self.user1, title='Original Title', description='Original Description')
    
    def test_edit_own_post_success(self):
        self.client.login(username='user1', password='pass123')
        url = reverse('community:edit_post', args=[self.post.id])
        new_data = {'title': 'Updated Title', 'description': 'Updated Description'}
        response = self.client.post(
            url, data=json.dumps(new_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')
    
    def test_edit_others_post_forbidden(self):
        self.client.login(username='user2', password='pass456')
        url = reverse('community:edit_post', args=[self.post.id])
        new_data = {'title': 'Hacked Title'}
        response = self.client.post(
            url, data=json.dumps(new_data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

class DeletePostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass456')
        self.post = Post.objects.create(author=self.user1, title='Post to Delete')
    
    def test_delete_own_post_success(self):
        self.client.login(username='user1', password='pass123')
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
    
    def test_delete_others_post_forbidden(self):
        self.client.login(username='user2', password='pass456')
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

# ==== PERBAIKAN PADA INTEGRATION TEST ====
class IntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='integrationuser', password='integpass123')
    
    def test_full_post_lifecycle(self):
        self.client.login(username='integrationuser', password='integpass123')
        
        # 2. Buat post
        response = self.client.post(
            reverse('community:community_home'),
            {'title': 'Integration Test Post', 'description': 'Testing full lifecycle'}
        )
        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(title='Integration Test Post')
        
        # 3. Tambah reply (AJAX)
        response = self.client.post(
            reverse('community:add_reply', args=[post.id]),
            {'content': 'First reply'}
        )
        # HARUSNYA 200 (BUKAN 302)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.replies.count(), 1)
        
        # 4. Edit post (AJAX)
        response = self.client.post(
            reverse('community:edit_post', args=[post.id]),
            data=json.dumps({'title': 'Edited Title', 'description': 'Edited Description'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Edited Title')
        
        # 5. Delete post
        response = self.client.post(reverse('community:delete_post', args=[post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=post.id).exists())