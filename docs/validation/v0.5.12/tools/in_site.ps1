# Run one command in the site's working copy (C:/Projetos/refute-site), for the metered site units
# of v0.5.12's close (#218 comment 7202383280, item 5). The command and its arguments are this
# script's arguments; its exit code is the command's. Nothing else is changed.
$ErrorActionPreference = 'Stop'
if ($args.Count -lt 1) { throw 'usage: in_site.ps1 <command> [args...]' }
Set-Location -LiteralPath 'C:/Projetos/refute-site'
$exe = [string]$args[0]
$rest = @()
if ($args.Count -gt 1) { $rest = $args[1..($args.Count - 1)] }
& $exe @rest
exit $LASTEXITCODE
