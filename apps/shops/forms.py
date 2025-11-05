from django import forms

from apps.perfil.models import OrderItem
from apps.shops.models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe tu comentario aquí...',
                'rows': 4,  # Ajusta el tamaño según lo que prefieras
                'style': 'resize: none; border-radius: 8px; box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);',
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not OrderItem.objects.filter(
            order__user=self.user,
            order__is_paid=True,
            product=self.product
        ).exists():
            raise forms.ValidationError("No puedes comentar sobre un producto que no has comprado.")
        return cleaned_data
