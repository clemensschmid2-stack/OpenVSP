"""Native force regression using a generated parity_wing fixture and known CD."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess


def history(path):
    header = None
    rows = []
    for line in path.read_text().splitlines():
        parts = line.replace('L2 Residual', 'L2_Residual').replace('Max Residual', 'Max_Residual').split()
        if parts and parts[0] == 'Iter' and 'CDo' in parts:
            header = parts
        elif header and len(parts) == len(header):
            try:
                row = dict(zip(header, map(float, parts)))
            except ValueError:
                continue
            rows.append(row)
    if not rows:
        raise ValueError('No history rows')
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    solver=args.solver.resolve(); work=args.work.resolve(); work.mkdir(parents=True,exist_ok=False)
    for suffix in ('.vspgeom','.vkey','.vspaero','.csf','.ControlSurfaces.taglist'):
        shutil.copy2(args.fixture / ('parity_wing'+suffix),work / ('wing'+suffix))
    for tag in args.fixture.glob('*.tag'):
        shutil.copy2(tag, work / tag.name)
    # One inexpensive operating point; force replacement cannot alter circulation.
    setup=(work/'wing.vspaero').read_text()
    (work/'wing.vspaero').write_text(setup)
    def run(label, extra):
        with (work/(label+'.log')).open('w') as log:
            subprocess.run([str(solver),'-omp','1',*extra,'wing'],cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    run('template',['-stall-strip-template','strips.csv'])
    strips=list(csv.DictReader((work/'strips.csv').open()))
    run('original',[]); original=history(work/'wing.history')
    baseline=history(args.fixture/'parity_wing.history')[-1]
    for name in ('CLi','CDi','CDo','CMix','CMiy','CMiz','CFix','CFiy','CFiz'):
        assert abs(original[-1][name]-baseline[name]) <= 1e-8+1e-6*abs(baseline[name]), name
    setup='\n'.join('AoA = 2' if line.startswith('AoA =') else line for line in setup.splitlines())+'\n'
    (work/'wing.vspaero').write_text(setup)
    run('original_single',[]); original=history(work/'wing.history')
    results={}
    for label,cd in [('zero',0.),('constant',.02)]:
        with (work/'profile.csv').open('w',newline='') as stream:
            writer=csv.writer(stream)
            for strip in strips:
                writer.writerow((strip['vortex_sheet'],strip['strip'],0,1,0,0,0,1e7,0,cd))
        run(label,['-profile-drag-table','profile.csv'])
        rows=history(work/'wing.history')
        assert len(rows)==len(original)
        for old,new in zip(original,rows):
            for name in ('CLi','CDi','CMix','CMiy','CMiz','CFix','CFiy','CFiz'):
                if name in old: assert abs(old[name]-new[name])<1e-10,(name,old[name],new[name])
            if cd==0: assert abs(new['CDo'])<1e-10,new['CDo']
        results[label]=rows[-1]['CDo']
        if cd: assert 'XFOIL profile drag clipped:' in (work/(label+'.log')).read_text()
    assert results['constant']>results['zero']
    # The native mesh's strip areas differ slightly from the declared Sref.
    # Compare against actual strip integration, not an idealized planform.
    header=None; area_velocity=0.
    for line in (work/'wing.lod').read_text().splitlines():
        parts=line.split()
        if parts and parts[0]=='Iter' and 'dArea' in parts: header=parts
        elif header and len(parts)==len(header):
            try: row=dict(zip(header,map(float,parts)))
            except ValueError: continue
            area_velocity+=row['dArea']*row['V/Vref']**2
    sref=float(next(line for line in setup.splitlines() if line.startswith('Sref')).split('=')[1])
    assert abs(results['constant']-.02*area_velocity/sref)<2e-8, results
    with (work/'profile.csv').open('w',newline='') as stream:
        writer=csv.writer(stream)
        for strip in strips:
            for re,cd in ((1e6,.01),(2e7,.03)):
                writer.writerow((strip['vortex_sheet'],strip['strip'],0,1,0,0,0,re,0,cd))
    run('reynolds',['-profile-drag-table','profile.csv'])
    expected=0.; header=None
    for line in (work/'wing.lod').read_text().splitlines():
        parts=line.split()
        if parts and parts[0]=='Iter' and 'dArea' in parts: header=parts
        elif header and len(parts)==len(header):
            try: row=dict(zip(header,map(float,parts)))
            except ValueError: continue
            local_re=1e7*row['V/Vref']*row['Chord']/1.5
            cd=.01+.02*(min(2e7,max(1e6,local_re))-1e6)/1.9e7
            expected+=row['dArea']*row['V/Vref']**2*cd/sref
    results['reynolds']=history(work/'wing.history')[-1]['CDo']
    assert abs(results['reynolds']-expected)<2e-8,(results,expected)
    (work/'report.json').write_text(json.dumps(dict(status='PASS',strips=len(strips),drag=results),indent=2))
    print(json.dumps(results))


if __name__=='__main__': main()
