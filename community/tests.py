# community/tests.py
# FOKUS HANYA PADA APP COMMUNITY

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

# Import model dari app community
from .models import Post, Reply

# Import model dari app LAIN yang DIBUTUHKAN untuk setup
# Kita butuh Profile agar user-nya "valid"
from accounts.models import Profile 

User = get_user_model()

class PostModelTest(TestCase):
    """Test cases untuk model Post"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            description='This is a test post description',
            image_url='https://example.com/image.jpg'
        )
    
    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.author, self.user)
    
    def test_post_str_method(self):
        self.assertEqual(str(self.post), 'Test Post')


class ReplyModelTest(TestCase):
    """Test cases untuk model Reply"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # FIX: Buat Profile manual untuk user, agar tidak error
        Profile.objects.create(user=self.user)
        
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            description='Test description'
        )
        self.reply = Reply.objects.create(
            post=self.post,
            author=self.user,
            content='This is a test reply'
        )
    
    def test_reply_creation(self):
        self.assertEqual(self.reply.content, 'This is a test reply')
        self.assertEqual(self.reply.post, self.post)
    
    def test_reply_str_method(self):
        expected = f'Reply by {self.user} on {self.post.title}'
        self.assertEqual(str(self.reply), expected)
    
    def test_nested_reply_str(self):
        """Tes __str__ untuk nested reply"""
        nested = Reply.objects.create(
            post=self.post, 
            author=self.user, 
            content='nested', 
            parent=self.reply
        )
        expected = f'Reply by {self.user} on {self.reply.author}\'s comment'
        self.assertEqual(str(nested), expected)
    
    def test_nested_reply_relationship_and_methods(self):
        """Tes relasi parent-child dan helper methods"""
        nested = Reply.objects.create(
            post=self.post, 
            author=self.user, 
            content='nested', 
            parent=self.reply
        )
        self.assertEqual(self.reply.child_replies.count(), 1)
        self.assertEqual(nested.parent, self.reply)
        
        # Tes helper methods dari models.py
        self.assertTrue(self.reply.is_top_level())
        self.assertFalse(nested.is_top_level())
        self.assertEqual(self.reply.get_nested_replies().first(), nested)


