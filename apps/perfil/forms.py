from django import forms
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['localidad', 'postal_code', 'barrio', 'whatsapp_number', 'email', 'main_street', 'secondary_street', 'house_number', 'description']
        widgets = {
            'localidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Localidad'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código postal'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barrio'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de WhatsApp'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'main_street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle principal'}),
            'secondary_street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle secundaria'}),
            'house_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de casa'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Descripción adicional', 'rows': 3}),
        }



class CouponForm(forms.Form):
    code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ingresa tu código de cupón'
    }))
