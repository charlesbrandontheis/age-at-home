#!/bin/csh -fb
setenv APP "aah"
setenv API "scored"
setenv WWW "www.dcmartin.com"
setenv LAN "192.168.1"
if ($?TMP == 0) setenv TMP "/var/lib/age-at-home"

# don't update statistics more than once per (in seconds)
set TTL = 15
set SECONDS = `date "+%s"`
set DATE = `/bin/echo $SECONDS \/ $TTL \* $TTL | bc`

/bin/echo `date` "$0 $$ -- START ($DATE)" >>! $TMP/LOG

if ($?QUERY_STRING) then
    set noglob
    set DB = `/bin/echo "$QUERY_STRING" | sed 's/.*db=\([^&]*\).*/\1/'`
    if ("$DB" == "$QUERY_STRING") set DB = rough-fog
    set match = `/bin/echo "$QUERY_STRING" | sed 's/.*match=\([^&]*\).*/\1/'`
    if ("$match" == "$QUERY_STRING") unset match
    set class = `/bin/echo "$QUERY_STRING" | sed 's/.*class=\([^&]*\).*/\1/'`
    if ("$class" == "$QUERY_STRING") unset class
    set mime = `/bin/echo "$QUERY_STRING" | sed 's/.*mime=\([^&]*\).*/\1/'`
    if ("$mime" == "$QUERY_STRING") unset mime
    set id = `/bin/echo "$QUERY_STRING" | sed 's/.*id=\([^&]*\).*/\1/'`
    if ("$id" == "$QUERY_STRING") unset id
    unset noglob
endif

if ($?DB) then
  set db = $DB:h
else
  set DB = rough-fog
  set db = $DB
