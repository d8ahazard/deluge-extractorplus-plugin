$python_vers = "35", "36", "37", "38", "39", "310", "311", "312", "313", "314"
$python_paths = "$env:LOCALAPPDATA\Programs\Python\", "$Env:Programfiles\"
for ( $i = 0; $i -lt $python_vers.count; $i++)
{
    $ver = $python_vers[$i]

    for ($j = 0; $j -lt $python_paths.count; $j++) {
        $path = $python_paths[$j]
        
        $fullpath = $path + "python" + $ver + "\python.exe"
        if (Get-Item -Path $fullpath -ErrorAction Ignore) {
            Write-Host "Fullpath exists: $fullpath"
            $exp = "'$fullpath' setup.py bdist_egg"
            Invoke-Expression "& $exp" 
        } else {
            Write-Host "FAIL: $fullpath"
        }
    }
}