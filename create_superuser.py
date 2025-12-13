from accounts.models import CustomUser

# Buat superuser baru
superadmin, created = CustomUser.objects.get_or_create(
    username='superadmin',
    defaults={
        'is_superuser': True,
        'is_staff': True,
        'is_club_admin': False,
        'is_fan': False,
    }
)

if created:
    superadmin.set_password('admin123')
    superadmin.save()
    print('✅ Superuser "superadmin" dibuat dengan password: admin123')
else:
    superadmin.set_password('admin123')
    superadmin.is_superuser = True
    superadmin.is_staff = True
    superadmin.save()
    print('✅ Password superadmin direset ke: admin123')

print('\n📝 Kredensial untuk Django Admin:')
print('   Username: superadmin')
print('   Password: admin123')
print('\n   Atau gunakan user "admin" yang sudah dijadikan superuser')