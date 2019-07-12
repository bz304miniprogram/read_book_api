import base64
import json
from Crypto.Cipher import AES
from functools import wraps

APPID = "wxa62d182b0330c59b"
APPSECRET = "ed54aa4d9c35db2e0664d4ae4501aacb"
GETSESSIONKEY = "https://api.weixin.qq.com/sns/jscode2session?appid=" + APPID + "&secret=" + APPSECRET + "&grant_type=authorization_code&js_code="
GETACCESSTOKEN = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&" + "appid=" + APPID + "&secret=" + APPSECRET
GETWXCODE = "https://api.weixin.qq.com/wxa/getwxacodeunlimit"


def get_json_dict(data={}, err_code=0, message="Success"):
    ret = {
        'err_code': err_code,
        'message': message,
        'data': data
    }
    return ret


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        kwargs.POST = json.loads(kwargs.body.decode('utf-8'))
        sessionId = kwargs.POST['sessionId']
    return decorated


class WXBizDataCrypt:
    def __init__(self, appId, sessionKey):
        self.appId = appId
        self.sessionKey = sessionKey

    def decrypt(self, encryptedData, iv):
        # base64 decode
        sessionKey = base64.b64decode(self.sessionKey)
        encryptedData = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)

        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)

        decrypted = json.loads(self._unpad(cipher.decrypt(encryptedData)))

        if decrypted['watermark']['appid'] != self.appId:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]
