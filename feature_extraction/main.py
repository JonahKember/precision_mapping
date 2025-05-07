import os
import argparse

from precision_mapping.main import check_dependencies
from feature_extraction import clusters, connectivity, utils, surface_area, sharpness

def parse_arguments():
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description='Run precision functional mapping.')
    parser.add_argument('--func', required=True, help='Path to GIFTI (.func.gii) BOLD time-series file. TRs stored as individual darrays.')
    parser.add_argument('--surf', required=True, help='Path to GIFTI (.surf.gii) mid-thickness surface file.')
    parser.add_argument('--output', required=True, help='Directory to store output results.')

    return parser.parse_args()


def prepare_parameters(args):
    """Prepare and return the parameter dictionary."""

    params = {
        'func': args.func,
        'surf': args.surf,
        'output': args.output,
        'tmp': f'{args.output}/tmp',
        'hemi': args.func.split('.func.gii')[0][-1]
    }

    params['networks'] = f"{args.output}/networks.{params['hemi']}.label.gii"

    if not os.path.exists(params['networks']):
        raise RuntimeError(f"networks.{params['hemi']}.label.gii not found. Please run precision_mapping first.")

    return params


def main():

    # Set-up.
    check_dependencies()
    args = parse_arguments()
    params = prepare_parameters(args)

    # Prepare clusters and dataframe to hold results.
    clusters.get_clusters(params)
    utils.initialize_dataframe(params)

    # Extract features.
    surface_area.get_surface_area(params)
    connectivity.get_network_connectivity(params)
    sharpness.get_boundary_sharpness(params)

if __name__ == '__main__':
    main()