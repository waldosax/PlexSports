@echo off
SETLOCAL
cd Shared

set curdir=
set shareddir=%cd%
call :treeProcess
goto :eof

:treeProcess
rem Do whatever you want here over the files of this subdir, for example:
for %%f in (*.*) do (
	if exist "%~dp0PlexSportsAgent.bundle\Contents\Code\%curdir%%%fc" del /F /Q "%~dp0PlexSportsAgent.bundle\Contents\Code\%curdir%%%fc"
	if exist "%~dp0PlexSportsAgent.bundle\Contents\Code\%curdir%%%f" del /F /Q "%~dp0PlexSportsAgent.bundle\Contents\Code\%curdir%%%f"
	mklink /H "%~dp0PlexSportsAgent.bundle\Contents\Code\%curdir%%%f" "%shareddir%\%curdir%%%f"
	
	if exist "%~dp0Scanners\Series\PlexSportsScanner\%curdir%%%fc" del /F /Q "%~dp0Scanners\Series\PlexSportsScanner\%curdir%%%fc"
	if exist "%~dp0Scanners\Series\PlexSportsScanner\%curdir%%%f" del /F /Q "%~dp0Scanners\Series\PlexSportsScanner\%curdir%%%f"
	mklink /H "%~dp0Scanners\Series\PlexSportsScanner\%curdir%%%f" "%shareddir%\%curdir%%%f"
)
for /D %%d in (*) do (
	set curdir=%curdir%%%d\
    cd %%d
    call :treeProcess
    cd ..
)

ENDLOCAL
cd %~dp0
exit /b

