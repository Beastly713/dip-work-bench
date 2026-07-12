# DIP Workbench Lena Experiment Report

## Input Image Summary
- File: `lena.png`
- Size: `512 x 512`
- Colour model: `RGB`
- Data type: `uint8`

## Methodology
Each academic operation was executed through the registered DIP Workbench executor path using a single curated parameter setup, with only the manifest-approved compact variants.

## M01-01 — Colour to Grayscale

Purpose: Convert a colour image to grayscale.

Parameters: `method=luminance`

Observation: The selected setup produced 1 concise artifact(s) suitable for visual comparison.

Files: [result.png](M01-01/result.png)

## M01-02 — Black-and-White Thresholding

Purpose: Convert an image to a binary mask.

Parameters: `manual={'mode': 'manual', 'threshold': 128, 'polarity': 'bright_foreground'}`, `otsu={'mode': 'otsu', 'threshold': 128, 'polarity': 'bright_foreground'}`

Observation: The selected setup produced clear visual output; the leading reported metric is Threshold Used = 117.000.

Files: [result_manual.png](M01-02/result_manual.png), [result_otsu.png](M01-02/result_otsu.png), [comparison.png](M01-02/comparison.png)

## M01-03 — Colour-Channel Extraction

Purpose: Extract red, green and blue channels from an RGB image.

Parameters: `channel=all`, `display=intensity`

Observation: The selected setup produced 4 concise artifact(s) suitable for visual comparison.

Files: [red_channel.png](M01-03/red_channel.png), [green_channel.png](M01-03/green_channel.png), [blue_channel.png](M01-03/blue_channel.png), [triptych.png](M01-03/triptych.png)

## M02-02 — Brightness and Contrast

Purpose: Apply linear brightness and contrast adjustment.

Parameters: `brightness=25`, `contrast=1.15`

Observation: The selected setup produced 1 concise artifact(s) suitable for visual comparison.

Files: [result.png](M02-02/result.png)

## M03-01 — Image Negative

Purpose: Create the photographic negative of the selected image.

Parameters: `colour_handling=luminance`

Observation: The selected setup produced 1 concise artifact(s) suitable for visual comparison.

Files: [result.png](M03-01/result.png)

## M03-03 — Gamma Correction

Purpose: Apply power-law gamma correction.

Parameters: `gamma_0_6={'gamma': 0.6}`, `gamma_1_8={'gamma': 1.8}`

Observation: The selected setup produced 7 concise artifact(s) suitable for visual comparison.

Files: [result_gamma_0_6.png](M03-03/result_gamma_0_6.png), [gamma_curve_0_6.png](M03-03/gamma_curve_0_6.png), [gamma_curve_0_6.csv](M03-03/gamma_curve_0_6.csv), [result_gamma_1_8.png](M03-03/result_gamma_1_8.png), [gamma_curve_1_8.png](M03-03/gamma_curve_1_8.png), [gamma_curve_1_8.csv](M03-03/gamma_curve_1_8.csv), [comparison.png](M03-03/comparison.png)

## M04-01 — Histogram Viewer and Analysis

Purpose: Inspect intensity histograms and image statistics.

Parameters: `mode=ordinary`, `bins=256`

Observation: The selected setup produced clear visual output; the leading reported metric is Mean = 124.049.

Files: [rgb_histogram.png](M04-01/rgb_histogram.png), [rgb_histogram.csv](M04-01/rgb_histogram.csv), [grayscale_histogram.png](M04-01/grayscale_histogram.png), [grayscale_histogram.csv](M04-01/grayscale_histogram.csv)

## M04-02 — Histogram Equalization

Purpose: Equalize image luminance contrast.

Parameters: 

Observation: The selected setup produced clear visual output; the leading reported metric is Input Mean = 124.049.

