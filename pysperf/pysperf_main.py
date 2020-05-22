"""
Main script file for pysperf.

This file contains the argument parser to interpret command line arguments to pysperf.
"""
import subprocess
from argparse import ArgumentParser
from pathlib import Path

from .analysis import collect_run_info, export_to_excel
from .config import options, runsdir
from .model_library_tools import list_model_stats
from .paver_utils.convert_to_paver import create_paver_tracefile, create_solu_file
from .run_manager import setup_new_matrix_run, setup_redo_matrix_run
from .solver_library_tools import list_solver_capabilities


def _build_list_subparser(list_parser: ArgumentParser):
    list_subparsers = list_parser.add_subparsers()
    list_models_parser = list_subparsers.add_parser('models')
    list_models_parser.set_defaults(call_function=_list_models)
    list_solvers_parser = list_subparsers.add_parser('solvers')
    list_solvers_parser.set_defaults(call_function=_list_solvers)
    list_runs_parser = list_subparsers.add_parser('runs')
    list_runs_parser.set_defaults(call_function=_list_runs)


def _list_models(args):
    print("Computing model statistics... this may take some time.")
    list_model_stats()


def _list_solvers(args):
    list_solver_capabilities()


def _list_runs(args):
    print("Runs directory contains:")
    runs_list = [str(path) for path in runsdir.glob("run*/") if path.is_dir()]
    for rundir in sorted(runs_list, key=lambda x: (len(x), x)):
        print(rundir)


def _build_run_subparser(run_parser: ArgumentParser):
    run_parser.set_defaults(call_function=_run)
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
    run_parser.add_argument('--models', action='store', nargs='+', help="Run only specified models.")
    run_parser.add_argument('--solvers', action='store', nargs='+', help="Run only specified solvers.")
    run_parser.add_argument('--model-types', action='store', nargs='+', help="Run only specified model types.")
    # Filtering for re-run
    run_parser.add_argument('--redo-existing', action='store_true', help="Rerun job if result file already exists.")
    run_parser.add_argument('--redo-failed', action='store_true', help="Rerun job if previous attempt failed.")


def _run(args):
    print(args)  # For debugging
    if args.time_limit:
        options.time_limit = args.time_limit
    run_number = args.r

    valid_models = args.models if args.models else set()
    valid_solvers = args.solvers if args.solvers else set()
    valid_model_types = args.model_types if args.model_types else set()

    # Perform setup
    if args.new:
        setup_new_matrix_run(
            model_set=valid_models, solver_set=valid_solvers, model_type_set=valid_model_types)
    elif args.redo:
        setup_redo_matrix_run(
            run_number=run_number, redo_existing=args.redo_existing, redo_failed=args.redo_failed,
            model_set=valid_models, solver_set=valid_solvers, model_type_set=valid_model_types)

    # Do the actual run
    if args.run_with == "torque":
        from .torque_run_manager import execute_run
        execute_run()
    elif args.run_with == "serial":
        from .serial_run_manager import execute_run
        execute_run()
    else:
        pass


def _build_analyze_subparser(analyze_parser: ArgumentParser):
    analyze_parser.set_defaults(call_function=_analyze)
    analyze_parser.add_argument('-r', help="Specify a run number.", type=int)


def _analyze(args):
    print(args)  # For debugging
    run_number = args.r
    collect_run_info(run_number)


def _build_export_subparser(export_parser: ArgumentParser):
    export_parser.set_defaults(call_function=_export)
    export_parser.add_argument('--make-solu-file', action='store_true', help="Make a Paver *.solu file.")
    export_parser.add_argument('--make-trace-file', action='store_true', help="Make a Paver *.trc file.")
    export_parser.add_argument('--to-excel', action='store_true', help="Export results to excel.")
    export_parser.add_argument('-r', '--runs', nargs="+", help="Specify one or more run numbers.", type=int)


def _export(args):
    print(args)  # For debugging
    run_numbers = args.runs
    if args.make_solu_file:
        create_solu_file()
    if args.make_trace_file:
        assert len(run_numbers) == 1
        create_paver_tracefile(run_numbers[0])
    if args.to_excel:
        export_to_excel(run_numbers)


def _update_self(args):
    print("WARNING: This is a convenience function. Developer use only.")
    subprocess.run(['git pull'], shell=True, cwd=Path(__file__).parent.resolve())
    subprocess.run(['git branch -vvv'], shell=True, cwd=Path(__file__).parent.resolve())


def parse_command_line_arguments_and_run():
    parser = ArgumentParser(
        description="Pysperf: the Pyomo Solver Performance benchmarking tool. "
                    "Access help for each command using 'pysperf <command> -h'."
    )
    subparsers = parser.add_subparsers(
        title="Pysperf commands")
    list_parser = subparsers.add_parser(
        'list',
        description='List library elements.',
        help="List library models, solvers, and runs.")
    run_parser = subparsers.add_parser(
        'run',
        description='Perform a benchmarking run.',
        help="Setup and execute a benchmarking run.")
    analyze_parser = subparsers.add_parser(
        'analyze',
        description="Analyze run results.",
        help="Analyze results from a benchmarking run.")
    export_parser = subparsers.add_parser(
        'export',
        description='Export data or results from pysperf.',
        help="Export analysis results to Excel or Paver.")
    update_parser = subparsers.add_parser(
        'update',
        description='Update pysperf source. [WARNING: Developer tool only].',
        help="Developer use only.")

    # Build the subparsers
    _build_list_subparser(list_parser)
    _build_run_subparser(run_parser)
    _build_analyze_subparser(analyze_parser)
    _build_export_subparser(export_parser)
    update_parser.set_defaults(call_function=_update_self)

    # Parse the arguments and call the correct function.
    args = parser.parse_args()
    try:
        args.call_function(args)
    except AttributeError as err:
        if "'Namespace' object has no attribute 'call_function'" in str(err):
            parser.print_help()
        else:
            raise


if __name__ == "__main__":
    parse_command_line_arguments_and_run()
