#!/bin/tcsh
setenv APP "aah"
setenv API "classifiers"

if ($?TMP == 0) setenv TMP "/var/lib/age-at-home"
# don't update statistics more than once per 15 minutes
set TTL = `echo "30 * 60" | bc`
set SECONDS = `date "+%s"`
set DATE = `echo $SECONDS \/ $TTL \* $TTL | bc`

echo `date` "$0 $$ -- START" >>! $TMP/LOG

set JSON = ~$USER/.aah-classifierSets.json
if (! -e "$JSON") then
    echo `date` "$0 $$ -- no $JSON" >>! $TMP/LOG
else
    echo `date` "$0 $$ -- using $JSON" >>! $TMP/LOG
endif


echo "Content-Type: application/json; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
set AGE = `echo "$SECONDS - $DATE" | bc`
echo "Age: $AGE"
echo "Cache-Control: max-age=$TTL"
echo "Last-Modified:" `date -r $DATE '+%a, %d %b %Y %H:%M:%S %Z'`
echo ""
/usr/local/bin/jq '.humans[].name' "$JSON"

echo `date` "$0 $$ -- FINISH" >>! $TMP/LOG
