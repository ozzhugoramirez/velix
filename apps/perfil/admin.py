from django.contrib import admin
from .models import *
from django.utils.html import format_html


admin.site.register(Perfil)
admin.site.register(Notification)
admin.site.register(NotificationGroup)
admin.site.register(NotificationReadStatus)


admin.site.register(CartItem)
admin.site.register(Coupon)

admin.site.register(Cart)
admin.site.register(CommentURL)


admin.site.register(Address)
admin.site.register(Order)
admin.site.register(Invoice)
admin.site.register(OrderItem)






