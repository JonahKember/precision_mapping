import os
import shutil
import argparse

from hipp_mapping import mapping


def main():

    if shutil.which('wb_command') is None:
        raise RuntimeError('wb_command not found. Please install Connectome Workbench and add to your path.')

    parser = argparse.ArgumentParser(description='Run precision functional mapping.')

    parser.add_argument('--surface_dtseries', required=True, help='Path to GIFTI (.func.gii) BOLD signal. TRs stored as individual darrays.')
    parser.add_argument('--volume_dtseries', required=True, help='Path to NIFTI (.nii.gz) 4D BOLD signal.')
    parser.add_argument('--hipp_midthickness', required=True, help='Path to GIFTI (.surf.gii) hippocampus mid-thickness surface file.')
    parser.add_argument('--output', required=True, help='Directory to store output results.')

    parser.add_argument('--dilation_threshold', type=int, default=25, help='Dilation threshold in mm^2 (default: 25).')
    parser.add_argument('--kernel_fwhm', type=int, default=2, help='FWHM of smoothing kernel for BOLD signal, in mm (default: 2).')

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(f'{args.output}/tmp', exist_ok=True)

    mapping.run(args)


if __name__ == '__main__':
    main()