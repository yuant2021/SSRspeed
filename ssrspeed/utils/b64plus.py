#coding:utf-8
import logging
import base64
logger = logging.getLogger("Sub")
def fillb64(data):
        if data[:2] == "ss" or data[:5] == "vmess":
                return data
        if len(data) % 4:
                data += "=" * (4 - (len(data) % 4))
        return data

def _url_safe_decode(s: str):
	s = fillb64(s)
	if s[:2] == "ss"or s[:5] == "vmess":
                return s
	s = s.replace("-", "+").replace("_", "/")
	a=base64.b64decode(s, validate=True)
	return base64.b64decode(s, validate=True)

def encode(s):
	s = s.encode("utf-8")
	return base64.urlsafe_b64encode(s)

def decode(s):
        return _url_safe_decode(s)
