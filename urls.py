from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from .views import OrderView, PayNotifyView, OrderQueryView


urlpatterns = [
    url(r"^order/$", OrderView.as_view(), name="order"),
    url(r"^notify/$", csrf_exempt(PayNotifyView.as_view()), name="notify"),
    url(r"^orderquery/$", OrderQueryView.as_view(), name="orderquery"),
]
