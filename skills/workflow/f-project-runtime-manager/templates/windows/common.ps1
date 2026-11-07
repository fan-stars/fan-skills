# Windows 进程库。生成时原样复制为 scripts/runtime/windows/lib/common.ps1。
# 适用于 Windows PowerShell 5.1。这里没有项目名；身份和命令数组由 lib/app-<app>.ps1 提供。
# 不要改写。不要使用 PowerShell 7 才有的语句连接符、三元运算符或空值合并运算符。

$ErrorActionPreference = 'Stop'
$script:LOG_PUMP_PID = ''

function Enable-Utf8Console {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = $utf8
    [Console]::InputEncoding = $utf8
    $global:OutputEncoding = $utf8
}

Enable-Utf8Console

$script:LogPumpSource = @'
param(
    [string]$StdoutPath,
    [string]$StderrPath,
    [string]$LogPath,
    [int]$ProcessId
)
$ErrorActionPreference = 'SilentlyContinue'

function Read-NewBytes([string]$Path, [ref]$Pos, $Writer) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $stream = $null
    try {
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    } catch {
        return
    }
    try {
        if ($Pos.Value -gt $stream.Length) { $Pos.Value = 0 }
        $stream.Position = $Pos.Value
        $buffer = New-Object byte[] 8192
        while (($count = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $Writer.BaseStream.Write($buffer, 0, $count)
            $Pos.Value = $Pos.Value + $count
        }
        $Writer.Flush()
    } finally {
        $stream.Dispose()
    }
}

