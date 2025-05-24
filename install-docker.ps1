# Встановлює Docker Desktop на Windows
$dockerInstallerUrl = "https://desktop.docker.com/win/main/amd64/Docker Desktop Installer.exe"
$installerPath = "$env:TEMP\DockerDesktopInstaller.exe"

Write-Host " Завантаження Docker Desktop..."
Invoke-WebRequest -Uri $dockerInstallerUrl -OutFile $installerPath

Write-Host " Запуск інсталятора..."
Start-Process -FilePath $installerPath -Wait

Write-Host "` Установка завершена. Будь ласка, перезавантаж комп'ютер перед використанням Docker."
