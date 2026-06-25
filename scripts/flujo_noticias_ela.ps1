param(
  [ValidateSet("buscar", "backup", "actualizar", "validar", "servir", "python")]
  [string]$Accion = "validar",

  [string]$Seleccion = "",
  [int]$Puerto = 8765,
  [switch]$ComprobarEnlacesNoticias
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..")

function Resolve-ProjectPython {
  $candidates = @()

  if ($env:CODEX_PYTHON) {
    $candidates += $env:CODEX_PYTHON
  }

  if ($env:USERPROFILE) {
    $candidates += Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  }

  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path -LiteralPath $candidate)) {
      return (Resolve-Path -LiteralPath $candidate).Path
    }
  }

  foreach ($command in @("python", "py", "python3")) {
    $resolved = Get-Command $command -ErrorAction SilentlyContinue

    if ($resolved) {
      return $resolved.Source
    }
  }

  throw "No se ha encontrado Python. Instala Python o define CODEX_PYTHON con la ruta del ejecutable."
}

$Python = Resolve-ProjectPython
Set-Location $Root

switch ($Accion) {
  "python" {
    Write-Host $Python
  }

  "buscar" {
    & $Python ".\scripts\buscar_noticias_ela.py"
  }

  "backup" {
    Copy-Item -LiteralPath ".\candidate-news.json" -Destination ".\candidate-news.backup.json" -Force
    Write-Host "Backup actualizado: candidate-news.backup.json"
  }

  "actualizar" {
    if (-not $Seleccion) {
      throw "Indica la lista de noticias validas con -Seleccion, por ejemplo: -Seleccion '1,2,3'."
    }

    & $Python ".\scripts\actualizar_ela_html.py" $Seleccion
  }

  "validar" {
    $args = @(".\scripts\verificar_ela.py")

    if ($ComprobarEnlacesNoticias) {
      $args += "--check-news-links"
    }

    & $Python @args
  }

  "servir" {
    $url = "http://127.0.0.1:$Puerto/ELA.html"
    Write-Host "Servidor local iniciado en $url"
    Write-Host "Pulsa Ctrl+C para detenerlo."
    & $Python -m http.server $Puerto --bind 127.0.0.1
  }
}
