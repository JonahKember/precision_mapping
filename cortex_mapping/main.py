import os
import shutil
import argparse
import feature_extraction
import cortex_mapping
import feature_extraction


def main():

    if shutil.which('wb_command') is None:
        raise RuntimeError('wb_command not found. Please install Connectome Workbench and add to your path.')

    parser = argparse.ArgumentParser(description='Run precision functional mapping.')
    parser.add_argument('--func', required=True, help='Path to GIFTI (.func.gii) BOLD time-series file. TRs stored as individual darrays.')
    parser.add_argument('--surf', required=True, help='Path to GIFTI (.surf.gii) mid-thickness surface file.')
    parser.add_argument('--output', required=True, help='Directory to store output results.')
    parser.add_argument('--dilation_threshold', type=int, default=25, help='Dilation threshold in mm^2 (default: 25).')

    args = parser.parse_args()
    args.hemi = args.func.split('.func.gii')[0][-1]
    args.networks = f'{args.output}/networks.{args.hemi}.label.gii'

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(f'{args.output}/tmp', exist_ok=True)

    cortex_mapping.mapping.run_mapping(args)
    feature_extraction.extract_features(args)


if __name__ == '__main__':
    main()
