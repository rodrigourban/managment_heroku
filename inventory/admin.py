from django.contrib import admin
from .models import Article, Stock, Sale, Order


# Register your models here.
admin.site.register(Article)
admin.site.register(Stock)
admin.site.register(Sale)
admin.site.register(Order)
