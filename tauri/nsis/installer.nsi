; AI Workmate - Custom NSIS Installer Script
; Provides a professional installation wizard with auto-detection

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "WinMessages.nsh"
!include "x64.nsh"

; Application Info
!define APP_NAME "AI Workmate"
!define APP_VERSION "0.1.0"
!define APP_PUBLISHER "AI Workmate Team"
!define APP_WEBSITE "https://github.com/Fabian1808/Compa-ero_IA"
!define APP_EXE "ai-workmate.exe"
!define MAIN_EXE "ai-workmate.exe"

; Installer settings
RequestExecutionLevel admin
InstallDir "$PROGRAMFILES64\AI Workmate"
InstallDirRegKey HKLM "Software\AI Workmate" "InstallDir"

; Modern UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome Page
!define MUI_WELCOMEPAGE_TITLE "Bienvenido al Asistente de Instalación de AI Workmate"
!define MUI_WELCOMEPAGE_TEXT "Este asistente le guiará en la instalación de AI Workmate, su compañero de organización inteligente local.\n\nHaga clic en Siguiente para continuar."

; License Page
!define MUI_LICENSEPAGE_TEXT_TOP "Por favor revise los términos de la licencia antes de continuar."
!define MUI_LICENSEPAGE_TEXT_BOTTOM "Si acepta los términos, seleccione 'Acepto' y haga clic en Siguiente."
!define MUI_LICENSEPAGE_CHECKBOX "Acepto los términos del acuerdo de licencia"
!define MUI_LICENSEPAGE_RADIOBUTTONS

; Directory Page
!define MUI_DIRPAGE_TEXT_TOP "Seleccione la carpeta donde desea instalar AI Workmate:"
!define MUI_DIRPAGE_TEXT_DESTINATION "Carpeta de destino"

; Installing Page
!define MUI_INSTFILESPAGE_TEXT_TOP "Instalando AI Workmate..."
!define MUI_INSTFILESPAGE_TEXT_BOTTOM "Por favor espere mientras se copian los archivos."
!define MUI_INSTFILESPAGE_FINISHHEADERTEXT "Instalación completada"
!define MUI_INSTFILESPAGE_FINISHTEXT "AI Workmate se ha instalado correctamente.\n\nHaga clic en Finalizar para cerrar el asistente."

; Finish Page
!define MUI_FINISHPAGE_TITLE "Instalación completada"
!define MUI_FINISHPAGE_TEXT "AI Workmate se ha instalado correctamente en su computadora.\n\nAl ejecutar por primera vez, la aplicación configurará automáticamente:\n• Motor de IA local (Ollama)\n• Modelos de lenguaje (phi3, embeddings)\n• Conexión con Microsoft 365\n\nHaga clic en Finalizar para abrir AI Workmate."
!define MUI_FINISHPAGE_LINK "Ejecutar AI Workmate ahora"
!define MUI_FINISHPAGE_LINK_LOCATION "https://github.com/Fabian1808/Compa-ero_IA"
!define MUI_FINISHPAGE_RUN "$INSTDIR\ai-workmate.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Ejecutar AI Workmate"
!define MUI_FINISHPAGE_SHOWREADME ""

; Components Page (optional - for future extensions)
; !define MUI_COMPONENTSPAGE_TEXT_TOP "Seleccione las características que desea instalar:"
; !define MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_TITLE "Descripción"
; !define MUI_COMPONENTSPAGE_TEXT_DESCRIPTION_INFO "Mueva el mouse sobre un componente para ver su descripción."

; Language
!insertmacro MUI_LANGUAGE "Spanish"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Variables
Var StartMenuFolder
Var PreviousInstallDir
Var HasOllama
Var HasModels
Var RunAfterInstall

; Custom Pages for Prerequisite Detection
!define MUI_CUSTOMFUNCTION_PRE PreInstall
!define MUI_CUSTOMFUNCTION_POST PostInstall

