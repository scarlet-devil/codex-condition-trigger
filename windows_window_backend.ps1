# Bounded standalone backend. Run through CommandBackend; UTF-8 JSON stdin/out.
# Uses visible UIA controls and normal Win32 window operations only.
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class CycleWindowNative {
 [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int n);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern bool SetProp(IntPtr h,string k,IntPtr v);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern IntPtr GetProp(IntPtr h,string k);
 [DllImport("user32.dll",SetLastError=true)] public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr c);
}
'@
$A = [System.Windows.Automation.AutomationElement]
$S = [System.Windows.Automation.TreeScope]
function Root([long]$handle) { return $A::FromHandle([IntPtr]$handle) }
function Document([long]$handle) {
    $root = Root $handle
    $condition = New-Object System.Windows.Automation.PropertyCondition($A::AutomationIdProperty,'RootWebArea')
    $docs = $root.FindAll($S::Descendants,$condition)
    if ($docs.Count -ne 1) { throw 'document_not_unique' }
    $doc = $docs[0]; $pattern = $null
    if (-not $doc.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)) { throw 'route_unavailable' }
    return @{name=$doc.Current.Name; url=$pattern.Current.Value}
}
function SameDocument($left,$right) { return ($left.name -ceq $right.name -and $left.url -ceq $right.url) }
function BeforeAction {
    if (-not $request.stop_file -or (Test-Path -LiteralPath $request.stop_file)) { throw 'stopped' }
    if (-not $request.options.supervised_no_navigation_until -or
        [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -ge $request.options.supervised_no_navigation_until) {
        throw 'supervision_expired'
    }
}
function StableDocument([long]$handle) {
    $first = Document $handle
    Start-Sleep -Milliseconds 150
    $second = Document $handle
    if (-not (SameDocument $first $second)) { throw 'document_refresh_unstable' }
    return $second
}
function WindowProcess([long]$handle) {
    [uint32]$id=0
    if (-not [CycleWindowNative]::IsWindow([IntPtr]$handle)) { throw 'window_absent' }
    [void][CycleWindowNative]::GetWindowThreadProcessId([IntPtr]$handle,[ref]$id)
    $process = Get-Process -Id $id
    return @{pid=[int]$id; path=$process.Path; started=$process.StartTime.ToUniversalTime().Ticks.ToString()}
}
function SameProcess($actual,$expected) {
    return ($actual.pid -eq $expected.pid -and $actual.path -ieq $expected.path -and $actual.started -ceq $expected.started)
}
function Windows([int]$processId) {
    $condition = New-Object System.Windows.Automation.PropertyCondition($A::ProcessIdProperty,$processId)
    return @($A::RootElement.FindAll($S::Children,$condition) | ForEach-Object { [long]$_.Current.NativeWindowHandle })
}
function ExactRoute($document,[string]$target) {
    # initialRoute proves creation identity, not current navigation by itself.
    # Also require the current Document title to remain the bound target title.
    $uri = [Uri]$document.url
    if ($uri.Scheme -cne 'app' -or $uri.Host -cne '-' -or $uri.AbsolutePath -cne '/index.html') { return $false }
    $routes = @($uri.Query.TrimStart('?').Split('&') | Where-Object { $_.StartsWith('initialRoute=') })
    return ($routes.Count -eq 1 -and [Uri]::UnescapeDataString($routes[0].Substring(13)) -ceq ('/local/' + $target))
}
function CheckLease($lease,$request) {
    # This UI version exposes initialRoute, not an authenticated current route.
    # Closing is therefore only offered inside an explicitly supervised, bounded
    # no-navigation interval. Never claim this switch verifies user behavior.
    if (-not $request.options.supervised_no_navigation_until -or
        $request.options.supervised_no_navigation_until -ne $lease.supervised_until -or
        [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -ge $request.options.supervised_no_navigation_until) {
        throw 'current_thread_not_independently_verified_supervision_required'
    }
    if ($lease.thread_id -cne $request.thread_id -or $lease.expected_cwd -cne $request.expected_cwd -or
        $lease.hwnd -eq $lease.main_hwnd -or -not $lease.token.StartsWith('CodexConditionTrigger.')) { throw 'lease_binding_mismatch' }
    $main = WindowProcess $lease.main_hwnd
    if (-not (SameProcess $main $lease.process)) { throw 'main_process_changed' }
    if (-not [CycleWindowNative]::IsWindow([IntPtr]$lease.hwnd)) { return 'absent' }
    if (-not (SameProcess (WindowProcess $lease.hwnd) $lease.process)) { return 'mismatch' }
    if ([CycleWindowNative]::GetProp([IntPtr]$lease.hwnd,$lease.token) -ne [IntPtr]1) { return 'mismatch' }
    $doc = StableDocument $lease.hwnd
    if (-not (ExactRoute $doc $request.thread_id) -or $doc.name -cne $lease.target_title) { return 'mismatch' }
    return 'owned'
}
try {
    $request = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $options = $request.options
    $output = $null
    if ($request.action -eq 'inventory') {
        $process = WindowProcess $options.main_hwnd
        if ($process.path -ine $options.executable) { throw 'unexpected_executable' }
        $output = @{process=$process; windows=@(Windows $process.pid | ForEach-Object {
            @{hwnd=$_;document=(StableDocument $_);minimized=[CycleWindowNative]::IsIconic([IntPtr]$_)}
        });foreground=[CycleWindowNative]::GetForegroundWindow().ToInt64()}
    } elseif ($request.action -eq 'open') {
        $supervisionRemaining=[double]$options.supervised_no_navigation_until-[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        if ($supervisionRemaining -le 0 -or $supervisionRemaining -gt 600) { throw 'bounded_supervision_required' }
        $mainHandle = [long]$options.main_hwnd
        $process = WindowProcess $mainHandle
        if ($process.path -ine $options.executable) { throw 'unexpected_executable' }
        $mainBefore = StableDocument $mainHandle
        if ($options.main_title -and $mainBefore.name -cne $options.main_title) { throw 'main_title_changed' }
        if (-not $options.target_title -or -not $options.open_menu_name) { throw 'missing_explicit_control_names' }
        $before = @(Windows $process.pid)
        $foregroundBefore = [CycleWindowNative]::GetForegroundWindow().ToInt64()
        BeforeAction
        if (-not [CycleWindowNative]::SetForegroundWindow([IntPtr]$mainHandle)) { throw 'cannot_activate_main' }
        Start-Sleep -Milliseconds 150
        if ([CycleWindowNative]::GetForegroundWindow().ToInt64() -ne $mainHandle) { throw 'main_not_foreground' }
        $root = Root $mainHandle
        $named = New-Object System.Windows.Automation.PropertyCondition($A::NameProperty,[string]$options.target_title)
        $items = @($root.FindAll($S::Descendants,$named) | Where-Object {
            $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::ListItem -and -not $_.Current.IsOffscreen
        })
        if ($items.Count -ne 1) { throw 'target_row_not_unique_or_visible' }
        if (-not (SameDocument $mainBefore (StableDocument $mainHandle))) { throw 'main_changed_before_action' }
        $box = $items[0].Current.BoundingRectangle
        if ($box.Width -lt 1 -or $box.Height -lt 1) { throw 'row_bounds_unavailable' }
        [void][CycleWindowNative]::SetThreadDpiAwarenessContext([IntPtr](-4))
        BeforeAction
        [void][CycleWindowNative]::SetCursorPos([int]($box.Left+$box.Width/2),[int]($box.Top+$box.Height/2))
        [CycleWindowNative]::mouse_event(8,0,0,0,[UIntPtr]::Zero)
        [CycleWindowNative]::mouse_event(16,0,0,0,[UIntPtr]::Zero)
        $deadline = [DateTime]::UtcNow.AddSeconds(5); $menu = @()
        do {
            $root = Root $mainHandle
            $named = New-Object System.Windows.Automation.PropertyCondition($A::NameProperty,[string]$options.open_menu_name)
            $menu = @($root.FindAll($S::Descendants,$named) | Where-Object {
                $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::MenuItem -and -not $_.Current.IsOffscreen
            })
            if ($menu.Count -eq 1) { break }
            Start-Sleep -Milliseconds 100
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($menu.Count -ne 1) { throw 'explicit_open_menu_not_unique' }
        if (-not (SameDocument $mainBefore (StableDocument $mainHandle))) { throw 'main_changed_before_open' }
        $invoke = $null
        if (-not $menu[0].TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$invoke)) { throw 'menu_not_invokable' }
        $openedAt = [DateTime]::UtcNow
        BeforeAction
        $invoke.Invoke() # Exactly one invocation. Never repeat on an unknown result.
        $deadline = [DateTime]::UtcNow.AddSeconds(10); $newHandle=0; $doc=$null
        do {
            $new = @(Windows $process.pid | Where-Object { $_ -notin $before })
            if ($new.Count -gt 1) { throw 'multiple_new_windows' }
            if ($new.Count -eq 1) {
                try { $doc=StableDocument $new[0] } catch { $doc=$null }
                if ($doc -and (ExactRoute $doc $request.thread_id) -and $doc.name -ceq $options.target_title) {
                    $newHandle=$new[0]; break
                }
            }
            Start-Sleep -Milliseconds 100
        } while ([DateTime]::UtcNow -lt $deadline)
        if (-not $newHandle) { throw 'new_window_identity_unconfirmed' }
        if (-not (SameDocument $mainBefore (StableDocument $mainHandle))) { throw 'main_changed_during_open' }
        $token='CodexConditionTrigger.'+[Guid]::NewGuid().ToString()
        if (-not [CycleWindowNative]::SetProp([IntPtr]$newHandle,$token,[IntPtr]1)) { throw 'window_marker_failed' }
        $lease=@{thread_id=$request.thread_id;expected_cwd=$request.expected_cwd;token=$token;hwnd=$newHandle;
            main_hwnd=$mainHandle;process=$process;target_title=$options.target_title;initial_document=$doc;
            supervised_until=$options.supervised_no_navigation_until;
            main_before=$mainBefore;opened_at=$openedAt.ToString('o');foreground_before=$foregroundBefore;
            foreground_before_minimize=[CycleWindowNative]::GetForegroundWindow().ToInt64()}
        BeforeAction
        [void][CycleWindowNative]::ShowWindow([IntPtr]$newHandle,7) # SW_SHOWMINNOACTIVE
        if (-not [CycleWindowNative]::IsIconic([IntPtr]$newHandle)) { throw 'minimize_unconfirmed' }
        if (-not (SameDocument $mainBefore (StableDocument $mainHandle))) { throw 'main_changed_after_minimize' }
        $lease.minimized_at=[DateTime]::UtcNow.ToString('o')
        $lease.foreground_after_minimize=[CycleWindowNative]::GetForegroundWindow().ToInt64()
        $output=@{lease=$lease;status='owned';minimized=$true}
    } elseif ($request.action -in @('inspect','close')) {
        $lease=$request.lease
        $status=CheckLease $lease $request
        $mainBefore=StableDocument $lease.main_hwnd
        $output=@{status=$status;main_before=$mainBefore}
        if ($request.action -eq 'close' -and $status -eq 'owned') {
            # Recheck immediately before normal close; no process termination.
            if ((CheckLease $lease $request) -ne 'owned') { throw 'lease_changed_before_close' }
            BeforeAction
            if (-not [CycleWindowNative]::PostMessage([IntPtr]$lease.hwnd,0x0010,[IntPtr]::Zero,[IntPtr]::Zero)) { throw 'close_message_failed' }
            $deadline=[DateTime]::UtcNow.AddSeconds(5)
            while ([CycleWindowNative]::IsWindow([IntPtr]$lease.hwnd) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 100 }
            if ([CycleWindowNative]::IsWindow([IntPtr]$lease.hwnd)) { throw 'close_not_confirmed' }
            $output.status='absent'
            $output.closed_at=[DateTime]::UtcNow.ToString('o')
        }
        $output.main_after=StableDocument $lease.main_hwnd
        if (-not (SameDocument $mainBefore $output.main_after)) { throw 'main_changed_during_operation' }
        $output.main_unchanged=$true
    } else { throw 'unsupported_action' }
    $output | ConvertTo-Json -Depth 12 -Compress
} catch {
    @{error='window_backend_failed';reason=$_.Exception.Message} | ConvertTo-Json -Compress
    exit 1
}