endif
set DBt = ( $DB:t )
set dbt = ( $db:t ) 
if ($#dbt && $dbt != $db && $?class == 0) then
  set class = $db:t
  set db = $db:h
endif
if ($#DBt && $#dbt && $?id == 0) then
  set id = $DB:t
  set ide = ( $id:e )
  if ($#ide == 0) unset id
endif
if ($?class) then
  set class = $class:h
endif
if ($?id) then
  set id = $id:r
endif

if ($?db && $?class && $?id) then
    setenv QUERY_STRING "db=$db&class=$class&id=$id"
else if ($?db && $?class && $?match) then
    setenv QUERY_STRING "db=$db&class=$class&match=$match"
else if ($?db && $?class) then
    setenv QUERY_STRING "db=$db&class=$class"
else if ($?db) then
    setenv QUERY_STRING "db=$db"
endif

if ($?DEBUG) /bin/echo `date` "$0 $$ -- query string ($QUERY_STRING)" >>! $TMP/LOG

# handle image
if ($?id) then
    set base = "$TMP/$db/$class"
    set images = ( `find "$base" -name "$id.jpg" -type f -print` )
    if ($?DEBUG) /bin/echo `date` "$0 $$ -- IMAGE ($id) count ($#images) " >>! $TMP/LOG
    # should be singleton image
    /bin/echo "Access-Control-Allow-Origin: *"
    set AGE = `/bin/echo "$SECONDS - $DATE" | bc`
    /bin/echo "Age: $AGE"
    /bin/echo "Cache-Control: max-age=$TTL"
    /bin/echo "Last-Modified:" `date -r $DATE '+%a, %d %b %Y %H:%M:%S %Z'`

    if ($#images == 1) then
	/bin/echo "Content-Type: image/jpeg"
	/bin/echo ""
	if ($?DEBUG) /bin/echo `date` "$0 $$ -- DD ($id) count ($images) " >>! $TMP/LOG
	dd if="$images"
    else if ($#images > 1) then
	/bin/echo "Content-Type: application/zip"
	/bin/echo ""
	zip - $images | dd of=/dev/stdout
    endif
    goto done
endif

#
# build HTML
#
set OUTPUT = "$TMP/$APP-$API-$QUERY_STRING.$DATE.html"
if (-s "$OUTPUT") then
    if ($?DEBUG) /bin/echo `date` "$0 $$ -- EXISTING $OUTPUT" >>! $TMP/LOG
    goto output
endif
set INPROGRESS = ( `/bin/echo "$OUTPUT".*` )
set OLD = ( `/bin/echo "$TMP/$APP-$API-$QUERY_STRING".*.html` )
if ($#INPROGRESS) then
    if ($?DEBUG) /bin/echo `date` "$0 $$ -- IN-PROGRESS $INPROGRESS" >>! $TMP/LOG
    if ($#OLD) then
	if (-s "$OLD[1]") then
	    set OUTPUT = $OLD[1]
	    goto output
	endif
    endif
    if ($?DEBUG) /bin/echo `date` "$0 $$ -- NO OLD HTML" >>! $TMP/LOG
    goto done
endif

# start work
touch "$OUTPUT.$$"

# cleanup old
if ($#OLD > 1) rm -f $OLD[2-]

if ($?class) then
    set base = "$TMP/$db/$class"
    if ($?id) then
	set images = ( `find "$base" -name "$id.jpg" -type f -print` )
    else if ($?match) then
	set images = ( `find "$base" -name "$match*.jpg" -type f -print | sed "s@$base/\(.*\)\.jpg@\1@"` )
    else
	set images = ( `find "$base" -name "*.jpg" -type f -print | sed "s@$base/\(.*\)\.jpg@\1@"` )
    endif
else 
    set base = "$TMP/$db"
    set classes = ( `find "$base" -name "[^\.]*" -type d -print | sed "s@$base@@" | sed "s@/@@"` )
endif

if ($?DEBUG) /bin/echo `date` "$0 $$ -- $db $?id ($?images) $?class ($?classes)" >>! $TMP/LOG

# check if listing requested
if ($?mime && $?images) then
    /bin/echo "Access-Control-Allow-Origin: *"
    /bin/echo "Cache-Control: no-cache"
    /bin/echo "Content-Type: text/plain"
    /bin/echo ""
    foreach i ( $images )
      set file = 'http://'"$WWW/CGI/$APP-$API"'.cgi?db='"$db"'&class='"$class"'&id='"$i"'.jpg'
      /bin/echo "$file"
    end
    goto done
endif

set MIXPANELJS = "http://$WWW/CGI/script/mixpanel-aah.js"

if ($?class) then
    # should be a directory listing of images
    set dir = "$db/$class"
    /bin/echo '<html><head><title>Index of '"$dir"'</title></head>' >! "$OUTPUT.$$"
    /bin/echo '<script type="text/javascript" src="'$MIXPANELJS'"></script><script>mixpanel.track('"'"$APP-$API"'"',{"db":"'$db'","class":"'$class'"});</script>' >> "$OUTPUT.$$"
    /bin/echo '<body bgcolor="white"><h1>Index of <a href="http://'"$WWW/CGI/$APP-$API"'.cgi?db='"$db"'&class='"$class"'&mime=text">'"$dir"'</a></h1><hr><pre><a href="http://'"$WWW/CGI/$APP-$API.cgi?db=$db"'/">../</a>' >>! "$OUTPUT.$$"
    foreach i ( $images )
      set file = '<a href="http://'"$WWW/CGI/$APP-$API"'.cgi?db='"$db"'&class='"$class"'&id='"$i"'.jpg">'"$i.jpg"'</a>' 
      set ctime = `date '+%d-%h-%Y %H:%M'`
      set fsize = `ls -l "$TMP/$db/$class/$i.jpg" | awk '{ print $5 }'`
      /bin/echo "$file		$ctime		$fsize" >>! "$OUTPUT.$$"
    end
    /bin/echo '</pre><hr></body></html>' >>! "$OUTPUT.$$"
else if ($?classes) then
    # should be a directory listing of directories
    set dir = "$db"
    /bin/echo '<html><head><title>Index of '"$dir"'/</title></head>' >! "$OUTPUT.$$"
    /bin/echo '<script type="text/javascript" src="'$MIXPANELJS'"></script><script>mixpanel.track('"'"$APP-$API"'"',{"db":"'$db'"});</script>' >> "$OUTPUT.$$"
    /bin/echo '<body bgcolor="white"><h1>Index of '"$dir"'/</h1><hr><pre><a href="http://'"$WWW/CGI/$APP-$API.cgi?db=$db"'/">../</a>' >>! "$OUTPUT.$$"
    foreach i ( $classes )
      set class = '<a href="http://'"$WWW/CGI/$APP-$API"'.cgi?db='"$db"'&class='"$i"'/">'"$i"'/</a>' >>! "$OUTPUT.$$"
      set ctime = `date '+%d-%h-%Y %H:%M'`
      set fsize = `du -sk "$TMP/$db/$i" | awk '{ print $1 }'`
      /bin/echo "$class		$ctime		$fsize" >>! "$OUTPUT.$$"
    end
    /bin/echo '</pre><hr></body></html>' >>! "$OUTPUT.$$"
endif

mv "$OUTPUT.$$" "$OUTPUT"

output:

/bin/echo "Access-Control-Allow-Origin: *"
set AGE = `/bin/echo "$SECONDS - $DATE" | bc`
/bin/echo "Age: $AGE"
/bin/echo "Cache-Control: max-age=$TTL"
/bin/echo "Last-Modified:" `date -r $DATE '+%a, %d %b %Y %H:%M:%S %Z'`
/bin/echo "Content-Type: text/html"
/bin/echo ""

cat "$OUTPUT"

done:

rm -f "$TMP/$APP-$API-"*.$$
/bin/echo `date` "$0 $$ -- FINISH" >>! $TMP/LOG
