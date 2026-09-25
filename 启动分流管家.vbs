' Start proxy-router in background, then open the web page
Set sh = CreateObject("WScript.Shell")
dir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
sh.Run "pythonw """ & dir & "\app.py""", 0, False
WScript.Sleep 1500
sh.Run "http://127.0.0.1:9123"
