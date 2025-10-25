# best_eleven/tests.py

import json
import uuid
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch
from django.http import Http404
from main.models import Player, Club
from .models import BestEleven

User = get_user_model()

class BestElevenModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testmodeluser', password='password123')

    def test_best_eleven_str_method(self):
        formation = BestEleven.objects.create(
            fan_account=self.user, name="My Awesome Team", layout="4-3-3"
        )
        self.assertEqual(str(formation), "My Awesome Team - by testmodeluser")

    def test_best_eleven_default_values(self):
        formation = BestEleven.objects.create(
            fan_account=self.user, name="Test Default Layout"
        )
        self.assertEqual(formation.layout, '4-3-3')
        self.assertEqual(formation.player_slot_data, [])

    def test_best_eleven_ordering(self):
        formation1 = BestEleven.objects.create(fan_account=self.user, name="Formation Old")
        formation1.save()
        time.sleep(0.01)
        formation2 = BestEleven.objects.create(fan_account=self.user, name="Formation New")
        formation2.save()
        formations = BestEleven.objects.all()
        self.assertEqual(formations.first(), formation2)
        self.assertEqual(formations.last(), formation1)

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

    def test_builder_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.builder_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/admin/login/')) # Sesuai login_url di view

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

    def test_api_requires_login(self):
        self.client.logout()
        api_urls = [
            self.api_builder_data_url,
            self.api_get_players_url,
            self.api_save_formation_url,
            reverse('best_eleven:api_get_formation_details', kwargs={'pk': self.formation1.pk}),
        ]
        methods = {
            self.api_save_formation_url: 'post',
            reverse('best_eleven:api_get_formation_details', kwargs={'pk': self.formation1.pk}): 'delete',
        }
        for url in api_urls:
            method = methods.get(url, 'get')
            response = None
            if method == 'get': response = self.client.get(url)
            elif method == 'post': response = self.client.post(url, data={}, content_type='application/json')
            elif method == 'delete': response = self.client.delete(url)
            self.assertEqual(response.status_code, 302, f"URL: {url} failed login redirect status test (method: {method})")
            # Cek redirect ke URL login default Django
            self.assertTrue(response.url.startswith('/accounts/login/'), f"URL: {url} failed redirect location check")

    def test_api_method_not_allowed(self):
        response_get_save = self.client.get(self.api_save_formation_url)
        self.assertEqual(response_get_save.status_code, 405)

        detail_url = reverse('best_eleven:api_get_formation_details', kwargs={'pk': self.formation1.pk})
        response_post_detail = self.client.post(detail_url, data={}, content_type='application/json')
        self.assertEqual(response_post_detail.status_code, 405)

        response_post_builder = self.client.post(self.api_builder_data_url, data={}, content_type='application/json')
        self.assertEqual(response_post_builder.status_code, 405)

        response_post_players = self.client.post(self.api_get_players_url, data={}, content_type='application/json')
        self.assertEqual(response_post_players.status_code, 405)


    def test_api_get_builder_data_success(self):
        response = self.client.get(self.api_builder_data_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/json')
        data = response.json()
        self.assertIn('clubs', data)
        self.assertIn('history', data)
        club_names = [c['name'] for c in data['clubs']]
        self.assertIn('Test Club A', club_names)
        self.assertIn('Test Club B', club_names)
        self.assertGreaterEqual(len(data['clubs']), 2)
        history_ids = {f['id'] for f in data['history']}
        self.assertIn(self.formation1.id, history_ids)
        self.assertIn(self.formation_no_slots.id, history_ids)
        self.assertIn(self.formation_bad_slots.id, history_ids)
        self.assertNotIn(self.other_formation.id, history_ids)
        self.assertEqual(len(data['history']), 3)


    def test_api_get_players_no_filter(self):
        response = self.client.get(self.api_get_players_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('players', data)
        self.assertEqual(len(data['players']), 12)
        player_names = [p['name'] for p in data['players']]
        self.assertIn('Pemain 1', player_names)
        self.assertIn('Pemain 12', player_names)

    def test_api_get_players_with_club_filter(self):
        response_a = self.client.get(f'{self.api_get_players_url}?club_id={self.club1.id}')
        self.assertEqual(response_a.status_code, 200)
        data_a = response_a.json()
        self.assertEqual(len(data_a['players']), 11)
        self.assertEqual(data_a['players'][0]['club_name'], 'Test Club A')

        response_b = self.client.get(f'{self.api_get_players_url}?club_id={self.club2.id}')
        self.assertEqual(response_b.status_code, 200)
        data_b = response_b.json()
        self.assertEqual(len(data_b['players']), 1)
        self.assertEqual(data_b['players'][0]['name'], 'Pemain 12')
        self.assertEqual(data_b['players'][0]['club_name'], 'Test Club B')

    def test_api_save_formation_create_success(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'NEW_SLOT_{i}'} for i in range(11)]
        payload = {
            'name': 'Newly Created Formation', 'layout': '4-4-2',
            'player_ids': player_ids_data, 'formation_id': None
        }
        initial_count = BestEleven.objects.filter(fan_account=self.user).count()
        response = self.client.post(
            self.api_save_formation_url, json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(BestEleven.objects.filter(fan_account=self.user).count(), initial_count + 1)
        new_formation = BestEleven.objects.get(id=data['formation']['id'])
        self.assertEqual(new_formation.name, 'Newly Created Formation')
        self.assertEqual(new_formation.layout, '4-4-2')
        self.assertEqual(new_formation.players.count(), 11)
        self.assertEqual(len(new_formation.player_slot_data), 11)
        self.assertEqual(new_formation.player_slot_data[0]['slotId'], 'NEW_SLOT_0')

    def test_api_save_formation_update_success(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'UPDATED_SLOT_{i}'} for i in range(1, 12)]
        payload = {
            'name': 'Updated Formation Name', 'layout': '3-5-2',
            'player_ids': player_ids_data, 'formation_id': self.formation1.id
        }
        response = self.client.post(
            self.api_save_formation_url, json.dumps(payload), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.formation1.refresh_from_db()
        self.assertEqual(self.formation1.name, 'Updated Formation Name')
        self.assertEqual(self.formation1.layout, '3-5-2')
        player_ids_in_formation = {str(p.id) for p in self.formation1.players.all()}
        expected_player_ids = {str(self.players[i].id) for i in range(1, 12)}
        self.assertEqual(player_ids_in_formation, expected_player_ids)
        self.assertEqual(len(self.formation1.player_slot_data), 11)
        self.assertEqual(self.formation1.player_slot_data[0]['slotId'], 'UPDATED_SLOT_1')

    def test_api_save_formation_fail_less_than_11_players(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        payload = {'name': 'Fail', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('11 pemain wajib diisi', response.json()['error'])

    def test_api_save_formation_fail_invalid_uuid(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        player_ids_data.append({'playerId': 'not-a-uuid', 'slotId': 'SLOT_10'})
        payload = {'name': 'Fail UUID', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('11 pemain dengan ID dan Slot valid', response.json()['error'])

    def test_api_save_formation_fail_incomplete_slot_data(self):
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        player_ids_data.append({'playerId': str(self.players[10].id)})
        payload = {'name': 'Fail Incomplete', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('11 pemain dengan ID dan Slot valid', response.json()['error'])


    def test_api_save_formation_fail_player_not_found(self):
        random_uuid = uuid.uuid4()
        player_ids_data = [{'playerId': str(self.players[i].id), 'slotId': f'SLOT_{i}'} for i in range(10)]
        player_ids_data.append({'playerId': str(random_uuid), 'slotId': 'SLOT_10'})
        payload = {'name': 'Fail Not Found', 'layout': '4-3-3', 'player_ids': player_ids_data}
        response = self.client.post(self.api_save_formation_url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Pemain tidak ditemukan', response.json()['error'])

    def test_api_get_formation_details_success(self):
        detail_url = reverse('best_eleven:api_get_formation_details', kwargs={'pk': self.formation1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.formation1.id)
        self.assertEqual(data['name'], self.formation1.name)
        self.assertEqual(len(data['players']), 11)
        self.assertEqual(data['players'][0]['id'], str(self.players[0].id))
        self.assertEqual(data['players'][0]['slotId'], 'POS1')

    def test_api_get_formation_details_no_slots(self):
        detail_url = reverse('best_eleven:api_get_formation_details', kwargs={'pk': self.formation_no_slots.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], self.formation_no_slots.name)
        self.assertIn('players', data)
        self.assertEqual(len(data['players']), 0)

    def test_api_get_formation_details_bad_slots(self):
        detail_url = reverse('best_eleven:api_get_formation_details', kwargs={'pk': self.formation_bad_slots.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], self.formation_bad_slots.name)
        self.assertIn('players', data)
        self.assertEqual(len(data['players']), 0)

    def test_api_delete_formation_success(self):
        to_delete = BestEleven.objects.create(fan_account=self.user, name="To Delete")
        delete_url = reverse('best_eleven:api_get_formation_details', kwargs={'pk': to_delete.pk})
        initial_count = BestEleven.objects.filter(fan_account=self.user).count()
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(BestEleven.objects.filter(fan_account=self.user).count(), initial_count - 1)
        with self.assertRaises(BestEleven.DoesNotExist):
            BestEleven.objects.get(pk=to_delete.pk)

    def test_api_access_other_user_formation_returns_404(self):
        other_detail_url = reverse('best_eleven:api_get_formation_details', kwargs={'pk': self.other_formation.pk})
        response_get = self.client.get(other_detail_url)
        self.assertEqual(response_get.status_code, 404)
        self.assertIn('denied', response_get.json()['error'])
        response_delete = self.client.delete(other_detail_url)
        self.assertEqual(response_delete.status_code, 404)
        self.assertIn('denied', response_delete.json()['error'])

    def test_api_access_nonexistent_formation_returns_404(self):
        non_existent_pk = 99999
        non_existent_url = reverse('best_eleven:api_get_formation_details', kwargs={'pk': non_existent_pk})
        response_get = self.client.get(non_existent_url)
        self.assertEqual(response_get.status_code, 404)
        self.assertIn('denied', response_get.json()['error'])
        response_delete = self.client.delete(non_existent_url)
        self.assertEqual(response_delete.status_code, 404)
        self.assertIn('denied', response_delete.json()['error'])