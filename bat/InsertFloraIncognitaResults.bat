cd /D %0
cd ../py3/requests
set /P f=Enter batchrequest save to insert Flora Incognita results:
py batchrequest_v201.py -add_florincog %f%
pause