# python-wechat-pay
Use Django, Django-rest-framework to achieve wechat payment.

微信支付、服务器异步通知、订单查询、退款

## 统一下单

### 应用场景

    商户系统先调用该接口在微信支付服务后台生成预支付交易单，返回正确的预支付交易回话标识后再在APP里调起支付

### 接口连接
    
    https://api.mch.weixin.qq.com/pay/unifiedorder

### 是否需要证书
    
    不需要

### 请求参数（必传字段）
    
    body （商品描述）
    total_fee （订单总金额，单位为分）
    appid（放置于服务端）
    mch_id （放置于服务端）
    nonce_str （随机字符串，不长于32位）
    trade_type = "APP" （交易类型）
    spbill_create_ip （ip地址）
    out_trade_no （商户系统内部订单号，要求32个字符内，只能是数字、大小写字母_-|*@ ，且在同一个商户号下唯一）
    notify_url （接收微信支付异步通知回调地址，通知url必须为直接可访问的url，不能携带参数。）
    sign (签名)
    

#### 随机字符串的生成Python代码

```
import string
import random

def nonce_str(size=32):
    charsets = string.ascii_uppercase + string.digits
    result = []
    for index in range(0, size):
        result.append(random.choice(charsets))
    return "".join(result)
    
```

#### 签名的生成Python代码
    sign_key设置路径：微信商户平台(pay.weixin.qq.com)-->账户设置-->API安全-->密钥设置
    
    设置图片url: http://img.blog.csdn.net/20151126154045054?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQv/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/Center

    payload即为支付请求参数的字典集合

```
# payload
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
```

```
import hashlib

def sign(payload, sign_key=None):
    lst = []
    for key, value in payload.items():
        lst.append("%s=%s" % (key, value))
    lst.sort()
    raw_str = "&".join(lst)
    if sign_key:
        raw_str += "&key=%s" % sign_key
    md5 = hashlib.md5()
    md5.update(raw_str.encode('utf8'))
    return md5.hexdigest().upper()
```

### 返回支付信息调起微信APP进行支付
```
import dicttoxml

req_xml = dicttoxml.dicttoxml(payload, custom_root="xml")
# 微信统一支付接口
url = "https://api.mch.weixin.qq.com/pay/unifiedorder"

res_xml = requests.post(url, req_xml, verify=False)
res_xml.encoding = 'utf8'
res_xml = res_xml.text
res_obj = xmltodict.parse(res_xml)["xml"]
return_code = res_obj["return_code"]
```
1. 如果return_code == 'FAIL': 签名配置出现问题，res_obj["return_msg"]中会介绍出现问题的原因
2. 如果return_code == 'SUCCESS':接口调用成功，返回如下格式代码（XML）
```
<xml>
   <return_code><![CDATA[SUCCESS]]></return_code>
   <return_msg><![CDATA[OK]]></return_msg>
   <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
   <mch_id><![CDATA[10000100]]></mch_id>
   <nonce_str><![CDATA[IITRi8Iabbblz1Jc]]></nonce_str>
   <sign><![CDATA[7921E432F65EB8ED0CE9755F0E86D72F]]></sign>
   <result_code><![CDATA[SUCCESS]]></result_code>
   <prepay_id><![CDATA[wx201411101639507cbf6ffd8b0779950874]]></prepay_id>
   <trade_type><![CDATA[APP]]></trade_type>
</xml>
```
### 调用支付接口(必传字段)
    appid
    partnerid
    prepayid（预支付交易会话ID）
    package （扩展字段）
    noncestr （随机字符串）
    timestamp （时间戳）
    sign （签名）

> 我们需要返回数据进行再次签名操作

```
prepay_id = res_obj["prepay_id"]
ts = str(int(time.time()))
nonce_str = generate_nonce_str()
package = "prepay_id=%s" % prepay_id
sign_type = "MD5"

sign_payload = {
    'appid': appid,
    'partnerid': mch_id,
    'prepayid': prepay_id,
    'noncestr': nonce_str,
    'timestamp': ts,
    'package': package
}

pay_sign = sign_func(
    sign_payload, settings.WEIXIN_ENTERPRISE_APP["SIGN_KEY"])

```
> 向前端发送与支付信息，调起微信APP进行支付

```
res = {
    "timestamp": ts,
    "nonce_str": nonce_str,
    "package": package,
    "sign_type": sign_type,
    "pay_sign": pay_sign,
    "prepay_id": prepay_id,
    "out_trade_no": out_trade_no,
    "partner_id": mch_id
}
```

### 微信2次签名问题

1. sign_payload中key使用小写方式，并且字段为确定的6个字段，不能修改；生成签名时，将生成的签名再转化成大写，传递到前端；
2. 关于时间戳，生成sign的时候，时间戳使用int类型；前端使用时，该字段应为str类型的；


