from typing import Any
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

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        selected_lines = cleaned_data.get('lines')
        selected_neighbours = cleaned_data.get('neighbours')
        if selected_lines is None or selected_neighbours is None:
            return cleaned_data
        selected_lines = set(selected_lines)
        for neighbour in selected_neighbours:
            neighbour_lines = set(neighbour.lines.all())
            if not len(neighbour_lines & selected_lines):
                raise forms.ValidationError('The station has no matching lines with some of the chosen neighbour(s)!')
        return cleaned_data

class LineForm(forms.ModelForm):
    
    class Meta:
        model = Line
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color', 'style': 'height: 40px; padding: 2px;'}),
        }
