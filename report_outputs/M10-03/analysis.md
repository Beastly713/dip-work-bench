# M10-03 — Difference of Gaussian Edge Detection

## Purpose
Demonstrate difference of gaussian edge detection on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `sigma_small`: `1.0`
- `sigma_large`: `2.0`
- `edge_threshold`: `5.0`

## Generated Artifacts
- `result.png` — DoG Edge Map
- `small_sigma_blur.png` — Small-Sigma Blur
- `large_sigma_blur.png` — Large-Sigma Blur
- `signed_response.png` — Signed Response

## Key Metrics
- Response Minimum: -40.318
- Response Maximum: 48.604
- Maximum Absolute Response: 48.604
- Edge Pixels: 43891
- Edge Percentage: 16.743

## Observation
The selected setup produced clear visual output; the leading reported metric is Response Minimum = -40.318.
