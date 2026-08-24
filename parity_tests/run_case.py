"""Worker process for one OpenVSP/VSPAERO parity case.

This file is launched with exactly one OpenVSP distribution on PYTHONPATH so
the official and locally built extension modules can never mix in one process.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def set_double(vsp, analysis: str, name: str, value: float) -> None:
    vsp.SetDoubleAnalysisInput(analysis, name, [value], 0)


def set_int(vsp, analysis: str, name: str, value: int) -> None:
    vsp.SetIntAnalysisInput(analysis, name, [value], 0)


def extract_numeric_results(vsp, result_name: str) -> list[dict[str, object]]:
    output = []
    for index in range(vsp.GetNumResults(result_name)):
        result_id = vsp.FindResultsID(result_name, index)
        values: dict[str, object] = {}
        for name in sorted(vsp.GetAllDataNames(result_id)):
            result_type = vsp.GetResultsType(result_id, name)
            if result_type == vsp.DOUBLE_DATA:
                values[name] = list(vsp.GetDoubleResults(result_id, name))
            elif result_type == vsp.INT_DATA:
                values[name] = list(vsp.GetIntResults(result_id, name))
        output.append(values)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--distribution", type=Path, required=True)
    parser.add_argument("--mode", choices=("thin", "thick"), required=True)
    parser.add_argument("--analysis", choices=("base", "stab"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    distribution = args.distribution.resolve()
    os.add_dll_directory(str(distribution))
    import openvsp as vsp

    vsp.SetVSPAEROPath(str(distribution))
    vsp.VSPRenew()

    # Cp slicing is unrelated to coefficient parity and launches vsploads.exe.
    # Disable it so the test exercises only geometry generation and VSPAERO;
    # some OpenVSP 3.51.2 Windows builds crash in the slicer after processing.
    settings_id = vsp.FindContainer("VSPAEROSettings", 0)
    cp_slice_id = vsp.FindParm(settings_id, "CpSliceFlag", "VSPAERO")
    if not cp_slice_id:
        raise RuntimeError("Could not find the VSPAERO CpSliceFlag parameter")
    vsp.SetParmVal(cp_slice_id, 0.0)

    wing_id = vsp.AddGeom("WING", "")
    vsp.SetGeomName(wing_id, "ParityWing")
    vsp.SetDriverGroup(
        wing_id,
        1,
        vsp.SPAN_WSECT_DRIVER,
        vsp.ROOTC_WSECT_DRIVER,
        vsp.TIPC_WSECT_DRIVER,
    )
    vsp.SetParmVal(wing_id, "Span", "XSec_1", 5.0)
    vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", 2.0)
    vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", 1.0)
    vsp.SetParmVal(wing_id, "Sweep", "XSec_1", 15.0)
    vsp.SetParmVal(wing_id, "Dihedral", "XSec_1", 3.0)
    vsp.SetParmVal(wing_id, "Twist", "XSec_1", -2.0)
    vsp.SetParmVal(wing_id, "Tess_W", "Shape", 25)
    vsp.AddSubSurf(wing_id, vsp.SS_CONTROL, 0)
    vsp.Update()
    vsp.AutoGroupVSPAEROControlSurfaces()
    vsp.SetVSPAERORefWingID(wing_id)
    vsp.WriteVSPFile("parity_wing.vsp3", vsp.SET_ALL)

    geometry = "VSPAEROComputeGeometry"
    vsp.SetAnalysisInputDefaults(geometry)
    if args.mode == "thin":
        set_int(vsp, geometry, "GeomSet", vsp.SET_NONE)
        set_int(vsp, geometry, "ThinGeomSet", vsp.SET_ALL)
    else:
        set_int(vsp, geometry, "GeomSet", vsp.SET_ALL)
        set_int(vsp, geometry, "ThinGeomSet", vsp.SET_NONE)
    geometry_id = vsp.ExecAnalysis(geometry)
    if not geometry_id:
        raise RuntimeError("VSPAEROComputeGeometry returned no result")

    sweep = "VSPAEROSweep"
    vsp.SetAnalysisInputDefaults(sweep)
    set_int(vsp, sweep, "GeomSet", vsp.SET_ALL)
    set_int(vsp, sweep, "RefFlag", 0)
    set_double(vsp, sweep, "Sref", 15.0)
    set_double(vsp, sweep, "bref", 10.0)
    set_double(vsp, sweep, "cref", 1.5)
    set_double(vsp, sweep, "MachStart", 0.15)
    set_double(vsp, sweep, "MachEnd", 0.15)
    set_int(vsp, sweep, "MachNpts", 1)
    set_double(vsp, sweep, "BetaStart", 0.0)
    set_double(vsp, sweep, "BetaEnd", 0.0)
    set_int(vsp, sweep, "BetaNpts", 1)
    set_int(vsp, sweep, "WakeNumIter", 3)

    if args.analysis == "base":
        set_double(vsp, sweep, "AlphaStart", -2.0)
        set_double(vsp, sweep, "AlphaEnd", 8.0)
        # Include alpha=4 exactly so State Sweep's zero-rate state can also be
        # checked against this independent normal-sweep result.
        set_int(vsp, sweep, "AlphaNpts", 6)
    else:
        set_double(vsp, sweep, "AlphaStart", 4.0)
        set_double(vsp, sweep, "AlphaEnd", 4.0)
        set_int(vsp, sweep, "AlphaNpts", 1)
        set_int(vsp, sweep, "UnsteadyType", vsp.STABILITY_DEFAULT)

    vsp.Update()
    sweep_id = vsp.ExecAnalysis(sweep)
    if not sweep_id:
        raise RuntimeError("VSPAEROSweep returned no result")

    payload = {
        "mode": args.mode,
        "analysis": args.analysis,
        "history": extract_numeric_results(vsp, "VSPAERO_History"),
        "stability": extract_numeric_results(vsp, "VSPAERO_Stab"),
    }
    if not payload["history"]:
        raise RuntimeError("VSPAERO produced no history results")
    if args.analysis == "stab" and not payload["stability"]:
        raise RuntimeError("VSPAERO produced no stability results")

    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
