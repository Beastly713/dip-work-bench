# M09-05 — Adaptive Thresholding

## Purpose
Demonstrate adaptive thresholding on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `block_size`: `11`
- `offset`: `2`
- `polarity`: `bright_foreground`
- `include_global_otsu_comparison`: `True`

## Generated Artifacts
- `adaptive_mask.png` — Adaptive Threshold Mask
- `global_otsu_comparison.png` — Global Otsu Comparison

## Key Metrics
- White Pixels: 165291
- Black Pixels: 96853
- White Percentage: 63.054
- Black Percentage: 36.946
- Global Otsu Threshold: 117.000

## Observation
The selected setup produced clear visual output; the leading reported metric is White Pixels = 165291.
