@echo off
set FRONTEND=frontend
set BACKEND=backend

echo ==> Building React app...
cd %FRONTEND%
call npm install
call npm run build
cd ..

echo ==> Copying assets...
rmdir /s /q %BACKEND%\static\assets 2>nul
xcopy /E /I %FRONTEND%\dist\assets %BACKEND%\static\assets

echo ==> Copying index.html...
copy %FRONTEND%\dist\index.html %BACKEND%\templates\index.html

echo ==> Done.