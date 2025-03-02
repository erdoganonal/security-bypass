@if (1==1) @if(1==0) @ELSE
@echo off&SETLOCAL ENABLEEXTENSIONS
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"||(
    cscript //E:JScript //nologo "%~f0" %*
    @goto :EOF
)
cd %1
start /B %2 -m authentication %3
@goto :EOF
@end @ELSE
var ShA = new ActiveXObject("Shell.Application");
var cmd = "/c \"" + WScript.ScriptFullName + "\"";
for (var i = 0; i < WScript.Arguments.length; i++) {
    cmd += " " + WScript.Arguments(i);
}
ShA.ShellExecute("cmd.exe", cmd, "", "runas", 5);
@end