<# Register one current-user logon task for an explicitly expiring trial.
   Requires the user's authorization to install this task. Does not start it.
   No credentials, SYSTEM principal, timer polling, or automatic renewal.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Config,
    [Parameter(Mandatory)][string]$Pythonw,
    [Parameter(Mandatory)][ValidatePattern('^Codex-ConditionTrigger-[A-Za-z0-9-]+$')][string]$TaskName,
    [Parameter(Mandatory)][string]$EvidenceDirectory,
    [switch]$Dry
)
$ErrorActionPreference = 'Stop'
$cfgPath = (Resolve-Path -LiteralPath $Config).Path
$pythonPath = (Resolve-Path -LiteralPath $Pythonw).Path
$workerPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'trial_worker.py')).Path
if ([IO.Path]::GetFileName($pythonPath) -ine 'pythonw.exe') { throw 'Use pythonw.exe to avoid an interactive console.' }
foreach ($p in @($cfgPath,$pythonPath,$workerPath)) {
    if ($p.Contains('"') -or $p.Contains("`r") -or $p.Contains("`n")) { throw 'Unsupported argument characters.' }
}
$rawConfig = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8
# PowerShell 7.5 otherwise converts ISO strings to DateTime, losing the
# original aware-string validation contract. Windows PowerShell keeps strings.
if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
    $cfg = $rawConfig | ConvertFrom-Json -DateKind String
} else {
    $cfg = $rawConfig | ConvertFrom-Json
}
if (-not $cfg.trial_expires_at_utc -or $cfg.trial_expires_at_utc -notmatch '(Z|[+-]\d{2}:\d{2})$') { throw 'An aware fixed deadline is required.' }
$deadline = [DateTimeOffset]::Parse($cfg.trial_expires_at_utc)
if ($deadline -le [DateTimeOffset]::UtcNow) { throw 'The authorized trial has expired.' }
if ((Test-Path -LiteralPath (Join-Path $cfg.state_dir 'STOP')) -or
    (Test-Path -LiteralPath (Join-Path $cfg.state_dir 'TRIAL_EXPIRED.json'))) { throw 'Trial is stopped; installation cannot clear it.' }
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { throw 'Task already exists; inspect it instead of overwriting.' }
$userSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$arguments = '-X utf8 -B "' + $workerPath + '" --config "' + $cfgPath + '"'
if ($Dry) { $arguments += ' --dry' }
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $arguments -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userSid
$trigger.EndBoundary = $deadline.UtcDateTime.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
$principal = New-ScheduledTaskPrincipal -UserId $userSid -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -Hidden -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -DeleteExpiredTaskAfter (New-TimeSpan -Days 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds ([Math]::Ceiling(($deadline - [DateTimeOffset]::UtcNow).TotalSeconds) + 30))
$definition = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description 'Bounded condition-trigger trial; original STOP/deadline/state preserved; no automatic renewal.'
if ($deadline -le [DateTimeOffset]::UtcNow -or (Test-Path -LiteralPath (Join-Path $cfg.state_dir 'STOP'))) { throw 'Stopped before registration.' }
$null = Register-ScheduledTask -TaskName $TaskName -InputObject $definition
$actual = Get-ScheduledTask -TaskName $TaskName
function Resolve-TaskSid([string]$identity) {
    if ($identity -match '^S-1-') { return $identity }
    return ([Security.Principal.NTAccount]::new($identity)).Translate([Security.Principal.SecurityIdentifier]).Value
}
if ($actual.Actions.Execute -ne $pythonPath -or $actual.Actions.Arguments -ne $arguments -or
    $actual.Principal.LogonType -ne 'Interactive' -or $actual.Settings.MultipleInstances -ne 'IgnoreNew' -or
    $actual.Principal.RunLevel -ne 'Limited' -or (Resolve-TaskSid $actual.Principal.UserId) -ne $userSid -or
    (Resolve-TaskSid $actual.Triggers.UserId) -ne $userSid -or
    [DateTimeOffset]::Parse($actual.Triggers.EndBoundary) -ne [DateTimeOffset]::Parse($trigger.EndBoundary)) { throw 'Registered task readback mismatch.' }
$null = New-Item -ItemType Directory -Path $EvidenceDirectory -Force
$xml = Export-ScheduledTask -TaskName $TaskName
[IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'scheduled-task.private.xml'), $xml, [Text.UTF8Encoding]::new($false))
$receipt = [ordered]@{ task_name=$TaskName; registered_at_utc=[DateTimeOffset]::UtcNow.ToString('o');
    deadline_utc=$deadline.UtcDateTime.ToString('o'); logon_trigger=$true; periodic_trigger=$false;
    interactive_current_user=$true; highest_privilege=$false; dry=[bool]$Dry;
    worker_exception_retries=3; worker_retry_seconds=30; os_failure_retry_relied_on=$false;
    multiple_instances='IgnoreNew'; started=$false;
    xml_sha256=(Get-FileHash -LiteralPath (Join-Path $EvidenceDirectory 'scheduled-task.private.xml') -Algorithm SHA256).Hash.ToLower() }
$json = $receipt | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'task-registration.json'), $json, [Text.UTF8Encoding]::new($false))
$json
