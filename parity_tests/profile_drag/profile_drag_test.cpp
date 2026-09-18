#include "../../src/vsp_aero/Solver/SectionProfileDrag.H"
#include <iostream>
#include <stdexcept>
void check(bool ok) { if (!ok) throw std::runtime_error("Profile drag regression failed"); }
int main() {
    vds_profile::Table t;
    auto &s=t.strips[{1,1}][0]; s.weight=1.; s.group=1; s.gain=1.;
    for (double delta: {0.,10.}) for(double re: {100.,200.}) for(double cl: {-1.,1.})
        s.data[delta][re][cl]=.01+.001*delta+.0001*re+.002*cl;
    bool clipped=false;
    double value=t.drag(1,1,150.,0.,[](int){return 5.;},clipped);
    check(std::abs(value-.03)<1.e-12 && !clipped);
    value=t.drag(1,1,150.,5.,[](int){return 5.;},clipped);
    check(std::abs(value-.032)<1.e-12 && clipped);
    clipped=false;
    value=t.drag(1,1,1000.,-5.,[](int){return -5.;},clipped);
    check(std::abs(value-.028)<1.e-12 && clipped);
    s.data[0.][100.].clear();
    bool rejected=false;
    try { t.drag(1,1,100.,0.,[](int){return 0.;},clipped); }
    catch(const std::runtime_error&) { rejected=true; }
    check(rejected);
    std::ofstream file("invalid.csv");
    file << "1,1,0,1,0,0,0,100,0,-0.2\n"; file.close();
    rejected=false; try { t.load("invalid.csv",0); } catch(const std::runtime_error&) {rejected=true;}
    check(rejected);
    std::cout << "PASS: interpolation, clipping, empty polar and invalid CD rejection\n";
}
