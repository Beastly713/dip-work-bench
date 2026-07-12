# M06-04 — Laplacian Sharpening

## Purpose
Demonstrate laplacian sharpening on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `neighbourhood`: `four`
- `strength`: `1.0`
- `colour_handling`: `preserve_luminance_colour`

## Generated Artifacts
- `result.png` — Sharpened Image
- `laplacian_response.png` — Laplacian Display
- `laplacian_kernel.csv` — Laplacian Kernel

## Key Metrics
- Laplacian Minimum: -239.000
- Laplacian Maximum: 181.000
- Input Standard Deviation: 47.855
- Output Standard Deviation: 54.653

## Observation
The selected setup produced clear visual output; the leading reported metric is Laplacian Minimum = -239.000.
