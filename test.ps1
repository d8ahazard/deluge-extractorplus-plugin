$ver = "39"
$eggver = "3.9"
if ($args) {
    $ver = $args[0]
}

$python_paths = "$env:LOCALAPPDATA\Programs\Python\", "$Env:Programfiles\"
$deluge_path = "$env:APPDATA\deluge\plugins\"
$built = $false
for ($j = 0; $j -lt $python_paths.count; $j++) {
    if ($built) {
        break
    }
    $path = $python_paths[$j]        
    $fullpath = $path + "python" + $ver + "\python.exe"
    if (Get-Item -Path $fullpath -ErrorAction Ignore) {
        Write-Host "Fullpath exists: $fullpath"
        $exp = "'$fullpath' setup.py bdist_egg"
        Invoke-Expression "& $exp"
        $built = $true
    } else {
        Write-Host "FAIL: $fullpath"
    }
}

if (Test-Path -Path ".\dist\ExtractorPlus-1.6.2-py$eggver.egg") {
    Write-Host "Copying egg to $deluge_path"
    Copy-Item ".\dist\ExtractorPlus-1.6.2-py$eggver.egg" -Destination $deluge_path -Force
} else {
    Write-Host "Can't find egg: .\dist\ExtractorPlus-1.6.2-py$eggver.egg"
}

$deluge = Get-Process deluge -ErrorAction SilentlyContinue
if ($deluge) {
    Write-Host "Killing deluge-debug"
    # try gracefully first
    $deluge.CloseMainWindow()
    # kill after five seconds
    Sleep 5
    if (!$deluge.HasExited) {
        $deluge | Stop-Process -Force
    }
    Write-Host "Restarting deluge"
    $cmd = "$env:PROGRAMFILES\Deluge\deluge.exe"
Invoke-Command "& $cmd" -AsJob
}
$delugeD = Get-Process deluge-debug -ErrorAction SilentlyContinue
if ($deluged) {
    Write-Host "Killing deluge-debug"
    # try gracefully first
    $deluged.CloseMainWindow()
    # kill after five seconds
    Sleep 5
    if (!$deluged.HasExited) {
        $delugeD | Stop-Process -Force
    }
    Write-Host "Restarting deluge-debug"    
}

Start-Process -FilePath 'C:\Program Files\Deluge\deluge-debug.exe' -ArgumentList "-l C:\b\deluge.log -L debug" -NoNewWindow
