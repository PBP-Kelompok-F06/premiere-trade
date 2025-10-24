from django import forms
from django.utils.html import strip_tags
from rumors.models import Rumors
from main.models import Player, Club

class RumorsForm(forms.ModelForm):
    club_asal = forms.ModelChoiceField(
        queryset=Club.objects.all(),
        required=True,
        label="Current Club"
    )
    club_tujuan = forms.ModelChoiceField(
        queryset=Club.objects.all(),
        required=True,
        label="Designated Club"
    )

    class Meta:
        model = Rumors
        fields = ['club_asal', 'club_tujuan', 'pemain', 'content']
        labels = {
            'pemain': 'Player',
            'content': 'Rumor Details',
        }
        widgets = {
            'pemain': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your rumor details here...'
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        return strip_tags(content).strip()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Kalau form baru dibuka (GET): kosongin dropdown pemain
        self.fields['pemain'].queryset = Player.objects.none()

        # Kalau ada data yang dikirim (POST)
        if 'club_asal' in self.data:
            try:
                club_asal_id = int(self.data.get('club_asal'))
                self.fields['pemain'].queryset = Player.objects.filter(current_club_id=club_asal_id).order_by('nama_pemain')
            except (ValueError, TypeError):
                pass  # kalau parsing gagal, biarkan kosong

        # Kalau form sedang mengedit instance lama
        elif self.instance.pk and self.instance.club_asal:
            self.fields['pemain'].queryset = Player.objects.filter(current_club=self.instance.club_asal)



    def clean(self):
        cleaned_data = super().clean()
        club_asal = cleaned_data.get("club_asal")
        club_tujuan = cleaned_data.get("club_tujuan")

        if club_asal == club_tujuan:
            raise forms.ValidationError("Club asal dan tujuan tidak boleh sama.")
        return cleaned_data