Files: [result.png](M04-02/result.png), [histogram_comparison.png](M04-02/histogram_comparison.png), [histogram_comparison.csv](M04-02/histogram_comparison.csv), [input_cdf.png](M04-02/input_cdf.png), [input_cdf.csv](M04-02/input_cdf.csv), [equalization_mapping.png](M04-02/equalization_mapping.png), [equalization_mapping.csv](M04-02/equalization_mapping.csv)

## M05-01 — Blur and Neighbourhood Filters

Purpose: Apply smoothing and neighbourhood filters.

Parameters: `filter_method=gaussian`, `kernel_size=5`, `gaussian_sigma=1.0`, `border=reflect`, `constant_value=0`

Observation: The selected setup produced 1 concise artifact(s) suitable for visual comparison.

Files: [result.png](M05-01/result.png)

## M05-05 — Custom Convolution

Purpose: Apply a custom convolution kernel.

Parameters: `preset=custom`, `kernel_size=3`, `kernel=[[-2.0, -1.0, 0.0], [-1.0, 1.0, 1.0], [0.0, 1.0, 2.0]]`, `normalize_kernel=False`, `colour_handling=per_channel`, `border=reflect`, `constant_value=0`, `display_mapping=normalized`

Observation: The selected setup produced clear visual output; the leading reported metric is Raw Response Minimum = -548.000.

Files: [result.png](M05-05/result.png), [resolved_kernel.csv](M05-05/resolved_kernel.csv), [flipped_kernel.csv](M05-05/flipped_kernel.csv)

## M06-01 — First-Order Gradient

Purpose: Calculate first derivative gradient responses.

Parameters: `method=prewitt`

Observation: The selected setup produced clear visual output; the leading reported metric is Gx Minimum = -517.000.

Files: [gradient_x.png](M06-01/gradient_x.png), [gradient_y.png](M06-01/gradient_y.png), [gradient_magnitude.png](M06-01/gradient_magnitude.png), [triptych.png](M06-01/triptych.png)

## M06-02 — Sobel Edge Enhancement

Purpose: Calculate Sobel gradient magnitude and optional threshold.

Parameters: `kernel_size=3`, `scale=1.0`, `threshold_enabled=False`, `threshold=100`

Observation: The selected setup produced clear visual output; the leading reported metric is Gx Minimum = -688.000.

Files: [sobel_x.png](M06-02/sobel_x.png), [sobel_y.png](M06-02/sobel_y.png), [sobel_magnitude.png](M06-02/sobel_magnitude.png), [triptych.png](M06-02/triptych.png)

## M06-03 — Laplacian Response

Purpose: Calculate second-order Laplacian response.

Parameters: `neighbourhood=eight`, `display=signed_heatmap`, `scale=1.0`

Observation: The selected setup produced clear visual output; the leading reported metric is Signed Minimum = -601.000.

Files: [result.png](M06-03/result.png), [laplacian_kernel.csv](M06-03/laplacian_kernel.csv)

## M06-04 — Laplacian Sharpening

Purpose: Sharpen an image by subtracting a negative-centre Laplacian response.

Parameters: `neighbourhood=four`, `strength=1.0`, `colour_handling=preserve_luminance_colour`

Observation: The selected setup produced clear visual output; the leading reported metric is Laplacian Minimum = -239.000.

Files: [result.png](M06-04/result.png), [laplacian_response.png](M06-04/laplacian_response.png), [laplacian_kernel.csv](M06-04/laplacian_kernel.csv)

## M06-05 — Unsharp Masking

Purpose: Sharpen an image by adding a scaled high-frequency detail mask.

Parameters: `kernel_size=5`, `sigma=1.0`, `amount=0.7`

Observation: The selected setup produced clear visual output; the leading reported metric is Detail Minimum = -52.704.

Files: [result.png](M06-05/result.png), [blurred_image.png](M06-05/blurred_image.png), [detail_mask.png](M06-05/detail_mask.png)

## M06-06 — High-Boost Filtering

Purpose: Sharpen an image by adding a boosted high-frequency detail mask.

Parameters: `kernel_size=5`, `sigma=1.0`, `boost=1.8`

