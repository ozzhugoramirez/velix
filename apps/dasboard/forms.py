
from django import forms
from apps.perfil.models import Coupon
from apps.user.models import UserAccount
from apps.shops.models import Product

class UserEditForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = [
            'username', 'first_name', 'last_name', 'email', 'whatsapp_number', 
            'is_active', 'is_verified', 'role', 'total_visitas',
            'verification_code', 'verification_code_expires_at', 'is_staff', 
            'is_superuser', 'groups', 'user_permissions'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'total_visitas': forms.NumberInput(attrs={'class': 'form-control'}),
        
            'verification_code': forms.TextInput(attrs={'class': 'form-control'}),
            'verification_code_expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'user_permissions': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }






class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'stock', 'category', 'image', 
            'is_daily_offer', 'offer_start_date', 'offer_end_date', 
            'is_promotional', 'promotion_start_date', 'promotion_end_date', 
            'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_daily_offer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'offer_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'offer_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_promotional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'promotion_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'promotion_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductEditForm(forms.ModelForm):
    nuevo_stock = forms.IntegerField(
        required=False,
        label="Añadir Stock",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Ingrese la cantidad adicional para agregar al stock actual."
    )

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'stock', 'category', 'image', 
            'is_daily_offer', 'offer_start_date', 'offer_end_date', 
            'is_promotional', 'promotion_start_date', 'promotion_end_date', 
            'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'offer_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'offer_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'promotion_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'promotion_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_daily_offer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_promotional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }




class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'discount_value', 'expiration_date', 'active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código (opcional)'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Valor de Descuento'}),
            'expiration_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
           
        }
