@echo off
chcp 65001 >nul
title Копирование ЭЦП с токена в реестр ПК (КриптоПро 5)
color 0A

:: ============================================================
::  Копирование контейнера с токена (Рутокен/JaCarta/eToken/флешка)
::  в реестр компьютера, чтобы работать без токена в браузере
::  Для КриптоПро CSP 5.x
::  Запускать ПРАВОЙ КНОПКОЙ -> Запуск от имени администратора
:: ============================================================

setlocal EnableDelayedExpansion

:: ---- 1. Ищем csptest.exe ----
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

:: пробуем найти через where
for /f "delims=" %%i in ('where csptest.exe 2^>nul') do (
  set "CSPT=%%i"
  goto :found
)

echo [ОШИБКА] Не найден csptest.exe
echo Проверьте что КриптоПро CSP 5 установлен.
echo Обычно он тут: C:\Program Files\Crypto Pro\CSP\
pause
exit /b 1

:found
echo Найден КриптоПро: "%CSPT%"
echo.

:: ---- 2. Показываем контейнеры ВЫБОРОМ ----
echo ===== ШАГ 1. Список контейнеров (токен должен быть вставлен!) =====
echo.
echo Сканирую контейнеры (пользователь + компьютер), подождите...
del "%TEMP%\csp_list.txt" 2>nul
"%CSPT%" -keyset -enum_cont -fqcn -verifyc > "%TEMP%\csp_list.txt" 2>&1
"%CSPT%" -keyset -enum_cont -fqcn -verifyc -machinekeys >> "%TEMP%\csp_list.txt" 2>&1
type "%TEMP%\csp_list.txt"
echo.
echo ----------------------------------------------------------------
:: Собираем список для выбора по номеру
set CNT=0
for /f "tokens=* delims=" %%A in ('type "%TEMP%\csp_list.txt" ^| findstr /L /C:"\\.\"') do (
  set /a CNT+=1
  set "CONT[!CNT!]=%%A"
  :: убираем ведущие пробелы (если есть)
  for /f "tokens=* delims= " %%B in ("%%A") do set "CONT[!CNT!]=%%B"
)
if !CNT! EQU 0 (
  echo.
  echo [ОШИБКА] Контейнеры не найдены.
  echo.
  echo Диагностика:
  echo  1. Токен точно вставлен? Горит ли лампочка?
  echo  2. Видит ли его Панель Рутокен / JaCarta? Откройте "Панель управления Рутокен".
  echo  3. В КриптоПро CSP -^> Оборудование -^> Настроить считыватели:
  echo     должен быть "Aktiv Rutoken ECP ..." или "JaCarta". Если нет - Добавьте.
  echo  4. Попробуйте БЕЗ "Запуск от администратора" - контейнеры пользователя
  echo     не всегда видны админу и наоборот.
  echo  5. Проверьте в "Инструменты КриптоПро -^> Контейнеры" - есть ли там токен?
  echo.
  echo Пробую показать считыватели:
  "%CSPT%" -enum -info -type PP_ENUMREADERS 2>&1
  echo.
  echo Нажмите 0 чтобы ввести имя вручную, Enter - выход.
  set "CHOICE="
  set /p CHOICE=Ваш выбор [0/Enter]: 
  if "!CHOICE!"=="0" goto :manual
  pause
  exit /b 1
)
echo Найдено контейнеров: !CNT!
echo.
for /l %%I in (1,1,!CNT!) do echo   %%I. !CONT[%%I]!
echo   0. Ввести вручную
echo ----------------------------------------------------------------
echo.
set "CHOICE="
set /p CHOICE=Выберите НОМЕР контейнера с токена [1-!CNT!]: 
if "%CHOICE%"=="" (
  echo Не выбран номер. Выход.
  pause
  exit /b 1
)
if "%CHOICE%"=="0" goto :manual
:: проверка что ввели число в диапазоне
call set "SRC=%%CONT[%CHOICE%]%%"
if "%SRC%"=="" (
  echo Неверный номер. Выход.
  pause
  exit /b 1
)
goto :src_ok

:manual
set "SRC="
set /p SRC=Вставьте ПОЛНОЕ имя исходного контейнера с токена (или короткое имя): 
if "%SRC%"=="" (
  echo Не введено имя. Выход.
  pause
  exit /b 1
)
:: Убираем кавычки если пользователь вставил с кавычками
set "SRC=%SRC:"=%"

:src_ok
echo.
echo Вы выбрали источник: %SRC%
echo.

