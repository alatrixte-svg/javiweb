@echo off
setlocal

cd /d "%~dp0"

set "DOWNLOAD_DRAFT=%USERPROFILE%\Downloads\draft-blog-post.json"
set "LOCAL_DRAFT=%~dp0draft-blog-post.json"

if not exist "%DOWNLOAD_DRAFT%" (
  echo No encuentro draft-blog-post.json en Descargas.
  echo Descargalo desde el panel privado con el boton "Descargar draft-blog-post.json".
  exit /b 1
)

copy /Y "%DOWNLOAD_DRAFT%" "%LOCAL_DRAFT%" >nul
if errorlevel 1 (
  echo No he podido reemplazar draft-blog-post.json.
  exit /b %errorlevel%
)

echo Borrador importado correctamente.
echo Ahora ejecuta publicar-blog.cmd.
