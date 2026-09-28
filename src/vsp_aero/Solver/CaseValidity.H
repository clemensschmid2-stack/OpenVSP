// Numerical validity checks, independent of aerodynamic convergence tolerances.
#ifndef VSPAERO_CASE_VALIDITY_H
#define VSPAERO_CASE_VALIDITY_H

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <vector>

namespace vspaero_validity {

// Diagnose the supplied cell; never weld nodes or alter the user's geometry.
// Scale locally so validity does not depend on the chosen length unit.
inline const char *cellError(const std::vector<std::array<double, 3> > &points)
{
    if (points.size() < 3) return "fewer than three nodes";
    double scale = 0.;
    for (size_t i = 0; i < points.size(); ++i) {
        for (int axis = 0; axis < 3; ++axis) {
            if (!std::isfinite(points[i][axis])) return "nonfinite node coordinate";
            const double edge = points[(i + 1) % points.size()][axis] - points[i][axis];
            if (!std::isfinite(edge)) return "nonfinite edge length";
            scale = (std::max)(scale, std::abs(edge));
        }
    }
    if (!(scale > 0.)) return "zero-length edges";
    for (size_t i = 0; i < points.size(); ++i) {
        double length2 = 0.;
        for (int axis = 0; axis < 3; ++axis) {
            const double edge = (points[(i + 1) % points.size()][axis] - points[i][axis]) / scale;
            length2 += edge * edge;
        }
        if (!(length2 > 0.)) return "zero-length edge";
    }
    // Triangulations, rather than a polygon's fan, define the solver cells.
    // Polygon concavity is valid; only test triangle area here.
    if (points.size() == 3) {
        double a[3], b[3], cross[3];
        for (int axis = 0; axis < 3; ++axis) {
            a[axis] = (points[1][axis] - points[0][axis]) / scale;
            b[axis] = (points[2][axis] - points[0][axis]) / scale;
        }
        cross[0] = a[1]*b[2] - a[2]*b[1];
        cross[1] = a[2]*b[0] - a[0]*b[2];
        cross[2] = a[0]*b[1] - a[1]*b[0];
        const double area2 = std::hypot(cross[0], cross[1], cross[2]);
        if (!std::isfinite(area2) || area2 <= 32.*std::numeric_limits<double>::epsilon())
            return "zero or roundoff-degenerate triangle area";
    }
    return NULL;
}

inline bool finiteValues(const double *values, size_t count)
{
    for (size_t i = 0; i < count; ++i)
        if (!std::isfinite(values[i])) return false;
    return true;
}

inline double localReynolds(double referenceRe, double localSpeed,
                            double referenceSpeed, double chord, double referenceChord)
{
    return referenceRe * (localSpeed / referenceSpeed) * (chord / referenceChord);
}

// Reference-Re derivative of the empirical branch's max(2, Re_local).
inline double localReynoldsReferenceDerivative(double referenceRe, double localSpeed,
                                               double referenceSpeed, double chord, double referenceChord)
{
    return localReynolds(referenceRe, localSpeed, referenceSpeed, chord, referenceChord) > 2.
         ? (localSpeed / referenceSpeed) * (chord / referenceChord) : 0.;
}

} // namespace vspaero_validity
#endif
