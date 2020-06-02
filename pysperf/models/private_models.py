"""
Models in the Grossmann Group private model library that are missing permission from collaborators to release,
or have simply not formatted for release yet.

If ggmodels package is available and installed, then these models will be imported.
Otherwise, they are omitted from the test library.
"""

try:
    import ggmodels
    _private_models_available = True
except ImportError:
    ggmodels = None
    _private_models_available = False

from pysperf.model_library_registration import register_model_builder


def _register_private_models():
    # Kaibel column
    @register_model_builder(bigM=1e6, best_value=115637)
    def Kaibel():
        from ggmodels.kaibel import build_model
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
    @register_model_builder(bigM=1e6, best_value=1441161)
    def Memb():
        from ggmodels.membrane import build_membrane_model
        return build_membrane_model()

    # Methanol
    @register_model_builder(opt_value=-1793.4)
    def MeOH():
        from ggmodels.methanol import build_model
        m = build_model()
        # initialize vapor pressures
        m.flash_13.vapor_pressure[:].set_value(0.001)
        return m


if _private_models_available:
    _register_private_models()
