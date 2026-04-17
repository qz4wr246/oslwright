function Trash {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline=$true, Position=0)]
        [string[]]$Path,

        # /S オプションに相当 (サブディレクトリも対象)
        [Alias("S")]
        [switch]$Recurse,

        # /F オプションに相当 (読み取り専用なども強制)
        [Alias("F")]
        [switch]$Force,

        # /Q オプションに相当 (確認なし)
        [Alias("Q")]
        [switch]$Quiet
    )

    process {
        foreach ($p in $Path) {
            $params = @{
                Path = $p
                Recycle = $true  # ゴミ箱へ送る
                Confirm = !$Quiet
                Force = $Force
            }
            if ($Recurse) { $params["Recurse"] = $true }

            Remove-Item @params
        }
    }
}

# 'del' というエイリアスをこの関数で上書きする場合（任意）
# Set-Alias del Trash
