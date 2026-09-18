// Optional section-profile drag tables. Absent tables retain the original model.
#ifndef SECTION_PROFILE_DRAG_H
#define SECTION_PROFILE_DRAG_H
#include <map>
#include <utility>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <algorithm>
#include <cmath>
#include <string>

namespace vds_profile {
typedef std::map<double, double> Curve;
typedef std::map<double, Curve> ReynoldsGrid;
typedef std::map<double, ReynoldsGrid> DeflectionGrid;
struct Section {
    double weight = 0.;
    int group = 0;
    double gain = 0.;
    DeflectionGrid data;
};
template<class Grid, class Evaluate>
double interpolate(const Grid &grid, double x, Evaluate evaluate, bool &clipped) {
    if (grid.empty() || !std::isfinite(x)) throw std::runtime_error("Invalid profile drag lookup");
    auto hi = grid.lower_bound(x);
    if (hi == grid.end()) { clipped |= x > grid.rbegin()->first; return evaluate(grid.rbegin()->second); }
    if (hi == grid.begin() || hi->first == x) { clipped |= x < hi->first; return evaluate(hi->second); }
    auto lo = std::prev(hi);
    double f = (x-lo->first)/(hi->first-lo->first);
    return (1.-f)*evaluate(lo->second)+f*evaluate(hi->second);
}
class Table {
public:
    std::map<std::pair<int,int>, std::map<int,Section> > strips;
    void load(const std::string &path, int groups) {
        std::ifstream in(path.c_str());
        if (!in) throw std::runtime_error("Cannot open profile drag table");
        strips.clear();
        std::string line;
        while (std::getline(in,line)) {
            if (line.empty() || line[0]=='#' || line.find("vortex_sheet")==0) continue;
            std::replace(line.begin(),line.end(),',',' ');
            std::istringstream row(line);
            int sheet,strip,part,group; double weight,gain,re,delta,cl,cd;
            std::string extra;
            if (!(row>>sheet>>strip>>part>>weight>>group>>gain>>delta>>re>>cl>>cd) || (row>>extra))
                throw std::runtime_error("Malformed profile drag row");
            if (sheet<1 || strip<1 || part<0 || group<0 || group>groups ||
                !std::isfinite(weight) || weight<=0 || !std::isfinite(gain) ||
                !std::isfinite(re) || re<=0 || !std::isfinite(delta) ||
                !std::isfinite(cl) || !std::isfinite(cd) || (cd<0 && cd!=-1.))
                throw std::runtime_error("Invalid profile drag row");
            Section &s = strips[{sheet,strip}][part];
            if (!s.data.empty() && (s.weight!=weight || s.group!=group || s.gain!=gain))
                throw std::runtime_error("Inconsistent profile section metadata");
            s.weight=weight; s.group=group; s.gain=gain;
            if (cd == -1.) {
                if (s.data[delta].count(re)) throw std::runtime_error("Duplicate empty profile");
                s.data[delta][re]; // Explicit missing polar, not a zero-drag coefficient.
                continue;
            }
            if (!s.data[delta][re].emplace(cl,cd).second)
                throw std::runtime_error("Duplicate profile lift sample");
        }
        if (strips.empty()) throw std::runtime_error("Empty profile drag table");
        for (const auto &strip: strips) {
            double sum=0.; for (const auto &s: strip.second) sum+=s.second.weight;
            if (std::abs(sum-1.)>1.e-10) throw std::runtime_error("Profile weights do not sum to one");
        }
    }
    template<class Angle>
    double drag(int sheet,int strip,double re,double cl,Angle angle,bool &clipped) const {
        auto found=strips.find({sheet,strip});
        if (found==strips.end()) throw std::runtime_error("Missing strip profile drag");
        double result=0.;
        for (const auto &part: found->second) {
            const Section &s=part.second;
            const double delta=s.group ? s.gain*angle(s.group) : 0.;
            result += s.weight*interpolate(s.data,delta,[&](const ReynoldsGrid &rg) {
                return interpolate(rg,re,[&](const Curve &curve) {
                    if (curve.empty()) throw std::runtime_error("Required Reynolds polar has no converged points");
                    return interpolate(curve,cl,[](double cd){return cd;},clipped);
                },clipped);
            },clipped);
        }
        return result;
    }
};
}
#endif
