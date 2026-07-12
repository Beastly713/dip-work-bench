# M01-02 — Black-and-White Thresholding

## Purpose
Demonstrate black-and-white thresholding on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `manual`: `{'mode': 'manual', 'threshold': 128, 'polarity': 'bright_foreground'}`
- `otsu`: `{'mode': 'otsu', 'threshold': 128, 'polarity': 'bright_foreground'}`

## Generated Artifacts
- `result_manual.png` — Binary Image
- `result_otsu.png` — Binary Image
- `comparison.png` — Manual/Otsu comparison plate

## Key Metrics
- Threshold Used: 117.000
- White Pixels: 152991
- Black Pixels: 109153
- White Percentage: 58.361
- Black Percentage: 41.639

## Observation
The selected setup produced clear visual output; the leading reported metric is Threshold Used = 117.000.