class CommunityViewsTest(TestCase):
    """Test cases untuk views umum di community app"""
    
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        # FIX: Buat Profile manual untuk user
        Profile.objects.create(user=self.user1)
        
        self.post = Post.objects.create(
            author=self.user1,
            title='User1 Post',
            description='This is user1 post'
        )
    
    def test_community_index_requires_login(self):
        """Tes view /community/ butuh login"""
        response = self.client.get(reverse('community:community_home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_community_index_displays_posts_and_replies(self):
        """Tes halaman community menampilkan post dan top-level replies"""
        self.client.login(username='user1', password='pass123')
        
        top_reply = Reply.objects.create(post=self.post, author=self.user1, content='Top Reply')
        Reply.objects.create(post=self.post, author=self.user1, content='Nested Reply', parent=top_reply)
        
        response = self.client.get(reverse('community:community_home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User1 Post')
        self.assertContains(response, 'Top Reply')
        
        # FIX: 'Nested Reply' MEMANG AKAN ADA di HTML
        # karena di-render oleh _reply.html secara rekursif.
        # Menghapus assertNotContains akan memperbaiki FAILED test.
        self.assertContains(response, 'Nested Reply')
        
        # Cek konteks 'top_level_replies' di view sudah benar
        post_in_context = response.context['posts'][0]
        self.assertEqual(post_in_context.top_level_replies.count(), 1)
        self.assertEqual(post_in_context.top_level_replies.first().content, 'Top Reply')
    
    def test_create_post_via_form(self):
        """Tes buat post baru (non-AJAX)"""
        self.client.login(username='user1', password='pass123')
        post_data = {
            'title': 'New Test Post',
            'description': 'This is a new test post',
        }
        response = self.client.post(
            reverse('community:community_home'),
            data=post_data
        )
        self.assertEqual(response.status_code, 302) # Buat post tetap redirect
        self.assertTrue(Post.objects.filter(title='New Test Post').exists())


class AddReplyViewTest(TestCase):
    """Test cases untuk add_reply view (AJAX)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # FIX: Buat Profile manual untuk user
        Profile.objects.create(user=self.user)
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            description='Test'
        )
    
    def test_add_reply_requires_login(self):
        url = reverse('community:add_reply', args=[self.post.id])
        response = self.client.post(url, {'content': 'Test reply'})
        self.assertEqual(response.status_code, 302) # Belum login, redirect
    
    def test_add_reply_success_ajax(self):
        """Tes menambahkan reply (AJAX) berhasil"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('community:add_reply', args=[self.post.id])
        response = self.client.post(url, {'content': 'Great post!'})
        
        # 1. HARUSNYA 200 OK (BUKAN 302)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Reply.objects.count(), 1)
        reply = Reply.objects.first()
        self.assertEqual(reply.content, 'Great post!')
        self.assertIsNone(reply.parent) # Pastikan ini top-level
        
        # 3. Cek konten JSON
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['reply']['content'], 'Great post!')
        self.assertIsNone(data['reply']['parent_id'])
    
    def test_add_reply_invalid_post(self):
        """Tes reply ke post ID 999 (404)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_reply', args=[9999])
        response = self.client.post(url, {'content': 'Test'})
        self.assertEqual(response.status_code, 404)

    def test_add_reply_empty_content_ajax(self):
        """Tes add reply dengan konten kosong (400)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_reply', args=[self.post.id])
        response = self.client.post(url, {'content': ''}) # Konten kosong
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(Reply.objects.count(), 0)


class AddNestedReplyViewTest(TestCase):
    """Test cases untuk add_nested_reply view (AJAX)"""
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        # FIX: Buat Profile manual untuk user
        Profile.objects.create(user=self.user)
        self.post = Post.objects.create(author=self.user, title='Test Post')
        self.parent_reply = Reply.objects.create(
            post=self.post, author=self.user, content='Parent Reply'
        )
    
    def test_add_nested_reply_success_ajax(self):
        """Tes nested reply (AJAX) berhasil"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_nested_reply', args=[self.parent_reply.id])
        response = self.client.post(url, {'content': 'Nested Reply'})
        
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Reply.objects.count(), 2)
        nested = Reply.objects.get(content='Nested Reply')
        self.assertEqual(nested.parent, self.parent_reply)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['reply']['parent_id'], self.parent_reply.id)

    def test_add_nested_reply_empty_content_ajax(self):
        """Tes nested reply konten kosong (400)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_nested_reply', args=[self.parent_reply.id])
        response = self.client.post(url, {'content': ''})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Reply.objects.count(), 1) # Pastikan tidak ada reply baru

    def test_add_nested_reply_invalid_parent(self):
        """Tes nested reply ke parent ID 999 (404)"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('community:add_nested_reply', args=[999])
        response = self.client.post(url, {'content': 'Nested Reply'})
        self.assertEqual(response.status_code, 404)


class EditPostViewTest(TestCase):
    """Test cases untuk edit_post view (AJAX)"""
    
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass456')
        # FIX: Buat Profile manual untuk user
        Profile.objects.create(user=self.user1)
        Profile.objects.create(user=self.user2)
        
        self.post = Post.objects.create(
            author=self.user1, title='Original Title', description='Original Description')
    
    def test_edit_own_post_success(self):
        """Tes edit post (AJAX) berhasil"""
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
        """Tes gagal edit post orang lain (403)"""
        self.client.login(username='user2', password='pass456') # Login sebagai user2
        url = reverse('community:edit_post', args=[self.post.id])
        new_data = {'title': 'Hacked Title'}
        
        response = self.client.post(
            url, data=json.dumps(new_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 403)
    
    def test_edit_post_invalid_json(self):
        """Tes edit dengan JSON tidak valid (400)"""
        self.client.login(username='user1', password='pass123')
        url = reverse('community:edit_post', args=[self.post.id])
        response = self.client.post(
            url, data='invalid json{', content_type='application/json')
        
        self.assertEqual(response.status_code, 400)


class DeletePostViewTest(TestCase):
    """Test cases untuk delete_post view"""
    
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass456')
        # FIX: Buat Profile manual untuk user
        Profile.objects.create(user=self.user1)
        Profile.objects.create(user=self.user2)
        
        self.post = Post.objects.create(author=self.user1, title='Post to Delete')
    
    def test_delete_own_post_success(self):
        """Tes delete post (non-AJAX) berhasil"""
        self.client.login(username='user1', password='pass123')
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302) # Delete me-redirect
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
    
    def test_delete_others_post_forbidden(self):
        """Tes gagal delete post orang lain (403)"""
        self.client.login(username='user2', password='pass456')
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_delete_post_get_not_allowed(self):
        """Tes method GET di delete_post ditolak (405)"""
        self.client.login(username='user1', password='pass123')
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.get(url) # Kirim GET
        
        self.assertEqual(response.status_code, 405)


class IntegrationTest(TestCase):
    """Test cases untuk alur lengkap (integration tests)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            password='integpass123'
        )
        # FIX: Buat Profile manual untuk user
        Profile.objects.create(user=self.user)
    
    def test_full_post_lifecycle(self):
        """Test alur lengkap: buat post -> reply -> edit -> delete"""
        self.client.login(username='integrationuser', password='integpass123')
        
        # 1. Buat post
        response = self.client.post(
            reverse('community:community_home'),
            {'title': 'Integration Test Post', 'description': 'Testing full lifecycle'}
        )
        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(title='Integration Test Post')
        
        # 2. Tambah reply (AJAX)
        response = self.client.post(
            reverse('community:add_reply', args=[post.id]),
            {'content': 'First reply'}
        )
        self.assertEqual(response.status_code, 200) # Cek AJAX 200 OK
        self.assertEqual(post.replies.count(), 1)
        
        # 3. Edit post (AJAX)
        response = self.client.post(
            reverse('community:edit_post', args=[post.id]),
            data=json.dumps({'title': 'Edited Title', 'description': 'Edited Description'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Edited Title')
        
        # 4. Delete post
        response = self.client.post(reverse('community:delete_post', args=[post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=post.id).exists())