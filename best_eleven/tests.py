import json
from urllib import response
import uuid
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from unittest.mock import patch

from main.models import Player, Club
from .models import BestEleven

User = get_user_model()

class BestElevenViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testviewuser', password='password123')
        cls.other_user = User.objects.create_user(username='otheruser', password='password123')
        cls.club1 = Club.objects.create(name='Test Club A')
        cls.club2 = Club.objects.create(name='Test Club B')
        cls.players = []
        positions = ['Kiper', 'Bek-Kiri', 'Bek-Tengah', 'Bek-Tengah', 'Bek-Kanan',
                     'Gel. Bertahan', 'Gel. Tengah', 'Gel. Tengah', 'Sayap Kiri',
                     'Penyerang', 'Sayap Kanan', 'Penyerang']
        for i in range(12):
            club = cls.club1 if i < 11 else cls.club2
            player = Player.objects.create(
                id=uuid.uuid4(), nama_pemain=f'Pemain {i+1}', current_club=club,
                position=positions[i % len(positions)], market_value=1000000 * (i + 1)
            )
            cls.players.append(player)

        cls.formation1 = BestEleven.objects.create(
            fan_account=cls.user, name="Initial Formation", layout="4-3-3"
        )
        cls.formation1.players.set(cls.players[:11])
        cls.formation1.player_slot_data = [
            {'playerId': str(cls.players[i].id), 'slotId': f'POS{i+1}'} for i in range(11)
        ]
        cls.formation1.save()

        cls.other_formation = BestEleven.objects.create(
            fan_account=cls.other_user, name="Other User Formation", layout="4-4-2"
        )
        cls.other_formation.players.add(cls.players[11])
        cls.other_formation.player_slot_data = [{'playerId': str(cls.players[11].id), 'slotId': 'FWD'}]
        cls.other_formation.save()

        cls.formation_no_slots = BestEleven.objects.create(
            fan_account=cls.user, name="No Slots Formation", layout="4-3-3"
        )
        cls.formation_no_slots.players.set(cls.players[:11])
        cls.formation_no_slots.player_slot_data = None
        cls.formation_no_slots.save()

        cls.formation_bad_slots = BestEleven.objects.create(
            fan_account=cls.user, name="Bad Slots Formation", layout="4-3-3"
        )
        cls.formation_bad_slots.players.add(cls.players[0])
        cls.formation_bad_slots.player_slot_data = [
            {'playerId': str(cls.players[0].id)},
            {'slotId': 'GK'},
            {'playerId': 'not-a-uuid', 'slotId': 'GK2'},
            'just a string'
        ]
        cls.formation_bad_slots.save()

    def setUp(self):
        self.client = Client()
        self.client.login(username='testviewuser', password='password123')
        
        self.builder_url = reverse('best_eleven:team_builder')
        self.api_builder_data_url = reverse('best_eleven:api_builder_data')
        self.api_get_players_url = reverse('best_eleven:api_get_players')
        self.api_save_formation_url = reverse('best_eleven:api_save_formation')
        self.api_detail_url_base = 'best_eleven:api_get_formation_details'

        try:
            self.detail_url = reverse('best_eleven:besteleven-detail', kwargs={'pk': self.formation1.pk})
            self.update_url = reverse('best_eleven:besteleven-update', kwargs={'pk': self.formation1.pk})
            self.delete_url = reverse('best_eleven:besteleven-delete', kwargs={'pk': self.formation1.pk})
            self.other_detail_url = reverse('best_eleven:besteleven-detail', kwargs={'pk': self.other_formation.pk})
            self.other_update_url = reverse('best_eleven:besteleven-update', kwargs={'pk': self.other_formation.pk})
            self.other_delete_url = reverse('best_eleven:besteleven-delete', kwargs={'pk': self.other_formation.pk})
            self.cbv_urls_configured = True
        except NoReverseMatch:
            self.cbv_urls_configured = False

    def test_builder_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.builder_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/admin/login/'))

    def test_builder_view_get_logged_in(self):
        response = self.client.get(self.builder_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'best_eleven/besteleven_builder.html')
        self.assertEqual(response.context['user'], self.user)

    def test_builder_view_context_data(self):
        response = self.client.get(f'{self.builder_url}?load=99&show_detail=88')
        self.assertEqual(response.status_code, 200)
        self.assertIn('load_formation_id', response.context)
        self.assertIn('show_detail_id', response.context)
        self.assertEqual(response.context['load_formation_id'], '99')
        self.assertEqual(response.context['show_detail_id'], '88')
        
    def test_builder_view_post_not_allowed(self):
        response = self.client.post(self.builder_url, {})
        self.assertEqual(response.status_code, 405)

    def test_cbv_views_require_login(self):
        if not self.cbv_urls_configured: self.skipTest("CBV URLs not configured")
        self.client.logout()
        response_detail = self.client.get(self.detail_url)
        response_update = self.client.get(self.update_url)
        response_delete = self.client.get(self.delete_url)
        self.assertEqual(response_detail.status_code, 302)
        self.assertTrue(response_detail.url.startswith('/accounts/login/'))
        self.assertEqual(response_update.status_code, 302)
        self.assertTrue(response_update.url.startswith('/accounts/login/'))
        self.assertEqual(response_delete.status_code, 302)
        self.assertTrue(response_delete.url.startswith('/accounts/login/'))

    def test_cbv_views_test_func_fail_for_other_user(self):
        if not self.cbv_urls_configured: self.skipTest("CBV URLs not configured")
        response_detail = self.client.get(self.other_detail_url)
        response_update = self.client.get(self.other_update_url)
        response_delete = self.client.get(self.other_delete_url)
        self.assertEqual(response_detail.status_code, 403)
        self.assertEqual(response_update.status_code, 403)
        self.assertEqual(response_delete.status_code, 403)
        response_update_post = self.client.post(self.other_update_url, {})
        self.assertEqual(response_update_post.status_code, 403)
        response_delete_post = self.client.post(self.other_delete_url, {})
        self.assertEqual(response_delete_post.status_code, 403)

    def test_cbv_detail_view_success(self):
        if not self.cbv_urls_configured: self.skipTest("CBV URLs not configured")
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'best_eleven/besteleven_detail.html')
        self.assertEqual(response.context['formasi'], self.formation1)

    def test_cbv_update_view_get_and_post(self):
        if not self.cbv_urls_configured: self.skipTest("CBV URLs not configured")
        response_get = self.client.get(self.update_url)
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response, 'best_eleven/besteleven_form.html')
        self.assertIn('form', response_get.context)
        post_data = {
            'name': 'Updated via CBV',
            'layout': '4-4-2',
            'players': [p.id for p in self.players[:11]]
        }
        response_post = self.client.post(self.update_url, post_data)
        self.assertEqual(response_post.status_code, 302)
        self.assertEqual(response_post.url, self.detail_url)
        self.formation1.refresh_from_db()
        self.assertEqual(self.formation1.name, 'Updated via CBV')
        self.assertEqual(self.formation1.layout, '4-4-2')

    def test_cbv_update_view_post_invalid(self):
        if not self.cbv_urls_configured: self.skipTest("CBV URLs not configured")
        post_data = {'name': '', 'layout': '4-4-2'}
        response_post = self.client.post(self.update_url, post_data)
        self.assertEqual(response_post.status_code, 200)
        self.assertIn('form', response_post.context)
        self.assertTrue(response_post.context['form'].errors)

    def test_cbv_delete_view_get_and_post(self):
        if not self.cbv_urls_configured: self.skipTest("CBV URLs not configured")
        to_delete = BestEleven.objects.create(fan_account=self.user, name="CBV Delete Test")
        delete_url = reverse('best_eleven:besteleven-delete', kwargs={'pk': to_delete.pk})
        try:
            success_url = reverse('best_eleven:besteleven-list')
        except NoReverseMatch:
            success_url = reverse('best_eleven:team_builder')
        
        response_get = self.client.get(delete_url)
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response, 'best_eleven/besteleven_confirm_delete.html')
        response_post = self.client.post(delete_url)
        self.assertEqual(response_post.status_code, 302)
        self.assertEqual(response_post.url, success_url)
        with self.assertRaises(BestEleven.DoesNotExist):
            BestEleven.objects.get(pk=to_delete.pk)

    def test_api_builder_data_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.api_builder_data_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        
    def test_api_builder_data_method_not_allowed(self):
        response = self.client.post(self.api_builder_data_url, {})
        self.assertEqual(response.status_code, 405)

    def test_api_builder_data_success(self):
        response = self.client.get(self.api_builder_data_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('clubs', data)
        self.assertIn('history', data)
        self.assertEqual(len(data['history']), 3)
        self.assertNotIn(self.other_formation.id, {f['id'] for f in data['history']})

    @patch('best_eleven.views.Club.objects.order_by')
    def test_api_builder_data_exception(self, mock_order_by):
        mock_order_by.side_effect = Exception('Database error')
        response = self.client.get(self.api_builder_data_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {'error': 'Gagal memuat data awal.'})

    def test_api_players_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.api_get_players_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_api_players_method_not_allowed(self):
        response = self.client.post(self.api_get_players_url, {})
        self.assertEqual(response.status_code, 405)

    def test_api_players_no_filter(self):
        response = self.client.get(self.api_get_players_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('players', data)
        self.assertEqual(len(data['players']), 12)

    def test_api_players_with_filter(self):
        response = self.client.get(f'{self.api_get_players_url}?club_id={self.club1.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['players']), 11)
        self.assertEqual(data['players'][0]['club_name'], 'Test Club A')

    @patch('best_eleven.views.Player.objects.prefetch_related')
    def test_api_players_exception(self, mock_prefetch):
        mock_prefetch.return_value.all.side_effect = Exception('Database error')
        response = self.client.get(self.api_get_players_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {'error': 'Gagal memuat daftar pemain.'})

    def test_api_save_method_not_allowed(self):
        response = self.client.get(self.api_save_formation_url)
        self.assertEqual(response.status_code, 405)

    def test_api_save_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.api_save_formation_url, {}, content_type='application/json')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    @patch('json.loads')
    def test_api_save_invalid_json_or_generic_exception(self, mock_json_loads):
        mock_json_loads.side_effect = Exception('JSON parsing error')
        response = self.client.post(self.api_save_formation_url, 'invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 500)
        self.assertIn('Gagal menyimpan formasi', response.json()['error'])

    def test_api_save_missing_data(self):
        payload = {'name': 'Incomplete', 'layout': '4-3-3'}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Nama, layout, dan 11 pemain wajib diisi', response.json()['error'])
        
    def test_api_save_not_11_players(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        payload = {'name': '10 Players', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Nama, layout, dan 11 pemain wajib diisi', response.json()['error'])

    def test_api_save_incomplete_slot_data(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        player_ids_data.append({'playerId': str(self.players[10].id)})
        payload = {'name': 'Incomplete Slot', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Harus ada tepat 11 pemain dengan ID dan Slot valid', response.json()['error'])

    def test_api_save_invalid_uuid(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        player_ids_data.append({'playerId': 'not-a-uuid', 'slotId': 'SLOT_10'})
        payload = {'name': 'Invalid UUID', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Harus ada tepat 11 pemain dengan ID dan Slot valid', response.json()['error'])

    def test_api_save_player_not_found(self):
        random_uuid = uuid.uuid4()
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        player_ids_data.append({'playerId': str(random_uuid), 'slotId': 'SLOT_10'})
        payload = {'name': 'Player Not Found', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Pemain tidak ditemukan', response.json()['error'])

    def test_api_save_create_success(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'NEW_SLOT_{i}'} for i in range(11)]
        payload = {
            'name': 'Newly Created', 'layout': '4-4-2',
            'player_ids': player_ids_data, 'formation_id': None
        }
        initial_count = BestEleven.objects.filter(fan_account=self.user).count()
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(BestEleven.objects.filter(fan_account=self.user).count(), initial_count + 1)
        new_formation = BestEleven.objects.get(id=data['formation']['id'])
        self.assertEqual(new_formation.name, 'Newly Created')
        self.assertEqual(new_formation.player_slot_data[0]['slotId'], 'NEW_SLOT_0')

    def test_api_save_update_success(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'UPDATED_SLOT_{i}'} for i in range(1, 12)]
        payload = {
            'name': 'Updated Name', 'layout': '3-5-2',
            'player_ids': player_ids_data, 'formation_id': self.formation1.id
        }
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.formation1.refresh_from_db()
        self.assertEqual(self.formation1.name, 'Updated Name')
        self.assertEqual(self.formation1.layout, '3-5-2')
        self.assertEqual(self.formation1.player_slot_data[0]['slotId'], 'UPDATED_SLOT_1')

    def test_api_save_update_not_owner(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(11)]
        payload = {
            'name': 'Hack Attempt', 'layout': '3-5-2',
            'player_ids': player_ids_data, 'formation_id': self.other_formation.id
        }
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 404) 

    @patch('uuid.UUID', side_effect=ValueError('Test UUID Error'))
    def test_api_save_value_error_exception(self, mock_uuid):
        player_ids_data = [{'playerId': 'abc', 'slotId': 'GK'}] * 11
        payload = {'name': 'ValueError', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Harus ada tepat 11 pemain', response.json()['error'])
        
    @patch('best_eleven.views.Player.objects.filter', side_effect=Exception('Generic DB Error'))
    def test_api_save_generic_exception(self, mock_filter):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(11)]
        payload = {'name': 'Generic Error', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 500)
        self.assertIn('Gagal menyimpan formasi: Generic DB Error', response.json()['error'])

    def test_api_details_method_not_allowed(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation1.pk})
        response = self.client.post(detail_url, {})
        self.assertEqual(response.status_code, 405)

    def test_api_details_not_logged_in(self):
        self.client.logout()
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_api_details_get_non_existent(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': 99999})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Formation not found or access denied.'})

    def test_api_details_get_not_owner(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.other_formation.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Formation not found or access denied.'})

    def test_api_details_get_success(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.formation1.id)
        self.assertEqual(len(data['players']), 11)
        self.assertEqual(data['players'][0]['slotId'], 'POS1')

    def test_api_details_get_no_slots(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation_no_slots.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['players']), 0)

    def test_api_details_get_bad_slots(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation_bad_slots.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['players']), 0)
        
    def test_api_details_get_player_not_in_map(self):
        player_ids_data = [{'playerId': str(self.players[0].id), 'slotId': 'GK'}]
        player_ids_data.append({'playerId': str(uuid.uuid4()), 'slotId': 'FW'})
        self.formation1.player_slot_data = player_ids_data
        self.formation1.save()
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['players']), 1)
        self.assertEqual(response.json()['players'][0]['id'], str(self.players[0].id))

    @patch('best_eleven.views.Player.objects.filter')
    def test_api_details_get_exception(self, mock_filter):
        mock_filter.side_effect = Exception('DB Error')
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {'error': 'Error processing formation details: DB Error'})

    def test_api_details_delete_non_existent(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': 99999})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 404)

    def test_api_details_delete_not_owner(self):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.other_formation.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 404)

    def test_api_details_delete_success(self):
        to_delete = BestEleven.objects.create(fan_account=self.user, name="To Delete")
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': to_delete.pk})
        initial_count = BestEleven.objects.filter(fan_account=self.user).count()
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(BestEleven.objects.filter(fan_account=self.user).count(), initial_count - 1)

    @patch.object(BestEleven, 'delete')
    def test_api_details_delete_exception(self, mock_delete):
        mock_delete.side_effect = Exception('Delete Error')
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation1.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {'error': 'Failed to delete formation: Delete Error'})
        
    @patch('best_eleven.views.get_object_or_404', side_effect=Exception('Unexpected Error'))
    def test_api_details_unexpected_exception(self, mock_get):
        detail_url = reverse(self.api_detail_url_base, kwargs={'pk': self.formation1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {'error': 'An unexpected error occurred: Unexpected Error'})