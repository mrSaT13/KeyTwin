@echo off
setlocal EnableDelayedExpansion
title Copy ECP from token to PC - CryptoPro 5
color 0A

REM ============================================================
REM  Copy container Rutoken / JaCarta / eToken / Flash
REM  to Windows Registry, to work without token in browser
REM  CryptoPro CSP 5.x
REM  Run as Administrator - right click - Run as administrator
REM ============================================================

REM ---- 1. Find csptest.exe ----
set "CSPT="
for %%P in (
  "C:\Program Files\Crypto Pro\CSP\csptest.exe"
  "C:\Program Files\CryptoPro\CSP\csptest.exe"
  "C:\Program Files (x86)\Crypto Pro\CSP\csptest.exe"
  "C:\Program Files (x86)\CryptoPro\CSP\csptest.exe"
) do (
  if exist %%P (
    set "CSPT=%%~P"
    goto :found
  )
)

for /f "delims=" %%i in ('where csptest.exe 2^>nul') do (
  set "CSPT=%%i"
  goto :found
)

echo [ERROR] csptest.exe not found. Install CryptoPro CSP 5.
pause
exit /b 1

:found
echo Found: "%CSPT%"
echo.

REM ---- 2. Scan containers ----
echo ===== STEP 1. Scan containers - token must be inserted =====
echo.
echo Scanning user + machine containers, please wait...
del "%TEMP%\csp_list.txt" 2>nul
"%CSPT%" -keyset -enum_cont -fqcn -verifyc > "%TEMP%\csp_list.txt" 2>&1
"%CSPT%" -keyset -enum_cont -fqcn -verifyc -machinekeys >> "%TEMP%\csp_list.txt" 2>&1
type "%TEMP%\csp_list.txt"
echo.
echo ---------------------------------------------------------------
REM Build numbered list - no findstr, check first 2 chars are backslashes
set CNT=0
for /f "tokens=* delims=" %%A in ('type "%TEMP%\csp_list.txt"') do (
  set "LINE=%%A"
  for /f "tokens=* delims= " %%B in ("%%A") do set "LINE=%%B"
  REM container lines start with double backslash
  if "!LINE:~0,2!"=="\\" (
    REM skip duplicates - user and machine scans overlap
    set "DUP=0"
    for /l %%I in (1,1,!CNT!) do if "!CONT[%%I]!"=="!LINE!" set "DUP=1"
    if "!DUP!"=="0" (
      set /a CNT+=1
      set "CONT[!CNT!]=!LINE!"
    )
  )
)
if !CNT! EQU 0 goto :nocont
echo Found containers: !CNT!
echo.
for /l %%I in (1,1,!CNT!) do echo   %%I. !CONT[%%I]!
echo   0. Enter manually
echo ---------------------------------------------------------------
echo.
set "CHOICE="
set /p CHOICE=Select container NUMBER [1-!CNT!]: 
if "%CHOICE%"=="" (
  echo No number selected. Exit.
  pause
  exit /b 1
)
if "%CHOICE%"=="0" goto :manual
call set "SRC=%%CONT[%CHOICE%]%%"
if "%SRC%"=="" (
  echo Bad number. Exit.
  pause
  exit /b 1
)
goto :src_ok

:nocont
echo.
echo [ERROR] No containers found.
echo.
echo Check list:
echo  1. Token inserted? LED on? Try another USB port, no hub.
echo  2. Rutoken Panel / JaCarta Client sees token?
echo  3. CryptoPro CSP - Hardware - Readers: Aktiv Rutoken ECP / JaCarta must exist.
echo  4. Try WITHOUT Run as administrator - user containers differ.
echo  5. Check CryptoPro Tools - Containers - is token there?
echo.
echo Readers:
"%CSPT%" -enum -info -type PP_ENUMREADERS 2>&1
echo.
echo Press 0 to enter name manually, Enter to exit.
set "CHOICE="
set /p CHOICE=Choice [0/Enter]: 
if "!CHOICE!"=="0" goto :manual
pause
exit /b 1

