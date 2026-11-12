Option Explicit

Dim fso, shell, baseDir, logPath, log, args, executable, command, argument, i, elevationArgs, elevationError
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
logPath = fso.BuildPath(baseDir, "security_bypass_batch.log")
shell.CurrentDirectory = baseDir

Set log = fso.OpenTextFile(logPath, 2, True)
log.WriteLine "Starting the security bypass application..."

Set args = WScript.Arguments
If args.Count > 0 Then
    If args(0) = "--elevate" Then
        If args.Count < 2 Then
            log.WriteLine "Cannot elevate: no executable was provided."
            log.Close
            WScript.Quit 1
        End If
        elevationArgs = "//nologo " & QuoteArgument(WScript.ScriptFullName)
        For i = 1 To args.Count - 1
            elevationArgs = elevationArgs & " " & QuoteArgument(args(i))
        Next
        log.WriteLine "Requesting administrator privileges."
        log.Close
        On Error Resume Next
        CreateObject("Shell.Application").ShellExecute WScript.FullName, elevationArgs, baseDir, "runas", 0
        elevationError = Err.Description
        If Err.Number <> 0 Then
            On Error GoTo 0
            Set log = fso.OpenTextFile(logPath, 8, True)
            log.WriteLine "Cannot request administrator privileges: " & elevationError
            log.Close
            WScript.Quit 1
        End If
        On Error GoTo 0
        WScript.Quit 0
    End If
End If

If args.Count = 0 Then
    executable = fso.BuildPath(baseDir, "env\Scripts\python.exe")
    command = QuoteArgument(executable) & " " & QuoteArgument(fso.BuildPath(baseDir, "security_bypass_wrapper.py"))
Else
    executable = args(0)
    If LCase(fso.GetFileName(executable)) = "pythonw.exe" Or LCase(executable) = "pythonw" Then
        If LCase(executable) = "pythonw" Then
            executable = "python"
        Else
            executable = fso.BuildPath(fso.GetParentFolderName(executable), "python.exe")
        End If
    End If
    command = QuoteArgument(executable)
    For i = 1 To args.Count - 1
        argument = args(i)
        command = command & " " & QuoteArgument(argument)
    Next
End If

shell.Environment("Process")("VIRTUAL_ENV") = fso.BuildPath(baseDir, "env")
shell.Environment("Process")("PATH") = fso.BuildPath(baseDir, "env\Scripts") & ";" & shell.Environment("Process")("PATH")
shell.Environment("Process").Remove "PYTHONHOME"
shell.Environment("Process")("PYTHONUNBUFFERED") = "1"

command = QuoteArgument(shell.ExpandEnvironmentStrings("%COMSPEC%")) & " /d /s /c " & Chr(34) & _
    command & " >> " & QuoteArgument(logPath) & " 2>&1" & Chr(34)
log.WriteLine "Launching application in the background."
log.Close
shell.Run command, 0, False

Function QuoteArgument(value)
    If InStr(value, Chr(34)) > 0 Or InStr(value, "%") > 0 Or _
       InStr(value, vbCr) > 0 Or InStr(value, vbLf) > 0 Then
        log.WriteLine "Cannot launch: an argument or path contains an unsupported character."
        log.Close
        WScript.Quit 1
    End If
    Do While Len(value) > 0
        If Right(value, 1) <> "\" Then Exit Do
        value = Left(value, Len(value) - 1)
        QuoteArgument = QuoteArgument & "\\"
    Loop
    QuoteArgument = Chr(34) & value & QuoteArgument & Chr(34)
End Function
