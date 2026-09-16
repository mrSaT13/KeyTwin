@echo off
setlocal EnableDelayedExpansion
chcp 866 >nul
title Копирование ЭЦП с токена в ПК - КриптоПро 5
color 0A

REM Копирование контейнера Рутокен JaCarta eToken флешка в реестр
REM Чтобы работать без токена в браузере. КриптоПро CSP 5.
REM Запускать правой кнопкой - Запуск от имени администратора

REM ---- 1. Поиск csptest.exe ----
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

echo [ОШИБКА] csptest.exe не найден. Установите КриптоПро CSP 5.
pause
exit /b 1

:found
echo Найден КриптоПро: "%CSPT%"
echo.

REM ---- 2. Сканирование контейнеров ----
echo ===== ШАГ 1. Список контейнеров - токен должен быть вставлен =====
echo.
echo Сканирую контейнеры пользователя и компьютера, подождите...
del "%TEMP%\csp_list.txt" 2>nul
"%CSPT%" -keyset -enum_cont -fqcn -verifyc > "%TEMP%\csp_list.txt" 2>&1
"%CSPT%" -keyset -enum_cont -fqcn -verifyc -machinekeys >> "%TEMP%\csp_list.txt" 2>&1
type "%TEMP%\csp_list.txt"
echo.
echo ---------------------------------------------------------------
REM Составляем нумерованный список - строки начинаются с двух слешей
set CNT=0
for /f "tokens=* delims=" %%A in ('type "%TEMP%\csp_list.txt"') do (
  set "LINE=%%A"
  for /f "tokens=* delims= " %%B in ("%%A") do set "LINE=%%B"
  if "!LINE:~0,2!"=="\\" (
    set "DUP=0"
    for /l %%I in (1,1,!CNT!) do if "!CONT[%%I]!"=="!LINE!" set "DUP=1"
    if "!DUP!"=="0" (
      set /a CNT+=1
      set "CONT[!CNT!]=!LINE!"
    )
  )
)
if !CNT! EQU 0 goto :nocont
echo Найдено контейнеров: !CNT!
echo.
for /l %%I in (1,1,!CNT!) do echo   %%I. !CONT[%%I]!
echo   0. Ввести вручную
echo ---------------------------------------------------------------
echo.
set "CHOICE="
set /p CHOICE=Выберите НОМЕР контейнера [1-!CNT!]: 
if "%CHOICE%"=="" (
  echo Номер не выбран. Выход.
  pause
  exit /b 1
)
if "%CHOICE%"=="0" goto :manual
call set "SRC=%%CONT[%CHOICE%]%%"
if "%SRC%"=="" (
  echo Неверный номер. Выход.
  pause
  exit /b 1
)
goto :src_ok

:nocont
echo.
echo [ОШИБКА] Контейнеры не найдены.
echo.
echo Проверьте:
echo  1. Токен вставлен. Лампочка горит. Попробуйте другой USB-порт без хаба.
echo  2. Панель Рутокен или JaCarta Client видит токен.
echo  3. КриптоПро CSP - Оборудование - Считыватели: должен быть Aktiv Rutoken или JaCarta.
echo  4. Попробуйте БЕЗ запуска от администратора - контейнеры разные.
echo  5. Проверьте Инструменты КриптоПро - Контейнеры - есть ли токен.
echo.
echo Считыватели:
"%CSPT%" -enum -info -type PP_ENUMREADERS 2>&1
echo.
echo Нажмите 0 чтобы ввести имя вручную, Enter - выход.
set "CHOICE="
set /p CHOICE=Выбор [0/Enter]: 
if "!CHOICE!"=="0" goto :manual
pause
exit /b 1

:manual
set "SRC="
set /p SRC=Введите ПОЛНОЕ имя контейнера: 
if "%SRC%"=="" (
  echo Пустое имя. Выход.
  pause
  exit /b 1
)
set "SRC=%SRC:"=%"

:src_ok
echo.
echo Выбран источник: %SRC%
echo.

REM Короткое имя - часть после последнего слеша, для имени копии
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

REM ---- 3. Имя копии ----
set "DSTNAME="
set /p DSTNAME=Введите ИМЯ копии в ПК латиницей без пробелов [Enter = !SRCSHORT!-copy]: 
if "!DSTNAME!"=="" set "DSTNAME=!SRCSHORT!-copy"
echo Копия будет: \\.\REGISTRY\!DSTNAME!
echo.

REM ---- 4. ПИН-коды ----
echo Стандартные PIN:
echo   Рутокен  - 12345678
echo   JaCarta  - 11111111
echo   eToken   - 1234567890
echo.
set "PIN1="
set /p PIN1=Введите PIN токена [Enter - пусто]: 
set "PIN2="
set /p PIN2=Введите пароль для копии в ПК [Enter - пусто]: 

echo.
echo ===== ШАГ 2. Копирование в РЕЕСТР =====
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

echo Выполняю копирование...
set "COPYERR="
del "%TEMP%\csp_copy.log" 2>nul
"%CSPT%" -keycopy -contsrc "%SRC%" -contdest "\\.\REGISTRY\%DSTNAME%" %PIN1OPT% %PIN2OPT% > "%TEMP%\csp_copy.log" 2>&1
type "%TEMP%\csp_copy.log"
REM csptest не выставляет ERRORLEVEL, проверяем текст лога
findstr /C:"0x00000000" "%TEMP%\csp_copy.log" >nul
if errorlevel 1 (
  echo.
  echo [ПРЕДУПРЕЖДЕНИЕ] contsrc не сработал, пробую старый синтаксис...
  echo.
  "%CSPT%" -keycopy -src "%SRC%" -pinsrc="%PIN1%" -dest "\\.\REGISTRY\%DSTNAME%" -pindest="%PIN2%" > "%TEMP%\csp_copy.log" 2>&1
  type "%TEMP%\csp_copy.log"
)

findstr /C:"0x00000000" "%TEMP%\csp_copy.log" >nul
if errorlevel 1 set "COPYERR=1"
if "%COPYERR%"=="1" (
  echo.
  echo ============================================================
  echo  ОШИБКА КОПИРОВАНИЯ. Копия НЕ создана.
  echo  Причины:
  echo   1. Неверный PIN токена
  echo   2. Такое имя уже есть в реестре - придумайте другое
  echo   3. Ключ НЕЭКСПОРТИРУЕМЫЙ - код 0x8009000B. Токены ФНС после 2022 года
  echo      скопировать нельзя, работайте только с оригиналом.
  echo   4. Запустите от имени администратора
  echo ============================================================
  pause
  exit /b 1
)

echo.
echo ===== ШАГ 3. Установка сертификата в Личные =====
echo.
"%CSPT%" -property -cinstall -cont "\\.\REGISTRY\%DSTNAME%"

echo.
echo ============================================================
echo  ГОТОВО. Скопировано в: \\.\REGISTRY\%DSTNAME%
echo.
echo  Проверка:
echo   1. КриптоПро CSP - Сервис - Посмотреть сертификаты в контейнере
echo   2. Выберите РЕЕСТР - сертификат должен открыться
echo   3. Перезапустите браузер и работайте без токена
echo.
echo  ВАЖНО: сохраните оригинальный токен. Копия умрет вместе с Windows.
echo ============================================================
echo.
pause
