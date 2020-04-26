import logging
from django.db import models

models_logger = logging.getLogger(__name__)


class Article(models.Model):
    """
    Article model
    Defines the attributes of every item on the inventory.
    """
    name = models.CharField(max_length=200, unique=True)
    sku = models.CharField(max_length=200, unique=True)
    location = models.CharField(max_length=200)
    suggested_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    status = models.BooleanField(default=True)
    image = models.ImageField(upload_to='images', default='default.png')
    link = models.CharField(max_length=200, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', related_name='article_creator', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(
        'auth.User', related_name='article_editor', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Stock(models.Model):
    """
    Article model
    Defines the attributes of every article's stock.
    """
    article = models.ForeignKey(
        Article, related_name='stock_article', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', related_name='stock_creator', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(
        'auth.User', related_name='stock_editor', on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (str(self.updated_at), self.article.name)


class Sale(models.Model):
    """
    Article model
    Defines the attributes of every sale made by the store.
    """
    stock = models.ForeignKey(
        Stock, related_name='sale_stock', on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', related_name='sale_creator', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(
        'auth.User', related_name='sale_editor', on_delete=models.CASCADE)


class Order(models.Model):
    """
    Article model
    Defines the attributes of every article's order.
    """
    # FRESHMAN = 'FR'
    # SOPHOMORE = 'SO'
    # JUNIOR = 'JR'
    # SENIOR = 'SR'
    # GRADUATE = 'GR'
    # YEAR_IN_SCHOOL_CHOICES = [
    #     (FRESHMAN, 'Freshman'),
    #     (SOPHOMORE, 'Sophomore'),
    #     (JUNIOR, 'Junior'),
    #     (SENIOR, 'Senior'),
    #     (GRADUATE, 'Graduate'),
    # ]
    # year_in_school = models.CharField(
    #     max_length=2,
    #     choices=YEAR_IN_SCHOOL_CHOICES,
    #     default=FRESHMAN,
    # )
    article = models.ForeignKey(
        Article, related_name='order_article', on_delete=models.CASCADE)
    body = models.TextField(default="")
    state = models.CharField(max_length=200, default="PENDIENTE")
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', related_name='order_creator', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(
        'auth.User', related_name='order_editor', on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (self.article.name, self.status)
