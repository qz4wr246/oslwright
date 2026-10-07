param (
  [String]$Target = "",
  [String]$Path = "",
  [String]$Exclude = "",
  [String]$Dest = ""
)

$exc_ptn = @("Dump of file","File Type: DLL", "MSVC.*\.dll", "VCRUNTIME.*\.dll", "KERNEL32\.dll", "ucrtbased\.dll", "api-ms-win.*\.dll") -join '|'
$dumpbin = "dumpbin.exe"

function getDllDirectories($directories) {
  $result = @()
  foreach ($dir in $directories) {
    if (-not (Test-Path -Path $dir)) { continue }
    $dlldir = Get-ChildItem -Path $dir -Recurse -Filter *.dll -ErrorAction SilentlyContinue | Select-Object -ExpandProperty DirectoryName | Sort-Object -Unique
    if ($dlldir) { $result += $dlldir }
  }
  return ($result | Sort-Object -Unique)
}

function getDependentDLL($target, $paths, $excludes) {
  $deps = & $dumpbin /DEPENDENTS $target 2>$null
  if (-not $deps) { return @() }

  $dlls = @()
  foreach ($line in $deps) {
    $trimmed = $line.Trim()
    if ($trimmed -match "dll" -and $trimmed -notmatch $script:exc_ptn) {
      if ($excludes -notcontains $trimmed) {
        $dlls += $trimmed
      }
    }
  }

  if ($dlls.Length -gt 0) {
    $dlls_full = Get-ChildItem -Path $paths -Filter *.dll -ErrorAction SilentlyContinue | Where-Object { $dlls -contains $_.Name } | Select-Object -ExpandProperty FullName
    return @($dlls_full)
  }
  return @()
}

function GetExternalDlls($target, $paths, $excludes){
  $find_dlls = @()
  $target_dlls = @($target)

  while ($target_dlls.Length -gt 0) {
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

  if ($find_dlls.Length -gt 0) {
    return ($find_dlls | Select-Object -Unique)
  }
  return @()
}

$dll_search_path = @()

if ($Path) {
  $dll_search_path = $Path.split(";")
} elseif($env:FINDDEPDLL_SEARCH_PATH) {
  $dll_search_path = $env:FINDDEPDLL_SEARCH_PATH.split(";")
}

if (-not $Target -and $env:FINDDEPDLL_TARGET) {
  $Target = $env:FINDDEPDLL_TARGET
}
if (-not $Exclude -and $env:FINDDEPDLL_EXCLUDE) {
  $Exclude = $env:FINDDEPDLL_EXCLUDE
}

if ($Target -and $dll_search_path.Length -gt 0){
  try {
    $dllpaths = getDllDirectories $dll_search_path
    $target_lst = @()
    $Target.split(";") | ForEach-Object { if (Test-Path -Path $_) { $target_lst += Convert-Path $_ } }

    $excludeArray = @()
    if ($Exclude) {
      $excludeArray = $Exclude.Split(";")
    }

    if ($target_lst.Length -gt 0) {
      $dlls = GetExternalDlls $target_lst $dllpaths $excludeArray
      if ($Dest -and $dlls){
        if (-not (Test-Path -Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force | Out-Null }
        Copy-Item -Path $dlls -Destination $Dest -Force
      } else {
        if ($dlls) {
          $formatted_dlls = @($dlls) | ForEach-Object { $_ -replace '\\','/' }
          Write-Host ($formatted_dlls -join ";")
        }
      }
    }
  }
  catch {
    Write-Output $_
    exit 1
  }
}

exit 0
