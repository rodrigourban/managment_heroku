from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ArticleSerializer, StockSerializer, SaleSerializer, OrderSerializer, UserSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, DecimalField, IntegerField
from django.contrib.auth import get_user_model
from .models import Article, Stock, Sale, Order
import logging
import copy

views_logger = logging.getLogger(__name__)
User = get_user_model()


class ArticleViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication,)
    pagination_class = PageNumberPagination

    def get_queryset(self):
        search = self.request.query_params.get('search', "")
        orderField = self.request.query_params.get('order', 'created_at')
        orderType = self.request.query_params.get('type', "")
        queryset = Article.objects.filter(status=True, name__icontains=search).order_by(
            '%s%s' % (orderType, orderField)) | Article.objects.filter(status=True, sku__icontains=search).order_by(
            '%s%s' % (orderType, orderField)) | Article.objects.filter(status=True, location__icontains=search).order_by(
            '%s%s' % (orderType, orderField)) | Article.objects.filter(status=True, created_at__icontains=search).order_by(
            '%s%s' % (orderType, orderField))
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            views_logger.info("%s IS CREATING AN ARTICLE", self.request.user)
            payload = copy.copy(request.data)
            views_logger.info("%s", payload)
            payload['created_by'] = self.request.user.pk
            payload['updated_by'] = self.request.user.pk
            payload['status'] = True
            views_logger.info("%s IS CREATING AN ARTICLE", payload)
            serializer = ArticleSerializer(data=payload)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            article = Article.objects.get(name=payload['name'])
            serializerStock = StockSerializer(data={
                'article': article.id,
                'quantity': payload['quantity'],
                'cost': payload['cost'],
                'created_by': self.request.user.pk,
                'updated_by': self.request.user.pk,
            })
            serializerStock.is_valid(raise_exception=True)
            serializerStock.save()
            views_logger.info("ARTICLE CREATED SUCCESSFULLY")
            return Response(serializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE CREATING ARTICLE %s", error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            views_logger.info("RETRIEVING ARTICLES FOR %s", self.request.user)
            instance = self.get_object()
            serializer = ArticleSerializer(
                instance=instance)
            return Response(serializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE RETRIEVING ARTICLE %s" % error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        try:
            views_logger.info("START PARTIAL UPDATE ARTICLE")
            payload = request.data
            views_logger.info("%s", payload)
            payload['updated_by'] = self.request.user.pk
            article = Article.objects.get(id=pk)
            serializer = ArticleSerializer(
                article, data=payload, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            views_logger.info("ARTICLE UPDATED SUCCESSFULLY")
            views_logger.info(serializer.data)
            return Response(serializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE UPDATING ARTICLE %s" % error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def create(self, request, *args, **kwargs):
        try:
            views_logger.info("%s IS CREATING AN STOCK", self.request.user)
            payload = copy.copy(request.data)
            views_logger.info("%s", payload)
            payload['created_by'] = self.request.user.pk
            payload['updated_by'] = self.request.user.pk
            serializerStock = StockSerializer(data=payload)
            serializerStock.is_valid(raise_exception=True)
            serializerStock.save()
            views_logger.info("ARTICLE CREATED SUCCESSFULLY")
            return Response(serializerStock.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE CREATING ARTICLE %s", error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        search = self.request.query_params.get('search', "")
        orderField = self.request.query_params.get(
            'order', 'created_at')
        orderType = ''
        if (orderField[0] == '-'):
            orderType = '-'
            orderField = orderField[1:]
        if (orderField == 'name' or orderField == '-name'):
            orderField = 'stock__article__name'
        queryset = Sale.objects.filter(
            status=True).order_by('%s%s' % (orderType, orderField))
        queryset = Sale.objects.filter(status=True, quantity__icontains=search).order_by(
            '%s%s' % (orderType, orderField)) | Sale.objects.filter(status=True, price__icontains=search).order_by(
            '%s%s' % (orderType, orderField)) | Sale.objects.filter(status=True, created_at__icontains=search).order_by(
            '%s%s' % (orderType, orderField))
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            views_logger.info("START CREATING SALE")
            views_logger.info("%s", request.data)
            quantity = int(self.request.data['quantity'])
            res = Stock.objects.filter(
                article=self.request.data['article']).aggregate(article_total_stock=Sum('quantity'))
            views_logger.info("TOTAL STOCK IS %s" %
                              res['article_total_stock'])
            if (res['article_total_stock'] >= quantity):
                views_logger.info("ENOUGH STOCK TO CREATE SALE")
                stocks = Stock.objects.filter(
                    article=self.request.data['article']).order_by('-created_at')
                i = 0
                while (quantity > 0):
                    new_quantity = stocks[i].quantity - quantity
                    stock_payload = {'quantity': new_quantity,
                                     'updated_by': self.request.user.pk}
                    sale_payload = {
                        'stock': stocks[i].pk,
                        'price': request.data['price'],
                        'quantity': quantity,
                        'created_by': self.request.user.pk,
                        'updated_by': self.request.user.pk
                    }
                    if (new_quantity < 0):
                        quantity = abs(new_quantity)
                        sale_payload['quantity'] = stocks[i].quantity
                        stock_payload['quantity'] = 0
                        stock_payload['status'] = False
                    else:
                        quantity = 0
                        if (new_quantity == 0):
                            stock_payload['status'] = False

                    saleSerializer = SaleSerializer(data=sale_payload)
                    stockSerializer = StockSerializer(
                        stocks[i], data=stock_payload, partial=True)
                    saleSerializer.is_valid(raise_exception=True)
                    stockSerializer.is_valid(raise_exception=True)
                    saleSerializer.save()
                    stockSerializer.save()
                    i += 1
                    new_quantity = 0
            else:
                views_logger.info("CANT CREATE SALE, NOT ENOUGH STOCK")
                return Response({'message': 'No hay stock suficiente.'}, status.HTTP_400_BAD_REQUEST)
            views_logger.info("ARTICLE CREATED SUCCESSFULLY")
            return Response(saleSerializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE CREATING ARTICLE %s", error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        try:
            views_logger.info("START PARTIAL UPDATE SALE")
            payload = request.data
            views_logger.info("%s", payload)
            payload['updated_by'] = self.request.user.pk
            sale = Sale.objects.get(id=pk)
            serializer = SaleSerializer(
                sale, data=payload, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            views_logger.info("SALE UPDATED SUCCESSFULLY")
            views_logger.info(serializer.data)
            return Response(serializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE UPDATING SALE %s" % error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        search = self.request.query_params.get('search', "")
        orderField = self.request.query_params.get('order', 'created_at')
        orderType = ''
        if (orderField[0] == '-'):
            orderType = '-'
            orderField = orderField[1:]
        if (orderField == 'name' or orderField == '-name'):
            orderField = 'article__name'
        queryset = Order.objects.filter(status=True, state__icontains=search).order_by(
            '%s%s' % (orderType, orderField)) | Order.objects.filter(status=True, body__icontains=search).order_by(
            '%s%s' % (orderType, orderField))
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            views_logger.info("START CREATE ORDER %s" % self.request.user)
            payload = request.data
            views_logger.info("%s", payload)
            payload['created_by'] = self.request.user.pk
            payload['updated_by'] = self.request.user.pk
            serializer = OrderSerializer(data=payload)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            views_logger.info("ORDER CREATED SUCCESSFULLY")
            return Response(serializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE RETRIEVING ARTICLE %s" % error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        try:
            views_logger.info("START PARTIAL UPDATE ORDER")
            payload = request.data
            views_logger.info("%s", payload)
            payload['updated_by'] = self.request.user.pk
            order = Order.objects.get(id=pk)
            serializer = OrderSerializer(
                order, data=payload, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            views_logger.info("ORDER UPDATED SUCCESSFULLY")
            views_logger.info(serializer.data)
            return Response(serializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE UPDATING ORDER %s" % error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)


class UserViewset(viewsets.ModelViewSet):
    # Viewset automatically provides "list" and "detail"
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        search = self.request.query_params.get('search', "")
        orderField = self.request.query_params.get('order', 'date_joined')
        orderType = ''
        queryset = User.objects.filter(is_active=True, username__icontains=search).order_by(
            '%s%s' % (orderType, orderField)) | User.objects.filter(is_active=True, email__icontains=search).order_by(
            '%s%s' % (orderType, orderField))
        return queryset

    def partial_update(self, request, pk=None):
        try:
            views_logger.info("START PARTIAL UPDATE USER")
            payload = request.data
            views_logger.info("%s", payload)
            user = User.objects.get(id=pk)
            serializer = UserSerializer(
                user, data=payload, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            views_logger.info("USER UPDATED SUCCESSFULLY")
            views_logger.info(serializer.data)
            return Response(serializer.data)
        except ValidationError as error:
            views_logger.error("ERROR WHILE UPDATING USER %s" % error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)


class getUser(APIView):
    # permission_classes = (permissions.IsAuthenticated,)
    def post(self, request, format=None):
        print("Averga ", request.data)
        if 'token' not in request.data:
            return Response({'message': 'Please enter token'})
        data = request.data
        token = Token.objects.get(key=data['token'])
        User = UserSerializer(token.user)
        return Response(User.data)


class getTotals(APIView):
    def get(self, request, format=None):
        try:
            res = Stock.objects.filter(article__status=True,
                                       status=True).aggregate(stock_total=Sum('quantity'), price_total=(Sum(F('quantity') * F('cost'), output_field=DecimalField())))
            # res2 = Stock.objects.filter(
            # status=True).aggregate(total=(Sum(F('quantity') * F('cost'))))['total']
            return Response(res)
        except ValidationError as error:
            views_logger.error("ERROR WHILE GET TOTALS %s" % error)
            return Response({'message': error.as_json}, status.HTTP_400_BAD_REQUEST)


class getEarnings(APIView):
    def post(self, request, format=None):
        try:
            if 'dateFrom' not in request.data.keys() or 'dateTo' not in request.data.keys():
                raise ValidationError("Please provide dateFrom and dateTo")
            dateFrom = self.request.data.get('dateFrom', None)
            dateTo = self.request.data.get('dateTo', None)
            dateType = self.request.data.get('dateType', None)
            sales = Sale.objects.filter(
                status=True, created_at__gte=dateFrom, created_at__lte=dateTo)
            labels = []
            earnings_data = []
            quantity_data = []
            earnings_total = 0
            quantity_total = 0
            import datetime
            for el in sales:
                cost = el.stock.cost
                labels.append(el.created_at.strftime("%d/%b/%Y"))
                earnings_data.append(
                    (el.quantity*el.price) - (el.quantity*cost))
                quantity_data.append(el.quantity)
                earnings_total += (el.quantity*el.price) - (el.quantity*cost)
                quantity_total += el.quantity
            return Response(
                {"labels": labels, "earnings": earnings_data, "quantity": quantity_data,
                    "quantity_total": quantity_total, "earnings_total": earnings_total},
                status.HTTP_200_OK
            )
        except ValidationError as error:
            views_logger.error("ERROR GET EARNINGS %s" % error)
            return Response({'message': error.message}, status.HTTP_400_BAD_REQUEST)
