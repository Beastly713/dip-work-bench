# M07-03 — Frequency-Domain Low-Pass Filter

## Purpose
Demonstrate frequency-domain low-pass filter on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `cutoff_percent`: `15.0`

## Generated Artifacts
- `result.png` — Low-Pass Filtered Image
- `input_spectrum.png` — Input Magnitude Spectrum
- `frequency_mask.png` — Low-Pass Frequency Mask
- `filtered_spectrum.png` — Filtered Magnitude Spectrum

## Key Metrics
- Cutoff Radius: 54.306
- Retained Frequency Bins: 9265
- Retained Frequency Percentage: 3.534
- Raw Reconstruction Minimum: 3.321
- Raw Reconstruction Maximum: 246.902

## Observation
The selected setup produced clear visual output; the leading reported metric is Cutoff Radius = 54.306.
