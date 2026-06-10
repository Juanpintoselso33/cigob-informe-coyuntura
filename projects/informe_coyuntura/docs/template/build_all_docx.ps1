# Regenera todos los .docx institucionales desde los .md correspondientes
# Uso: desde projects/informe_coyuntura/docs/template/
#   .\build_all_docx.ps1

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$docs = Split-Path -Parent $here
$ref  = Join-Path $here "cigob_reference.docx"

if (-not (Test-Path $ref)) {
    Write-Output "ERROR: no existe $ref"
    Write-Output "Generar primero con: pandoc -o cigob_reference.docx --print-default-data-file reference.docx; python build_reference.py"
    exit 1
}

$archivos = @(
    "260523_proyecto_pais_estado_extraccion",
    "cinturon_espiritu_epoca",
    "cinturon_gestion",
    "cinturon_macro",
    "cinturon_politica",
    "cinturon_vida_cotidiana"
)

foreach ($f in $archivos) {
    $md  = Join-Path $docs "$f.md"
    $out = Join-Path $docs "$f.docx"
    if (-not (Test-Path $md)) {
        Write-Output "SKIP $f.md no existe"
        continue
    }
    $result = pandoc $md -o $out --reference-doc=$ref 2>&1
    if ($LASTEXITCODE -eq 0) {
        $size = (Get-Item $out).Length
        Write-Output "OK   $f.docx ($size bytes)"
    } else {
        Write-Output "FAIL $f.docx : $result"
    }
}
