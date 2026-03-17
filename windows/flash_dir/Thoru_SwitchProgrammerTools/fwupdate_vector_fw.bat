@echo off
if "%~1"=="" goto NO_FILE
SET FWFILE=%1%
SHIFT

spi_flash.exe -jtagmode=MAX -update=SP -fastverify -infile=%FWFILE% %1 %2 %3 %4 %5 %6 %7 %8 %9
SET ERRLEV=%ERRORLEVEL%
IF %ERRLEV% GTR 0 GOTO ERROR
GOTO END

:NO_FILE
ECHO "ERROR:No firmware filename given!"
SET ERRLEV=9
GOTO ERROR

:ERROR
ECHO ERRORLEVEL: %ERRLEV%
EXIT /B %ERRLEV%
:END
EXIT /B 0