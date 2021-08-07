@echo off
SETLOCAL EnableDelayedExpansion
cd Shared

set shareddir=!cd!
ECHO !shareddir!
(echo "%shareddir%" & echo.) | findstr /O . | more +1 | (set /P RESULT= & call exit /B %%RESULT%%)
set /A shareddirLength=%ERRORLEVEL%-5
SET /A subdirStart=!shareddirLength!+1
set curdir=

SET agentcodepath=PlexSportsAgent.bundle\Contents\Code
SET scannercodepath=Scanners\Series\PlexSportsScanner

REM ECHO %shareddirLength%
REM ECHO %subdirStart%



REM Push Plugin Support everywhere before recursing
if not exist "%shareddir%\Data" mkdir "%shareddir%\Data" >nul
if exist "%shareddir%\Data\PlugInSupport.py" del /F /Q "%shareddir%\Data\PlugInSupport.py" >nul
if exist "%shareddir%\Data\PlugInSupport.pyc" del /F /Q "%shareddir%\Data\PlugInSupport.pyc" >nul
mklink /H "%shareddir%\Data\PlugInSupport.py" "%shareddir%\PlugInSupport.py" >nul

REM Push Plugin Support everywhere before recursing
if not exist "%shareddir%\Data" mkdir "%shareddir%\Data" >nul
if exist "%shareddir%\Data\PathUtils.py" del /F /Q "%shareddir%\Data\PathUtils.py" >nul
if exist "%shareddir%\Data\PathUtils.pyc" del /F /Q "%shareddir%\Data\PathUtils.pyc" >nul
mklink /H "%shareddir%\Data\PathUtils.py" "%shareddir%\PathUtils.py" >nul



call :treeProcess
goto :eof

:treeProcess

REM ECHO !curdir!
REM echo Looking in %curdir%
REM ECHO !cd!
REM ECHO !curdir!
for %%f in (*.*) do (
	REM ECHO %%f
	REM ECHO !curdir!%%f
	REM ECHO %shareddir%!curdir!%%f
	REM ECHO !cd!\%%f
	if not exist "%~dp0%agentcodepath%\!curdir!" mkdir "%~dp0%agentcodepath%\!curdir!" >nul
	if exist "%~dp0%agentcodepath%\!curdir!%%fc" del /F /Q "%~dp0%agentcodepath%\!curdir!%%fc" >nul
	if exist "%~dp0%agentcodepath%\!curdir!%%f" del /F /Q "%~dp0%agentcodepath%\!curdir!%%f" >nul
	mklink /H "%~dp0%agentcodepath%\!curdir!%%f" "%shareddir%\!curdir!%%f" >nul
	
	if not exist "%~dp0%scannercodepath%\!curdir!" mkdir "%~dp0%scannercodepath%\!curdir!" >nul
	if exist "%~dp0%scannercodepath%\!curdir!%%fc" del /F /Q "%~dp0%scannercodepath%\!curdir!%%fc" >nul
	if exist "%~dp0%scannercodepath%\!curdir!%%f" del /F /Q "%~dp0%scannercodepath%\!curdir!%%f" >nul
	mklink /H "%~dp0%scannercodepath%\!curdir!%%f" "%shareddir%\!curdir!%%f" >nul
)
for /D %%d in (*) do (
	REM ECHO --recursing %%d
	REM ECHO --switching to !curdir!
	REM ECHO CURRENT: !cd!
	REM ECHO EXPECTED: %shareddir%\!curdir!
    REM if exist %%d (
		cd %%d
		CALL SET curdir=!!cd:~%subdirStart%!!\
		REM ECHO --switched to !cd!
		call :treeProcess
		cd ..
	REM )
)

REM ENDLOCAL
REM cd %~dp0
exit /b

