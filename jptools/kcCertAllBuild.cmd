set SCONSOPTIONS=%* --silent

set VERSION=2017.2jp
set UPDATEVERSIONTYPE=nvdajp

for /F "usebackq" %%t in (`python -c "from datetime import datetime as dt; print dt.now().strftime('%%y%%m%%d')"`) do set NOWDATE=%%t
set VERSION=%VERSION%-beta
set VERSION=%VERSION%-%NOWDATE%
set UPDATEVERSIONTYPE=%UPDATEVERSIONTYPE%beta

set PUBLISHER=nvdajp
set PFX=jptools\secret\knowlec-key161005.pfx
set PWFILE=jptools\secret\knowlec-key-pass.txt
@for /F "delims=" %%s in ('type %PWFILE%') do @set PASSWORD=%%s
set TIMESERVER=http://timestamp.comodoca.com/authenticode

@rem test nmake and check errorlevel
cl
if "%ERRORLEVEL%" neq "9009" goto :done

if exist "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\vcvars32.bat" goto x64
call "C:\Program Files\Microsoft Visual Studio 14.0\VC\bin\vcvars32.bat"
goto done
:x64
call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\vcvars32.bat"
:done
SET CL=/arch:IA32 /D "_USING_V110_SDK71_"

set VERIFYLOG=output\nvda_%VERSION%_verify.log
del /Q %VERIFYLOG%

@rem call scons.bat -c
call jptools\setupMiscDepsJp.cmd

set FILE1=source\synthDrivers\jtalk\libmecab.dll
@signtool sign /f %PFX% /p %PASSWORD% /t %TIMESERVER% %FILE1%
signtool verify /pa %FILE1% >> %VERIFYLOG%
@if not "%ERRORLEVEL%"=="0" goto onerror
timeout /T 5 /NOBREAK

set FILE2=source\synthDrivers\jtalk\libopenjtalk.dll
@signtool sign /f %PFX% /p %PASSWORD% /t %TIMESERVER% %FILE2%
signtool verify /pa %FILE2% >> %VERIFYLOG%
@if not "%ERRORLEVEL%"=="0" goto onerror
timeout /T 5 /NOBREAK

call jptools\kcCertBuild.cmd

signtool verify /pa dist\lib\*.dll >> %VERIFYLOG%
@if not "%ERRORLEVEL%"=="0" goto onerror
signtool verify /pa dist\lib64\*.dll >> %VERIFYLOG%
@if not "%ERRORLEVEL%"=="0" goto onerror
signtool verify /pa dist\*.exe >> %VERIFYLOG%
@if not "%ERRORLEVEL%"=="0" goto onerror
signtool verify /pa output\nvda_%VERSION%.exe >> %VERIFYLOG%
@if not "%ERRORLEVEL%"=="0" goto onerror

@rem copy output\nvda_%VERSION%.exe %USERPROFILE%\Dropbox\Public

cd jptools
call buildControllerClient.cmd
@if not "%ERRORLEVEL%"=="0" goto onerror
cd ..
:skip_client

exit /b 0

:onerror
echo nvdajp build error %ERRORLEVEL%
@if "%PAUSE%"=="1" pause
exit /b -1
