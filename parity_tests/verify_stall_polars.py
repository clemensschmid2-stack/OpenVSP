"""Compare approved-polar native stall limits with equivalent fixed strip limits."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess
from verify_profile_drag import history


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solver',type=Path,required=True)
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    solver=args.solver.resolve(); work=args.work.resolve(); work.mkdir(parents=True,exist_ok=False)
    for suffix in ('.vspgeom','.vkey','.vspaero','.csf','.ControlSurfaces.taglist'):
        shutil.copy2(args.fixture/('parity_wing'+suffix),work/('wing'+suffix))
    for tag in args.fixture.glob('*.tag'): shutil.copy2(tag,work/tag.name)
    setup=(work/'wing.vspaero').read_text()
    def run(label,extra,ok=True):
        with (work/(label+'.log')).open('w') as log:
            result=subprocess.run([str(solver),'-omp','1',*extra,'wing'],cwd=work,
                stdout=log,stderr=subprocess.STDOUT,timeout=120)
        assert (result.returncode==0)==ok,(label,result.returncode)
        return history(work/'wing.history') if ok and label!='template' else []
    run('template',['-stall-strip-template','strips.csv'])
    with (work/'strips.csv').open() as stream: strips=list(csv.DictReader(stream))
    results=[]
    expected_states={}
    # Exercise both lift signs and changing physical control/Reynolds endpoints.
    for index,(re,angle,positive,negative) in enumerate(((100.,-10.,.7,-1.1),(100.,10.,.9,-1.),(1e9,-10.,1.1,-1.),(1e9,10.,1.3,-.9))):
        lines=setup.splitlines()
        for i,line in enumerate(lines):
            if line.startswith('AoA ='): lines[i]='AoA = -8, 8'
            if line.startswith('StallModel ='): lines[i]='StallModel = 1'
            if line.startswith('WakeIters ='): lines[i]='WakeIters = 30'
            if line.startswith('ForwardGMRESConvergenceFactor ='): lines[i]='ForwardGMRESConvergenceFactor = 1e-8'
            if line.startswith('ReCref ='): lines[i]=f'ReCref = {re}'
            if line.startswith('NumberOfControlGroups'): lines[i+4]=str(angle)
        (work/'wing.vspaero').write_text('\n'.join(lines)+'\n')
        with (work/'fixed.csv').open('w',newline='') as stream:
            writer=csv.writer(stream)
            writer.writerow(('vortex_sheet','strip','cl_max_positive','cl_min_negative'))
            for row in strips: writer.writerow((row['vortex_sheet'],row['strip'],positive,negative))
        with (work/'polars.csv').open('w',newline='') as stream:
            writer=csv.writer(stream)
            for row in strips:
                for delta in (-10,10):
                    for node_re in (1e5,1e7):
                        # Endpoint combinations match fixed limits; both dimensions affect results.
                        pos=.7+.2*(delta==10)+.4*(node_re==1e7)
                        neg=1.1-.1*(delta==10)-.1*(node_re==1e7)
                        for sign,value in ((-1,neg),(1,pos)):
                            writer.writerow((row['vortex_sheet'],row['strip'],0,1,1,1,delta,node_re,sign,value))
        fixed=run(f'fixed-{index}',['-stall-strip-table','fixed.csv'])
        polar=run(f'polar-{index}',['-stall-polar-table','polars.csv'])
        assert len(fixed)==len(polar)
        count=0
        for a,b in zip(fixed,polar):
            for key in ('CL','CD','CS','CMx','CMy','CMz','CLi','CDi','CFix','CFiy','CFiz'):
                if key in a:
                    assert abs(a[key]-b[key]) <= 1e-9,(index,key,a[key],b[key])
                    count+=1
        assert count>0
        assert 'XFOIL stall limits clipped' in (work/f'polar-{index}.log').read_text()
        results.append(dict(re=re,angle=angle,compared=count))
        run(f'fixed-state-{index}',['-state-sweep','-state-output-dir',f'fixed-state-{index}',
                                  '-stall-strip-table','fixed.csv'])
        with (work/f'fixed-state-{index}'/'part-000000.csv').open() as stream:
            for row in csv.DictReader(stream): expected_states[re,angle,float(row['alpha_deg'])]=row
    sweep_setup=(work/'wing.vspaero').read_text()
    sweep_setup='\n'.join('ReCref = 100, 1000000000' if line.startswith('ReCref =') else line
                          for line in sweep_setup.splitlines())+'\n'
    (work/'wing.vspaero').write_text(sweep_setup)
    sweep_args=['-state-sweep','-state-output-dir','polar-states','-state-control','1','-10,10',
                '-stall-polar-table','polars.csv']
    run('polar-states',sweep_args)
    with (work/'polar-states'/'part-000000.csv').open() as stream: states=list(csv.DictReader(stream))
    assert len(states)==8
    for row in states:
        control=next(k for k in row if k.endswith('_deflection_deg'))
        expected=expected_states[float(row['reynolds']),float(row[control]),float(row['alpha_deg'])]
        for key in ('CFx','CFy','CFz','CMx','CMy','CMz','stall_factor'):
            assert abs(float(row[key])-float(expected[key]))<=1e-9,(key,row,expected)
    run('resume-unchanged',sweep_args+['-state-resume'])
    with (work/'polars.csv').open('a') as stream: stream.write('# changed provenance\n')
    run('resume-changed',sweep_args+['-state-resume'],False)

    run('regular-reynolds',['-stall-polar-table','polars.csv'])
    assert (work/'regular-reynolds.log').read_text().count('Solving... Mach:')==4
    # Reynolds stability samples must also solve circulation, not just profile drag.
    stability_setup='\n'.join('ReCref = 1000000' if line.startswith('ReCref =') else line
                              for line in sweep_setup.splitlines())+'\n'
    (work/'wing.vspaero').write_text(stability_setup)
    run('reynolds-stability',['-stab','-stab-map-csv','-stab-select','reynolds',
                              '-stall-polar-table','polars.csv'])
    with (work/'wing.stability_cases.csv').open() as stream: stability=list(csv.DictReader(stream))
    assert len(stability)==6
    changed=False
    for point in {r['map_point_id'] for r in stability}:
        samples={r['direction']:r for r in stability if r['map_point_id']==point and r['derivative']=='ln_reynolds'}
        assert set(samples)=={'positive','negative'}
        assert float(samples['positive']['reynolds'])==1050000
        assert float(samples['negative']['reynolds'])==950000
        changed |= abs(float(samples['positive']['stall_factor'])-float(samples['negative']['stall_factor']))>1e-8
    assert changed, 'Reynolds perturbations did not update the nonlinear stall solution'
    (work/'stability-columns.json').write_text(json.dumps(stability,indent=2))
    run('reject-conflicting',['-stall-strip-table','fixed.csv','-stall-polar-table','polars.csv'],False)
    (work/'polars.csv').write_text('1,1,0,1,0,0,0,100,1,1\n')
    run('reject-incomplete',['-stall-polar-table','polars.csv'],False)
    (work/'report.json').write_text(json.dumps(dict(passed=True,cases=results,state_sweep_states=len(states),resume_hash_checked=True,stability_rows=len(stability)),indent=2))
    print(json.dumps(results))

if __name__=='__main__': main()
