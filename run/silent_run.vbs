' Exec silencieuse pour run_bourse (évite le pop de la console)

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' On récupère le chemin complet du script VBS
scriptPath = WScript.ScriptFullName
' On en déduit le dossier où il se trouve
parentFolder = fso.GetParentFolderName(scriptPath)

' On lance le .bat avec le chemin complet et des guillemets pour les espaces
WshShell.Run """" & parentFolder & "\run_bourse.bat" & """", 0, False