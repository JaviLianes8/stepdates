# Regenerate tests/data/dotnet_calendar.csv: calendar arithmetic computed by .NET's
# System.DateTime (AddDays, AddMonths, AddYears), an implementation independent of this
# library. AddMonths and AddYears use the last day of a shorter month, which is the
# library's default "clamp" convention. Run with PowerShell 7:  pwsh scripts/dotnet_oracle.ps1
$ErrorActionPreference = "Stop"
$out = Join-Path $PSScriptRoot "..\tests\data\dotnet_calendar.csv"
$rng = [System.Random]::new(20261023)
$rows = [System.Collections.Generic.List[string]]::new()
$rows.Add("# Produced by scripts/dotnet_oracle.ps1 with .NET $([System.Environment]::Version) on $((Get-Date).ToString('yyyy-MM-dd'))")
$rows.Add("start,unit,amount,result")
$min = [DateTime]::new(1, 1, 1); $span = ([DateTime]::new(9999, 12, 31) - $min).Days
$units = @("days", "months", "years")
$amounts = @(1, -1, 2, -2, 3, 6, 11, 12, 13, -12, 24, 48, 100, -100, 400, 1200, -1200, 9998)
while ($rows.Count -lt 3002) {
    $start = $min.AddDays($rng.Next(0, $span + 1))
    if ($rng.NextDouble() -lt 0.6) {  # month ends and leap days are where conventions differ
        $month = @(1, 3, 5, 7, 8, 10, 12, 2)[$rng.Next(0, 8)]
        $last = [DateTime]::DaysInMonth($start.Year, $month)
        $start = [DateTime]::new($start.Year, $month, $last - $rng.Next(0, 3))
    }
    $unit = $units[$rng.Next(0, 3)]
    $amount = $amounts[$rng.Next(0, $amounts.Count)]
    if ($unit -eq "days") { $amount = $amount * ($rng.Next(1, 400)) }
    try {
        switch ($unit) {
            "days" { $result = $start.AddDays($amount) }
            "months" { $result = $start.AddMonths($amount) }
            "years" { $result = $start.AddYears($amount) }
        }
        $text = $result.ToString("yyyy-MM-dd")
    } catch [System.ArgumentOutOfRangeException] {
        $text = "out of range"
    }
    $rows.Add("$($start.ToString('yyyy-MM-dd')),$unit,$amount,$text")
}
[System.IO.File]::WriteAllText($out, ($rows -join "`n") + "`n")