Section "Main Application" SEC_MAIN
    SectionIn RO
    
    ; Set output path
    SetOutPath "$INSTDIR"
    
    ; Main executable (sidecar binary)
    File "/oname=ai-workmate.exe" "..\backend\dist\ai-workmate.exe"
    
    ; Frontend assets
    File /r "..\frontend\dist\*"
    
    ; Resources
    File /r "..\resources\*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Write registry keys for detection
    WriteRegStr HKLM "Software\AI Workmate" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\AI Workmate" "Version" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "DisplayIcon" "$INSTDIR\ai-workmate.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "InstallLocation" "$INSTDIR"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate" "NoRepair" 1
    
    ; Start Menu Shortcuts
    CreateDirectory "$SMPROGRAMS\AI Workmate"
    CreateShortcut "$SMPROGRAMS\AI Workmate\AI Workmate.lnk" "$INSTDIR\ai-workmate.exe" "" "$INSTDIR\ai-workmate.exe" 0
    CreateShortcut "$SMPROGRAMS\AI Workmate\Desinstalar AI Workmate.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
    
    ; Desktop Shortcut
    CreateShortcut "$DESKTOP\AI Workmate.lnk" "$INSTDIR\ai-workmate.exe" "" "$INSTDIR\ai-workmate.exe" 0
    
    ; Set run flag for finish page
    StrCpy $RunAfterInstall 1
    
SectionEnd

; Optional: System Tray Component
Section "System Tray Integration" SEC_TRAY
    ; This is handled by the app itself
SectionEnd

; Prerequisite Detection Functions
Function PreInstall
    ; Check for previous installation
    ReadRegStr $PreviousInstallDir HKLM "Software\AI Workmate" "InstallDir"
    StrCmp $PreviousInstallDir "" NoPreviousInstall
    
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Se detectó una instalación previa de AI Workmate en:\n$PreviousInstallDir\n\n¿Desea actualizarla?" \
        IDYES UpdateInstall
    
    NoPreviousInstall:
    Return
    
    UpdateInstall:
    StrCpy $INSTDIR $PreviousInstallDir
    Return
FunctionEnd

Function PostInstall
    ; Check for Ollama
    ExecWait '"$SYSDIR\where.exe" ollama' $0
    StrCmp $0 0 OllamaFound
    StrCpy $HasOllama 0
    Goto CheckModels
    
    OllamaFound:
    StrCpy $HasOllama 1
    
    CheckModels:
    ; Check if models exist (will be verified by app on first run)
    StrCpy $HasModels 0
    
    ; Write detection results for app to read
    WriteRegDWORD HKLM "Software\AI Workmate" "HasOllama" $HasOllama
    WriteRegDWORD HKLM "Software\AI Workmate" "HasModels" $HasModels
    WriteRegStr HKLM "Software\AI Workmate" "InstallDate" "$(GetDate)"
FunctionEnd

; Custom Uninstall
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\AI Workmate\AI Workmate.lnk"
    Delete "$SMPROGRAMS\AI Workmate\Desinstalar AI Workmate.lnk"
    RMDir "$SMPROGRAMS\AI Workmate"
    Delete "$DESKTOP\AI Workmate.lnk"
    
    ; Remove registry
    DeleteRegKey HKLM "Software\AI Workmate"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AI Workmate"
    
    ; Remove start menu folder
    RMDir "$SMPROGRAMS\AI Workmate"
SectionEnd

; Helper Functions
Function GetDate
    Push $0
    Push $1
    Push $2
    Push $3
    System::Call 'KERNEL32::GetLocalTime(lr0)'
    Pop $0 $1 $2 $3
    StrCpy $0 "$1/$2/$3"
    Exch $0
    Pop $3
    Pop $2
    Pop $1
    Pop $0
FunctionEnd

; Custom Pages for Prerequisite Check (shown during install)
!define MUI_CUSTOMFUNCTION_PRE CheckPrerequisites
!define MUI_CUSTOMFUNCTION_POST InstallPrerequisites

Function CheckPrerequisites
    ; This runs before the directory page
    ; We'll check what's missing and show info
    Return
FunctionEnd

Function InstallPrerequisites
    ; After installation, we could auto-install Ollama here
    ; But better to let the app handle it on first run for better UX
    Return
FunctionEnd

; Uninstaller
Function un.onInit
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "¿Está seguro de que desea desinstalar AI Workmate?\n\nSus datos locales (base de datos, configuración) NO se eliminarán.\n\n¿Continuar?" \
        IDYES +2
    Abort
FunctionEnd

; Modern UI Finish
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_RESERVEFILE_INSTALLDIR
!insertmacro MUI_RESERVEFILE_UNINSTALLER