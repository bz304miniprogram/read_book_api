from django.http import JsonResponse
from django.shortcuts import HttpResponse

import json
import requests
from . import util
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from dbTables.models import User
from dbTables.models import Variable
from hashlib import sha1
import os
import datetime
from .util import WXBizDataCrypt


@require_GET
def code2id(request):
    url = util.GETSESSIONKEY + request.GET["code"]
    r = requests.get(url, verify=False)
    if r.status_code == 200:
        r = r.json()
        # try:
        User.objects.get_or_create(openId=r["openid"])
        update = User.objects.get(openId=r["openid"])
        update.session_key = r["session_key"]
        update.save()
        response = JsonResponse(util.get_json_dict(data={"sessionId": update.id}), charset="utf-8")
        return response
        # except:
    response = JsonResponse(util.get_json_dict(err_code=1, message="code2id failed", data={}))
    return response


def get_access_token():
    access_token = Variable.objects.get_or_create(name="wx_access_token")[0]
    now = datetime.datetime.now()
    if access_token.lifeTime != '':
        if (now - datetime.timedelta(0, int(access_token.lifeTime))) < access_token.lastModify:
            return access_token.value

    r = requests.get(util.GETACCESSTOKEN)
    r = r.json()
    access_token.lifeTime = str(r["expires_in"])
    access_token.lastModify = now
    access_token.value = r["access_token"]
    access_token.save()
    return r["access_token"]

# invalid when mini program isn't posted
def get_wxcode(request):
    if not os.path.exists("../images"):
        os.mkdir("../images")
        access_token = get_access_token()
        params = {
            "access_token": access_token,
        }
        data = {
            "scene": "1"
        }
        header = {
            "Content-Type": "application/json; charset=UTF-8"}
        r = requests.post(util.GETWXCODE, params=params, json=data, headers=header)
        file = open('../images/wxcode.jpg', 'wb')
        file.write(r.content)
        file.close()
        print ("file write finished")
    file = open('../images/wxcode.jpg', 'rb')
    response = HttpResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="wxcode.jpg"'
    file.close()
    return response


@csrf_exempt
@require_POST
def update_user(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    sessionId = request.POST["sessionId"]
    userInfo = request.POST["userInfo"]
    User.objects.filter(id=int(sessionId)).update(**userInfo)
    return JsonResponse(util.get_json_dict(message='update success'))


# except:
# return JsonResponse(util.get_json_dict(err_code=1, message="update_user failed", data={}))

@csrf_exempt
@require_POST
def check_with_session_key(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    session_key = User.object.filter(id=int(request.POST["sessionId"]))
    signature2 = sha1(request.POST["rawData"], session_key)
    if signature2 == request.POST["signature"]:
        return JsonResponse(util.get_json_dict(data={"valid_user": True}))
    else:
        return JsonResponse(util.get_json_dict(data={"valid_user": False}))

# @csrf_exempt
# @require_POST
# def update_nickName(request):
#     request.POST = json.loads(request.body.decode('utf-8'))
#     user = User.object.filter(id=int(request.POST["sessionId"]))
#     user.nickName = request.POST["nickName"]
#     user.save()
#     return JsonResponse(util.get_json_dict())
