from rest_framework import serializers
from .models import Order

class OrderSerialzier(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = '__all__'

class QuerySerializer(serializers.Serializer):
    out_trade_no = serializers.CharField()
