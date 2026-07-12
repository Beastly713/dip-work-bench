# M10-02 — Laplacian of Gaussian Edge Detection

## Purpose
Demonstrate laplacian of gaussian edge detection on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `gaussian_kernel`: `5`
- `sigma`: `1.0`
- `neighbourhood`: `eight`
- `zero_crossing_contrast`: `10.0`

## Generated Artifacts
- `result.png` — LoG Edge Map
- `smoothed_input.png` — Smoothed Input
- `signed_response.png` — Signed Response

## Key Metrics
- Response Minimum: -186.289
- Response Maximum: 151.168
- Maximum Absolute Response: 186.289
- Edge Pixels: 110337
- Edge Percentage: 42.090

## Observation
The selected setup produced clear visual output; the leading reported metric is Response Minimum = -186.289.
