cd /D %0
cd ../py3/requests
set /P f=Enter batchrequest save to edit:
py batchrequest_v201.py -releve_table "standard" -f %f% -u
pause