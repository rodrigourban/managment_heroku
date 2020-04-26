from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db.models import Sum
from .models import Article, Stock, Sale, Order

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "pk",
            "username",
            "email",
            "date_joined",
            "is_staff",
            "is_active"
        )


class ArticleSerializer(serializers.ModelSerializer):
    cost = serializers.SerializerMethodField('get_cost')
    quantity = serializers.SerializerMethodField('get_stock')
    stock_list = serializers.SerializerMethodField('get_stock_list')

    def get_cost(self, obj):
        stock = Stock.objects.filter(
            article=obj.pk).order_by('created_at')
        count = 0
        if stock.count() >= 1:
            count = stock[0].cost
        return count

    def get_stock(self, obj):
        res = Stock.objects.filter(article=obj.pk, status=True).aggregate(
            article_total_stock=Sum('quantity'))
        stock = 0
        if res['article_total_stock']:
            stock = res['article_total_stock']
        return stock

    def get_stock_list(self, obj):
        stock = Stock.objects.filter(article=obj.pk, status=True)
        stockSerializer = StockSerializer(stock, many=True)
        return stockSerializer.data

    class Meta:
        model = Article
        fields = (
            "id",
            "name",
            "sku",
            "location",
            "suggested_price",
            "cost",
            "quantity",
            "status",
            "image",
            "link",
            "stock_list",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by"
        )


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = (
            "id",
            "article",
            "quantity",
            "cost",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by"
        )


class SaleSerializer(serializers.ModelSerializer):
    article = serializers.ReadOnlyField()
    additional = serializers.SerializerMethodField('get_net_gross')

    def get_net_gross(self, obj):
        stock = obj.stock
        article = obj.stock.article
        _gross = (obj.quantity * obj.price)
        return {
            'cost': stock.cost,
            'net': _gross,
            'gross': _gross - (obj.quantity * stock.cost),
            'article': article.name
        }

    class Meta:
        model = Sale
        fields = (
            "id",
            "additional",
            "stock",
            "quantity",
            "article",
            "price",
            "status",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by"
        )


class OrderSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('get_article_name')

    def get_article_name(self, obj):
        return obj.article.name

    class Meta:
        model = Order
        fields = (
            "id",
            "article",
            "name",
            "body",
            "status",
            "state",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by"
        )
