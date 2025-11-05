from django import forms

class MagicEmailForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "nombre@dominio.com",
            "autocomplete": "email",
            "inputmode": "email",
            "autocapitalize": "off",
            "spellcheck": "false",
            "id": "id_email",  # opcional, para asegurar coincidencia con CSS/JS
        })
    )
    next = forms.CharField(required=False, widget=forms.HiddenInput)

class EmailForm(forms.Form):
    email = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={
            "autofocus": True,
            "class": "form-control"
        })
    )

class PasswordForm(forms.Form):
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

class CodeForm(forms.Form):
    code = forms.CharField(
        label="Código",
        max_length=6,
        min_length=6,
        widget=forms.NumberInput(attrs={"inputmode": "numeric", "class": "form-control text-center"})
    )

class RegisterForm(forms.Form):
    first_name = forms.CharField(
        label="Nombre",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