:: Вычисляем короткое имя (после последнего \) для имени копии по умолчанию
set "SRCSHORT=%SRC%"
:loop_short
for /f "tokens=1* delims=\" %%a in ("!SRCSHORT!") do (
  if "%%b"=="" goto :short_done
  set "SRCSHORT=%%b"
  goto :loop_short
)
:short_done
:: убираем пробелы по краям
for /f "tokens=* delims= " %%B in ("!SRCSHORT!") do set "SRCSHORT=%%B"
if "!SRCSHORT!"=="" set "SRCSHORT=copy1"

:: ---- 4. Имя для копии ----
set "DSTNAME="
set /p DSTNAME=Придумайте ИМЯ для копии в ПК [Enter = !SRCSHORT!-copy]: 
if "!DSTNAME!"=="" set "DSTNAME=!SRCSHORT!-copy"
:: если ввели полное имя - оставляем только имя
echo Копия будет: \\.\REGISTRY\!DSTNAME!
echo.

:: ---- 5. PIN-коды ----
echo Стандартные PIN:
echo   Рутокен       - 12345678
echo   JaCarta       - 11111111 (или 1234567890 для PKI)
echo   eToken        - 1234567890
echo   Если PIN меняли - вводите свой.
echo.
set "PIN1="
set /p PIN1=Введите PIN от ТОКЕНА (если нет пароля - просто Enter): 
set "PIN2="
set /p PIN2=Введите ПАРОЛЬ для копии в ПК (можно пусто - просто Enter, но лучше задать): 

echo.
echo ===== ШАГ 2. Копирование %SRC% -^> РЕЕСТР =====
echo.

:: Формируем команду. Используем новый синтаксис -contsrc/-contdest,
:: он100%% работает в КриптоПро 5. Если не сработает - ниже закомментирован старый -src/-dest.
if "%PIN1%"=="" (
  set "PIN1OPT="
) else (
  set "PIN1OPT=-pinsrc %PIN1%"
)
if "%PIN2%"=="" (
  set "PIN2OPT=-pindest """" "
) else (
  set "PIN2OPT=-pindest %PIN2%"
)

echo Выполняю:
echo "%CSPT%" -keycopy -contsrc "%SRC%" -contdest "\\.\REGISTRY\%DSTNAME%" %PIN1OPT% %PIN2OPT%
echo.
"%CSPT%" -keycopy -contsrc "%SRC%" -contdest "\\.\REGISTRY\%DSTNAME%" %PIN1OPT% %PIN2OPT%

if errorlevel 1 (
  echo.
  echo [ВНИМАНИЕ] Копирование через -contsrc не получилось (код %ERRORLEVEL%), пробую старый синтаксис -src/-dest...
  echo.
  "%CSPT%" -keycopy -src "%SRC%" -pinsrc="%PIN1%" -dest "\\.\REGISTRY\%DSTNAME%" -pindest="%PIN2%"
)

if errorlevel 1 (
  echo.
  echo ============================================================
  echo  ОШИБКА КОПИРОВАНИЯ.
  echo  Частые причины:
  echo   1. Неверный PIN от токена
  echo   2. Такое имя в реестре уже есть - придумайте другое
  echo   3. Ключ НЕЭКСПОРТИРУЕМЫЙ (0x8009000B). Это все токены ФНС
  echo      после 2022г - их скопировать НЕЛЬЗЯ по закону, только оригинал.
  echo   4. Не запущена от имени Администратора
  echo ============================================================
  pause
  exit /b 1
)

echo.
echo ===== ШАГ 3. Установка сертификата в хранилище ЛИЧНЫЕ =====
echo Это нужно чтобы браузер/Госуслуги/Сбер/1С видели подпись без токена.
echo.
"%CSPT%" -property -cinstall -cont "\\.\REGISTRY\%DSTNAME%"

echo.
echo ============================================================
echo  ГОТОВО! Контейнер скопирован в: \\.\REGISTRY\%DSTNAME%
echo.
echo  Проверка:
echo   1. Пуск -^> КриптоПро CSP -^> Сервис -^> Посмотреть сертификаты в контейнере
echo   2. Выберите \\.\REGISTRY\%DSTNAME% - должен открыться сертификат
echo   3. Перезапустите браузер (Chrome/Edge/Yandex) и заходите на площадку
echo.
echo  ВАЖНО:
echo   - Токен теперь можно вынуть, но ОРИГИНАЛ НЕ ТЕРЯЙТЕ!
echo   - Копия в реестре живет пока жива Windows. Сделайте еще копию на USB:
echo     Скопируйте этот же батник, только dest = \\.\FAT12_H\имя
echo   - Поставьте пароль на ПК и не давайте доступ посторонним -
echo     ключ теперь всегда подключен!
echo ============================================================
echo.
pause
