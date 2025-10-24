# community/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post, Reply
import json

User = get_user_model()

class PostModelTest(TestCase):
    """Test cases untuk model Post"""
    
    def setUp(self):
        """Setup data yang dibutuhkan untuk setiap test"""
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
        """Test apakah post berhasil dibuat"""
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.description, 'This is a test post description')
        self.assertEqual(self.post.author, self.user)
        self.assertIsNotNone(self.post.created_at)
    
    def test_post_str_method(self):
        """Test __str__ method dari Post"""
        self.assertEqual(str(self.post), 'Test Post')
    
    def test_post_without_image(self):
        """Test post tanpa gambar"""
        post_no_img = Post.objects.create(
            author=self.user,
            title='Post Without Image',
            description='No image here'
        )
        self.assertIsNone(post_no_img.image_url)


class ReplyModelTest(TestCase):
    """Test cases untuk model Reply"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
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
        """Test apakah reply berhasil dibuat"""
        self.assertEqual(self.reply.content, 'This is a test reply')
        self.assertEqual(self.reply.post, self.post)
        self.assertEqual(self.reply.author, self.user)
        self.assertIsNotNone(self.reply.created_at)
    
    def test_reply_str_method(self):
        """Test __str__ method dari Reply"""
        expected = f'Reply by {self.user} on {self.post.title}'
        self.assertEqual(str(self.reply), expected)
    
    def test_reply_related_name(self):
        """Test apakah related_name 'replies' bekerja"""
        self.assertEqual(self.post.replies.count(), 1)
        self.assertEqual(self.post.replies.first(), self.reply)


class CommunityViewsTest(TestCase):
    """Test cases untuk views di community app"""
    
    def setUp(self):
        """Setup user dan client untuk testing"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass456'
        )
        self.post = Post.objects.create(
            author=self.user1,
            title='User1 Post',
            description='This is user1 post'
        )
    
    def test_community_index_requires_login(self):
        """Test apakah community index memerlukan login"""
        response = self.client.get(reverse('community:community_home'))
        # Harus redirect ke login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_community_index_displays_posts(self):
        """Test apakah halaman community menampilkan posts"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('community:community_home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User1 Post')
        self.assertContains(response, 'This is user1 post')
    
    def test_create_post_via_form(self):
        """Test membuat post baru melalui form"""
        self.client.login(username='user1', password='pass123')
        
        post_data = {
            'title': 'New Test Post',
            'description': 'This is a new test post',
            'image_url': 'https://example.com/new.jpg'
        }
        
        response = self.client.post(
            reverse('community:community_home'),
            data=post_data
        )
        
        # Harus redirect setelah berhasil
        self.assertEqual(response.status_code, 302)
        
        # Cek apakah post benar-benar dibuat
        new_post = Post.objects.filter(title='New Test Post').first()
        self.assertIsNotNone(new_post)
        self.assertEqual(new_post.description, 'This is a new test post')
        self.assertEqual(new_post.author, self.user1)
    
    def test_create_post_without_image(self):
        """Test membuat post tanpa image_url"""
        self.client.login(username='user1', password='pass123')
        
        post_data = {
            'title': 'Post Without Image',
            'description': 'No image'
        }
        
        response = self.client.post(
            reverse('community:community_home'),
            data=post_data
        )
        
        self.assertEqual(response.status_code, 302)
        new_post = Post.objects.filter(title='Post Without Image').first()
        self.assertIsNotNone(new_post)


class AddReplyViewTest(TestCase):
    """Test cases untuk add_reply view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            description='Test'
        )
    
    def test_add_reply_requires_login(self):
        """Test apakah add reply memerlukan login"""
        url = reverse('community:add_reply', args=[self.post.id])
        response = self.client.post(url, {'content': 'Test reply'})
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
    
    def test_add_reply_success(self):
        """Test menambahkan reply berhasil"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('community:add_reply', args=[self.post.id])
        response = self.client.post(url, {'content': 'Great post!'})
        
        # Harus redirect
        self.assertEqual(response.status_code, 302)
        
        # Cek apakah reply dibuat
        self.assertEqual(Reply.objects.count(), 1)
        reply = Reply.objects.first()
        self.assertEqual(reply.content, 'Great post!')
        self.assertEqual(reply.author, self.user)
        self.assertEqual(reply.post, self.post)
    
    def test_add_reply_invalid_post(self):
        """Test reply ke post yang tidak ada"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('community:add_reply', args=[9999])  # ID tidak ada
        response = self.client.post(url, {'content': 'Test'})
        
        self.assertEqual(response.status_code, 404)


