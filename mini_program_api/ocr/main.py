import requests
import json
import base64
import time
from dbTables.models import Variable
from django.db import transaction
import datetime
import re

AK_SK_LIST = [("XUOonTSYCPuppXpa1o7FdyZ8", "gYfWM3SsYHGYnElcmodY0CuCtjnuyrsi"),#cy
              ("QMDr4b5i97snhhA4USRlszuH", "MFEzm1XBgvjIORGpdBoQBuz10ktytjBu"),#hyx
              ]
# AK = "XUOonTSYCPuppXpa1o7FdyZ8"
# SK = "gYfWM3SsYHGYnElcmodY0CuCtjnuyrsi"
ACCESSTOKENURL = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials"
OCRURL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
OCRURLB = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
OCRLIMIT = "50000"


def word_filter(word):
    result = []
    for char in word:
        if re.search("[\u4e00-\u9fff]", char) is not None:
            result.append(char)
    return ''.join(result)


@transaction.atomic
def get_idel_access_token():
    (possessings, _) = Variable.objects.get_or_create(name="possessings")
    (lifeTimes, isCreated) = Variable.objects.get_or_create(name="lifeTimes")
    if isCreated:
        lifeTimes.value = ",".join([OCRLIMIT for i in range(len(AK_SK_LIST))])
    possessing_list = [int(item) for item in possessings.value.split(",") if item != ""]
    lifeTime_list = [int(item) for item in lifeTimes.value.split(",")]
    if len(possessing_list) == len(AK_SK_LIST):
        return -1
    else:
        argmax = -1
        max = 0
        for idx, lifeTime in enumerate(lifeTime_list):
            if idx not in possessing_list and lifeTime > max:
                argmax = idx
                max = lifeTime
        if argmax == -1:
            return -1
        else:
            possessing_list = [str(item) for item in possessing_list]
            possessing_list.append(str(argmax))
            possessings.value = ",".join(possessing_list)
            possessings.save()
            lifeTime_list[argmax] -= 1
            lifeTimes.value = ",".join([str(item) for item in lifeTime_list])
            lifeTimes.save()
            return argmax


def get_access_token(index):
    access_token, isCreated = Variable.objects.get_or_create(name="baidu_access_token_{}".format(index))
    now = datetime.datetime.now()
    if access_token.lifeTime != '':
        if (now - datetime.timedelta(0, int(access_token.lifeTime))) < access_token.lastModify:
            return access_token.value
    params = {
        "client_id": AK_SK_LIST[index][0],
        "client_secret": AK_SK_LIST[index][1]
    }
    header = {
        "Content-Type": "application/json; charset=UTF-8"}
    r = requests.post(ACCESSTOKENURL, params=params, headers=header)
    r = json.loads(r.text)
    access_token.lifeTime = str(r["expires_in"])
    access_token.lastModify = now
    access_token.value = r["access_token"]
    access_token.save()
    return r["access_token"]


def ocr(pics):
    index = get_idel_access_token()
    if index == -1:
        return []
    access_token = get_access_token(index)
    params = {
        "access_token": access_token
    }
    header = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    data = {
        "probability": "true"
    }
    ocr_result_list = []
    for pic_group in pics:
        search_string = ""
        search_words = []
        ### try with cut images
        for pic in pic_group[:-1]:
            data["image"] = base64.b64encode(pic).decode("utf-8")
            r = requests.post(OCRURLB, params=params, headers=header, data=data)
            print(r)
            result = json.loads(r.text)
            print("this is text_cut img", result)
            if "words_result" in result:
                for keyword in result["words_result"]:
                    word = word_filter(keyword["words"])
                    if len(word) > 0:
                        search_string = search_string + word + "+"
                        search_words.append(word)
        search_string = search_string[:-1]
        ### use the origin image
        if search_string == "":
            data["image"] = base64.b64encode(pic_group[-1]).decode("utf-8")
            r = requests.post(OCRURLB, params=params, headers=header, data=data)
            result = json.loads(r.text)
            print("this is cut img", result)
            if "words_result" in result:
                for keyword in result["words_result"]:
                    word = word_filter(keyword["words"])
                    if len(word) > 0:
                        search_string = search_string + word + "+"
                        search_words.append(word)
            search_string = search_string[:-1]
        print("search_string", search_string)
        if search_string != "":
            ocr_result_list.append({"search_string": search_string, "search_words": search_words})
    possessings = Variable.objects.get(name="possessings")
    possessings.value = possessings.value.replace(str(index), "")
    possessings.save()
    return ocr_result_list


if __name__ == '__main__':
    with open("./examples/cut/img1_cut/cut_3.png", 'rb') as pic:
        pic = pic.read()
        ocr(pic)
