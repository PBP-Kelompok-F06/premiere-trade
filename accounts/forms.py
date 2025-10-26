from django import forms
from django.contrib.auth import get_user_model
from .models import Profile
from main.models import Club, Player
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]


ROLE_CHOICES = (
    ("fan", "Fan Account"),
    ("admin", "Club Admin"),
)


class SuperUserEditForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, widget=forms.RadioSelect, label="Peran Pengguna"
    )

    managed_club = forms.ModelChoiceField(
        queryset=Club.objects.all(),
        required=False,
        label="Klub yang Dikelola",
        help_text="Wajib diisi jika peran adalah Club Admin.",
    )

    class Meta:
        model = User
        fields = ["username"]  

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        if user_instance:
            # Tentukan nilai awal radio button berdasarkan status user
            if user_instance.is_club_admin:
                self.fields["role"].initial = "admin"
            else:
                self.fields["role"].initial = "fan"

            # Isi field managed_club
            if hasattr(user_instance, "profile"):
                self.fields["managed_club"].queryset = Club.objects.exclude(name__iexact="Admin")

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        managed_club = cleaned_data.get("managed_club")

        # Tambahkan validasi: jika admin, klub harus dipilih
        if role == "admin" and not managed_club:
            self.add_error(
                "managed_club", "Admin Klub harus memilih klub yang dikelola."
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        selected_role = self.cleaned_data.get("role")

        # Set is_fan dan is_club_admin berdasarkan pilihan role
        if selected_role == "admin":
            user.is_club_admin = True
            user.is_fan = False  # Admin tidak dianggap sebagai fan biasa
        else:  # 'fan'
            user.is_club_admin = False
            user.is_fan = True

        if commit:
            user.save()

        # Simpan data profile
        if hasattr(user, "profile"):
            if selected_role == "admin":
                user.profile.managed_club = self.cleaned_data.get("managed_club")
            else:
                user.profile.managed_club = None  # Hapus klub jika user adalah fan
            if commit:
                user.profile.save()
        return user


class SuperUserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    # Gunakan field 'role' yang sama
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial="fan",
        label="Peran Pengguna",
    )

    managed_club = forms.ModelChoiceField(
        queryset=Club.objects.all(),
        required=False,
        label="Klub yang Dikelola",
        help_text="Wajib diisi jika peran adalah Club Admin.",
    )

    class Meta:
        model = User
        fields = ["username", "password"]  # Hapus is_fan dan is_club_admin
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['managed_club'].queryset = Club.objects.exclude(name__iexact='Admin')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        managed_club = cleaned_data.get("managed_club")

        if role == "admin" and not managed_club:
            self.add_error(
                "managed_club", "Admin Klub harus memilih klub yang dikelola."
            )
        return cleaned_data

    def save(self, commit=True):
        selected_role = self.cleaned_data.get("role")
        is_admin = selected_role == "admin"

        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            is_fan=not is_admin,
            is_club_admin=is_admin,
        )

        Profile.objects.create(
            user=user,
            managed_club=self.cleaned_data.get("managed_club") if is_admin else None,
        )
        return user


class PasswordChangeCustomForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ganti label default agar lebih user-friendly
        self.fields["old_password"].label = "Password Lama"
        self.fields["new_password1"].label = "Password Baru"
        self.fields["new_password2"].label = "Konfirmasi Password Baru"
        
class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ('name', 'country', 'logo_url') 

class ClubDeleteForm(forms.Form):
    pass

# Forms untuk Player
class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        exclude = ('id',)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_club'].queryset = Club.objects.exclude(name__iexact='Admin')

class PlayerDeleteForm(forms.Form):
    pass