class EditPostViewTest(TestCase):
    """Test cases untuk edit_post view (AJAX)"""
    
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass456'
        )
        self.post = Post.objects.create(
            author=self.user1,
            title='Original Title',
            description='Original Description',
            image_url='https://example.com/original.jpg'
        )
    
    def test_edit_post_requires_login(self):
        """Test apakah edit post memerlukan login"""
        url = reverse('community:edit_post', args=[self.post.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
    
    def test_edit_own_post_success(self):
        """Test edit post milik sendiri berhasil"""
        self.client.login(username='user1', password='pass123')
        
        url = reverse('community:edit_post', args=[self.post.id])
        new_data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'image_url': 'https://example.com/updated.jpg'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(new_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON response
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['post']['title'], 'Updated Title')
        
        # Cek di database
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')
        self.assertEqual(self.post.description, 'Updated Description')
    
    def test_edit_others_post_forbidden(self):
        """Test edit post orang lain harus ditolak"""
        self.client.login(username='user2', password='pass456')  # Login sebagai user2
        
        url = reverse('community:edit_post', args=[self.post.id])
        new_data = {
            'title': 'Hacked Title',
            'description': 'Should not work'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(new_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Pastikan data tidak berubah
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Original Title')
    
    def test_edit_post_invalid_json(self):
        """Test edit dengan JSON tidak valid"""
        self.client.login(username='user1', password='pass123')
        
        url = reverse('community:edit_post', args=[self.post.id])
        response = self.client.post(
            url,
            data='invalid json{',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class DeletePostViewTest(TestCase):
    """Test cases untuk delete_post view"""
    
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass456'
        )
        self.post = Post.objects.create(
            author=self.user1,
            title='Post to Delete',
            description='Will be deleted'
        )
    
    def test_delete_post_requires_login(self):
        """Test delete post memerlukan login"""
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        # Post harus masih ada
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())
    
    def test_delete_own_post_success(self):
        """Test delete post milik sendiri berhasil"""
        self.client.login(username='user1', password='pass123')
        
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Post harus sudah terhapus
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
    
    def test_delete_others_post_forbidden(self):
        """Test delete post orang lain ditolak"""
        self.client.login(username='user2', password='pass456')
        
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Post harus masih ada
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())
    
    def test_delete_post_with_replies(self):
        """Test delete post yang punya replies (CASCADE)"""
        self.client.login(username='user1', password='pass123')
        
        # Buat beberapa reply
        Reply.objects.create(post=self.post, author=self.user1, content='Reply 1')
        Reply.objects.create(post=self.post, author=self.user2, content='Reply 2')
        
        self.assertEqual(Reply.objects.filter(post=self.post).count(), 2)
        
        # Delete post
        url = reverse('community:delete_post', args=[self.post.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        
        # Post dan replies harus terhapus (CASCADE)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
        self.assertEqual(Reply.objects.count(), 0)


class IntegrationTest(TestCase):
    """Test cases untuk alur lengkap (integration tests)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            password='integpass123'
        )
    
    def test_full_post_lifecycle(self):
        """Test alur lengkap: buat post -> reply -> edit -> delete"""
        # 1. Login
        self.client.login(username='integrationuser', password='integpass123')
        
        # 2. Buat post
        response = self.client.post(
            reverse('community:community_home'),
            {
                'title': 'Integration Test Post',
                'description': 'Testing full lifecycle'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        post = Post.objects.get(title='Integration Test Post')
        
        # 3. Tambah reply
        response = self.client.post(
            reverse('community:add_reply', args=[post.id]),
            {'content': 'First reply'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(post.replies.count(), 1)
        
        # 4. Edit post (AJAX)
        response = self.client.post(
            reverse('community:edit_post', args=[post.id]),
            data=json.dumps({
                'title': 'Edited Title',
                'description': 'Edited Description'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        post.refresh_from_db()
        self.assertEqual(post.title, 'Edited Title')
        
        # 5. Delete post
        response = self.client.post(
            reverse('community:delete_post', args=[post.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=post.id).exists())