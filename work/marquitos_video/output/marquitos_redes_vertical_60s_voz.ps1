
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -match 'In[eé]s|Ines' } | Select-Object -First 1
if (-not $voice) { $voice = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -match 'Laura' } | Select-Object -First 1 }
if (-not $voice) { $voice = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -match 'Helena' } | Select-Object -First 1 }
if (-not $voice) { $voice = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'es-ES' } | Select-Object -First 1 }
if ($voice) { $s.SelectVoice($voice.VoiceInfo.Name) }
$s.Rate = 0
$s.Volume = 100
$s.SetOutputToWaveFile('C:\Users\Qrent_395\Documents\Codex\javiweb\work\marquitos_video\output\marquitos_redes_vertical_60s_voz.wav')
$s.Speak((Get-Content -LiteralPath 'C:\Users\Qrent_395\Documents\Codex\javiweb\work\marquitos_video\output\marquitos_redes_vertical_60s_voz.txt' -Raw -Encoding UTF8))
$s.Dispose()
