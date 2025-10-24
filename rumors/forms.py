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

        # === Tambahin styling umum buat semua field ===
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'form-select border rounded-lg py-2 px-3 w-full text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': 'form-textarea border rounded-lg py-3 px-4 w-full text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-input border rounded-lg py-2 px-3 w-full text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500'
                })

        # === Filter pemain ===
        self.fields['pemain'].queryset = Player.objects.none()
        if 'club_asal' in self.data:
            try:
                club_asal_id = int(self.data.get('club_asal'))
                self.fields['pemain'].queryset = Player.objects.filter(current_club_id=club_asal_id).order_by('nama_pemain')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.club_asal:
            self.fields['pemain'].queryset = Player.objects.filter(current_club=self.instance.club_asal)

    def clean(self):
        cleaned_data = super().clean()
        club_asal = cleaned_data.get("club_asal")
        club_tujuan = cleaned_data.get("club_tujuan")

        if club_asal == club_tujuan:
            raise forms.ValidationError("Club asal dan tujuan tidak boleh sama.")
        return cleaned_data
