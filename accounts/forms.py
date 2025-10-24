from django import forms
from django.contrib.auth import get_user_model
from .models import Profile
from main.models import Club

User = get_user_model()


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["managed_club"]


class SuperUserEditForm(forms.ModelForm):
    """
    Form untuk superuser mengedit detail user lain.
    Menggabungkan field dari CustomUser dan Profile.
    """

    # Ambil field dari model Profile
    managed_club = forms.ModelChoiceField(
        queryset=Club.objects.all(),
        required=False,  # Tidak wajib diisi
        widget=forms.Select(attrs={"class": "your-tailwind-classes-here"}),
    )

    class Meta:
        model = User
        fields = ["username", "is_fan", "is_club_admin"]

    def __init__(self, *args, **kwargs):
        # Ambil instance user dari argumen
        user_instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        # Jika user sudah ada (sedang mengedit), isi field managed_club
        if user_instance and hasattr(user_instance, "profile"):
            self.fields["managed_club"].initial = user_instance.profile.managed_club

    def save(self, commit=True):
        # Simpan data user dari form
        user = super().save(commit=commit)

        # Simpan data profile (managed_club)
        if hasattr(user, "profile"):
            user.profile.managed_club = self.cleaned_data.get("managed_club")
            if commit:
                user.profile.save()
        return user


class SuperUserCreateForm(forms.ModelForm):
    """
    Form untuk superuser membuat user baru.
    """

    # Tambahkan field password secara eksplisit
    password = forms.CharField(
        widget=forms.PasswordInput, help_text="Masukkan password untuk pengguna baru."
    )

    managed_club = forms.ModelChoiceField(
        queryset=Club.objects.all(),
        required=False,
        label="Klub yang Dikelola",
        help_text="Pilih klub jika pengguna ini adalah Admin Klub.",
    )

    class Meta:
        model = User
        fields = ["username", "password", "is_fan", "is_club_admin"]

    def save(self, commit=True):
        # Ambil data user dari form
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            is_fan=self.cleaned_data.get("is_fan", True),
            is_club_admin=self.cleaned_data.get("is_club_admin", False),
        )

        # Buat profile untuk user baru
        Profile.objects.create(
            user=user, managed_club=self.cleaned_data.get("managed_club")
        )

        return user