$writer = $null
try {
    $fs = [System.IO.File]::Open($LogPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $writer = New-Object System.IO.StreamWriter($fs)
    $writer.AutoFlush = $true
    $outPos = 0
    $errPos = 0
    while ($true) {
        Read-NewBytes $StdoutPath ([ref]$outPos) $writer
        Read-NewBytes $StderrPath ([ref]$errPos) $writer
        $alive = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($null -eq $alive) { break }
        Start-Sleep -Milliseconds 300
    }
    Start-Sleep -Milliseconds 200
    Read-NewBytes $StdoutPath ([ref]$outPos) $writer
    Read-NewBytes $StderrPath ([ref]$errPos) $writer
} finally {
    if ($null -ne $writer) { $writer.Dispose() }
}
Remove-Item -LiteralPath $StdoutPath, $StderrPath -Force -ErrorAction SilentlyContinue
'@

$script:CwdReaderSource = @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class RuntimeProcessCwd {
    [StructLayout(LayoutKind.Sequential)]
    struct PROCESS_BASIC_INFORMATION {
        public IntPtr Reserved1;
        public IntPtr PebBaseAddress;
        public IntPtr Reserved2_0;
        public IntPtr Reserved2_1;
        public IntPtr UniqueProcessId;
        public IntPtr Reserved3;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, int pid);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool CloseHandle(IntPtr handle);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool IsWow64Process(IntPtr process, out bool wow64);

    [DllImport("ntdll.dll")]
    static extern int NtQueryInformationProcess(IntPtr process, int infoClass, ref PROCESS_BASIC_INFORMATION info, int size, out int returned);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool ReadProcessMemory(IntPtr process, IntPtr address, byte[] buffer, int size, out int read);

    public static string TryGet(int pid) {
        if (pid <= 0 || IntPtr.Size != 8) return null;
        IntPtr handle = OpenProcess(0x0410, false, pid);
        if (handle == IntPtr.Zero) handle = OpenProcess(0x1010, false, pid);
        if (handle == IntPtr.Zero) return null;
        try {
            bool wow64;
            if (!IsWow64Process(handle, out wow64) || wow64) return null;
            PROCESS_BASIC_INFORMATION pbi = new PROCESS_BASIC_INFORMATION();
            int returned;
            int status = NtQueryInformationProcess(handle, 0, ref pbi, Marshal.SizeOf(typeof(PROCESS_BASIC_INFORMATION)), out returned);
            if (status != 0 || pbi.PebBaseAddress == IntPtr.Zero) return null;
            byte[] ptr = new byte[8];
            int n;
            if (!ReadProcessMemory(handle, new IntPtr(pbi.PebBaseAddress.ToInt64() + 0x20), ptr, 8, out n) || n != 8) return null;
            long procParams = BitConverter.ToInt64(ptr, 0);
            if (procParams == 0) return null;
            byte[] us = new byte[16];
            if (!ReadProcessMemory(handle, new IntPtr(procParams + 0x38), us, 16, out n) || n != 16) return null;
            int length = BitConverter.ToUInt16(us, 0);
            long buffer = BitConverter.ToInt64(us, 8);
            if (length <= 0 || length > 32768 || buffer == 0) return null;
            byte[] chars = new byte[length];
            if (!ReadProcessMemory(handle, new IntPtr(buffer), chars, length, out n) || n != length) return null;
            string path = Encoding.Unicode.GetString(chars);
            if (string.IsNullOrWhiteSpace(path)) return null;
            return path;
        } catch {
            return null;
        } finally {
            CloseHandle(handle);
        }
    }
}
'@

function die([string]$Message) {
    [Console]::Error.WriteLine($Message)
    exit 1
}

function Join-Workspace([string]$Relative) {
    $rel = ([string]$Relative).Trim().Replace('/', '\')
    if ([string]::IsNullOrWhiteSpace($rel)) { return [string]$WORKSPACE_ROOT }
    return Join-Path ([string]$WORKSPACE_ROOT) $rel
}

function Get-Argv($Value) {
    if ($null -eq $Value) { return }
    if ($Value -is [string]) {
        Write-Output $Value
        return
    }
    foreach ($item in @($Value)) {
        if ($null -ne $item) { Write-Output ([string]$item) }
    }
}

function ConvertTo-CommandArgument([string]$Text) {
    if ($null -eq $Text -or $Text.Length -eq 0) { return '""' }
    if ($Text -notmatch '[\s"]') { return $Text }
    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $slash = 0
    foreach ($ch in $Text.ToCharArray()) {
        if ($ch -eq '\') {
            $slash++
            continue
        }
        if ($ch -eq '"') {
            $i = 0
            $need = $slash * 2 + 1
            while ($i -lt $need) {
                [void]$builder.Append('\')
                $i++
            }
            [void]$builder.Append('"')
            $slash = 0
            continue
        }
        if ($slash -gt 0) {
            $i = 0
            while ($i -lt $slash) {
                [void]$builder.Append('\')
                $i++
            }
            $slash = 0
        }
        [void]$builder.Append($ch)
    }
    if ($slash -gt 0) {
        $i = 0
        $need = $slash * 2
        while ($i -lt $need) {
            [void]$builder.Append('\')
            $i++
        }
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function ConvertTo-ArgumentLine {
    param([string[]]$ArgumentList)
    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($arg in @(Get-Argv $ArgumentList)) {
        [void]$parts.Add((ConvertTo-CommandArgument ([string]$arg)))
    }
    return ($parts.ToArray() -join ' ')
}

function Resolve-ToolLaunch([string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Name)) { die '缺少启动命令' }
    $file = ''
    if (Test-Path -LiteralPath $Name) {
        $file = (Resolve-Path -LiteralPath $Name).Path
    } else {
        $all = @(Get-Command -Name $Name -All -ErrorAction SilentlyContinue)
        foreach ($ext in @('.exe', '.cmd', '.bat', '.com')) {
            foreach ($cmd in $all) {
                if ($null -eq $cmd) { continue }
                $src = [string]$cmd.Source
                if ([string]::IsNullOrWhiteSpace($src)) { $src = [string]$cmd.Path }
                if ([string]::IsNullOrWhiteSpace($src)) { continue }
                if ($src.EndsWith($ext, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $file = $src
                    break
                }
            }
            if (-not [string]::IsNullOrWhiteSpace($file)) { break }
        }
        if ([string]::IsNullOrWhiteSpace($file)) {
            foreach ($cmd in $all) {
                if ($null -eq $cmd) { continue }
                if ([string]$cmd.CommandType -ne 'ExternalScript') { continue }
                $src = [string]$cmd.Source
                if ([string]::IsNullOrWhiteSpace($src)) { $src = [string]$cmd.Path }
                if ([string]::IsNullOrWhiteSpace($src)) { continue }
                $file = $src
                break
            }
        }
        if ([string]::IsNullOrWhiteSpace($file)) { die "找不到命令 $Name" }
    }
    $prefix = New-Object System.Collections.Generic.List[string]
    if ($file.EndsWith('.ps1', [System.StringComparison]::OrdinalIgnoreCase)) {
        [void]$prefix.Add('-NoProfile')
        [void]$prefix.Add('-ExecutionPolicy')
        [void]$prefix.Add('Bypass')
        [void]$prefix.Add('-File')
        [void]$prefix.Add($file)
        $file = Join-Path $PSHOME 'powershell.exe'
    }
    $result = New-Object psobject
    Add-Member -InputObject $result -NotePropertyName File -NotePropertyValue $file
    Add-Member -InputObject $result -NotePropertyName Prefix -NotePropertyValue $prefix
    return ,$result
}

function Get-LaunchArguments($Launch, $Argv) {
    foreach ($prefix in @($Launch.Prefix)) {
        Write-Output ([string]$prefix)
    }
    $items = @($Argv)
    $index = 1
    while ($index -lt $items.Count) {
        Write-Output ([string]$items[$index])
        $index++
    }
}

function Write-TextFile([string]$Path, [string]$Text) {
    $dir = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, ($Text.Trim() + "`r`n"), [System.Text.Encoding]::ASCII)
}

function Read-PidFile([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) { return '' }
    $text = [System.IO.File]::ReadAllText($Path)
    if ($text.Length -gt 0 -and [int][char]$text[0] -eq 0xFEFF) { $text = $text.Substring(1) }
    $text = $text.Trim()
    if ($text -notmatch '^[0-9]+$') { return '' }
    return $text
}

function Add-LogText([string]$Text) {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $bytes = $utf8.GetBytes($Text)
    $fs = [System.IO.File]::Open($script:LOG_FILE, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    try {
        $fs.Write($bytes, 0, $bytes.Length)
    } finally {
        $fs.Dispose()
    }
}

function Append-BinaryFile([string]$Destination, [string]$Source) {
    if (-not (Test-Path -LiteralPath $Source)) { return }
    $inputStream = $null
    $outputStream = $null
    try {
        $inputStream = [System.IO.File]::Open($Source, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $outputStream = [System.IO.File]::Open($Destination, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
        $inputStream.CopyTo($outputStream)
    } catch {
        return
    } finally {
        if ($null -ne $inputStream) { $inputStream.Dispose() }
        if ($null -ne $outputStream) { $outputStream.Dispose() }
    }
}

function Wait-LogPump {
    if ($script:LOG_PUMP_PID -notmatch '^[0-9]+$') { return }
    $left = 0
    while ($left -lt 10 -and (Test-PidAlive $script:LOG_PUMP_PID)) {
        Start-Sleep -Milliseconds 100
        $left++
    }
}

function Show-LogTail {
    if (-not (Test-Path -LiteralPath $script:LOG_FILE)) { return }
    Wait-LogPump
    [Console]::Error.WriteLine("last lines of $($script:LOG_FILE):")
    $utf8 = New-Object System.Text.UTF8Encoding $false
    $text = ''
    $stream = $null
    try {
        $stream = [System.IO.File]::Open($script:LOG_FILE, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $memory = New-Object System.IO.MemoryStream
        $stream.CopyTo($memory)
        $raw = $memory.ToArray()
        if ($raw.Length -gt 0) { $text = $utf8.GetString($raw) }
    } catch {
        [Console]::Error.WriteLine("无法读取日志: $($_.Exception.Message)")
        return
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
    }
    if ($text.Length -gt 0 -and [int][char]$text[0] -eq 0xFEFF) { $text = $text.Substring(1) }
    $lines = @($text -split "\r\n|\n|\r")
    $start = 0
    if ($lines.Count -gt 80) { $start = $lines.Count - 80 }
    $i = $start
    while ($i -lt $lines.Count) {
        [Console]::Error.WriteLine([string]$lines[$i])
        $i++
    }
}

function runtime_prepare {
    if ([string]::IsNullOrWhiteSpace([string]$SCRIPT_DIR)) { die '缺少 SCRIPT_DIR' }
    if ([string]::IsNullOrWhiteSpace([string]$APP_NAME)) { die '缺少 APP_NAME' }
    if ([string]::IsNullOrWhiteSpace([string]$WORKSPACE_ROOT)) { die '缺少 WORKSPACE_ROOT' }
    $script:LOG_PUMP_PID = ''
    $script:RUN_DIR = Join-Path $SCRIPT_DIR 'run'
    $script:LOG_DIR = Join-Path $SCRIPT_DIR 'logs'
    $script:CONFIG_DIR = Join-Path $SCRIPT_DIR 'config'
    $script:PID_FILE = Join-Path $script:RUN_DIR ($APP_NAME + '.pid')
    $script:LAUNCHER_FILE = Join-Path $script:RUN_DIR ($APP_NAME + '.launcher.pid')
    $script:MODE_FILE = Join-Path $script:RUN_DIR ($APP_NAME + '.mode')
    $script:LOG_FILE = Join-Path $script:LOG_DIR ($APP_NAME + '.log')
    $script:ENV_FILE = Join-Path $script:CONFIG_DIR ($APP_NAME + '.env')
    $script:EXAMPLE_FILE = Join-Path $script:CONFIG_DIR ($APP_NAME + '.env.example')
    if ([string]$APP_KIND -eq 'java') {
        $script:REACTOR_DIR = Join-Workspace ([string]$REACTOR_REL)
        $script:UNIT_DIR = Join-Workspace ([string]$UNIT_REL)
        $script:JAR_PATH = Join-Workspace ([string]$JAR_REL)
        if ([string]::IsNullOrWhiteSpace([string]$APP_CMD_MARKER) -and -not [string]::IsNullOrWhiteSpace([string]$MAIN_CLASS)) {
            $script:APP_CMD_MARKER = [string]$MAIN_CLASS
        } else {
            $script:APP_CMD_MARKER = [string]$APP_CMD_MARKER
        }
        if (-not [string]::IsNullOrWhiteSpace([string]$FINAL_NAME)) {
            $script:APP_JAR_MARKER = 'target/' + [string]$FINAL_NAME + '.jar'
        } else {
            $script:APP_JAR_MARKER = ''
        }
    } else {
        $script:WORK_DIR = Join-Workspace ([string]$WORK_REL)
        $script:PACKAGE_DIR = Join-Workspace ([string]$PACKAGE_REL)
        $script:APP_CMD_MARKER = [string]$APP_CMD_MARKER
        $script:APP_JAR_MARKER = ''
    }
    foreach ($dir in @($script:RUN_DIR, $script:LOG_DIR, $script:CONFIG_DIR)) {
        if (-not (Test-Path -LiteralPath $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
}

function Ensure-EnvFile {
    if ((-not (Test-Path -LiteralPath $script:ENV_FILE)) -and (Test-Path -LiteralPath $script:EXAMPLE_FILE)) {
        Copy-Item -LiteralPath $script:EXAMPLE_FILE -Destination $script:ENV_FILE
    }
}

function Import-RuntimeEnv([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) { return }
    $lines = [System.IO.File]::ReadAllLines($Path)
    foreach ($line in $lines) {
        $text = $line.Trim()
        if ($text.Length -eq 0) { continue }
        if ($text.StartsWith('#')) { continue }
        $eq = $text.IndexOf('=')
        if ($eq -lt 1) { continue }
        $key = $text.Substring(0, $eq).Trim()
        $value = $text.Substring($eq + 1).Trim()
        if ($key -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { continue }
        if ($value.Length -eq 0) { continue }
        if ($value -eq 'change-me') { continue }
        Set-Item -Path ('Env:' + $key) -Value $value
    }
}

function Get-AppPort {
    $value = ''
    if (-not [string]::IsNullOrWhiteSpace([string]$APP_PORT_VAR)) {
        $item = Get-Item -Path ('Env:' + [string]$APP_PORT_VAR) -ErrorAction SilentlyContinue
        if ($null -ne $item) { $value = [string]$item.Value }
    }
    if ([string]::IsNullOrWhiteSpace($value) -or $value -eq 'change-me') {
        $value = [string]$APP_PORT_DEFAULT
    }
    if ($value -eq 'change-me') { return '' }
    return $value
}

function Test-PidAlive([string]$ProcessId) {
    if ($ProcessId -notmatch '^[0-9]+$') { return $false }
    $id = [int]$ProcessId
    if ($id -le 0) { return $false }
    $proc = Get-Process -Id $id -ErrorAction SilentlyContinue
    return ($null -ne $proc)
}

function Initialize-CwdReader {
    if ('RuntimeProcessCwd' -as [type]) { return }
    Add-Type -TypeDefinition $script:CwdReaderSource -Language CSharp
}

function Get-ProcessCwd([int]$ProcessId) {
    if ($ProcessId -le 0) { return '' }
    try {
        Initialize-CwdReader
        $value = [RuntimeProcessCwd]::TryGet($ProcessId)
        if ([string]::IsNullOrWhiteSpace($value)) { return '' }
        return [string]$value
    } catch {
        return ''
    }
}

function Get-ProcessCommandLine([int]$ProcessId) {
    if ($ProcessId -le 0) { return '' }
    try {
        $row = Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId=" + $ProcessId) -ErrorAction SilentlyContinue
    } catch {
        return ''
    }
    if ($null -eq $row) { return '' }
    return [string]$row.CommandLine
}

function Get-ParentProcessId([int]$ProcessId) {
    if ($ProcessId -le 0) { return 0 }
    try {
        $row = Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId=" + $ProcessId) -ErrorAction SilentlyContinue
    } catch {
        return 0
    }
    if ($null -eq $row -or $null -eq $row.ParentProcessId) { return 0 }
    return [int]$row.ParentProcessId
}

function Get-ProcessRows {
    try {
        return @(Get-CimInstance -ClassName Win32_Process -ErrorAction SilentlyContinue | Select-Object ProcessId, ParentProcessId, CommandLine)
    } catch {
        return @()
    }
}

function ConvertTo-ComparablePath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
    $text = $Path.Trim()
    if ($text.StartsWith('\\?\')) { $text = $text.Substring(4) }
    $text = $text.Replace('/', '\')
    while ($text.Length -gt 3 -and $text.EndsWith('\')) {
        $text = $text.Substring(0, $text.Length - 1)
    }
    return $text.ToLowerInvariant()
}

function Test-CwdSame([string]$Cwd, [string]$Dir) {
    $left = ConvertTo-ComparablePath $Cwd
    $right = ConvertTo-ComparablePath $Dir
    if ($left.Length -eq 0 -or $right.Length -eq 0) { return $false }
    return ($left -eq $right)
}

function Test-CwdUnder([string]$Cwd, [string]$Dir) {
    $left = ConvertTo-ComparablePath $Cwd
    $right = ConvertTo-ComparablePath $Dir
    if ($left.Length -eq 0 -or $right.Length -eq 0) { return $false }
    if ($left -eq $right) { return $true }
    return $left.StartsWith($right + '\')
}

function Test-HasMarker([string]$CommandLine, [string]$Marker) {
    if ([string]::IsNullOrEmpty($CommandLine) -or [string]::IsNullOrEmpty($Marker)) { return $false }
    $left = $CommandLine.Replace('\', '/')
    $right = $Marker.Replace('\', '/')
    return ($left.IndexOf($right, [System.StringComparison]::Ordinal) -ge 0)
}

function Test-CommandHasToken([string]$CommandLine, [string]$Token) {
    if ([string]::IsNullOrEmpty($CommandLine) -or [string]::IsNullOrEmpty($Token)) { return $false }
    return ($CommandLine.IndexOf($Token, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
}

function Test-ProcessMatch {
    param([int]$ProcessId, [string]$CommandLine)
    if ($ProcessId -le 0 -or $ProcessId -eq 4) { return $false }
    if ($script:LOG_PUMP_PID -match '^[0-9]+$' -and [int]$script:LOG_PUMP_PID -eq $ProcessId) { return $false }
    if (-not (Test-PidAlive ([string]$ProcessId))) { return $false }
    if ([string]::IsNullOrWhiteSpace($CommandLine)) { $CommandLine = Get-ProcessCommandLine $ProcessId }
    if ([string]::IsNullOrWhiteSpace($CommandLine)) { return $false }
    $need = ''
    if ([string]$APP_KIND -eq 'java') {
        if (Test-HasMarker $CommandLine ([string]$APP_CMD_MARKER)) {
            $need = 'unit'
        } elseif (Test-HasMarker $CommandLine ([string]$APP_JAR_MARKER)) {
            $need = 'jar'
        } else {
            return $false
        }
    } else {
        if (-not (Test-HasMarker $CommandLine ([string]$APP_CMD_MARKER))) { return $false }
        $need = 'package'
    }
    $cwd = Get-ProcessCwd $ProcessId
    if ([string]::IsNullOrWhiteSpace($cwd)) { return $true }
    if ($need -eq 'unit') { return (Test-CwdUnder $cwd ([string]$UNIT_DIR)) }
    if ($need -eq 'jar') {
        if (Test-CwdSame $cwd ([string]$REACTOR_DIR)) { return $true }
        return (Test-CwdUnder $cwd ([string]$UNIT_DIR))
    }
    return (Test-CwdSame $cwd ([string]$PACKAGE_DIR))
}

function Test-LauncherMatch([int]$ProcessId) {
    if ($ProcessId -le 0 -or $ProcessId -eq 4) { return $false }
    if (-not (Test-PidAlive ([string]$ProcessId))) { return $false }
    $cmd = Get-ProcessCommandLine $ProcessId
    if ([string]::IsNullOrWhiteSpace($cmd)) { return $false }
    $cwd = Get-ProcessCwd $ProcessId
    if ([string]$APP_KIND -eq 'java') {
        $token = (Test-CommandHasToken $cmd 'mvn') -or (Test-CommandHasToken $cmd 'gradle') -or (Test-CommandHasToken $cmd 'classworlds')
        if (-not $token) { return $false }
        if ([string]::IsNullOrWhiteSpace($cwd)) { return $true }
        return (Test-CwdSame $cwd ([string]$REACTOR_DIR))
    }
    if ([string]::IsNullOrWhiteSpace([string]$NODE_PM)) { return $false }
    if (-not (Test-CommandHasToken $cmd ([string]$NODE_PM))) { return $false }
    if ([string]::IsNullOrWhiteSpace($cwd)) { return $true }
    if (Test-CwdSame $cwd ([string]$WORK_DIR)) { return $true }
    return (Test-CwdSame $cwd ([string]$PACKAGE_DIR))
}

function Get-DescendantText([int]$RootId, $Rows) {
    $children = @{}
    foreach ($row in @($Rows)) {
        $id = 0
        $ppid = 0
        try { $id = [int]$row.ProcessId } catch { continue }
        try { $ppid = [int]$row.ParentProcessId } catch { $ppid = 0 }
        if (-not $children.ContainsKey($ppid)) {
            $children[$ppid] = New-Object System.Collections.Generic.List[int]
        }
        [void]$children[$ppid].Add($id)
    }
    $result = New-Object System.Collections.Generic.List[int]
    $queue = New-Object System.Collections.Generic.Queue[int]
    $seen = @{}
    if ($children.ContainsKey($RootId)) {
        foreach ($child in @($children[$RootId])) { $queue.Enqueue($child) }
    }
    while ($queue.Count -gt 0) {
        $id = $queue.Dequeue()
        if ($seen.ContainsKey($id)) { continue }
        $seen[$id] = $true
        if ($id -eq $RootId -or $id -eq 0 -or $id -eq 4) { continue }
        [void]$result.Add($id)
        if ($children.ContainsKey($id)) {
            foreach ($child in @($children[$id])) {
                if (-not $seen.ContainsKey($child)) { $queue.Enqueue($child) }
            }
        }
    }
    if ($result.Count -eq 0) { return '' }
    return ($result.ToArray() -join ' ')
}

function Split-PidText([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return }
    foreach ($part in @($Text -split '\s+')) {
        if ($part -match '^[0-9]+$') { Write-Output $part }
    }
}

function Get-RowCommand($Rows, [int]$ProcessId) {
    foreach ($row in @($Rows)) {
        $id = 0
        try { $id = [int]$row.ProcessId } catch { continue }
        if ($id -eq $ProcessId) { return [string]$row.CommandLine }
    }
    return ''
}

function Find-MatchingText {
    param([string]$LauncherId)
    $rows = @(Get-ProcessRows)
    $result = New-Object System.Collections.Generic.List[int]
    if ($LauncherId -match '^[0-9]+$') {
        $root = [int]$LauncherId
        foreach ($idText in @(Split-PidText (Get-DescendantText $root $rows))) {
            $id = [int]$idText
            if ($id -eq $root) { continue }
            $cmd = Get-RowCommand $rows $id
            if (Test-ProcessMatch $id $cmd) {
                if (-not $result.Contains($id)) { [void]$result.Add($id) }
            }
        }
    } else {
        foreach ($row in $rows) {
            $id = 0
            try { $id = [int]$row.ProcessId } catch { continue }
            if ($id -eq $PID -or $id -eq 0 -or $id -eq 4) { continue }
            $cmd = [string]$row.CommandLine
            $markerHit = (Test-HasMarker $cmd ([string]$APP_CMD_MARKER)) -or (Test-HasMarker $cmd ([string]$APP_JAR_MARKER))
            if (-not $markerHit) { continue }
            if (Test-ProcessMatch $id $cmd) {
                if (-not $result.Contains($id)) { [void]$result.Add($id) }
            }
        }
    }
    if ($result.Count -eq 0) { return '' }
    return ($result.ToArray() -join ' ')
}

function Stop-OnePid([string]$ProcessId) {
    if ($ProcessId -notmatch '^[0-9]+$') { return $true }
    $id = [int]$ProcessId
    if ($id -eq 0 -or $id -eq 4) { return $true }
    if (-not (Test-PidAlive ([string]$id))) { return $true }
    [Console]::Error.WriteLine("stopping pid $id")
    try { Stop-Process -Id $id -ErrorAction Stop } catch { }
    try { Wait-Process -Id $id -Timeout 25 -ErrorAction Stop } catch { }
    if (Test-PidAlive ([string]$id)) {
        try { Stop-Process -Id $id -Force -ErrorAction Stop } catch { }
        Start-Sleep -Seconds 1
    }
    if (Test-PidAlive ([string]$id)) { return $false }
    return $true
}

function Stop-ParentsOf([string]$ProcessId) {
    if ($ProcessId -notmatch '^[0-9]+$') { return $true }
    $id = [int]$ProcessId
    $parent = Get-ParentProcessId $id
    if (-not (Stop-OnePid ([string]$id))) { return $false }
    $guard = 0
    while ($parent -ne 0 -and $parent -ne 4 -and $guard -lt 8) {
        $next = Get-ParentProcessId $parent
        if (Test-LauncherMatch $parent) {
            if (-not (Stop-OnePid ([string]$parent))) { return $false }
        } else {
            break
        }
        $parent = $next
        $guard++
    }
    return $true
}

function Remove-PidFiles {
    Remove-Item -LiteralPath $script:PID_FILE, $script:LAUNCHER_FILE -Force -ErrorAction SilentlyContinue
}

function Remove-RuntimeFiles {
    Remove-Item -LiteralPath $script:PID_FILE, $script:LAUNCHER_FILE, $script:MODE_FILE -Force -ErrorAction SilentlyContinue
}

function runtime_stop {
    runtime_prepare
    $procId = Read-PidFile $script:PID_FILE
    $launcher = Read-PidFile $script:LAUNCHER_FILE
    if (-not [string]::IsNullOrWhiteSpace($procId) -and (Test-PidAlive $procId) -and (Test-ProcessMatch ([int]$procId) '')) {
        if (-not (Stop-ParentsOf $procId)) { die "${APP_NAME} 停止失败" }
    } elseif (-not [string]::IsNullOrWhiteSpace($procId) -and (Test-PidAlive $procId)) {
        [Console]::Error.WriteLine("${APP_NAME} 的 pid $procId 与应用命令行或工作目录不符，未停止该进程")
    } else {
        $found = @(Split-PidText (Find-MatchingText ''))
        if ($found.Count -gt 1) {
            [Console]::Error.WriteLine("${APP_NAME} 匹配到多个进程，未停止: $($found -join ' ')")
            exit 1
        }
        if ($found.Count -eq 1) {
            if (-not (Stop-ParentsOf ([string]$found[0]))) { die "${APP_NAME} 停止失败" }
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($launcher) -and (Test-PidAlive $launcher) -and (Test-LauncherMatch ([int]$launcher))) {
        if (-not (Stop-OnePid $launcher)) { die "${APP_NAME} 启动器停止失败" }
    }
    Remove-PidFiles
    $left = @(Split-PidText (Find-MatchingText ''))
    if ($left.Count -gt 0) {
        [Console]::Error.WriteLine("${APP_NAME} 停止后仍有进程: $($left -join ' ')")
        exit 1
    }
    [Console]::Out.WriteLine("${APP_NAME}: stopped")
}

function Test-ListenRow($Row) {
    if ($null -eq $Row -or $null -eq $Row.RemotePort) { return $false }
    $remote = 0
    try { $remote = [int]$Row.RemotePort } catch { return $false }
    if ($remote -ne 0) { return $false }
    $state = $Row.State
    if ($null -eq $state) { return $true }
    $text = [string]$state
    if ([string]::IsNullOrWhiteSpace($text) -or $text -eq 'Listen' -or $text -eq '0') { return $true }
    return $false
}

function Get-ListenInfo([string]$Port) {
    $info = New-Object psobject -Property @{
        Pids = @()
        Unreadable = $false
    }
    if ($Port -notmatch '^[0-9]+$') { return $info }
    $rows = @()
    try {
        $rows = @(Get-NetTCPConnection -LocalPort ([int]$Port) -ErrorAction Stop)
    } catch {
        return $info
    }
    $ids = New-Object System.Collections.Generic.List[int]
    $saw = $false
    foreach ($row in $rows) {
        if (-not (Test-ListenRow $row)) { continue }
        $saw = $true
        $own = 0
        try { $own = [int]$row.OwningProcess } catch { $own = 0 }
        if ($own -gt 0 -and $own -ne 4 -and -not $ids.Contains($own)) { [void]$ids.Add($own) }
    }
    if ($saw -and $ids.Count -eq 0) { $info.Unreadable = $true }
    if ($ids.Count -gt 0) { $info.Pids = $ids.ToArray() }
    return $info
}

function Test-IdInList([string]$Needle, $List) {
    foreach ($item in @($List)) {
        if ([string]$item -eq [string]$Needle) { return $true }
    }
    return $false
}

function refuse_port_conflict {
    $port = Get-AppPort
    if ([string]::IsNullOrWhiteSpace($port)) { return }
    $info = Get-ListenInfo $port
    if ($info.Unreadable) { die "端口 $port 已被占用，但读不到监听 PID" }
    $conflicts = New-Object System.Collections.Generic.List[int]
    foreach ($id in @($info.Pids)) {
        if (-not (Test-ProcessMatch ([int]$id) '')) { [void]$conflicts.Add([int]$id) }
    }
    if ($conflicts.Count -gt 0) {
        die ("端口 $port 已被其他 PID 占用: " + ($conflicts.ToArray() -join ' '))
    }
}

function Get-PortWaitLimit {
    $raw = ''
    if (Test-Path Env:PORT_WAIT_SECONDS) { $raw = [string]$env:PORT_WAIT_SECONDS }
    if ([string]::IsNullOrWhiteSpace($raw) -or $raw -eq 'change-me') { return 180 }
    if ($raw -notmatch '^[1-9][0-9]{0,6}$') { return 180 }
    return [int]$raw
}

function confirm_port([string]$ProcessId) {
    $port = Get-AppPort
    if ([string]::IsNullOrWhiteSpace($port)) { return }
    $limit = Get-PortWaitLimit
    $elapsed = 0
    while ($elapsed -lt $limit) {
        if (-not (Test-PidAlive $ProcessId)) {
            Remove-RuntimeFiles
            Show-LogTail
            die "${APP_NAME} 在监听端口 $port 前退出"
        }
        $info = Get-ListenInfo $port
        if (Test-IdInList $ProcessId $info.Pids) {
            [Console]::Out.WriteLine("port $port is listening (pid $ProcessId)")
            return
        }
        if ($info.Unreadable) { die "端口 $port 已被占用，但读不到监听 PID" }
        $holders = @($info.Pids)
        if ($holders.Count -gt 0) {
            die ("端口 $port 由其他 PID 监听: " + ($holders -join ' '))
        }
        Start-Sleep -Seconds 1
        $elapsed++
    }
    if (-not (Test-PidAlive $ProcessId)) {
        Remove-RuntimeFiles
        Show-LogTail
        die "${APP_NAME} 在监听端口 $port 前退出"
    }
    die "端口 $port 在 $limit 秒内尚未监听，进程 $ProcessId 仍保留"
}

function Fail-Launcher([string]$LauncherId) {
    [Console]::Error.WriteLine("${APP_NAME} 未能在 60 秒内确认唯一的应用进程")
    if ($LauncherId -match '^[0-9]+$' -and (Test-PidAlive $LauncherId)) {
        [void](Stop-OnePid $LauncherId)
    }
    Remove-RuntimeFiles
    Show-LogTail
    exit 1
}

function Wait-AppDescendant([string]$LauncherId) {
    $elapsed = 0
    while ($elapsed -lt 60) {
        $found = @(Split-PidText (Find-MatchingText $LauncherId))
        if ($found.Count -eq 1) {
            Write-TextFile $script:PID_FILE ([string]$found[0])
            Write-TextFile $script:MODE_FILE 'run'
            return [string]$found[0]
        }
        if ($found.Count -gt 1) {
            [Console]::Error.WriteLine("${APP_NAME} 匹配到多个子孙进程: $($found -join ' ')")
            Fail-Launcher $LauncherId
        }
        Start-Sleep -Seconds 1
        $elapsed++
    }
    Fail-Launcher $LauncherId
    return ''
}

function Get-JavaMajor([string]$JavaHome) {
    $exe = Join-Path $JavaHome 'bin\java.exe'
    if (-not (Test-Path -LiteralPath $exe)) { return '' }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $exe
    $psi.Arguments = '-version'
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardOutput = $true
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    try {
        [void]$proc.Start()
    } catch {
        return ''
    }
    $errTask = $proc.StandardError.ReadToEndAsync()
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    [void]$proc.WaitForExit()
    $text = [string]$errTask.Result + "`n" + [string]$outTask.Result
    $match = [regex]::Match($text, 'version "([^"]+)"')
    if (-not $match.Success) { return '' }
    $version = $match.Groups[1].Value
    if ($version.StartsWith('1.')) { $version = $version.Substring(2) }
    $majorText = ($version -split '[^0-9]')[0]
    if ($majorText -notmatch '^[0-9]+$') { return '' }
    return $majorText
}

function Test-JavaHome([string]$JavaHome, [string]$Required) {
    if ([string]::IsNullOrWhiteSpace($JavaHome)) { return '' }
    $major = Get-JavaMajor $JavaHome
    if ($major -notmatch '^[0-9]+$') { return '' }
    if (-not [string]::IsNullOrWhiteSpace($Required) -and [int]$major -lt [int]$Required) { return '' }
    return $JavaHome
}

function Get-JavaHomeFromExe([string]$ExePath) {
    if ([string]::IsNullOrWhiteSpace($ExePath)) { return '' }
    $item = Get-Item -LiteralPath $ExePath -ErrorAction SilentlyContinue
    if ($null -eq $item) { return '' }
    $full = $item.FullName
    $name = [System.IO.Path]::GetFileName($full)
    if ($name -notmatch '^(?i)java(\.exe)?$') { return '' }
    $dir = [System.IO.Path]::GetDirectoryName($full)
    if ([System.IO.Path]::GetFileName($dir) -notmatch '^(?i)bin$') { return '' }
    return [System.IO.Path]::GetDirectoryName($dir)
}

function Add-JavaHomes([string]$Root, $List) {
    if ([string]::IsNullOrWhiteSpace($Root) -or -not (Test-Path -LiteralPath $Root)) { return }
    $direct = Join-Path $Root 'bin\java.exe'
    if (Test-Path -LiteralPath $direct) { [void]$List.Add($Root) }
    foreach ($child in @(Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue)) {
        $exe = Join-Path $child.FullName 'bin\java.exe'
        if (Test-Path -LiteralPath $exe) {
            [void]$List.Add($child.FullName)
            continue
        }
        foreach ($grand in @(Get-ChildItem -LiteralPath $child.FullName -Directory -ErrorAction SilentlyContinue)) {
            $exe2 = Join-Path $grand.FullName 'bin\java.exe'
            if (Test-Path -LiteralPath $exe2) { [void]$List.Add($grand.FullName) }
        }
    }
}

function Resolve-JavaHome([string]$Required) {
    if (-not [string]::IsNullOrWhiteSpace($env:JAVA_HOME)) {
        $ok = Test-JavaHome $env:JAVA_HOME $Required
        if (-not [string]::IsNullOrWhiteSpace($ok)) { return $ok }
    }
    if ([string]::IsNullOrWhiteSpace($Required)) { return '' }
    $cmd = Get-Command java -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $cmd -and -not [string]::IsNullOrWhiteSpace([string]$cmd.Source)) {
        $fromPath = Get-JavaHomeFromExe ([string]$cmd.Source)
        if (-not [string]::IsNullOrWhiteSpace($fromPath)) {
            $ok = Test-JavaHome $fromPath $Required
            if (-not [string]::IsNullOrWhiteSpace($ok)) { return $ok }
        }
    }
    $homes = New-Object System.Collections.Generic.List[string]
    $programFiles = [Environment]::GetFolderPath('ProgramFiles')
    foreach ($vendor in @('Java', 'Eclipse Adoptium', 'Microsoft', 'Amazon Corretto', 'Zulu', 'BellSoft', 'SapMachine')) {
        Add-JavaHomes (Join-Path $programFiles $vendor) $homes
    }
    $best = ''
    $bestMajor = 999
    foreach ($jdkHome in @($homes)) {
        $major = Get-JavaMajor $jdkHome
        if ($major -notmatch '^[0-9]+$') { continue }
        $majorNum = [int]$major
        if ($majorNum -ge [int]$Required -and $majorNum -lt $bestMajor) {
            $best = $jdkHome
            $bestMajor = $majorNum
        }
    }
    return $best
}

# $HOME 是只读自动变量，且大小写不敏感。JDK 路径不要赋值给 $home。
function setup_java {
    if ([string]$APP_KIND -ne 'java') { return }
    $required = [string]$JAVA_REQUIRED
    $hasHome = -not [string]::IsNullOrWhiteSpace($env:JAVA_HOME)
    if ([string]::IsNullOrWhiteSpace($required) -and -not $hasHome) { return }
    $jdkHome = Resolve-JavaHome $required
    if ([string]::IsNullOrWhiteSpace($jdkHome)) {
        die "找不到 JDK $required+；把 JAVA_HOME 写到 $($script:ENV_FILE)"
    }
    $env:JAVA_HOME = $jdkHome
    $env:PATH = (Join-Path $jdkHome 'bin') + ';' + $env:PATH
    [Console]::Out.WriteLine("JAVA_HOME=$env:JAVA_HOME")
}

$script:HandleSource = @'
using System;
using System.Runtime.InteropServices;
public static class RuntimeHandleInherit {
    [DllImport("kernel32.dll")]
    static extern IntPtr GetStdHandle(int nStdHandle);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool SetHandleInformation(IntPtr hObject, uint mask, uint flags);
    public static void DisableStdInherit() {
        int[] ids = new int[] { -10, -11, -12 };
        for (int i = 0; i < ids.Length; i++) {
            IntPtr handle = GetStdHandle(ids[i]);
            if (handle == IntPtr.Zero || handle == new IntPtr(-1)) continue;
            SetHandleInformation(handle, 1, 0);
        }
    }
}
'@

function Disable-StdHandleInherit {
    if (-not ('RuntimeHandleInherit' -as [type])) {
        Add-Type -TypeDefinition $script:HandleSource -Language CSharp
    }
    [RuntimeHandleInherit]::DisableStdInherit()
}

function Start-LogPump {
    param([string]$StdoutPath, [string]$StderrPath, [int]$ProcessId)
    $pumpPath = Join-Path $script:RUN_DIR 'log-pump.ps1'
    $utf8 = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($pumpPath, $script:LogPumpSource, $utf8)
    $ps = Join-Path $PSHOME 'powershell.exe'
    $argLine = ConvertTo-ArgumentLine @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $pumpPath,
        '-StdoutPath', $StdoutPath, '-StderrPath', $StderrPath,
        '-LogPath', $script:LOG_FILE, '-ProcessId', ([string]$ProcessId)
    )
    Disable-StdHandleInherit
    $pumpOut = Join-Path $script:RUN_DIR 'log-pump.out'
    $pumpErr = Join-Path $script:RUN_DIR 'log-pump.err'
    $pump = Start-Process -FilePath $ps -ArgumentList $argLine -WorkingDirectory $script:RUN_DIR -WindowStyle Hidden -PassThru -RedirectStandardOutput $pumpOut -RedirectStandardError $pumpErr
    if ($null -ne $pump) { $script:LOG_PUMP_PID = [string]$pump.Id }
}

function Start-LoggedProcess {
    param([string[]]$ArgumentList, [string]$WorkingDirectory)
    $argv = @(Get-Argv $ArgumentList)
    if ($argv.Count -eq 0) { die '缺少启动命令' }
    if ([string]::IsNullOrWhiteSpace($WorkingDirectory) -or -not (Test-Path -LiteralPath $WorkingDirectory)) {
        die "缺少目录 $WorkingDirectory"
    }
    $launch = Resolve-ToolLaunch ([string]$argv[0])
    $rest = @(Get-LaunchArguments $launch $argv)
    Disable-StdHandleInherit
    $safe = ([string]$APP_NAME -replace '[^A-Za-z0-9._-]', '-')
    $stamp = [DateTime]::UtcNow.Ticks.ToString()
    $stdout = Join-Path $script:LOG_DIR ('.' + $safe + '.' + $stamp + '.stdout')
    $stderr = Join-Path $script:LOG_DIR ('.' + $safe + '.' + $stamp + '.stderr')
    $params = @{
        FilePath = [string]$launch.File
        WorkingDirectory = $WorkingDirectory
        WindowStyle = 'Hidden'
        PassThru = $true
        RedirectStandardOutput = $stdout
        RedirectStandardError = $stderr
    }
    if ($rest.Count -gt 0) { $params.ArgumentList = (ConvertTo-ArgumentLine $rest) }
    $proc = $null
    $startError = ''
    try {
        $proc = Start-Process @params
    } catch {
        $startError = [string]$_.Exception.Message
    }
    if (-not [string]::IsNullOrWhiteSpace($startError)) {
        Append-BinaryFile $script:LOG_FILE $stdout
        Append-BinaryFile $script:LOG_FILE $stderr
        Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
        Show-LogTail
        die ("命令失败: " + ($argv -join ' ') + " (" + $startError + ")")
    }
    if ($null -eq $proc -or $proc.Id -notmatch '^[0-9]+$') { die "${APP_NAME} 启动失败" }
    try {
        Start-LogPump -StdoutPath $stdout -StderrPath $stderr -ProcessId ([int]$proc.Id)
    } catch {
        try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch { }
        Append-BinaryFile $script:LOG_FILE $stdout
        Append-BinaryFile $script:LOG_FILE $stderr
        Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
        die "无法把输出追加到 $($script:LOG_FILE)"
    }
    return [string]$proc.Id
}

function Invoke-Logged {
    param([string[]]$ArgumentList)
    $argv = @(Get-Argv $ArgumentList)
    if ($argv.Count -eq 0) { die '缺少启动命令' }
    $launch = Resolve-ToolLaunch ([string]$argv[0])
    $rest = @(Get-LaunchArguments $launch $argv)
    Disable-StdHandleInherit
    $safe = ([string]$APP_NAME -replace '[^A-Za-z0-9._-]', '-')
    $stdout = Join-Path $script:LOG_DIR ('.' + $safe + '.sync.stdout')
    $stderr = Join-Path $script:LOG_DIR ('.' + $safe + '.sync.stderr')
    $params = @{
        FilePath = [string]$launch.File
        WorkingDirectory = (Get-Location).Path
        WindowStyle = 'Hidden'
        PassThru = $true
        Wait = $true
        RedirectStandardOutput = $stdout
        RedirectStandardError = $stderr
    }
    if ($rest.Count -gt 0) { $params.ArgumentList = (ConvertTo-ArgumentLine $rest) }
    $proc = $null
    $startError = ''
    try {
        $proc = Start-Process @params
    } catch {
        $startError = [string]$_.Exception.Message
    } finally {
        Append-BinaryFile $script:LOG_FILE $stdout
        Append-BinaryFile $script:LOG_FILE $stderr
        Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
    }
    if (-not [string]::IsNullOrWhiteSpace($startError)) {
        Show-LogTail
        die ("命令失败: " + ($argv -join ' ') + " (" + $startError + ")")
    }
    $code = 1
    if ($null -ne $proc -and $null -ne $proc.ExitCode) { $code = [int]$proc.ExitCode }
    if ($code -ne 0) {
        Show-LogTail
        die ("命令失败: " + ($argv -join ' '))
    }
}

function Get-JavaUtf8EncodingArguments {
    return @(
        '-Dstdout.encoding=UTF-8',
        '-Dstderr.encoding=UTF-8',
        '-Dsun.stdout.encoding=UTF-8',
        '-Dsun.stderr.encoding=UTF-8'
    )
}

function Enable-JavaUtf8ToolOptions {
    $current = [string]$env:JAVA_TOOL_OPTIONS
    foreach ($flag in @(Get-JavaUtf8EncodingArguments)) {
        if ($current.IndexOf($flag, [System.StringComparison]::Ordinal) -ge 0) { continue }
        if ([string]::IsNullOrWhiteSpace($current)) {
            $current = $flag
        } else {
            $current = $current + ' ' + $flag
        }
    }
    $env:JAVA_TOOL_OPTIONS = $current
}

function start_java_run {
    if (-not (Test-Path -LiteralPath $script:REACTOR_DIR)) { die "缺少目录 $($script:REACTOR_DIR)" }
    Set-Location -LiteralPath $script:REACTOR_DIR
    $prepare = @(Get-Argv $JAVA_PREPARE_ARGV)
    if ($prepare.Count -gt 0) { Invoke-Logged -ArgumentList $prepare }
    $run = @(Get-Argv $JAVA_RUN_ARGV)
    if ($run.Count -eq 0) { die '缺少 JAVA_RUN_ARGV' }
    Enable-JavaUtf8ToolOptions
    $launcher = Start-LoggedProcess -ArgumentList $run -WorkingDirectory $script:REACTOR_DIR
    Write-TextFile $script:LAUNCHER_FILE $launcher
    [void](Wait-AppDescendant $launcher)
}

function start_java_jar {
    if (-not (Test-Path -LiteralPath $script:REACTOR_DIR)) { die "缺少目录 $($script:REACTOR_DIR)" }
    Set-Location -LiteralPath $script:REACTOR_DIR
    $package = @(Get-Argv $JAVA_PACKAGE_ARGV)
    if ($package.Count -eq 0) { die '缺少 JAVA_PACKAGE_ARGV' }
    Invoke-Logged -ArgumentList $package
    if (-not (Test-Path -LiteralPath $script:JAR_PATH)) { die "打包后找不到 $($script:JAR_PATH)" }
    $cmd = New-Object System.Collections.Generic.List[string]
    [void]$cmd.Add('java')
    $opts = [string]$env:JAVA_OPTS
    if (-not [string]::IsNullOrWhiteSpace($opts) -and $opts -ne 'change-me') {
        foreach ($part in @($opts -split '\s+')) {
            if (-not [string]::IsNullOrWhiteSpace($part)) { [void]$cmd.Add($part) }
        }
    }
    foreach ($flag in @(Get-JavaUtf8EncodingArguments)) {
        [void]$cmd.Add($flag)
    }
    [void]$cmd.Add('-jar')
    [void]$cmd.Add([string]$script:JAR_PATH)
    if (Test-Path -LiteralPath $script:LAUNCHER_FILE) {
        Remove-Item -LiteralPath $script:LAUNCHER_FILE -Force -ErrorAction SilentlyContinue
    }
    $appPid = Start-LoggedProcess -ArgumentList $cmd.ToArray() -WorkingDirectory $script:REACTOR_DIR
    Write-TextFile $script:PID_FILE $appPid
    Write-TextFile $script:MODE_FILE 'jar'
    Start-Sleep -Seconds 1
    if (-not (Test-PidAlive $appPid) -or -not (Test-ProcessMatch ([int]$appPid) '')) {
        Remove-Item -LiteralPath $script:PID_FILE, $script:MODE_FILE -Force -ErrorAction SilentlyContinue
        Show-LogTail
        die "${APP_NAME} jar 进程没有留下来"
    }
}

function start_node {
    if (-not (Test-Path -LiteralPath $script:WORK_DIR)) { die "缺少目录 $($script:WORK_DIR)" }
    if (-not (Test-Path -LiteralPath $script:PACKAGE_DIR)) { die "缺少目录 $($script:PACKAGE_DIR)" }
    if ([string]::IsNullOrWhiteSpace([string]$APP_CMD_MARKER)) { die '缺少 APP_CMD_MARKER' }
    Set-Location -LiteralPath $script:WORK_DIR
    $argv = @(Get-Argv $NODE_ARGV)
    if ($argv.Count -eq 0) { die '缺少 NODE_ARGV' }
    if ([string]::IsNullOrWhiteSpace([string]$NODE_PM)) { $script:NODE_PM = [string]$argv[0] }
    $modules = Join-Path $script:WORK_DIR 'node_modules'
    if (-not (Test-Path -LiteralPath $modules)) {
        if ([string]::IsNullOrWhiteSpace([string]$NODE_PM)) { die '缺少 NODE_PM' }
        Invoke-Logged -ArgumentList @([string]$NODE_PM, 'install')
    }
    $launcher = Start-LoggedProcess -ArgumentList $argv -WorkingDirectory $script:WORK_DIR
    Write-TextFile $script:LAUNCHER_FILE $launcher
    [void](Wait-AppDescendant $launcher)
}

function print_running {
    $mode = 'unknown'
    if (Test-Path -LiteralPath $script:MODE_FILE) {
        $mode = ([System.IO.File]::ReadAllText($script:MODE_FILE)).Trim()
        if ([string]::IsNullOrWhiteSpace($mode)) { $mode = 'unknown' }
    }
    $procId = Read-PidFile $script:PID_FILE
    if ([string]::IsNullOrWhiteSpace($procId)) { $procId = 'none' }
    $launcher = Read-PidFile $script:LAUNCHER_FILE
    if ([string]::IsNullOrWhiteSpace($launcher)) { $launcher = 'none' }
    $port = Get-AppPort
    if ([string]::IsNullOrWhiteSpace($port)) { $port = 'none' }
    [Console]::Out.WriteLine("${APP_NAME} mode=$mode pid=$procId launcher=$launcher port=$port log=$($script:LOG_FILE) config=$($script:ENV_FILE)")
}

function usage_and_exit {
    $name = 'app.ps1'
    foreach ($frame in @(Get-PSCallStack)) {
        if ([string]::IsNullOrWhiteSpace($frame.ScriptName)) { continue }
        $file = [System.IO.Path]::GetFileName($frame.ScriptName)
        if ($file -eq 'common.ps1') { continue }
        $name = $file
        break
    }
    if ([string]$APP_KIND -eq 'java') {
        [Console]::Error.WriteLine("用法: $name [run|jar]")
    } else {
        [Console]::Error.WriteLine("用法: $name [run]")
    }
    exit 2
}

function runtime_start {
    param([string]$Mode = 'run')
    runtime_prepare
    if ([string]::IsNullOrWhiteSpace($Mode)) { $Mode = 'run' }
    if ($Mode -ne 'run' -and $Mode -ne 'jar') { usage_and_exit }
    if ([string]$APP_KIND -ne 'java' -and $Mode -eq 'jar') {
        [Console]::Error.WriteLine("${APP_NAME} 没有 jar 模式")
        usage_and_exit
    }
    runtime_stop
    Ensure-EnvFile
    Import-RuntimeEnv $script:ENV_FILE
    setup_java
    refuse_port_conflict
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-LogText ("`r`n===== " + $Mode + ' ' + $stamp + " =====`r`n")
    if ([string]$APP_KIND -eq 'java' -and $Mode -eq 'jar') {
        start_java_jar
    } elseif ([string]$APP_KIND -eq 'java') {
        start_java_run
    } else {
        start_node
    }
    $appPid = Read-PidFile $script:PID_FILE
    confirm_port $appPid
    if (-not [string]::IsNullOrWhiteSpace((Get-AppPort))) { print_running }
}

function runtime_restart {
    param([string]$Mode = '')
    runtime_prepare
    $use = 'run'
    if (-not [string]::IsNullOrWhiteSpace($Mode)) {
        if ($Mode -ne 'run' -and $Mode -ne 'jar') { usage_and_exit }
        $use = $Mode
    } elseif (Test-Path -LiteralPath $script:MODE_FILE) {
        $use = ([System.IO.File]::ReadAllText($script:MODE_FILE)).Trim()
        if ([string]::IsNullOrWhiteSpace($use)) { $use = 'run' }
    }
    if ([string]$APP_KIND -ne 'java' -and $use -eq 'jar') {
        [Console]::Error.WriteLine("${APP_NAME} 没有 jar 模式")
        usage_and_exit
    }
    runtime_start -Mode $use
}

function runtime_status {
    runtime_prepare
    Ensure-EnvFile
    Import-RuntimeEnv $script:ENV_FILE
    $procId = Read-PidFile $script:PID_FILE
    if (-not [string]::IsNullOrWhiteSpace($procId) -and (Test-PidAlive $procId) -and (Test-ProcessMatch ([int]$procId) '')) {
        print_running
        return
    }
    $port = Get-AppPort
    [Console]::Out.WriteLine("${APP_NAME}: stopped port=$port")
}
