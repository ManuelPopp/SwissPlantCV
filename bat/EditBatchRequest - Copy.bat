cd ../py3/requests
set /P f=Enter batchrequest save to edit:
set /P m=Enter API name:
py batchrequest_v201.py -releve_table "standard" -r %m% -f %f% -u
pause