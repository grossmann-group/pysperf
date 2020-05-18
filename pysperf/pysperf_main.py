# Main script
from argparse import ArgumentParser

from .analysis import collect_run_info, export_to_excel
from .config import options, runsdir
from .model_library_tools import list_model_stats
from .paver_utils.convert_to_paver import create_paver_tracefile, create_solu_file
from .run_manager import setup_new_matrix_run
from .solver_library_tools import list_solver_capabilities


# TODO This module will host all of the argument parsing to support different operations on the test suite
# e.g. setting up runs, restarting runs, re-running failed tests, etc.

# list model statistics

def list_models(args):
    print("Computing model statistics... this may take some time.")
    list_model_stats()


def list_solvers(args):
    list_solver_capabilities()


def list_runs(args):
    print("Runs directory contains:")
    runs_list = [str(path) for path in runsdir.glob("run*/") if path.is_dir()]
    for rundir in sorted(runs_list, key=lambda x: (len(x), x)):
        print(rundir)


def run(args):
    if args.time_limit:
        options.time_limit = args.time_limit
    if args.new:
        setup_new_matrix_run()
        if args.run_with == "torque":
            from .torque_run_manager import execute_run
            execute_run()
        elif args.run_with == "serial":
            from .serial_run_manager import execute_run
            execute_run()
        else:
            pass
    elif args.redo:
        pass
    print(args)


def analyze(args):
    run_number = args.r
    collect_run_info(run_number)
    print(args)


def export(args):
    run_number = args.r
    if args.make_solu_file:
        create_solu_file()
    if args.make_trace_file:
        create_paver_tracefile(run_number)
    if args.to_excel:
        export_to_excel(run_number)
    print(args)


def parse_command_line_arguments_and_run():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title="Subcommands")

    list_parser = subparsers.add_parser('list', description='List library elements')
    list_subparsers = list_parser.add_subparsers()
    list_models_parser = list_subparsers.add_parser('models')
    list_models_parser.set_defaults(call_function=list_models)
    list_solvers_parser = list_subparsers.add_parser('solvers')
    list_solvers_parser.set_defaults(call_function=list_solvers)
    list_runs_parser = list_subparsers.add_parser('runs')
    list_runs_parser.set_defaults(call_function=list_runs)

    run_parser = subparsers.add_parser('run', description='perform a benchmarking run')
    run_parser.set_defaults(call_function=run)
    new_or_redo = run_parser.add_mutually_exclusive_group(required=True)
    new_or_redo.add_argument('--new', action='store_true', help="Create a new run.")
    new_or_redo.add_argument('--redo', action='store_true', help="Redo an existing run.")
    # Run number
    run_parser.add_argument('-r', help="Specify a run number.", type=int)
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
    analyze_parser.add_argument('-r', help="Specify a run number.", type=int)

    export_parser = subparsers.add_parser('export', description='Export data or results from pysperf')
    export_parser.set_defaults(call_function=export)
    export_parser.add_argument('--make-solu-file', action='store_true', help="Make a Paver *.solu file.")
    export_parser.add_argument('--make-trace-file', action='store_true', help="Make a Paver *.trc file.")
    export_parser.add_argument('--to-excel', action='store_true', help="Export results to excel.")
    export_parser.add_argument('-r', help="Specify a run number.", type=int)

    args = parser.parse_args()
    try:
        args.call_function(args)
    except AttributeError as err:
        if "'Namespace' object has no attribute 'call_function'" in str(err):
            print("For usage directions, run 'pysperf -h'.")
        else:
            raise


if __name__ == "__main__":
    parse_command_line_arguments_and_run()
