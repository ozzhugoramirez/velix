from apps.perfil.models import Cart

def cart_item_count(request):
    if request.user.is_authenticated:
        # Obtener el carrito activo (si existe) o None
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        
        if cart:
            # Si el carrito existe, contar los productos
            item_count = sum(item.quantity for item in cart.items.all())
        else:
            # Si no hay carrito activo, no hay productos
            item_count = 0
    else:
        # Si el usuario no está autenticado, no hay carrito
        item_count = 0

    return {
        'cart_item_count': item_count
    }
