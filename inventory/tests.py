import io
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient
from inventory.serializers import ArticleSerializer, SaleSerializer, OrderSerializer, StockSerializer, UserSerializer
from inventory.models import Article, Stock, Sale, Order

# ARTICLES_URL = reverse('api:articles')
# Test cases to add:
# isAuthenticated on everyview.
# message errors on fail
# there is not enough stock to do that sell
# filtered list
# sorted list
# pagination
# user role different fields on list
User = get_user_model()


class TestUser(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_user_list(self):
        # Only admins can see this list
        User.objects.create(
            username='testuser1@gmail.com',
            password='testpassw00rd'
        )
        User.objects.create(
            username='testuser2@gmail.com',
            password='testpassw00rd'
        )
        User.objects.create(
            username='testuser3@gmail.com',
            password='testpassw00rd'
        )
        users = User.objects.all()
        userSerializer = UserSerializer(users, many=True)
        res = self.client.get('/api/users/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], userSerializer.data)


class TestArticle(TestCase):
    """ Test module for Article model """

    def setUp(self):
        self.client = APIClient()
        self.unauthenticated_client = APIClient()

        self.user = get_user_model().objects.create(
            username='testuser@gmail.com',
            password='testpassw00rd'
        )
        self.client.force_authenticate(self.user)

    def generate_image(self):
        file = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)
        return file

    def test_get_all_articles(self):
        Article.objects.create(
            name="Articulo 1", sku="ART1331", location="Caja 1",
            suggested_price=350.65, link="mercadolibre.com.mx/articulo-mex",
            created_by=self.user, updated_by=self.user
        )
        Article.objects.create(
            name="Articulo 2", sku="ART244421", location="Caja 2",
            suggested_price=450.65, link="mercadolibre.com.mx/articulo-mex/2",
            created_by=self.user, updated_by=self.user
        )
        res = self.client.get('/api/articles/')
        articles = Article.objects.filter(status=True)
        serializer = ArticleSerializer(articles, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 2)

    def test_create_article_and_stock(self):
        payload = {
            'name': "Articulo 3",
            'sku': "ART123",
            'location': 'CAJA 1',
            'suggested_price': 560.32,
            'image': self.generate_image(),
            'link': 'mercadolibre.com.mx/test',
            'quantity': 3,
            'cost': 300.52,
        }
        res = self.client.post('/api/articles/', payload, format='multipart')
        article = Article.objects.filter(
            name=payload['name']
        )
        stock = Stock.objects.filter(
            article=article[0].id
        )
        self.assertTrue(article.exists())
        self.assertTrue(stock.exists())

    def test_create_article_without_photo(self):
        payload = {
            'name': "Articulo 3",
            'sku': "ART123",
            'location': 'CAJA 1',
            'suggested_price': 560.32,
            'link': 'mercadolibre.com.mx/test',
            'quantity': 3,
            'cost': 300.52,
        }
        res = self.client.post('/api/articles/', payload, format='multipart')
        article = Article.objects.filter(
            name=payload['name']
        )
        stock = Stock.objects.filter(
            article=article[0].id
        )
        self.assertTrue(article.exists())
        self.assertTrue(stock.exists())

    def test_article_list_not_authenticated(self):
        res = self.unauthenticated_client.get('/api/articles/')
        self.assertEquals(status.HTTP_401_UNAUTHORIZED, res.status_code)

    def test_get_articles_filtered(self):
        Article.objects.create(
            name="Black helmet", sku="HHH1", location="Caja 1",
            suggested_price=350.65, link="mercadolibre.com.mx/articulo-mex/1",
            created_by=self.user, updated_by=self.user
        )
        Article.objects.create(
            name="Wheels", sku="ART1331", location="Caja 1",
            suggested_price=350.65, link="mercadolibre.com.mx/articulo-mex/2",
            created_by=self.user, updated_by=self.user
        )
        Article.objects.create(
            name="Red helmet %s", sku="HHH2", location="Caja 1",
            suggested_price=350.65, link="mercadolibre.com.mx/articulo-mex/3",
            created_by=self.user, updated_by=self.user
        )
        res = self.client.get('/api/articles/?search=helmet')
        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.assertEquals(res.data['count'], 2)


class TestSale(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            username='testuser@gmail.com',
            password='testpassw00rd'
        )
        self.client.force_authenticate(self.user)

        Article.objects.create(
            name="Articulo 3", sku="ART3", location="Caja 3",
            suggested_price=350.65, link="mercadolibre.com.mx/articulo-mex/3",
            created_by=self.user, updated_by=self.user
        )
        self.article = Article.objects.get(name="Articulo 3")

    def test_create_sale_quantity_bigger_than_stock(self):
        Stock.objects.create(article=self.article, quantity=3,
                             cost=300.53, created_by=self.user, updated_by=self.user)
        Stock.objects.create(article=self.article, quantity=3,
                             cost=300.53, created_by=self.user, updated_by=self.user)
        payload = {
            "article": self.article.id,
            "quantity": 5,
            "price": 550.54
        }
        res = self.client.post('/api/sales/', payload)
        stock = Stock.objects.filter(
            article=self.article).order_by('-created_at')
        print("Hola %s %s %s %s" % (
            stock[0].quantity, stock[0].status, stock[1].status, stock[1].quantity))
        first_sale = Sale.objects.filter(stock=stock[0])
        second_sale = Sale.objects.filter(stock=stock[1])
        self.assertTrue(first_sale.exists())
        self.assertTrue(second_sale.exists())
        self.assertFalse(stock[0].status)
        self.assertEqual(stock[1].quantity, 1)
        self.assertTrue(stock[1].status)

    def test_create_sale_quantity_equal_than_stock(self):
        Stock.objects.create(article=self.article, quantity=5,
                             cost=300.53, created_by=self.user, updated_by=self.user)
        payload = {
            "article": self.article.id,
            "quantity": 5,
            "price": 550.54
        }
        res = self.client.post('/api/sales/', payload)
        stock = Stock.objects.get(article=self.article)
        sale = Sale.objects.filter(stock=stock)
        self.assertTrue(sale.exists())
        self.assertFalse(stock.status)

    def test_create_sale_quantity_smaller_than_stock(self):
        Stock.objects.create(article=self.article, quantity=5,
                             cost=300.53, created_by=self.user, updated_by=self.user)
        payload = {
            "article": self.article.id,
            "quantity": 2,
            "price": 550.54
        }
        res = self.client.post('/api/sales/', payload)
        stock = Stock.objects.get(article=self.article)
        sale = Sale.objects.filter(stock=stock)
        self.assertTrue(sale.exists())
        self.assertEqual(stock.quantity, 3)
        self.assertTrue(stock.status)

    def test_get_sales(self):
        Stock.objects.create(article=self.article, quantity=5,
                             cost=300.53, created_by=self.user, updated_by=self.user)
        stock = Stock.objects.get(article=self.article)
        Sale.objects.create(
            stock=stock, quantity=5, price=550.54,
            created_by=self.user, updated_by=self.user
        )
        Sale.objects.create(
            stock=stock, quantity=2, price=350.54,
            created_by=self.user, updated_by=self.user
        )
        res = self.client.get('/api/sales/')
        sales = Sale.objects.filter(status=True)
        serializer = SaleSerializer(sales, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['results'], serializer.data)

    def test_sell_more_that_stock(self):
        stock = Stock.objects.create(article=self.article, quantity=5,
                                     cost=300.53, created_by=self.user, updated_by=self.user)
        payload = {
            'article': self.article.id,
            'quantity': 10,
            'price': 200.50,
        }
        res = self.client.post('/api/sales/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class TestOrder(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            username='testuser@gmail.com',
            password='testpassw00rd'
        )
        self.client.force_authenticate(self.user)
        Article.objects.create(
            name="Articulo 4", sku="ART4", location="Caja 4",
            suggested_price=350.65, link="mercadolibre.com.mx/articulo-mex/4",
            created_by=self.user, updated_by=self.user
        )
        self.article = Article.objects.get(name="Articulo 4")

    def test_create_order(self):
        payload = {
            "article": self.article.id,
            "body": "Todavia no se pidio",
        }
        res = self.client.post('/api/orders/', payload)
        order = Order.objects.filter(
            article=payload['article']
        )
        self.assertTrue(order.exists())
        self.assertEqual(order[0].state, "PENDIENTE")

    def test_update_order_status(self):
        Order.objects.create(article=self.article, body="Nothing",
                             created_by=self.user, updated_by=self.user)
        order = Order.objects.filter(article=self.article)
        payload = {
            "article": self.article.id,
            "state": "EN CAMINO",
        }
        res = self.client.patch('/api/orders/%s/' % order[0].id, payload)
        order = Order.objects.filter(
            article=self.article
        )
        self.assertTrue(order.exists())
        self.assertEqual(order[0].state, "EN CAMINO")


class TestHelpers(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            username='testuser@gmail.com',
            password='testpassw00rd'
        )
        self.client.force_authenticate(self.user)

    def test_get_inventory_configuration_info(self):
        # retrieve columns, stock_total, money_total
        pass
