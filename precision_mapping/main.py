import os
import shutil
import argparse
from precision_mapping import mapping


def check_dependencies():
    """Check if external dependencies are installed."""

    if shutil.which('wb_command') is None:
        raise RuntimeError('wb_command not found. Please install Connectome Workbench and add to your path.')


def parse_arguments():
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description='Run precision functional mapping.')
    parser.add_argument('--func', required=True, help='GIFTI (.func.gii) BOLD time-series, TRs stored as individual darrays.')
    parser.add_argument('--midthickness', required=True, help='GIFTI (.surf.gii), mid-thickness surface file.')
    parser.add_argument('--output', required=True, help='Output directory')

    return parser.parse_args()


def prepare_parameters(args):
    """Prepare and return the parameter dictionary."""

    params = {
        'func': args.func,
        'midthickness': args.midthickness,
        'output': args.output,
        'dilation_threshold': 40,  # units = mm^2, can be modified for more/less dilation.
        'tmp': os.path.join(args.output, 'tmp'), # define temporary directory in 'output'.
        'hemi': args.func.split('.func.gii')[0][-1]  # Extract hemisphere from file name.
    }

    return params


def ensure_directories_exist(params):
    """Ensure the output and temporary directories exist."""

    os.makedirs(params['output'], exist_ok=True)
    os.makedirs(params['tmp'], exist_ok=True)


def main():

    # Check for wb_command install.
    check_dependencies()

    # Prepare parameter dictionary.
    args = parse_arguments()
    params = prepare_parameters(args)

    # Create output and tmp dir if non-existant.
    ensure_directories_exist(params)

    # Run precision-mapping pipeline.
    mapping.run(params)

if __name__ == '__main__':
    main()
