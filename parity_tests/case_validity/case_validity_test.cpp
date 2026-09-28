#ifdef _WIN32
// Match the CLI translation unit's include order, including Windows min/max macros.
#include <windows.h>
#endif
#include "../../src/vsp_aero/Solver/CaseValidity.H"
#include <iostream>
#include <limits>

int main()
{
    using namespace vspaero_validity;
    int failures = 0;
    auto require = [&](bool valid, const char *message) {
        if (!valid) { std::cerr << message << '\n'; ++failures; }
    };
    const double nan = std::numeric_limits<double>::quiet_NaN();
    const double inf = std::numeric_limits<double>::infinity();
    require(cellError({{{0,0,0}},{{1,0,0}},{{0,1,0}}}) == NULL, "valid triangle rejected");
    require(cellError({{{0,0,0}},{{1,0,0}},{{1,0,0}}}) != NULL, "coincident distinct nodes accepted");
    require(cellError({{{0,0,0}},{{1,0,0}},{{2,0,0}}}) != NULL, "collinear triangle accepted");
    require(cellError({{{0,0,0}},{{1,0,0}},{{1,1,0}},{{1,1,0}},{{0,1,0}}}) != NULL,
            "polygon zero edge accepted");
    require(cellError({{{0,0,0}},{{1,0,0}},{{1,1,0}},{{.5,.5,0}},{{0,1,0}}}) == NULL,
            "valid concave polygon rejected");
    require(cellError({{{0,0,0}},{{nan,0,0}},{{0,1,0}}}) != NULL, "nonfinite node accepted");
    for (double scale : {1e-120, 1., 1e120}) {
        require(cellError({{{0,0,0}},{{scale,0,0}},{{0,scale,0}}}) == NULL,
                "triangle validity depends on length units");
    }
    const double good[] = {-.1,0.,1.5};
    const double badResidual[] = {1e-9,nan};
    const double badMoment[] = {.01,0.,0.,0.,inf,0.};
    require(finiteValues(good,3), "finite negative coefficient rejected");
    require(!finiteValues(badResidual,2), "NaN L2 hidden behind finite maximum residual");
    require(!finiteValues(badMoment,6), "finite drag hides invalid moment");
    for (double speed : {5.,10.,15.}) {
        require(std::abs(localReynolds(1e6,speed,speed,.1,.2)-5e5) < 1e-8,
                "local Reynolds changes with dimensional speed at fixed reference Re");
        require(std::abs(localReynolds(1e6,1.3*speed,speed,.1,.2)-6.5e5) < 1e-8,
                "local rotational velocity ratio missing from Reynolds");
    }
    // Differentiate the actual empirical force term at unequal local/reference
    // speeds and chords. Also exercise the low-Re clamp away from its corner.
    for (double referenceRe : {1., 1e6}) {
        const double localSpeed = 13., referenceSpeed = 10., chord = .1, referenceChord = .2;
        auto force = [&](double reynolds) {
            double re = (std::max)(2., localReynolds(reynolds,localSpeed,referenceSpeed,chord,referenceChord));
            return .5 * localSpeed * localSpeed * chord * 1.5 / std::pow(std::log10(re),2.58);
        };
        double re = (std::max)(2.,localReynolds(referenceRe,localSpeed,referenceSpeed,chord,referenceChord));
        double dCf = -2.58 * 1.5 / (re * std::log(10.) * std::pow(std::log10(re),3.58));
        double analytic = .5 * localSpeed * localSpeed * chord * dCf *
            localReynoldsReferenceDerivative(referenceRe,localSpeed,referenceSpeed,chord,referenceChord);
        double step = referenceRe * 1e-4;
        double finiteDifference = (force(referenceRe + step)-force(referenceRe-step))/(2.*step);
        require(std::abs(analytic-finiteDifference) <= 1e-12 + 1e-7*std::abs(finiteDifference),
                "empirical force reference-Re derivative disagrees with finite difference");
    }
    return failures ? 1 : 0;
}
