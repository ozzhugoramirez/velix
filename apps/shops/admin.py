from django.contrib import admin
from .models import *

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductView)
admin.site.register(ProductRecommendation)
admin.site.register(UserPoints)

admin.site.register(ProductShare)
admin.site.register(ShareVisit)
admin.site.register(Comment)

admin.site.register(Proveedor)
admin.site.register(VendedorExterno)




