from django import forms
from django.utils.html import strip_tags
from rumors.models import Rumors
from main.models import Player, Club
from django.db.models import Q


class RumorsForm(forms.ModelForm):
    club_asal = forms.ModelChoiceField(
        queryset=Club.objects.exclude(name="Admin"),
        required=True,
        label="Current Club",
        empty_label=None
    )
    club_tujuan = forms.ModelChoiceField(
        queryset=Club.objects.exclude(name="Admin"),
        required=True,
        label="Designated Club",
        empty_label=None
    )

    class Meta:
        model = Rumors
        fields = ['club_asal', 'club_tujuan', 'pemain', 'content']
        labels = {
            'pemain': 'Player',
            'content': 'Rumor Details',
        }
        widgets = {
            'pemain': forms.Select(),
            'content': forms.Textarea(attrs={
                'placeholder': 'Write your rumor details here...'
            }),
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        return strip_tags(content).strip()

    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            # Styling
            for field_name, field in self.fields.items():
                css_class = (
                    'border rounded-lg py-2 px-3 w-full text-sm bg-white shadow-sm '
                    'focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                )
                field.widget.attrs.update({'class': css_class})

            # === Filter pemain ===
            if 'club_asal' in self.data and self.data.get('club_asal'):
                # Kalau sedang create atau user ubah dropdown
                club_asal_id = self.data.get('club_asal')
                self.fields['pemain'].queryset = Player.objects.filter(
                    current_club_id=club_asal_id
                ).order_by('nama_pemain')
            elif self.instance.pk and self.instance.club_asal:
                # Kalau sedang edit rumor
                self.fields['pemain'].queryset = Player.objects.filter(
                    Q(current_club=self.instance.club_asal) | Q(id=self.instance.pemain.id)
                ).order_by('nama_pemain')
            else:
                self.fields['pemain'].queryset = Player.objects.none()

            # === Filter club_tujuan ===
            club_asal_value = self.data.get('club_asal') or None
            if club_asal_value:
                current_club_id = club_asal_value
            elif self.instance.pk and self.instance.club_asal:
                current_club_id = self.instance.club_asal.id
            else:
                current_club_id = None

            qs = Club.objects.exclude(name="Admin")
            if current_club_id:
                qs = qs.exclude(id=current_club_id)
            self.fields['club_tujuan'].queryset = qs
            self.fields['club_tujuan'].empty_label = None




    def clean(self):
        cleaned_data = super().clean()
        club_asal = cleaned_data.get("club_asal")
        club_tujuan = cleaned_data.get("club_tujuan")

        if club_asal and club_tujuan and club_asal == club_tujuan:
            raise forms.ValidationError("Club asal dan tujuan tidak boleh sama.")
        return cleaned_data