:manual
set "SRC="
set /p SRC=Enter FULL container name: 
if "%SRC%"=="" (
  echo Empty name. Exit.
  pause
  exit /b 1
)
set "SRC=%SRC:"=%"

:src_ok
echo.
echo Selected source: %SRC%
echo.

REM Short name = part after last backslash, for default copy name
set "SRCSHORT=%SRC%"
:loop_short
for /f "tokens=1* delims=\" %%a in ("!SRCSHORT!") do (
  if "%%b"=="" goto :short_done
  set "SRCSHORT=%%b"
  goto :loop_short
)
:short_done
for /f "tokens=* delims= " %%B in ("!SRCSHORT!") do set "SRCSHORT=%%B"
if "!SRCSHORT!"=="" set "SRCSHORT=copy1"

REM ---- 3. Dest name ----
set "DSTNAME="
set /p DSTNAME=Enter NAME for PC copy [Enter = !SRCSHORT!-copy]: 
if "!DSTNAME!"=="" set "DSTNAME=!SRCSHORT!-copy"
echo Copy to: \\.\REGISTRY\!DSTNAME!
echo.

REM ---- 4. PINs ----
echo Default PINs:
echo   Rutoken  - 12345678
echo   JaCarta  - 11111111
echo   eToken   - 1234567890
echo.
set "PIN1="
set /p PIN1=Enter token PIN [Enter = empty]: 
set "PIN2="
set /p PIN2=Enter password for PC copy [Enter = empty]: 

echo.
echo ===== STEP 2. Copy to REGISTRY =====
echo.

if "%PIN1%"=="" (
  set "PIN1OPT="
) else (
  set "PIN1OPT=-pinsrc %PIN1%"
)
if "%PIN2%"=="" (
  set "PIN2OPT=-pindest """
) else (
  set "PIN2OPT=-pindest %PIN2%"
)

echo Running copy...
set "COPYERR="
del "%TEMP%\csp_copy.log" 2>nul
"%CSPT%" -keycopy -contsrc "%SRC%" -contdest "\\.\REGISTRY\%DSTNAME%" %PIN1OPT% %PIN2OPT% > "%TEMP%\csp_copy.log" 2>&1
type "%TEMP%\csp_copy.log"
REM csptest does not set ERRORLEVEL, check log text for success code
findstr /C:"0x00000000" "%TEMP%\csp_copy.log" >nul
if errorlevel 1 (
  echo.
  echo [WARN] contsrc failed, trying old syntax src-dest...
  echo.
  "%CSPT%" -keycopy -src "%SRC%" -pinsrc="%PIN1%" -dest "\\.\REGISTRY\%DSTNAME%" -pindest="%PIN2%" > "%TEMP%\csp_copy.log" 2>&1
  type "%TEMP%\csp_copy.log"
)

findstr /C:"0x00000000" "%TEMP%\csp_copy.log" >nul
if errorlevel 1 set "COPYERR=1"
if "%COPYERR%"=="1" (
  echo.
  echo ============================================================
  echo  COPY ERROR.
  echo  Reasons:
  echo   1. Wrong token PIN
  echo   2. Name already exists in Registry - use another name
  echo   3. Key is NON-EXPORTABLE - 0x8009000B. FNS tokens after 2022
  echo      cannot be copied, use original only.
  echo   4. Run as Administrator
  echo ============================================================
  pause
  exit /b 1
)

echo.
echo ===== STEP 3. Install cert to Personal store =====
echo.
"%CSPT%" -property -cinstall -cont "\\.\REGISTRY\%DSTNAME%"

echo.
echo ============================================================
echo  DONE! Copied to: \\.\REGISTRY\%DSTNAME%
echo.
echo  Check:
echo   1. CryptoPro CSP - Service - View certs in container
echo   2. Select REGISTRY - cert must open
echo   3. Restart browser and work without token
echo.
echo  NOTE: keep original token! Registry copy dies with Windows.
echo ============================================================
echo.
pause
