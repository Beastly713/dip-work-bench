# M08-01 — Add Noise

## Purpose
Demonstrate add noise on the standard Lena input.

## Input
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`

## Parameters Used
- `gaussian`: `{'noise_type': 'gaussian', 'processing': 'luminance', 'seed': 42, 'gaussian_mean': 0.0, 'gaussian_std': 20.0, 'salt_probability': 0.05, 'pepper_probability': 0.05, 'speckle_std': 0.1}`
- `salt_and_pepper`: `{'noise_type': 'salt_and_pepper', 'processing': 'luminance', 'seed': 42, 'gaussian_mean': 0.0, 'gaussian_std': 20.0, 'salt_probability': 0.03, 'pepper_probability': 0.03, 'speckle_std': 0.1}`
- `speckle`: `{'noise_type': 'speckle', 'processing': 'luminance', 'seed': 42, 'gaussian_mean': 0.0, 'gaussian_std': 20.0, 'salt_probability': 0.05, 'pepper_probability': 0.05, 'speckle_std': 0.1}`

## Generated Artifacts
- `result_gaussian.png` — Noisy Image
- `noise_distribution_gaussian.png` — Applied Noise Distribution
- `noise_distribution_gaussian.csv` — Applied Noise Distribution
- `result_salt_and_pepper.png` — Noisy Image
- `result_speckle.png` — Noisy Image
- `comparison.png` — Variant comparison plate

## Key Metrics
- Seed: 42
- Mean Applied Delta: -0.014
- Standard Deviation of Applied Delta: 13.295
- Changed Pixels Percentage: 95.988

## Observation
The selected setup produced clear visual output; the leading reported metric is Seed = 42.
