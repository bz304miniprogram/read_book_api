from django.http import JsonResponse
import json

from . import util
from ocr.main import ocr
from douban_query.query import search_list, search_book_intro
from ocr.segmentation import segment
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from dbTables.models import Bookshelf, ReadTracker


@csrf_exempt
@require_POST
def upload_pic(request):
    sessionId = request.POST.get("sessionId")
    pic = request.FILES.get("pic")
    # pic = ImageFile(pic)
    pics = segment(pic.read(), DEBUG=1)
    book_list_recommond = []
    for pic in pics:
        result = ocr(pic)
        search_string = ""
        print("ocr result")
        print(result)
        if "words_result" in result:
            for keyword in result["words_result"]:
                search_string = search_string + keyword["words"] + "+"
            search_string = search_string[:-1]
            print(search_string)
            if search_string == "":
                continue
            searchList = search_list(search_string)
            print("search result")
            print(searchList)
            if searchList:
                searchList[0]["isFirst"] = True
                book_list_recommond.append(searchList[0])
                book_list_recommond.extend(book_candidate(searchList, 3))
    return JsonResponse(util.get_json_dict(message='analyse success', data=book_list_recommond))


def book_candidate(searchList, n):
    book_list_candidate = []
    for i in range(1, min(len(searchList), n)):
        searchList[i]["isFirst"] = False
        book_list_candidate.append(searchList[i])
    return book_list_candidate


@csrf_exempt
@require_POST
def book_intro(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    webUrl = request.POST.get("webUrl")
    data = search_book_intro(webUrl)
    print("book_intro data:")
    print(data)
    if data:
        return JsonResponse(util.get_json_dict(data={"intro": data}))
    else:
        return JsonResponse(util.get_json_dict(data={"intro": "暂无简介"}))


@csrf_exempt
@require_POST
def bookshelf_add(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    chosen_books = request.POST.get("chosen_books")
    for book in chosen_books:
        Bookshelf.objects.get_or_create(**book)
    return JsonResponse(util.get_json_dict(message="bookshelf_add success"))


@csrf_exempt
@require_POST
def get_bookshelf(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    sessionId = request.POST.get("sessionId")
    print(sessionId)
    bookList = list(Bookshelf.objects.filter(sessionId=sessionId).values())
    for book in bookList:
        book["lastRead"] = book["lastRead"].date()
    return JsonResponse(util.get_json_dict(message="bookshelf_add success", data=bookList))


@csrf_exempt
@require_POST
def delete_book(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    sessionId = request.POST.get("sessionId")
    webUrl = request.POST.get("webUrl")
    try:
        Bookshelf.objects.filter(sessionId=sessionId, webUrl=webUrl).delete()
    finally:
        return JsonResponse(util.get_json_dict(message="delete book success"))


@csrf_exempt
@require_POST
def start_read(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    return JsonResponse(util.get_json_dict(message="start_read success",
                                           data={"ReadTrackerId": ReadTracker.objects.create(**request.POST).id}))

@csrf_exempt
@require_POST
def read_success(request):
    request.POST = json.loads(request.body.decode('utf-8'))
    readTracker = ReadTracker.objects.get(id=request.POST["ReadTrackerId"])
    readTracker.isSuccess= True
    readTracker.save()
    return JsonResponse(util.get_json_dict(message="read success success"))



