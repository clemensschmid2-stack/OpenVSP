"""Isolated worker for official OpenVSP geometry-analysis parity."""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path

CASES = ('mass_solid', 'mass_shell', 'mass_selected', 'comp_geom', 'planar_slice',
         'projection', 'degen_geom', 'parasite_drag', 'shell_analytic')


def numeric_results(vsp):
    output = {}
    for kind in sorted(vsp.GetAllResultsNames()):
        records = []
        for index in range(vsp.GetNumResults(kind)):
            result = vsp.FindResultsID(kind, index)
            record = {}
            for name in sorted(vsp.GetAllDataNames(result)):
                data_type = vsp.GetResultsType(result, name)
                values = []
                for entry in range(vsp.GetNumData(result, name)):
                    if data_type == vsp.DOUBLE_DATA:
                        data = list(vsp.GetDoubleResults(result, name, entry))
                    elif data_type == vsp.INT_DATA:
                        data = list(vsp.GetIntResults(result, name, entry))
                    elif data_type == vsp.VEC3D_DATA:
                        data = [[v.x(), v.y(), v.z()] for v in vsp.GetVec3dResults(result, name, entry)]
                    elif data_type == vsp.DOUBLE_MATRIX_DATA:
                        data = [list(row) for row in vsp.GetDoubleMatResults(result, name, entry)]
                    else:
                        continue  # generated IDs, paths and labels are not numerical results
                    values.append(data)
                if values:
                    record[name] = values
            # Projection returns component arrays in generated-ID order.
            # Match physical components by their stable fixture names.
            if kind == 'Projection' and 'Comp_Names' in vsp.GetAllDataNames(result):
                names = list(vsp.GetStringResults(result, 'Comp_Names'))
                order = sorted(range(len(names)), key=names.__getitem__)
                for name in record:
                    if name.startswith('Comp_'):
                        record[name] = [[values[i] for i in order] if len(values) == len(names) else values
                                        for values in record[name]]
            records.append(record)
        output[kind] = records
    return output


