cd /D %0
cd ../py3/requests
py batchrequest_v201.py -releve_table "standard" -from_checkpoint True --shutdown
pause