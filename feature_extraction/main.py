import os
import argparse
from feature_extraction import sharpness
from precision_mapping.main import check_dependencies

def parse_arguments():
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description='Run precision functional mapping.')

    # Input BOLD time-series.
    parser.add_argument('--func', required=True, help='Path to GIFTI (.func.gii) BOLD time-series file. TRs stored as individual darrays.')

    # Input mid-thickness surface file.
    parser.add_argument('--surf', required=True, help='Path to GIFTI (.surf.gii) mid-thickness surface file.')

    # Output directory to store results
    parser.add_argument('--output', required=True, help='Directory to store output results.')


    return parser.parse_args()


def prepare_parameters(args):
    """Prepare and return the parameter dictionary."""

    params = {
        'func': args.func,
        'surf': args.surf,
        'output': args.output,
        'tmp': f'{args.output}/tmp',  # define temporary directory in 'output'.
        'hemi': args.func.split('.func.gii')[0][-1]  # Extract hemisphere from file name.
    }

    params['networks'] = f"{args.output}/networks.{params['hemi']}.label.gii"

    if not os.path.exists(params['networks']):
        raise RuntimeError(f"networks.{params['hemi']}.label.gii not found. Please run precision_mapping first.")

    return params


def main():
    check_dependencies()
    args = parse_arguments()
    params = prepare_parameters(args)
    sharpness.get_boundary_sharpness(params)


if __name__ == '__main__':
    main()