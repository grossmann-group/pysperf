# Main script
from argparse import ArgumentParser, FileType

from pyutilib.misc import Container

from model_library_tools import compute_model_stats, list_model_stats
from paver_utils.convert_to_paver import create_solu_file
from run_manager import setup_new_matrix_run, collect_run_info
from torque_run_manager import execute_run
from solver_library_tools import list_solver_capabilities


# TODO This module will host all of the argument parsing to support different operations on the test suite
# e.g. setting up runs, restarting runs, re-running failed tests, etc.

# list model statistics

def list_models(args):
    print("Computing model statistics... this may take some time.")
    from pysperf.model_library import models
    list_model_stats()
    if args.make_solu_file:
        create_solu_file()


def list_solvers(args):
    list_solver_capabilities()


def run(args):
    print(args)


def analyze(args):
    print(args)


def parse_command_line_arguments():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title="Subcommands")

    list_parser = subparsers.add_parser('list', description='list library elements')
    list_subparsers = list_parser.add_subparsers()
    list_models_parser = list_subparsers.add_parser('models')
    list_models_parser.add_argument('--make-solu-file', action='store_true', help="Make a Paver *.solu file.")
    list_models_parser.set_defaults(call_function=list_models)
    list_solvers_parser = list_subparsers.add_parser('solvers')
    list_solvers_parser.set_defaults(call_function=list_solvers)

    run_parser = subparsers.add_parser('run', description='perform a benchmarking run')
    run_parser.set_defaults(call_function=run)
    new_or_redo = run_parser.add_mutually_exclusive_group(required=True)
    new_or_redo.add_argument('--new', action='store_true', help="Create a new run.")
    new_or_redo.add_argument('--redo', action='store_true', help="Redo an existing run.")
    # Run number
    run_parser.add_argument('-n', help="Specify a run number.", type=int)
    run_parser.add_argument('--time-limit', help="Override the config file time limit (seconds).", type=float)
    # Run engine
    run_parser.add_argument(
        '--run-with', choices=['serial', 'torque', 'setup-only'],
        help="Specify an execution engine.", default='torque')
    # Filtering which models and solvers to execute
    run_parser.add_argument('--models', action='append', nargs='+', help="Run only specified models.")
    run_parser.add_argument('--solvers', action='append', nargs='+', help="Run only specified solvers.")
    run_parser.add_argument('--model-types', action='append', nargs='+', help="Run only specified model types.")
    # Filtering for re-run
    run_parser.add_argument('--redo-existing', action='store_true', help="Rerun job if result file already exists.")
    run_parser.add_argument('--redo-failed', action='store_true', help="Rerun job if previous attempt failed.")

    analyze_parser = subparsers.add_parser('analyze', description="Analyze run results.")
    analyze_parser.set_defaults(call_function=analyze)

    args = parser.parse_args()
    args.call_function(args)


if __name__ == "__main__":
    parse_command_line_arguments()
