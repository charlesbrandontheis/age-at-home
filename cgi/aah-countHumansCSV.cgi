#!/bin/csh -fb
setenv APP "aah"
setenv API "countHumansCSV"
setenv LAN "192.168.1"
if ($?TMP == 0) setenv TMP "/var/lib/age-at-home"
# don't update statistics more than once per 15 minutes
set TTL = `echo "30 * 60" | bc`
set SECONDS = `date "+%s"`
set DATE = `echo $SECONDS \/ $TTL \* $TTL | bc`

echo `date` "$0 $$ -- START" >>! $TMP/LOG

if ($?QUERY_STRING) then
    set DB = `echo "$QUERY_STRING" | sed "s/.*db=\([^&]*\).*/\1/"`
    if ($#DB == 0) set DB = rough-fog
else
    set DB = rough-fog
endif
setenv QUERY_STRING "db=$DB"

set OUTPUT = "$TMP/$APP-$API-$QUERY_STRING.$DATE.csv"
if (! -e "$OUTPUT") then
    rm -f "$TMP/$APP-$API-$QUERY_STRING".*.csv
    if ($DB == "damp-cloud") then
	curl -L -s -q -o "$OUTPUT" "https://ibmcds.looker.com/looks/gXpvq8ykFPkMv2xFF3Tzg3mrG3jVt4HJ.csv?apply_formatting=true"
    else
	curl -L -s -q -o "$OUTPUT" "https://ibmcds.looker.com/looks/M9B2vPX7RD9Sf4PwDyNWQ6dR46pCS5qd.csv?apply_formatting=true"
    endif
    if ($DB == "damp-cloud") then
	cat "$OUTPUT" \
	    | sed "s/Intervals Interval/Interval/" \
	    | sed "s/\([^ ]\) Dampcloud Visual Scores Count/\1/g" >> "$OUTPUT".$$
    else
	cat "$OUTPUT" \
	    | sed "s/Intervals Interval/Interval/" \
	    | sed "s/\([^ ]*\) Roughfog Visual Scores Count/\1/g" >> "$OUTPUT".$$
    endif
    mv -f "$OUTPUT".$$ "$OUTPUT"
endif

output:

echo "Content-Type: text/csv; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
set AGE = `echo "$SECONDS - $DATE" | bc`
echo "Age: $AGE"
echo "Cache-Control: max-age=$TTL"
echo "Last-Modified:" `date -r $DATE '+%a, %d %b %Y %H:%M:%S %Z'`
echo ""
cat "$OUTPUT"

done:

echo `date` "$0 $$ -- FINISH" >>! $TMP/LOG