@echo off

@rem check whether python exists or not
for %%v in (12 11 10) do (
    for /f "delims=" %%i in ('where python ^| findstr /i "python3%%v"') do (
        set "PYTHON_PATH=%%i"
    )

    if defined PYTHON_PATH (
        goto :start
    )
)

echo No Python version has been found. Please intall python 10, 11 or 12 first.
pause
exit /b 1

:start
echo Python executable path: %PYTHON_PATH%
echo.

set TOOLS_FOLDER=%~d0\pytools
set DESTINATION_FOLDER="%TOOLS_FOLDER%\windows_security_bypass"

@rem create the pytools folder if does not exist
if not exist "%TOOLS_FOLDER%" mkdir %TOOLS_FOLDER%

echo Extracting files...
cd tmp
powershell -command "Expand-Archive -Force 'windows_security_bypass.zip'" %DESTINATION_FOLDER% || goto :error
echo Files have been extraced.
echo.

cd %DESTINATION_FOLDER% || goto :error

%PYTHON_PATH% -m pip install --upgrade pip > nul || goto :error
%PYTHON_PATH% initial_setup.py || goto :error

pause
exit /b 0

:error
echo Failed with error #%errorlevel%.
pause
exit /b %errorlevel%