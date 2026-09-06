@echo off
setlocal

cd /d "%~dp0"

set "CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if exist "%CODEX_PYTHON%" (
  "%CODEX_PYTHON%" scripts\publicar_blog_post.py draft-blog-post.json
  goto :done
)

where py >nul 2>nul
if not errorlevel 1 (
  py scripts\publicar_blog_post.py draft-blog-post.json
  goto :done
)

where python >nul 2>nul
if not errorlevel 1 (
  python scripts\publicar_blog_post.py draft-blog-post.json
  goto :done
)

echo No encuentro Python para publicar el post.
echo Pidele a Codex: publicar ultimo post del blog.
exit /b 1

:done
if errorlevel 1 exit /b %errorlevel%

echo.
echo Listo. Revisa blog.html y haz commit de:
echo - blog-posts.json
echo - blog-posts.js
echo - posts\*.md
