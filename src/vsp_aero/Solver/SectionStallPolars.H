// Approved signed section limits, using the shared section/Re/flap interpolator.
#ifndef SECTION_STALL_POLARS_H
#define SECTION_STALL_POLARS_H
#include "SectionProfileDrag.H"
namespace vds_stall {
class Table : public vds_profile::Table {
public:
    void load(const std::string &path, int groups) {
        vds_profile::Table::load(path, groups);
        for (const auto &strip : strips)
            for (const auto &part : strip.second)
                for (const auto &delta : part.second.data)
                    for (const auto &re : delta.second) {
                        const auto &curve = re.second;
                        if (curve.size()!=2 || !curve.count(-1.) || !curve.count(1.) ||
                            curve.at(-1.)<=0. || curve.at(1.)<=0.)
                            throw std::runtime_error("Stall polar requires positive magnitudes for both lift signs");
                    }
    }
    template<class Angle>
    double limit(int sheet,int strip,double re,double signedLift,Angle angle,bool &clipped) const {
        return drag(sheet,strip,re,signedLift>=0. ? 1. : -1.,angle,clipped);
    }
};
}
#endif
