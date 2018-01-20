from django.db import models

class Order(models.Model):
    prepay_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="预支付交易会话标识")
    out_trade_no = models.CharField(max_length=64, null=True, blank=True, verbose_name="商户订单号")
    transaction_id = models.CharField(max_length=64, null=True, blank=True, verbose_name="微信支付订单号")
    bank_type = models.CharField(max_length=64, null=True, blank=True, verbose_name="付款银行")
    cash_fee = models.IntegerField(null=True, blank=True, verbose_name="现金支付金额")
    time_end = models.DateTimeField(null=True, blank=True, verbose_name="支付完成时间")
    busname = models.CharField(max_length=16, null=True, blank=True, verbose_name="业务")
    description = models.TextField(verbose_name="商品描述")
    total_fee = models.IntegerField(verbose_name="订单总金额", help_text="订单总金额，单位分")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.description