def shell_analytic(vsp):
    # A closed tetrahedral shell represented by exactly four flat triangles.
    # The three edge midpoints form an exact degree-two quadrature rule.
    points = [(1.,2.,3.), (3.,2.,3.), (1.,5.,3.), (1.,2.,7.)]
    faces = [(0,2,1), (0,1,3), (0,3,2), (1,2,3)]
    triangles = [[points[i] for i in face] for face in faces]
    text = 'solid tetra\n'
    weighted = []
    for triangle in triangles:
        a,b,c = triangle
        u,v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        area = math.sqrt(sum(x*x for x in cross))/2
        for j,k in ((0,1),(1,2),(2,0)):
            weighted.append((2.*area/3, [(triangle[j][i]+triangle[k][i])/2 for i in range(3)]))
        text += 'facet normal 0 0 0\nouter loop\n'
        text += ''.join('vertex '+' '.join(map(str, p))+'\n' for p in triangle)
        text += 'endloop\nendfacet\n'
    Path('tetra.stl').write_text(text+'endsolid tetra\n')
    geom = vsp.ImportFile('tetra.stl', vsp.IMPORT_STL, '')
    vsp.SetParmVal(geom, 'Shell_Flag', 'Mass_Props', 1.)
    vsp.SetParmVal(geom, 'Mass_Area', 'Mass_Props', 2.)
    vsp.SetParmVal(geom, 'Density', 'Mass_Props', 0.)
    vsp.Update()
    vsp.SetAnalysisInputDefaults('MassProp')
    result = vsp.ExecAnalysis('MassProp')
    mass = sum(w for w,p in weighted)
    cg = [sum(w*p[i] for w,p in weighted)/mass for i in range(3)]
    second = [[sum(w*(p[i]-cg[i])*(p[j]-cg[j]) for w,p in weighted) for j in range(3)] for i in range(3)]
    expected = dict(Total_Mass=[mass], Total_CG=cg,
                    Total_Ixx=[second[1][1]+second[2][2]], Total_Iyy=[second[0][0]+second[2][2]],
                    Total_Izz=[second[0][0]+second[1][1]], Total_Ixy=[second[0][1]],
                    Total_Ixz=[second[0][2]], Total_Iyz=[second[1][2]])
    actual = {name: list(vsp.GetDoubleResults(result, name)) for name in expected if name != 'Total_CG'}
    cg_result = vsp.GetVec3dResults(result, 'Total_CG')[0]
    actual['Total_CG'] = [cg_result.x(), cg_result.y(), cg_result.z()]
    return dict(expected=expected, actual=actual)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--distribution', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    dll_handle = os.add_dll_directory(str(args.distribution.resolve()))
    import openvsp as vsp
    vsp.VSPRenew()
    if args.case == 'shell_analytic':
        args.output.write_text(json.dumps(shell_analytic(vsp), indent=2, allow_nan=False))
        return

    def parm(geom, name, group, value):
        pid = vsp.FindParm(geom, name, group)
        if not pid:
            raise RuntimeError(f'Missing parameter {group}/{name}')
        actual = vsp.SetParmVal(pid, value)
        if not math.isclose(actual, value, rel_tol=1e-10, abs_tol=1e-10):
            raise RuntimeError(f'Parameter clamped: {name}: {actual} != {value}')

    # Unequal densities, asymmetric offsets and rotations exercise all inertia
    # tensor components and CG aggregation, rather than a zero/default mass.
    for index, (location, rotation, density) in enumerate([
            ((0., 0., 0.), (5., 12., 18.), 650.),
            ((2.5, 1.7, .8), (-7., 23., -11.), 1200.)]):
        geom = vsp.AddGeom('POD', '')
        vsp.SetGeomName(geom, f'Pod{index}')
        parm(geom, 'Length', 'Design', 3.0 + index)
        parm(geom, 'FineRatio', 'Design', 5.0 + index)
        parm(geom, 'Density', 'Mass_Props', density)
        parm(geom, 'Tess_U', 'Shape', 31)
        parm(geom, 'Tess_W', 'Shape', 25)
        for axis, value in zip('XYZ', location):
            parm(geom, f'{axis}_Rel_Location', 'XForm', value)
        for axis, value in zip('XYZ', rotation):
            parm(geom, f'{axis}_Rel_Rotation', 'XForm', value)
        if args.case == 'mass_shell':
            parm(geom, 'Shell_Flag', 'Mass_Props', 1.)
            parm(geom, 'Mass_Area', 'Mass_Props', 4. + index)
        vsp.SetSetFlag(geom, vsp.SET_FIRST_USER, index == 1)
    wing = vsp.AddGeom('WING', '')
    vsp.SetGeomName(wing, 'AnalysisWing')
    parm(wing, 'Density', 'Mass_Props', 400.)
    parm(wing, 'Z_Rel_Location', 'XForm', 2.)
    parm(wing, 'Y_Rel_Rotation', 'XForm', 8.)
    parm(wing, 'Tess_W', 'Shape', 25)
    vsp.SetSetFlag(wing, vsp.SET_FIRST_USER, False)
    vsp.Update()
    vsp.WriteVSPFile('fixture.vsp3', vsp.SET_ALL)
    vsp.DeleteAllResults()
    analysis = {'mass_solid': 'MassProp', 'mass_shell': 'MassProp', 'mass_selected': 'MassProp',
                'comp_geom': 'CompGeom', 'planar_slice': 'PlanarSlice', 'projection': 'Projection',
                'degen_geom': 'DegenGeom', 'parasite_drag': 'ParasiteDrag'}[args.case]
    vsp.SetAnalysisInputDefaults(analysis)
    def integer(name, value):
        vsp.SetIntAnalysisInput(analysis, name, [value], 0)
    if analysis == 'MassProp':
        integer('Set', vsp.SET_FIRST_USER if args.case == 'mass_selected' else vsp.SET_ALL)
        integer('NumMassSlices', 81)
        integer('MassSliceDir', vsp.Y_DIR if args.case == 'mass_shell' else vsp.X_DIR)
    elif analysis == 'PlanarSlice':
        integer('Set', vsp.SET_ALL)
        integer('NumSlices', 21)
        vsp.SetVec3dAnalysisInput(analysis, 'Norm', [vsp.vec3d(1., 0., 0.)], 0)
    elif analysis == 'ParasiteDrag':
        integer('GeomSet', vsp.SET_ALL)
        vsp.SetStringAnalysisInput(analysis, 'FileName', ['parasite.csv'], 0)
        vsp.SetDoubleAnalysisInput(analysis, 'Vinf', [50.], 0)
        vsp.SetDoubleAnalysisInput(analysis, 'Sref', [10.], 0)
    result = vsp.ExecAnalysis(analysis)
    if not result:
        raise RuntimeError(f'{analysis} returned no result')
    errors = []
    manager = vsp if hasattr(vsp, 'GetNumTotalErrors') else vsp.ErrorMgrSingleton.getInstance()
    while manager.GetNumTotalErrors():
        errors.append(manager.PopLastError().GetErrorString())
    if errors:
        raise RuntimeError('; '.join(errors))
    results = numeric_results(vsp)
    if analysis == 'MassProp':
        for name in ('Total_Mass', 'Total_CG', 'Total_Ixx', 'Total_Iyy', 'Total_Izz', 'Total_Ixy', 'Total_Ixz', 'Total_Iyz'):
            if name not in vsp.GetAllDataNames(result):
                raise RuntimeError(f'Missing mass-property field: {name}')
        if vsp.GetDoubleResults(result, 'Total_Mass')[0] <= 0:
            raise RuntimeError('Non-positive total mass')
    args.output.write_text(json.dumps(dict(analysis=analysis, results=results), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
