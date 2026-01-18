from django import forms
from .models import Address


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'latitude', 'longitude', 
            'localidad', 'postal_code', 'barrio', 
            'main_street', 'secondary_street', 'house_number', 
            'floor', 'apartment', 'description',
            'whatsapp_number', 'email'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- CONFIGURACIÓN CRÍTICA ---
        # Hacemos estos campos opcionales en la validación del formulario.
        # Esto evita que falle si el JavaScript del mapa no envía el dato exacto 
        # o si el usuario deja campos vacíos que el modelo permite.
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['secondary_street'].required = False
        self.fields['floor'].required = False
        self.fields['apartment'].required = False
        self.fields['description'].required = False
        self.fields['postal_code'].required = False
        self.fields['barrio'].required = False
        
        # Los campos obligatorios siguen siéndolo por definición del Modelo:
        # main_street, localidad, house_number, whatsapp_number

class CouponForm(forms.Form):
    code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ingresa tu código de cupón'
    }))
