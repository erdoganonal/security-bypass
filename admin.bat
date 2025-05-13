@if (1==1) @if(1==0) @ELSE
REM This construct is used to embed both Batch and JScript code in the same file.
REM The Batch part runs when executed normally, while the JScript part runs when invoked via cscript.

@echo off
SETLOCAL ENABLEEXTENSIONS

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system" || (
    cscript //E:JScript //nologo "%~f0" %*
    @goto :EOF
)

@end @ELSE
var ShA = new ActiveXObject("Shell.Application");
var cmd = "";

for (var i = 2; i < WScript.Arguments.length; i++) {
    cmd += " " + WScript.Arguments(i);
}

var shell = new ActiveXObject("WScript.Shell");
shell.CurrentDirectory = WScript.Arguments(0);

ShA.ShellExecute(WScript.Arguments(1), cmd, "", "runas", 5);
@end