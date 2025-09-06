# Params:
#   -Target  <string>  path to .exe or .dll
#   -Path    <string>  search path. exp. "path1;path2;..."
#   -Exclude <string>  exclude dlls
#   -Dest    <string>  copy dlls to directory
#
param (
  [parameter(mandatory)][String]$Target,
  [String]$Path,
  [String]$Exclude,
  [String]$Dest
)

$exc_ptn = @("Dump of file", "MSVC.*\.dll", "VCRUNTIME.*\.dll", "KERNEL32\.dll", "ucrtbased\.dll", "api-ms-win.*\.dll")
$dumpbin = "dumpbin.exe"

function getDllDirectories($directories) {
  $result = @()
  foreach ($dir in $directories) {
    $dlldir = Get-ChildItem -Path $dir -Recurse -Filter *.dll | Select-Object -ExpandProperty DirectoryName | Sort-Object -Unique
    $result = $result + $dlldir
  }
  return $result
}

function getDependentDLL($target, $path, $excludes) {
  $cmd =  """$dumpbin"" /DEPENDENTS ""$target"" | findstr ""dll"""

  # Write-Host "## cmd=$cmd"
  $deps = (cmd.exe /c $cmd) | ForEach-Object { $_.Trim()} | Select-String -Pattern $exc_ptn -NotMatch
  $dlls = ($deps | Where-Object { $excludes -notcontains $_ })
  if ($dlls.Length) {
    $dlls_ptn = $dlls -join '|'
    $dlls_full = Get-ChildItem -Path $paths | Where-Object { $_.Name -match $dlls_ptn} | Select-Object -ExpandProperty FullName
    return @($dlls_full)
  } else {
    return @()
  }
}

function GetExternalDlls($target, $paths, $excludes){
  $find_dlls = @()
  $target_dlls = @($target)
  while($target_dlls.Length) {
    $next_target = @()
    foreach($f in $target_dlls) {
      $ret = @(getDependentDLL $f $paths $excludes)
      foreach($r in $ret) {
        if ($find_dlls -notcontains $r) {
          $find_dlls = $find_dlls + $r
          $next_target = $next_target + $r
        }
      }
    }
    $target_dlls = $next_target
  }
  if ($find_dlls.Length) {
    return $find_dlls | Select-Object -Unique
  } else {
    return @()
  }
}

# __main__
if ($Path) {
  $dll_search_path = $Path.split(";")
} elseif($env:FINDDEPDLL_SERCH_PATH) {
  $dll_search_path = $env:FINDDEPDLL_SERCH_PATH.split(";")
}
if ($Target -and $dll_search_path){
  try {
    $dllpaths = getDllDirectories $dll_search_path
    $target_lst = @()
    $Target.split(";") | ForEach-Object { $target_lst += Convert-Path $_ }
    $excludeArray = $Exclude.Split(";")
    $dlls = GetExternalDlls $target_lst $dllpaths $excludeArray
    if ($Dest -and $dlls){
      Copy-Item -Path $dlls -Destination $Dest -Force
    } else {
      Write-Host ($dlls -replace '\\','/' -join ";")
    }
  }
  catch {
    Write-Output $_
    exit 1
  }
}
exit 0
