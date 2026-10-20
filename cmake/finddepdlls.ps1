param (
  [String]$Target = "",
  [String]$TargetFile = "",
  [String]$Path = "",
  [String]$PathFile = "",
  [String]$Exclude = "",
  [String]$ExcludeFile = "",
  [String]$Dest = ""
)

$exc_ptn = @("Dump of file","File Type: DLL", "MSVC.*\.dll", "VCRUNTIME.*\.dll", "KERNEL32\.dll", "ucrtbased\.dll", "api-ms-win.*\.dll") -join '|'
$dumpbin = "dumpbin.exe"

function getDllDirectories($directories) {
  $result = @()
  foreach ($dir in $directories) {
    if (-not (Test-Path -Path $dir)) { continue }
    $dlldir = Get-ChildItem -Path $dir -Recurse -Filter *.dll -ErrorAction SilentlyContinue | Where-Object { $_.DirectoryName -notmatch '(^|[\\/])__oslw_dep_dlls([\\/]|$)' } | Select-Object -ExpandProperty DirectoryName | Sort-Object -Unique
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

try {
  if ($PathFile) {
    $dll_search_path = @(Get-Content -LiteralPath $PathFile -ErrorAction Stop | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  } elseif ($Path) {
    $dll_search_path = $Path.split(";")
  }

  $excludeArray = @()
  if ($ExcludeFile) {
    $excludeArray = @(Get-Content -LiteralPath $ExcludeFile -ErrorAction Stop | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  } elseif ($Exclude) {
    $excludeArray = $Exclude.Split(";")
  }

  $targetArray = @()
  if ($TargetFile) {
    $targetArray = @(Get-Content -LiteralPath $TargetFile -ErrorAction Stop | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  } elseif ($Target) {
    $targetArray = $Target.Split(";")
  }

  if ($targetArray.Length -gt 0 -and $dll_search_path.Length -gt 0){
    $dllpaths = getDllDirectories $dll_search_path
    $target_lst = @()
    $targetArray | ForEach-Object { if (Test-Path -Path $_) { $target_lst += Convert-Path $_ } }

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
}
catch {
  Write-Output $_
  exit 1
}

exit 0