Observation: The selected setup produced clear visual output; the leading reported metric is Detail Minimum = -52.704.

Files: [result.png](M06-06/result.png), [blurred_image.png](M06-06/blurred_image.png), [detail_mask.png](M06-06/detail_mask.png)

## M07-01 — Fourier Magnitude Spectrum

Purpose: Display Fourier magnitude and optional phase spectra.

Parameters: `center_spectrum=True`, `logarithmic_scale=True`, `show_phase=False`

Observation: The selected setup produced clear visual output; the leading reported metric is Minimum Magnitude = 1.806.

Files: [magnitude_spectrum.png](M07-01/magnitude_spectrum.png)

## M07-03 — Frequency-Domain Low-Pass Filter

Purpose: Apply an ideal circular low-pass filter in the Fourier domain.

Parameters: `cutoff_percent=15.0`

Observation: The selected setup produced clear visual output; the leading reported metric is Cutoff Radius = 54.306.

Files: [result.png](M07-03/result.png), [input_spectrum.png](M07-03/input_spectrum.png), [frequency_mask.png](M07-03/frequency_mask.png), [filtered_spectrum.png](M07-03/filtered_spectrum.png)

## M07-04 — Frequency-Domain High-Pass Filter

Purpose: Apply an ideal circular high-pass filter in the Fourier domain.

Parameters: `cutoff_percent=10.0`

Observation: The selected setup produced clear visual output; the leading reported metric is Cutoff Radius = 36.204.

Files: [result.png](M07-04/result.png), [input_spectrum.png](M07-04/input_spectrum.png), [frequency_mask.png](M07-04/frequency_mask.png), [filtered_spectrum.png](M07-04/filtered_spectrum.png)

## M08-01 — Add Noise

Purpose: Add reproducible synthetic noise.

Parameters: `gaussian={'noise_type': 'gaussian', 'processing': 'luminance', 'seed': 42, 'gaussian_mean': 0.0, 'gaussian_std': 20.0, 'salt_probability': 0.05, 'pepper_probability': 0.05, 'speckle_std': 0.1}`, `salt_and_pepper={'noise_type': 'salt_and_pepper', 'processing': 'luminance', 'seed': 42, 'gaussian_mean': 0.0, 'gaussian_std': 20.0, 'salt_probability': 0.03, 'pepper_probability': 0.03, 'speckle_std': 0.1}`, `speckle={'noise_type': 'speckle', 'processing': 'luminance', 'seed': 42, 'gaussian_mean': 0.0, 'gaussian_std': 20.0, 'salt_probability': 0.05, 'pepper_probability': 0.05, 'speckle_std': 0.1}`

Observation: The selected setup produced clear visual output; the leading reported metric is Seed = 42.

Files: [result_gaussian.png](M08-01/result_gaussian.png), [noise_distribution_gaussian.png](M08-01/noise_distribution_gaussian.png), [noise_distribution_gaussian.csv](M08-01/noise_distribution_gaussian.csv), [result_salt_and_pepper.png](M08-01/result_salt_and_pepper.png), [result_speckle.png](M08-01/result_speckle.png), [comparison.png](M08-01/comparison.png)

## M09-02 — Intensity-Range Thresholding

Purpose: Segment pixels whose grayscale intensity falls inside a selected range.

Parameters: `intensity_range=[80, 180]`, `include_boundaries=True`

Observation: The selected setup produced clear visual output; the leading reported metric is Selected Pixels = 173762.

Files: [mask.png](M09-02/mask.png), [overlay.png](M09-02/overlay.png)

## M09-03 — Colour-Range Segmentation

Purpose: Segment RGB pixels inside inclusive channel ranges.

Parameters: `red_range=[150, 255]`, `green_range=[70, 210]`, `blue_range=[50, 190]`

Observation: The selected setup produced clear visual output; the leading reported metric is Selected Pixels = 168119.

