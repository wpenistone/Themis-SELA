$mainScriptFile = "Themis SELA.py"
$specFile = "Themis_SELA.spec"

Set-ExecutionPolicy RemoteSigned -Scope Process -Force

function Check-Setup-Error {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "A critical error occurred during setup. Halting script." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "--- Starting Themis SELA Setup & Launcher ---" -ForegroundColor Cyan

Write-Host "`n--- 1. Checking for Python... ---" -ForegroundColor Yellow
$pythonExists = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonExists) {
    Write-Host "Python not found. Searching for the latest version from the Microsoft Store..."
    
    $latestPythonId = winget search --id "Python.Python.3" --source msstore --accept-source-agreements | `
        Select-String 'Python\.Python\.3\.' | `
        ForEach-Object { ($_ -split '\s+')[1] } | `
        Sort-Object -Descending | `
        Select-Object -First 1

    if ($null -ne $latestPythonId) {
        Write-Host "Latest version found: $latestPythonId. Installing..." -ForegroundColor Green
        winget install --id $latestPythonId --source msstore --accept-package-agreements
        Check-Setup-Error
        Write-Host "Python has been installed." -ForegroundColor Green
        Write-Host "IMPORTANT: You MUST CLOSE and REOPEN this terminal for the 'python' command to be available." -ForegroundColor Magenta
        Write-Host "Please close this window, open a new PowerShell, and run this script again." -ForegroundColor Magenta
        Read-Host "Press Enter to exit"
        exit
    } else {
        Write-Host "Could not automatically find a Python version to install from the Microsoft Store." -ForegroundColor Red
        Write-Host "Please install Python 3 manually and run this script again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Python is already installed." -ForegroundColor Green
}

Write-Host "`n--- 2. Upgrading pip... ---" -ForegroundColor Yellow
python -m pip install --upgrade pip
Check-Setup-Error

Write-Host "`n--- 3. Installing dependencies... ---" -ForegroundColor Yellow
$dependencies = @(
    "PyQt6",
    "easyocr",
    "Pillow",
    "numpy",
    "PyInstaller"
)
python -m pip install --quiet $dependencies
Check-Setup-Error
Write-Host "All libraries are installed and up to date." -ForegroundColor Green

while ($true) {
    Write-Host "`n==========================================================" -ForegroundColor Cyan
    Write-Host "          SETUP COMPLETE! What would you like to do?" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "  [1] Run the application" -ForegroundColor White
    Write-Host "  [2] Build the executable (.exe) file" -ForegroundColor White
    Write-Host "  [Q] Quit" -ForegroundColor White
    
    $choice = Read-Host "Enter your choice (1, 2, or Q)"

    switch ($choice.ToLower()) {
        '1' {
            Write-Host "`n--- Launching the application... ---" -ForegroundColor Yellow
            if (Test-Path $mainScriptFile) {
                Start-Process python -ArgumentList "'$mainScriptFile'"
                Write-Host "Application has been launched in a new window." -ForegroundColor Green
                exit 
            } else {
                Write-Host "ERROR: Main script file '$mainScriptFile' not found!" -ForegroundColor Red
                Read-Host "Press Enter to continue."
            }
            break
        }
        '2' {
            Write-Host "`n--- Building the executable... ---" -ForegroundColor Yellow
            if (Test-Path $specFile) {
                pyinstaller $specFile
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "`nBuild successful! Check the 'dist' folder for your executable." -ForegroundColor Green
                } else {
                    Write-Host "`nBuild failed. Please check the output above for errors." -ForegroundColor Red
                }
            } else {
                Write-Host "ERROR: PyInstaller spec file '$specFile' not found!" -ForegroundColor Red
            }
            Read-Host "`nBuild process finished. Press Enter to return to the menu."
        }
        'q' {
            Write-Host "Exiting."
            exit
        }
        default {
            Write-Host "`nInvalid choice. Please select 1, 2, or Q." -ForegroundColor Red
        }
    }
}