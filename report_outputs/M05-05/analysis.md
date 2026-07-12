# M05-05 — Custom Convolution

## Purpose
Demonstrate custom convolution on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `preset`: `custom`
- `kernel_size`: `3`
- `kernel`: `[[-2.0, -1.0, 0.0], [-1.0, 1.0, 1.0], [0.0, 1.0, 2.0]]`
- `normalize_kernel`: `False`
- `colour_handling`: `per_channel`
- `border`: `reflect`
- `constant_value`: `0`
- `display_mapping`: `normalized`

## Generated Artifacts
- `result.png` — Convolution Result
- `resolved_kernel.csv` — Resolved Kernel
- `flipped_kernel.csv` — Flipped Kernel Used

## Key Metrics
- Raw Response Minimum: -548.000
- Raw Response Maximum: 908.000
- Kernel Sum: 1.000

## Observation
The selected setup produced clear visual output; the leading reported metric is Raw Response Minimum = -548.000.
