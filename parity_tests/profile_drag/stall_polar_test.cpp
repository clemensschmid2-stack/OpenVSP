#include "../../src/vsp_aero/Solver/SectionStallPolars.H"
#include <iostream>
#include <stdexcept>
void check(bool ok) { if (!ok) throw std::runtime_error("Stall polar regression failed"); }
int main() {
    std::ofstream file("stall.csv");
    // Two span stations, two Reynolds nodes and two flap nodes, asymmetric limits.
    for (int part : {0,1}) for (double delta : {-10.,10.}) for (double re : {100.,200.})
        for (double sign : {-1.,1.})
            file << "1,1," << part << ',' << (part ? .25 : .75) << ",1,-1," << delta << ',' << re << ',' << sign
                 << ',' << 1.+.1*part+.01*delta+.001*re+.2*sign << '\n';
    file.close();
    vds_stall::Table t; t.load("stall.csv",1);
    bool clipped=false;
    // Physical +5 deg with gain -1 selects canonical -5 deg.
    double pos=t.limit(1,1,150.,1.,[](int){return 5.;},clipped);
    double neg=t.limit(1,1,150.,-1.,[](int){return 5.;},clipped);
    check(std::abs(pos-1.325)<1e-12 && std::abs(neg-.925)<1e-12 && !clipped);
    check(std::abs(t.limit(1,1,300.,1.,[](int){return -20.;},clipped)-1.525)<1e-12 && clipped);
    for (const char *rows : {"1,1,0,1,0,0,0,100,1,1\n", "1,1,0,1,0,0,0,100,0,-1\n",
                             "1,1,0,1,0,0,0,100,-1,0\n1,1,0,1,0,0,0,100,1,1\n"}) {
        std::ofstream bad("bad-stall.csv"); bad << rows; bad.close();
        bool rejected=false; try { t.load("bad-stall.csv",0); } catch(const std::runtime_error&) {rejected=true;}
        check(rejected);
    }
    std::cout << "PASS: signed limits, span/Re/flap interpolation, physical gain, clipping and invalid tables\n";
}
