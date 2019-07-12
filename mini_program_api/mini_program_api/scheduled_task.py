from dbTables.models import Variable
import ocr.main

def ocr_api_refresh():
    (lifeTimes, _) = Variable.objects.get_or_create(name="lifeTimes")
    lifeTimes.value = ",".join([main.OCRLIMIT for i in range(len(main.AK_SK_LIST))])
    lifeTimes.save()
    print ("sql refresh")