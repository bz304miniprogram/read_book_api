from django.http import JsonResponse
import json
import datetime

from . import util
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from dbTables.models import ReadTracker, Bookshelf


@csrf_exempt
@require_POST
def start_read(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    sessionId = request.POST['sessionId']
    title = request.POST['title']
    bookshelf = Bookshelf.objects.get(sessionId=sessionId, title=title)
    bookshelf.lastRead = datetime.datetime.now()
    bookshelf.save()
    return JsonResponse(util.get_json_dict(message="start_read success",
                                           data={"ReadTrackerId": ReadTracker.objects.create(**request.POST).id}))


@csrf_exempt
@require_POST
def read_success(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    readTracker = ReadTracker.objects.get(id=request.POST["ReadTrackerId"])
    readTracker.isSuccess = True
    readTracker.save()
    return JsonResponse(util.get_json_dict(message="read success success"))


@csrf_exempt
@require_POST
def get_week_track(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    sessionId = request.POST["sessionId"]
    today = datetime.date.today()
    d = today.isoweekday()
    start = datetime.date.today() - datetime.timedelta(days=(d - 1))
    end = start - datetime.timedelta(days=-7)
    endTitle = start - datetime.timedelta(days=-6)
    title = str(start.year) + '年' + str(start.month) + '月' + str(start.day) + '日至' + str(endTitle.month) + '月' + str(
        endTitle.day) + '日'
    readTracker = ReadTracker.objects.filter(modify__range=(start, end), sessionId=sessionId)
    readSuccess = [0 for i in range(7)]
    readFailed = [0 for i in range(7)]
    successTimes = 0
    failedTimes = 0
    for tracker in readTracker:
        if tracker.isSuccess:
            readSuccess[tracker.modify.weekday()] = readSuccess[tracker.modify.weekday()] + tracker.readTime
            successTimes = successTimes + 1
        else:
            readFailed[tracker.modify.weekday()] = readFailed[tracker.modify.weekday()] + tracker.readTime
            failedTimes = failedTimes + 1
    return JsonResponse(util.get_json_dict(
        data={"title": title, "readSuccess": readSuccess, "readFailed": readFailed, "successTimes": successTimes,
              "failedTimes": failedTimes}))


@csrf_exempt
@require_POST
def get_month_track(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    sessionId = request.POST["sessionId"]
    month = request.POST["month"]
    year = datetime.date.today().year
    start = datetime.datetime(year=year, month=month, day=1)
    if month == 12:
        year = year + 1
        month = 0
    end = datetime.datetime(year=year, month=month + 1, day=1)
    readTracker = ReadTracker.objects.filter(modify__range=(start, end), sessionId=sessionId)
    days = (end - start).days
    readSuccess = []
    for i in range(days):
        readSuccess.append([(start + datetime.timedelta(days=i)).weekday(), int((start.weekday() + i) / 7), 0.1])
    successTimes = 0
    failedTimes = 0
    for tracker in readTracker:
        if tracker.isSuccess:
            index = (tracker.modify - start).days
            readSuccess[index][2] = readSuccess[index][2] + tracker.readTime
            successTimes = successTimes + 1
        else:
            failedTimes = failedTimes + 1
    return JsonResponse(
        util.get_json_dict({"readSuccess": readSuccess, "successTimes": successTimes, "failedTimes": failedTimes}))


@csrf_exempt
@require_POST
def get_annual_poster(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    sessionId = request.POST['sessionId']
    start = datetime.datetime(year=datetime.datetime.now().year, month=1, day=1)
    end = datetime.datetime(year=datetime.datetime.now().year + 1, month=1, day=1)
    readTracker = ReadTracker.objects.filter(modify__range=(start, end), sessionId=sessionId)
    timeFreq = {}
    tagFreq = {}
    sum = 0
    for tracker in readTracker:
        if tracker.isSuccess:
            sum = sum + tracker.readTime
            if tracker.title in timeFreq.keys():
                timeFreq[tracker.title][0] = timeFreq[tracker.title][0] + tracker.readTime
                timeFreq[tracker.title][1] = timeFreq[tracker.title][1] + 1
            else:
                timeFreq[tracker.title] = [tracker.readTime, 1]

            tags = tracker.tags.split(',')
            for tag in tags:
                if tag == "":
                    continue
                if tag in tagFreq.keys():
                    tagFreq[tag] = tagFreq[tag] + 1
                else:
                    tagFreq[tag] = 1
    max_time = [0, '']
    max_times = [0, '']
    for key in timeFreq.keys():
        if timeFreq[key][0] > max_time[0]:
            max_time = [timeFreq[key][0], key]
        if timeFreq[key][1] > max_times[0]:
            max_times = [timeFreq[key][1], key]
    sortedTagFreq = sorted(tagFreq.items(), key=lambda kv: kv[1],reverse=True)  # greater case
    maxTime =  (ReadTracker.objects.filter(sessionId=sessionId,title=max_time[1]).values()[0])
    maxTimes = (ReadTracker.objects.filter(sessionId=sessionId,title=max_times[1]).values()[0])
    maxTime["time"] = max_time[0]
    maxTimes["time"] = max_times[0]
    return JsonResponse(util.get_json_dict(
        data={'sum': sum, 'maxTime': maxTime, 'maxTimes': maxTimes, 'topTag': sortedTagFreq[0:6]}))
