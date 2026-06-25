from core.bg40_defaults import BG40_DEFAULT
from core.dpt_seismic import dpt_general_spectrum, lookup_general_ss_s1, seismic_design_category_from_sd1, seismic_design_category_from_sds
from core.load_models import en_dynamic_factor_standard_maintenance, hunting_force_en1991, longitudinal_force_en1991, sdl_totals, wind_load_en1991_dpt


def test_sdl_totals_read_from_single_component_table():
    out = sdl_totals(BG40_DEFAULT["load_components"]["sdl_components"])
    assert abs(out["single_total"] - 62.14) < 0.02
    assert abs(out["double_total"] - 84.19) < 0.02


def test_dynamic_factor_bg40_report_value():
    out = en_dynamic_factor_standard_maintenance(35.0, 40.0)
    assert abs(out["Lphi_m"] - 35.0) < 1e-9
    assert abs(out["phi"] - 1.1079) < 0.001


def test_longitudinal_force_bg40():
    out = longitudinal_force_en1991(40.0, 40.0)
    assert out["Qlak_raw_kn"] == 1320.0
    assert out["Qlak_kn"] == 1000.0
    assert out["Qlbk_kn"] == 800.0
    assert out["LF_design_kn"] == 1000.0
    assert out["LF_design_kn_m"] == 25.0


def test_hunting_force_is_not_reduced_for_alpha_below_one_by_default():
    out = hunting_force_en1991(100.0, 0.8, False)
    assert out["HF_adopted_kn"] == 100.0
    assert "not reduced" in out["decision_basis"]


def test_wind_load_bg40_values():
    out = wind_load_en1991_dpt(1.25, 25.0, 4.6, 5.7, 3.9, 6.8, 40.0)
    assert abs(out["WSsuper_kn_m"] - 7.01) < 0.05
    assert abs(out["WSsuper_WL_kn_m"] - 15.14) < 0.10


def test_dpt_seed_lookup_sadao_songkhla():
    out = lookup_general_ss_s1("สงขลา", "สะเดา")
    assert out["found"] is True
    assert abs(float(out["Ss"]) - 0.079) < 1e-9
    assert abs(float(out["S1"]) - 0.084) < 1e-9


def test_dpt_seismic_general_workflow_sadao_soil_d():
    out = dpt_general_spectrum(0.079, 0.084, "D", 0.835, 1.25, 2.0)
    assert abs(out["Fa"] - 1.6) < 1e-9
    assert abs(out["Fv"] - 2.4) < 1e-9
    assert out["Cs"] >= 0.01
    assert out["category_governing"] in {"ก", "ข", "ค", "ง"}


def test_dpt_design_category_tables_reproduce_boundaries():
    assert seismic_design_category_from_sds(0.10, 1.0) == "ก"
    assert seismic_design_category_from_sds(0.20, 1.25) == "ข"
    assert seismic_design_category_from_sds(0.40, 1.5) == "ง"
    assert seismic_design_category_from_sd1(0.08, 1.0) == "ข"
    assert seismic_design_category_from_sd1(0.16, 1.25) == "ค"
