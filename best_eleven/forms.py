# best_eleven/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import BestEleven, Player

class TailwindCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = 'widgets/checkbox.html'
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs']['class'] = 'space-y-2'
        super().__init__(*args, **kwargs)

class BestElevenForm(forms.ModelForm):
    
    name = forms.CharField(
        label='Nama Formasi',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Misal: Tim Impian 2025'
        })
    )
    
    layout = forms.ChoiceField(
        choices=BestEleven.FORMATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500'
        })
    )
    
    players = forms.ModelMultipleChoiceField(
        queryset=Player.objects.all(),
        widget=TailwindCheckboxSelectMultiple(),
        required=True,
        label='Pilih Pemain (Harus 11)'
    )

    class Meta:
        model = BestEleven
        fields = ['name', 'layout', 'players']

    def clean_players(self):
        selected_players = self.cleaned_data.get('players')
        
        if selected_players and selected_players.count() != 11:
            raise ValidationError("Harap pilih tepat 11 pemain.")
            
        return selected_players