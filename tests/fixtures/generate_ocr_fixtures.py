"""
Script to generate OCR image fixtures and ground truth JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

OCR_DIR = Path(__file__).resolve().parent / "ocr"
OCR_DIR.mkdir(parents=True, exist_ok=True)

GROUND_TRUTH = {
    "english_sample.png": {
        "language": "eng",
        "text": "Page to Voice Intelligent Audiobook Platform\nAutomatic text extraction and speech synthesis",
    },
    "tamil_sample.png": {
        "language": "tam",
        "text": "பக்கம் முதல் குரல் வரை அறிவார்ந்த தளம்\nஎழுத்துக்களை இயற்கையான பேச்சாக மாற்றும் மென்பொருள்",
    },
    "sinhala_sample.png": {
        "language": "sin",
        "text": "පිටුවෙන් හඬට බුද්ධිමත් ශ්‍රව්‍ය වේදිකාව\nලිඛිත ලේඛන ස්වාභාවික හඬ බවට පරිවර්තනය කරයි",
    },
    "english_noisy.png": {
        "language": "eng",
        "text": "Page to Voice Intelligent Audiobook Platform\nAutomatic text extraction and speech synthesis",
    },
    "english_skewed.png": {
        "language": "eng",
        "text": "Page to Voice Intelligent Audiobook Platform\nAutomatic text extraction and speech synthesis",
    },
}

# Save ground_truth.json
gt_path = OCR_DIR / "ground_truth.json"
with open(gt_path, "w", encoding="utf-8") as f:
    json.dump(GROUND_TRUTH, f, ensure_ascii=False, indent=2)
print(f"Generated {gt_path}")

# Generate PowerShell script to render images using Windows native System.Drawing
ps1_content = """\ufeffAdd-Type -AssemblyName System.Drawing
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ocrDir = "tests/fixtures/ocr"

function Render-TextImage {
    param(
        [string]$text,
        [string]$fontName,
        [float]$fontSize,
        [string]$outputPath,
        [bool]$addNoise = $false,
        [float]$rotateAngle = 0.0
    )
    $bmp = New-Object System.Drawing.Bitmap 900, 200
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::White)
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

    if ($rotateAngle -ne 0.0) {
        $g.TranslateTransform(450, 100)
        $g.RotateTransform($rotateAngle)
        $g.TranslateTransform(-450, -100)
    }

    $font = New-Object System.Drawing.Font $fontName, $fontSize, [System.Drawing.FontStyle]::Regular
    $brush = [System.Drawing.Brushes]::Black
    $rect = New-Object System.Drawing.RectangleF 30, 30, 840, 140
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Near
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    $g.DrawString($text, $font, $brush, $rect, $format)
    $g.Dispose()

    if ($addNoise) {
        $rand = New-Object System.Random 42
        $noiseCount = [int](900 * 200 * 0.03)
        for ($i = 0; $i -lt $noiseCount; $i++) {
            $rx = $rand.Next(0, 900)
            $ry = $rand.Next(0, 200)
            $color = if ($rand.Next(0, 2) -eq 0) { [System.Drawing.Color]::Black } else { [System.Drawing.Color]::White }
            $bmp.SetPixel($rx, $ry, $color)
        }
    }

    $bmp.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Host "Generated $outputPath"
}

$en = @"
Page to Voice Intelligent Audiobook Platform
Automatic text extraction and speech synthesis
"@

$tam = @"
பக்கம் முதல் குரல் வரை அறிவார்ந்த தளம்
எழுத்துக்களை இயற்கையான பேச்சாக மாற்றும் மென்பொருள்
"@

$sin = @"
පිටුවෙන් හඬට බුද්ධිමත් ශ්‍රව්‍ය වේදිකාව
ලිඛිත ලේඛන ස්වාභාවික හඬ බවට පරිවර්තනය කරයි
"@

Render-TextImage -text $en -fontName "Arial" -fontSize 22 -outputPath "$ocrDir/english_sample.png"
Render-TextImage -text $tam -fontName "Nirmala UI" -fontSize 22 -outputPath "$ocrDir/tamil_sample.png"
Render-TextImage -text $sin -fontName "Nirmala UI" -fontSize 22 -outputPath "$ocrDir/sinhala_sample.png"
Render-TextImage -text $en -fontName "Arial" -fontSize 22 -outputPath "$ocrDir/english_noisy.png" -addNoise $true
Render-TextImage -text $en -fontName "Arial" -fontSize 22 -outputPath "$ocrDir/english_skewed.png" -rotateAngle 5.0
"""

render_script = Path(__file__).resolve().parent / "render_images.ps1"
with open(render_script, "w", encoding="utf-8-sig") as f:
    f.write(ps1_content)

print(f"Executing {render_script}...")
res = subprocess.run(
    ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(render_script)],
    capture_output=True,
    text=True,
)
print(res.stdout)
if res.stderr:
    print("Stderr:", res.stderr)

# Clean up temporary ps1 script
if render_script.exists():
    render_script.unlink()

# Also clean up old generate_ocr_fixtures.ps1 if present
old_ps1 = Path(__file__).resolve().parent / "generate_ocr_fixtures.ps1"
if old_ps1.exists():
    old_ps1.unlink()

print("OCR fixtures generation completed.")
