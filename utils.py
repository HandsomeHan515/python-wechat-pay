import string
import random
import hashlib


def nonce_str(size=32):
    charsets = string.ascii_uppercase + string.digits
    result = []
    for index in range(0, size):
        result.append(random.choice(charsets))
    return "".join(result)


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
