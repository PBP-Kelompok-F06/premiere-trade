from accounts.models import Profile, CustomUser
from main.models import Club

# Cek user admin
admin = CustomUser.objects.get(username='admin')
print(f'User: {admin.username}')
print(f'is_club_admin: {admin.is_club_admin}')
print(f'is_superuser: {admin.is_superuser}')

# Cek profile
profile, created = Profile.objects.get_or_create(user=admin)
print(f'\nProfile exists: {not created}')
print(f'managed_club: {profile.managed_club}')

if profile.managed_club:
    print(f'Club name: {profile.managed_club.name}')
    # Cek pemain di klub ini
    from main.models import Player
    players = Player.objects.filter(current_club=profile.managed_club)[:5]
    print(f'\nPemain di klub {profile.managed_club.name}:')
    for p in players:
        print(f'  - {p.nama_pemain} (ID: {p.id})')
else:
    print('managed_club is None - perlu di-set!')
    clubs = Club.objects.all()[:5]
    print(f'\nAvailable clubs:')
    for c in clubs:
        print(f'  - {c.name} (ID: {c.id})')