Files: [mask.png](M09-03/mask.png), [extracted_region.png](M09-03/extracted_region.png), [overlay.png](M09-03/overlay.png)

## M09-05 — Adaptive Thresholding

Purpose: Segment local bright or dark foreground with mean adaptive thresholding.

Parameters: `block_size=11`, `offset=2`, `polarity=bright_foreground`, `include_global_otsu_comparison=True`

Observation: The selected setup produced clear visual output; the leading reported metric is White Pixels = 165291.

Files: [adaptive_mask.png](M09-05/adaptive_mask.png), [global_otsu_comparison.png](M09-05/global_otsu_comparison.png)

## M10-01 — Canny Edge Detection

Purpose: Detect edges using Gaussian smoothing and Canny hysteresis.

Parameters: `blur_kernel=5`, `sigma=1.0`, `low_threshold=50`, `high_threshold=150`, `aperture_size=3`, `l2_gradient=True`

Observation: The selected setup produced clear visual output; the leading reported metric is Edge Pixels = 12228.

Files: [result.png](M10-01/result.png), [smoothed_input.png](M10-01/smoothed_input.png)

## M10-02 — Laplacian of Gaussian Edge Detection

Purpose: Detect zero-crossing edges in a Laplacian of Gaussian response.

Parameters: `gaussian_kernel=5`, `sigma=1.0`, `neighbourhood=eight`, `zero_crossing_contrast=10.0`

Observation: The selected setup produced clear visual output; the leading reported metric is Response Minimum = -186.289.

Files: [result.png](M10-02/result.png), [smoothed_input.png](M10-02/smoothed_input.png), [signed_response.png](M10-02/signed_response.png)

## M10-03 — Difference of Gaussian Edge Detection

Purpose: Detect edges from a signed difference of Gaussian response.

Parameters: `sigma_small=1.0`, `sigma_large=2.0`, `edge_threshold=5.0`

Observation: The selected setup produced clear visual output; the leading reported metric is Response Minimum = -40.318.

Files: [result.png](M10-03/result.png), [small_sigma_blur.png](M10-03/small_sigma_blur.png), [large_sigma_blur.png](M10-03/large_sigma_blur.png), [signed_response.png](M10-03/signed_response.png)

## M10-04 — Hough Line Detection

Purpose: Detect line segments using a probabilistic Hough transform.

Parameters: `canny_low=50`, `canny_high=150`, `rho_resolution=1.0`, `theta_resolution_degrees=1.0`, `vote_threshold=50`, `minimum_line_length=30`, `maximum_line_gap=10`, `maximum_lines=30`

Observation: The selected setup produced clear visual output; the leading reported metric is Detected Lines = 30.

Files: [overlay.png](M10-04/overlay.png), [line_edge_map.png](M10-04/line_edge_map.png), [line_detections.csv](M10-04/line_detections.csv)

## M10-05 — Hough Circle Detection

Purpose: Detect circles using the Hough gradient transform.

Parameters: `median_kernel=5`, `dp=1.2`, `minimum_distance=20`, `canny_high_threshold=100.0`, `accumulator_threshold=30.0`, `minimum_radius=5`, `maximum_radius=80`, `maximum_circles=10`

Observation: The selected setup produced clear visual output; the leading reported metric is Detected Circles = 10.

Files: [overlay.png](M10-05/overlay.png), [circle_preprocessed.png](M10-05/circle_preprocessed.png), [circle_detections.csv](M10-05/circle_detections.csv)

## M10-06 — Harris Corner Detection

Purpose: Detect corner points using a Harris response map.

Parameters: `block_size=2`, `aperture_size=3`, `harris_k=0.04`, `quality_level=0.01`, `minimum_distance=10`, `maximum_corners=100`, `subpixel_refinement=False`

Observation: The selected setup produced clear visual output; the leading reported metric is Detected Corners = 100.

Files: [overlay.png](M10-06/overlay.png), [harris_response.png](M10-06/harris_response.png), [corner_detections.csv](M10-06/corner_detections.csv)
