@echo off
SETLOCAL EnableDelayedExpansion
cd Shared

set shareddir=!cd!
REM ECHO !shareddir!
(echo "%shareddir%" & echo.) | findstr /O . | more +1 | (set /P RESULT= & call exit /B %%RESULT%%)
set /A shareddirLength=%ERRORLEVEL%-5
SET /A subdirStart=!shareddirLength!+1
set curdir=

REM ECHO %shareddirLength%
REM ECHO %subdirStart%

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
	if not exist "%~dp0PlexSportsAgent.bundle\Contents\Code\!curdir!" mkdir "%~dp0PlexSportsAgent.bundle\Contents\Code\!curdir!" >nul
	if exist "%~dp0PlexSportsAgent.bundle\Contents\Code\!curdir!%%fc" del /F /Q "%~dp0PlexSportsAgent.bundle\Contents\Code\!curdir!%%fc" >nul
	if exist "%~dp0PlexSportsAgent.bundle\Contents\Code\!curdir!%%f" del /F /Q "%~dp0PlexSportsAgent.bundle\Contents\Code\!curdir!%%f" >nul
	mklink /H "%~dp0PlexSportsAgent.bundle\Contents\Code\!curdir!%%f" "%shareddir%\!curdir!%%f" >nul
	
	if not exist "%~dp0Scanners\Series\PlexSportsScanner\!curdir!" mkdir "%~dp0Scanners\Series\PlexSportsScanner\!curdir!" >nul
	if exist "%~dp0Scanners\Series\PlexSportsScanner\!curdir!%%fc" del /F /Q "%~dp0Scanners\Series\PlexSportsScanner\!curdir!%%fc" >nul
	if exist "%~dp0Scanners\Series\PlexSportsScanner\!curdir!%%f" del /F /Q "%~dp0Scanners\Series\PlexSportsScanner\!curdir!%%f" >nul
	mklink /H "%~dp0Scanners\Series\PlexSportsScanner\!curdir!%%f" "%shareddir%\!curdir!%%f" >nul
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

