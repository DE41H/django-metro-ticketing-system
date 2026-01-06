from django import forms
from stations.models import Station, Line

class StationForm(forms.ModelForm):
    
    class Meta:
        model = Station
        fields = ['name', 'lines', 'neighbours']
        widgets = {
            'lines': forms.CheckboxSelectMultiple(),
            'neighbours': forms.CheckboxSelectMultiple()
        }

class LineForm(forms.ModelForm):
    
    class Meta:
        model = Line
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px; padding: 2px;'}),
        }
