"""Models from the GDPlib public GDP model repository.
"""

try:
    import gdplib

    _library_models_available = True
except ImportError:
    gdplib = None
    _library_models_available = False

from pysperf.model_library_tools import register_model, register_model_builder


def _register_gdplib_models():
    register_model(
        name="batchp",
        build_function=gdplib.pyomo_examples.build_batch_processing_model,
        bigM=1000, opt_value=679365)
    register_model(
        name="disease",
        build_function=gdplib.pyomo_examples.build_jobshop_model,
        bigM=1000, opt_value=304.4)
    register_model(
        name="jobshop",
        build_function=gdplib.pyomo_examples.build_batch_processing_model,
        bigM=None, opt_value=11)
    register_model(
        name="purchasing",
        build_function=gdplib.pyomo_examples.build_med_term_purchasing_model,
        bigM=None, opt_value=6797.5)

    # heat exchanger network synthesis models
    @register_model_builder(opt_value=106767)
    def HENS_conv():
        return gdplib.mod_hens.build_conventional()
    @register_model_builder(best_value=134522)
    def HENS_int_sing():
        return gdplib.mod_hens.build_integer_single_module()
    @register_model_builder(best_value=112270)
    def HENS_int_mult():
        return gdplib.mod_hens.build_integer_single_module()
    @register_model_builder(best_value=101505)
    def HENS_int_opt():
        return gdplib.mod_hens.build_integer_modular_option()
    @register_model_builder(best_value=134522)
    def HENS_disc_sing():
        return gdplib.mod_hens.build_discrete_single_module()
    @register_model_builder(best_value=111520)
    def HENS_disc_mult():
        return gdplib.mod_hens.build_discrete_require_modular()
    @register_model_builder(best_value=101505)
    def HENS_disc_opt():
        return gdplib.mod_hens.build_discrete_modular_option()

    # Modular network design - capacity expansion
    @register_model_builder(bigM=7000, opt_value=3593)
    def Mod_grow():
        from gdplib.modprodnet import build_cap_expand_growth
        return build_cap_expand_growth()
    @register_model_builder(bigM=7000, opt_value=2096)
    def Mod_dip():
        from gdplib.modprodnet import build_cap_expand_dip
        return build_cap_expand_dip()
    @register_model_builder(bigM=7000, opt_value=851)
    def Mod_decay():
        from gdplib.modprodnet import build_cap_expand_decay
        return build_cap_expand_decay()

    # Modular network design - distributed facility location
    @register_model_builder(bigM=10000, best_value=36262)
    def Mod_dist():
        from gdplib.modprodnet import build_distributed_model
        return build_distributed_model()
    @register_model_builder(bigM=10000, best_value=19568)
    def Mod_qtr():
        from gdplib.modprodnet import build_quarter_distributed_model
        return build_quarter_distributed_model()

    # Biofuel network
    register_model(
        name="Biofuel",
        build_function=gdplib.biofuel.build_model,
        bigM=7800,
        opt_value=4067
    )

    # Stranded gas models
    def build_stranded_gas_function(valid_modules):
        def model_builder():
            from gdplib.stranded_gas import build_model
            m = build_model()

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
        best_value=-12.34
    )
    register_model(
        name="Gas_250",
        build_function=build_stranded_gas_function(valid_modules=['U250']),
        best_value=-18.37
    )
    register_model(
        name="Gas_500",
        build_function=build_stranded_gas_function(valid_modules=['U500']),
        best_value=-4.690
    )
    register_model(
        name="Gas_small",
        build_function=build_stranded_gas_function(valid_modules=['U100', 'U250']),
        best_value=-18.37
    )
    register_model(
        name="Gas_large",
        build_function=build_stranded_gas_function(valid_modules=['U250', 'U500']),
        best_value=-18.37
    )

    # Logical
    register_model(
        name="Spectralog",
        build_function=gdplib.logical.build_spectralog_model,
        opt_value=12.0893)
    register_model(
        name="Positioning",
        build_function=gdplib.logical.build_positioning_model,
        opt_value=-8.06)
    pass


if _library_models_available:
    _register_gdplib_models()
