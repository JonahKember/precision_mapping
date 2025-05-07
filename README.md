# precision-mapping

Python package for precision functional mapping of the cortex.

- Assigns vertices to networks based on the spatial similarity of their neocortical connectivity profile to a set of template networks (default: [Yeo-17 network parcellation](https://journals.physiology.org/doi/full/10.1152/jn.00338.2011)).
- Cleans solutions using spatial dilation (default: 25mm<sup>2</sup>).

Useful in:
- Enhancing the SNR of network-specific BOLD activity.
- Extracting features related to spatial topography.
- Reducing the dimensionality of cortex-wide BOLD signals.


## Installation
```bash
pip install precision-mapping
```

## Useage
```bash
precision_mapping [-h] --func --surf --output [--dilation_threshold]

options:
  -h, --help            show help message and exit
  --func FUNC           Path to GIFTI (.func.gii) BOLD time-series file. TRs stored as individual darrays.
  --surf SURF           Path to GIFTI (.surf.gii) mid-thickness surface file.
  --output OUTPUT       Directory to store output results.
  --dilation_threshold DILATION_THRESHOLD
```
*requires [Connectome Workbench](https://www.humanconnectome.org/software/get-connectome-workbench) to be installed.

## Outputs

### precision_mapping
![networks](/precision_mapping/data/figures/networks.png)
![network_similarities](/precision_mapping/data/figures/network_similarities.png)
![clusters](/precision_mapping/data/figures/clusters.png)
![borders](/precision_mapping/data/figures/borders.png)

### feature_extraction
![features](/precision_mapping/data/figures/features.png)