from collections import defaultdict
from pathlib import Path

import pandas
from pyutilib.misc import import_file

from pysperf.base_classes import InfeasibleExpected
from pysperf.model_library_registration import register_model

minlplibdir = Path(__file__).parent.joinpath("minlplib/")

# Read in solu file
with minlplibdir.joinpath("MINLP.solu").open() as solufile:
    pd = pandas.read_csv(solufile, sep=r'\s+', header=None)
    pd.columns = ['soln_type', 'model', 'value']

    model_solution_data = defaultdict(dict)
    for row in pd.itertuples(index=False):
        soln_type = row.soln_type
        model = row.model
        value = row.value
        if soln_type == "=opt=":
            model_solution_data[model]['opt_value'] = value
        elif soln_type == "=best=":
            model_solution_data[model]['best_value'] = value
        elif soln_type == "=bestdual=":
            model_solution_data[model]['best_dual'] = value
        elif soln_type == "=inf=":
            model_solution_data[model]['opt_value'] = InfeasibleExpected
        else:
            raise NotImplementedError(f"Unrecognized solu file solution type: '{soln_type}'")
    model_solution_data = dict(model_solution_data)


def _build_from_file_import(model_file_path: Path):
    def model_constructor():
        import sys
        # Some larger MINLPlib models are massive single *.py files.
        # These do not build properly unless recursion depth is increased.
        sys.setrecursionlimit(50000)
        model_module = import_file(str(model_file_path.resolve()))
        return model_module.m
    return model_constructor


for modelfile in minlplibdir.glob("*.py"):
    try:
        model_info = model_solution_data[modelfile.stem]
        register_model(
            name=modelfile.stem,
            build_function=_build_from_file_import(modelfile),
            opt_value=model_info.get('opt_value', None),
            best_value=model_info.get('best_value', None),
            best_dual=model_info.get('best_dual', None),
        )
    except KeyError as err:
        if str(err) == f"'{modelfile.stem}'":
            print(f"Model {modelfile.stem} missing solution information. Omitting from library.")
            continue
        else:
            raise
