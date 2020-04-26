from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory import views

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet, basename='article')
router.register(r'stocks', views.StockViewSet)
router.register(r'sales', views.SaleViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'users', views.UserViewset)


urlpatterns = [
    path("/", include(router.urls)),
    path("/getUser", views.getUser.as_view()),
    path("/getTotals", views.getTotals.as_view()),
    path("/getEarnings", views.getEarnings.as_view()),
]
