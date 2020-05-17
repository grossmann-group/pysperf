from pathlib import Path

import pandas
from pyutilib.misc import import_file

from pysperf.model_library_tools import register_model

minlplibdir = Path(__file__).parent.joinpath("minlplib/")

# Read in solu file
with minlplibdir.joinpath("MINLP.solu").open() as solufile:
    pd = pandas.read_csv(solufile, sep=r'\s+', header=None)
    pd.columns = ['soln_type', 'model', 'value']
    pd = pd.set_index('model')

    model_solution_data = {}
    for model, data in pd.to_dict('index').items():
        if data['soln_type'] == "=opt=":
            model_solution_data[model] = {'opt_value': data['value']}
        else:
            model_solution_data[model] = {'best_value': data['value']}


def _build_from_file_import(model_file_path: Path):
    def model_constructor():
        model_module = import_file(str(model_file_path.resolve()))
        return model_module.m
    return model_constructor


for modelfile in minlplibdir.glob("*.py"):
    register_model(
        name=modelfile.stem,
        build_function=_build_from_file_import(modelfile),
        opt_value=model_solution_data[modelfile.stem].get('opt_value', None),
        best_value=model_solution_data[modelfile.stem].get('best_value', None)
    )
