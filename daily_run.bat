@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ================================
:: Script quotidien FPL Radar
:: Génère résumés, images placeholders, voix Hazel UK, vidéo finale
:: + Exporte les idées du jour vers data/ideas.json
:: + Génère un rapport HTML (avec images) et envoi Outlook optionnel
:: ================================

:: 1) Date du jour (format YYYY-MM-DD)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set DATE=!dt:~0,4!-!dt:~4,2!-!dt:~6,2!

echo 📅 Date du jour = %DATE%

:: 2) Génération des résumés + scripts sociaux
python youtube_fpl_agent.py --multi --limit 2 --generate-social --generate-images --voiceover

:: 3) Génération d’images placeholders (si tu utilises des placeholders)
python render_placeholders.py %DATE%

:: 4) Génération de la voix Hazel UK (locale)
python tts_pyttsx3.py fpl_summaries\social_%DATE%.md social_audio\%DATE%\voice_uk_local_v2.wav Hazel 140 1.0 gentle

:: 5) Génération du fichier list.txt (UTF-8 sans BOM) pour ffmpeg
powershell -Command ^
  "$files = Get-ChildItem .\social_images_out\%DATE%\*.png | Sort-Object Name; $lines=@(); for ($i=0; $i -lt $files.Count; $i++){ $p=$files[$i].FullName -replace '\\','/'; $lines += \"file '$p'\"; if ($i -lt $files.Count-1){ $lines += \"duration 5.6\" } }; [System.IO.File]::WriteAllLines('list.txt',$lines,(New-Object System.Text.UTF8Encoding($false)))"

:: 6) Assemblage vidéo finale avec ffmpeg (1080x1080 + audio normalisé + fades)
C:\Users\admin\Downloads\ffmpeg-2025-09-01-git-3ea6c2fe25-essentials_build\bin\ffmpeg.exe -y ^
  -f concat -safe 0 -i list.txt ^
  -i social_audio\%DATE%\voice_uk_local_v2.wav ^
  -filter_complex "[0:v]fps=30,scale=1080:1080:flags=lanczos,format=yuv420p[v];[1:a]dynaudnorm=f=200:g=25,afade=t=in:st=0:d=0.5,afade=t=out:st=30:d=3[a]" ^
  -map "[v]" -map "[a]" -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k -movflags +faststart -shortest out\short_%DATE%.mp4
powershell -ExecutionPolicy Bypass -Command "Import-Module BurntToast; New-BurntToastNotification -Text 'FPL Radar', 'Résumé du jour prêt !'"

echo ✅ Terminé : vidéo disponible dans out\short_%DATE%.mp4

:: 6.5) Export des idées du jour à partir des visuels -> data/ideas.json
python export_ideas_today.py

:: 7) Rapport HTML + envoi Outlook (si REPORT_EMAIL_TO est défini)
python report_build_and_send.py

endlocal
pause
