"""Example models imported from the Pyomo GDP examples library."""

from os.path import join, normpath

from pyutilib.misc import import_file

from pysperf.model_library_tools import register_model
from pyomo.common.fileutils import PYOMO_ROOT_DIR


pyomo_gdp_examples_path = normpath(join(PYOMO_ROOT_DIR, 'examples', 'gdp'))


def _build_from_gdp_examples(build_name, *path):
    model_module = import_file(join(pyomo_gdp_examples_path, *path))
    return getattr(model_module, build_name)


register_model(
    name="8PP",
    build_function=_build_from_gdp_examples('build_eight_process_flowsheet', 'eight_process', 'eight_proc_model.py'),
    bigM=100, opt_value=68.01)
register_model(
    name="9PP",
    build_function=_build_from_gdp_examples('build_model', 'nine_process', 'small_process.py'),
    bigM=1e8, opt_value=-36.62)
register_model(
    name="9PPnex",
    build_function=_build_from_gdp_examples('build_nonexclusive_model', 'nine_process', 'small_process.py'),
    bigM=1e8, opt_value=-88.22)
register_model(
    name="CLAY",
    build_function=_build_from_gdp_examples(
        'build_constrained_layout_model', 'constrained_layout', 'cons_layout_model.py'),
    bigM=500, opt_value=41573)
register_model(
    name="BS",
    build_function=_build_from_gdp_examples(
        'build_gdp_model', 'small_lit', 'basic_step.py'),
    bigM=100, opt_value=2.99)
register_model(
    name="LeeEx1",
    build_function=_build_from_gdp_examples(
        'build_model', 'small_lit', 'ex1_Lee.py'),
    bigM=100, opt_value=1.17)
register_model(
    name="Ex633",
    build_function=_build_from_gdp_examples(
        'build_simple_nonconvex_gdp', 'small_lit', 'ex_633_trespalacios.py'),
    bigM=100, opt_value=4.46)
register_model(
    name="HENS_ncvx",
    build_function=_build_from_gdp_examples(
        'build_gdp_model', 'small_lit', 'nonconvex_HEN.py'),
    bigM=100000, opt_value=114385)
register_model(
    name="strip8",
    build_function=_build_from_gdp_examples(
        'build_rect_strip_packing_model', 'strip_packing', 'strip_packing_8rect.py'),
    bigM=None, opt_value=11)
register_model(
    name="strip4",
    build_function=_build_from_gdp_examples(
        'build_rect_strip_packing_model', 'strip_packing', 'strip_packing_concrete.py'),
    bigM=None, opt_value=11)
register_model(
    name="rxn2",
    build_function=_build_from_gdp_examples(
        'build_model', 'two_rxn_lee', 'two_rxn_model.py'),
    bigM=100, opt_value=1.01)
register_model(
    name="stickies",
    build_function=_build_from_gdp_examples(
        'build_model', 'stickies.py'),
    bigM=None, opt_value=110.3)
