# Deploy dsh-token-saver into the running DSH profile.
#
# DSH installs `file:` bundles by COPY, so editing the workspace source does not
# affect the running plugin. The installed host half is therefore a thin shim that
# imports the workspace source through a cache-busting module URL; only the client
# bundle (snapshotted by the host at publication) has to be copied.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File F:\EngineeringProject\dsh-token-saver\deploy.ps1
# Then restart the loader entry (set_plugin false -> true on include:dsh-token-saver)
# or relaunch DSH.

$ErrorActionPreference = 'Stop'

$src = 'F:\EngineeringProject\dsh-token-saver'
$dst = 'C:\Users\Administrator\.dsh\profiles\desktop\node_modules\dsh-token-saver'

if (-not (Test-Path $dst)) { throw "installed plugin not found at $dst" }

$shim = @'
/**
 * Installed shim for dsh-token-saver. See F:\EngineeringProject\dsh-token-saver\README.md
 * The workspace source is imported through a fresh module URL on every activation so a
 * loader restart picks up new host code without reinstalling the bundle.
 */
const SOURCE = 'file:///F:/EngineeringProject/dsh-token-saver/index.js';

export async function apply(ctx, config) {
  const url = SOURCE + (SOURCE.includes('?') ? '&' : '?') + 'v=' + Date.now();
  const mod = await import(url);
  return mod.apply(ctx, config);
}
'@

[System.IO.File]::WriteAllText((Join-Path $dst 'index.js'), $shim, (New-Object System.Text.UTF8Encoding($false)))
Copy-Item (Join-Path $src 'client.js') (Join-Path $dst 'client.js') -Force

node --check (Join-Path $src 'client.js')
if ($LASTEXITCODE -ne 0) { throw 'client.js failed node --check' }
node --check (Join-Path $src 'index.js')
if ($LASTEXITCODE -ne 0) { throw 'index.js failed node --check' }

Get-ChildItem $dst | Select-Object Name, Length, LastWriteTime | Format-Table
Write-Output 'deployed. restart the loader entry to load the new host code and republish the bundle.'
