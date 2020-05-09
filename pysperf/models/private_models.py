"""
Models in my personal library that I do not yet have permission to release,
or have simply not been released yet.
"""
from functools import partial

import qmodels

from pysperf.model_library_tools import register_model, register_model_builder
from pysperf.config import models

# from qmodels.pyomo_convert.batch_processing import build_model

register_model(
    name="batchp",
    build_function=qmodels.pyomo_convert.batch_processing.build_model,
    bigM=1000, opt_value=679365)
register_model(
    name="disease",
    build_function=qmodels.pyomo_convert.disease_model.build_model,
    bigM=1000, opt_value=304.4)
register_model(
    name="jobshop",
    build_function=qmodels.pyomo_convert.jobshop.build_small_concrete,
    bigM=None, opt_value=11)
register_model(
    name="purchasing",
    build_function=qmodels.pyomo_convert.med_term_purchasing.build_concrete,
    bigM=None, opt_value=6797.5)


# heat exchanger network synthesis models
@register_model_builder(opt_value=106767)
def HENS_conv():
    return qmodels.hens.conventional.build_conventional(True, 4)[0]
@register_model_builder(soln_value=134522)
def HENS_int_sing():
    return qmodels.hens.modular_integer.build_single_module(True, 4)[0]
@register_model_builder(soln_value=112270)
def HENS_int_mult():
    return qmodels.hens.modular_integer.build_require_modular(True, 4)[0]
@register_model_builder(soln_value=101505)
def HENS_int_opt():
    return qmodels.hens.modular_integer.build_modular_option(True, 4)[0]
@register_model_builder(soln_value=134522)
def HENS_disc_sing():
    return qmodels.hens.modular_discrete_single_module.build_single_module(True, 4)[0]
@register_model_builder(soln_value=111520)
def HENS_disc_mult():
    return qmodels.hens.modular_discrete.build_require_modular(True, 4)[0]
@register_model_builder(soln_value=101505)
def HENS_disc_opt():
    return qmodels.hens.modular_discrete.build_modular_option(True, 4)[0]


# Kaibel column
@register_model_builder(bigM=1e6, soln_value=115637)
def Kaibel():
    from qmodels.kaibel.kaibel_solve_gdp import build_model
    m = build_model()

    m.F[1].fix(50)
    m.F[2].fix(50)
    m.F[3].fix(50)
    m.F[4].fix(50)
    m.q.fix(m.q_init)
    m.dv[2].fix(0.394299)

    for sec in m.section:
        for n_tray in m.tray:
            m.P[sec, n_tray].fix(m.Preb)

    # Initial values for the tray existence or absence
    for n_tray in m.candidate_trays_main:
        for sec in m.section_main:
            m.tray_exists[sec, n_tray].indicator_var.set_value(1)
            m.tray_absent[sec, n_tray].indicator_var.set_value(0)
    for n_tray in m.candidate_trays_feed:
        m.tray_exists[2, n_tray].indicator_var.set_value(1)
        m.tray_absent[2, n_tray].indicator_var.set_value(0)
    for n_tray in m.candidate_trays_product:
        m.tray_exists[3, n_tray].indicator_var.set_value(1)
        m.tray_absent[3, n_tray].indicator_var.set_value(0)

    return m


# Membrane model
@register_model_builder()
def Memb():
    from qmodels.membrane.cascade_v3_STELLA import build_model, adding_integerConstr
    m = build_model()

    adding_integerConstr(m)  # GDP model
    for i in m.i:
        m.FB[i, 'S5'].fix(0)  # bypass of last stage is 0
        m.CPJ[i, 'S5'].fix(0)  # compressed air feeding S5 is 0
    from pyomo.environ import Constraint
    m.nf_lb = Constraint(expr=m.nf['S1'] >= 0.001)  # S1 is selected
    return m


# Modular network design - capacity expansion
@register_model_builder(bigM=7000, opt_value=3593)
def Mod_grow():
    from qmodels.modular_econ.model import build_model
    return build_model(case="Growth")
@register_model_builder(bigM=7000, opt_value=2096)
def Mod_dip():
    from qmodels.modular_econ.model import build_model
    return build_model(case="Dip")
@register_model_builder(bigM=7000, opt_value=851)
def Mod_decay():
    from qmodels.modular_econ.model import build_model
    return build_model(case="Decay")


# Modular network design - distributed facility location
@register_model_builder(bigM=10000, soln_value=36262)
def Mod_dist():
    from qmodels.modular_econ.distributed import build_modular_model
    return build_modular_model()
@register_model_builder(bigM=10000, soln_value=19568)
def Mod_qtr():
    from qmodels.modular_econ.quarter_distributed import build_modular_model
    return build_modular_model()


# Biofuel network
register_model(
    name="Biofuel",
    build_function=qmodels.modular_facility.model.build_model,
    bigM=7800,
    opt_value=4067
)


# Stranded gas models
def build_stranded_gas_function(valid_modules):
    def model_builder():
        from qmodels.stranded_gas.model import build_model as build_stranded_gas_model
        m = build_stranded_gas_model()

        for mtype in m.module_types - valid_modules:
            m.gas_consumption[:, mtype, :].fix(0)
            m.num_modules[mtype, :, :].fix(0)
            m.modules_transferred[mtype, :, :, :].fix(0)
            m.modules_purchased[mtype, :, :].fix(0)
            m.mtype_exists[mtype].deactivate()
            m.mtype_absent[mtype].indicator_var.fix(1)
        return m
    return model_builder
register_model(
    name="Gas_100",
    build_function=build_stranded_gas_function(valid_modules=['U100']),
    soln_value=-12.34
)
register_model(
    name="Gas_250",
    build_function=build_stranded_gas_function(valid_modules=['U250']),
    soln_value=-18.37
)
register_model(
    name="Gas_500",
    build_function=build_stranded_gas_function(valid_modules=['U500']),
    soln_value=-4.690
)
register_model(
    name="Gas_small",
    build_function=build_stranded_gas_function(valid_modules=['U100', 'U250']),
    soln_value=-18.37
)
register_model(
    name="Gas_large",
    build_function=build_stranded_gas_function(valid_modules=['U250', 'U500']),
    soln_value=-18.37
)


# Methanol
@register_model_builder(opt_value=-1793.4)
def MeOH():
    from qmodels.methanol.methanol_disjunctive import MethanolModel
    m = MethanolModel().model
    # initialize vapor pressures
    m.flash_13.vapor_pressure[:].set_value(0.001)
    return m


# Logical
register_model(
    name="Spectralog",
    build_function=qmodels.logical.spectralog.build_model,
    opt_value=12.0893)
register_model(
    name="Positioning",
    build_function=qmodels.logical.positioning.build_model,
    opt_value=-8.06)
