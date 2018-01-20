from django.conf import settings
from django.views import View
from django.utils import timezone
from django.http import HttpResponse


from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework import permissions


from .serializers import SignatureSerialzier, AccessTokenSerializer, \
    UnifiedOrderSerialzier, OrderQuerySerializer
from .models import JsApiTicket, Order, AccessToken
from .utils import nonce_str as generate_nonce_str
from .utils import sign as sign_func

from .config import APP_ID, MCH_ID, NOTIFY_URL, SIGN_KEY, ORDER_URL

import time
import hashlib
import json
import dicttoxml
import xmltodict
import requests

class OrderView(GenericAPIView):
    serializer_class = OrderSerialzier
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.request.user
        busname = serializer.validated_data.get("busname")
        description = serializer.validated_data.get("description")
        total_fee = serializer.validated_data.get("total_fee")

        appid = APP_ID
        mch_id = MCH_ID

        nonce_str = generate_nonce_str()
        trade_type = "APP"
        notify_url = NOTIFY_URL

        if "HTTP_X_FORWARDED_FOR" in request.META:
            spbill_create_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            spbill_create_ip = request.META['REMOTE_ADDR']

        instance = Order.objects.create(
            owner=user,
            busname=busname,
            description=description,
            total_fee=total_fee,
        )

        instance.out_trade_no = timezone.now().strftime("%Y%m%d") + '{}'.format(instance.id)
        instance.save()

        payload = {
            "appid": appid,
            "mch_id": mch_id,
            "nonce_str": nonce_str,
            "body": description,
            "out_trade_no": instance.out_trade_no,
            "total_fee": total_fee,
            "spbill_create_ip": spbill_create_ip,
            "notify_url": notify_url,
            "trade_type": trade_type,
        }

        sign = sign_func(payload, SIGN_KEY)
        payload["sign"] = sign

        req_xml = dicttoxml.dicttoxml(payload, custom_root="xml")
        url = ORDER_URL

        res_xml = requests.post(url, req_xml, verify=False)
        res_xml.encoding = 'utf8'
        res_xml = res_xml.text
        res_obj = xmltodict.parse(res_xml)["xml"]
        return_code = res_obj["return_code"]

        if return_code == "FAIL":
            res = {
                "code": -1,
                "message": res_obj["return_msg"]
            }
        else:
            result_code = res_obj["result_code"]
            if result_code == "SUCCESS":
                prepay_id = res_obj["prepay_id"]
                instance.prepay_id = prepay_id
                instance.save()
                ts = int(time.time())
                nonce_str = generate_nonce_str()
                package = 'Sign=WXPay'
                sign_type = "MD5"

                sign_payload = {
                    'appid': appid,
                    'partnerid': mch_id,
                    'prepayid': prepay_id,
                    'noncestr': nonce_str,
                    'timestamp': ts,
                    'package': package
                }

                pay_sign = sign_func(sign_payload, SIGN_KEY])

                res = {
                    "code": 0,
                    "message": "ok",
                    "timestamp": ts,
                    "nonce_str": nonce_str,
                    "package": package,
                    "sign_type": sign_type,
                    "pay_sign": pay_sign,
                    "prepay_id": prepay_id,
                    "out_trade_no": instance.out_trade_no,
                    "partner_id": mch_id
                }
            else:
                res = {
                    "code": 1,
                    "message": res_obj["err_code_des"]
                }
                
        return Response(res)

# 微信通知
class PayNotifyView(View):  

    def post(self, request, *args, **kwargs):
        raw_data = request.read()
        xml_obj = xmltodict.parse(raw_data)["xml"]

        return_code = xml_obj["return_code"]
        if return_code != "SUCCESS":
            pass
        else:
            result_code = xml_obj["result_code"]
            if result_code == "SUCCESS":
                bank_type = xml_obj["bank_type"]
                total_fee = xml_obj["total_fee"]
                cash_fee = xml_obj.get("cash_fee")
                transaction_id = xml_obj["transaction_id"]
                out_trade_no = xml_obj["out_trade_no"]
                time_end = timezone.datetime.strptime(xml_obj["time_end"], "%Y%m%d%H%M%S")
                order = Order.objects.filter(out_trade_no=out_trade_no).first()
                if order:
                    if "%s" % order.total_fee == "%s" % total_fee:
                        order.bank_type = bank_type
                        order.cash_fee = cash_fee
                        order.transaction_id = transaction_id
                        order.time_end = time_end
                        order.status = True
                        order.save()

        res_xml = """<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"""
        return HttpResponse(res_xml, content_type="application/xml")


class OrderQueryView(GenericAPIView):
    serializer_class = OrderQuerySerializer
    permission_classes = (permissions.AllowAny, )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prepay_id = serializer.validated_data.get("prepay_id")
        out_trade_no = serializer.validated_data.get("out_trade_no")

        instance = Order.objects.filter(out_trade_no=out_trade_no).first()
        if not instance:
            return Response({"code": -1, "message": "订单号错误"})
        if instance.status == "1":
            return Response({"code": 0, "message": "支付成功"})
        appid = APP_ID
        mch_id = MCH_ID
        nonce_str = generate_nonce_str()
        payload = {
            "appid": appid,
            "mch_id": mch_id,
            "nonce_str": nonce_str,
            "out_trade_no": out_trade_no
        }
        sign = sign_func(payload, SIGN_KEY)
        payload["sign"] = sign
        req_xml = dicttoxml.dicttoxml(payload, custom_root="xml")
        url = QUERY_URL
        res_xml = requests.post(url, req_xml, verify=False)
        res_xml.encoding = 'utf8'
        res_xml = req_xml.text
        res_obj = xmltodict.parse(res_xml)["xml"]
        return_code = res_obj["return_code"]
        if return_code == "FAIL":
            res = {
                "code": -1,
                "message": res_obj["return_msg"]
            }
        else:
            result_code = res_obj["result_code"]
            trade_state = res_obj["trade_state"]
            if result_code == "SUCCESS" and trade_state == "SUCCESS":
                appid = res_obj["appid"]
                mch_id = res_obj["mch_id"]
                nonce_str = res_obj["nonce_str"]
                sign = res_obj["sign"]
                openid = res_obj["openid"]
                trade_type = res_obj["trade_type"]
                bank_type = res_obj["bank_type"]
                total_fee = res_obj["total_fee"]
                cash_fee = res_obj.get("cash_fee")
                transaction_id = res_obj["transaction_id"]
                out_trade_no = res_obj["out_trade_no"]
                time_end = timezone.datetime.strptime(
                    res_obj["time_end"], "%Y%m%d%H%M%S")
                order = Order.objects.filter(
                    openid=openid, out_trade_no=out_trade_no)
                if order:
                    if order.total_fee == total_fee:
                        order.bank_type = bank_type
                        order.cash_fee = cash_fee
                        order.transaction_id = transaction_id
                        order.time_end = time_end
                        order.status = True
                        order.save()
                        return Response({"code": 0, "message": "支付成功"})
        return Response({"code": 1, "message": "支付未完成"})
