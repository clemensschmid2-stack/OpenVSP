// Optional read-only visualization snapshots for accepted State Sweep rows.
// NASA Open Source Agreement 1.3; see LICENSE.
#ifndef VDS_WAKE_ARCHIVE_H
#define VDS_WAKE_ARCHIVE_H
#include <vector>
#include <string>
#include <map>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <cmath>

class WakeArchive {
    FILE *file_ = NULL;
    uint64_t chunk_ = UINT64_MAX, start_;
    std::vector<unsigned char> geometry_, wake_;
    static void integer(std::vector<unsigned char>& out, uint64_t n) {
        for (int i=0; i<8; ++i) out.push_back((unsigned char)(n >> (8*i)));
    }
    static void real(std::vector<unsigned char>& out, double value) {
        if (!std::isfinite(value)) fail("Non-finite wake archive coordinate");
        uint64_t bits; memcpy(&bits, &value, 8); integer(out,bits);
    }
    static void fail(const char *message) { fprintf(stderr,"%s\n",message); exit(1); }
    void write(const std::vector<unsigned char>& data) {
        if (!data.empty() && fwrite(data.data(),1,data.size(),file_) != data.size())
            fail("Could not write wake archive (check available disk space)");
    }
public:
    explicit WakeArchive(uint64_t start): start_(start) {}
    ~WakeArchive() { if (file_) fclose(file_); }
    template<class Solver> void save(Solver& solver, const char *directory,
                                     uint64_t row, uint64_t chunkSize) {
        auto& geom = solver.VSPGeom();
        auto& grid = geom.Grid();
        std::vector<unsigned char> geometry, wake;
        // Grid(0) also contains appended wake panels. Archive only the vehicle
        // surface here; trailing-vortex polylines are stored separately below.
        std::vector<int> nodeMap(grid.NumberOfNodes()+1,-1);
        uint64_t triangles=0, nodes=0;
        for (int i=1;i<=grid.NumberOfLoops();++i) {
            auto& loop=grid.LoopList(i);
            if (loop.SurfaceID()==0) continue;
            triangles+=loop.NumberOfNodes()-2;
            for (int j=1;j<=loop.NumberOfNodes();++j) nodeMap[loop.Node(j)]=0;
        }
        for (int i=1;i<=grid.NumberOfNodes();++i) if (nodeMap[i]==0) nodeMap[i]=(int)nodes++;
        // Recent VSPGEOM versions supply tagged loops but no polygon nodes.
        // Extract each boundary edge without changing the solver's mesh.
        std::vector<unsigned char> controls;
        uint64_t controlLines=0;
        for (int i=1;i<=geom.NumberOfControlSurfaces();++i) {
            auto& surface=geom.ControlSurface(i);
            std::map<std::pair<int,int>,int> edges;
            for (int j=1;j<=surface.NumberOfLoops();++j) {
                auto& loop=grid.LoopList(surface.LoopList(j));
                for (int k=1;k<=loop.NumberOfNodes();++k) {
                    int a=loop.Node(k), b=loop.Node(k%loop.NumberOfNodes()+1);
                    if (a>b) std::swap(a,b);
                    edges[std::make_pair(a,b)]++;
                }
            }
            for (const auto& edge: edges) if (edge.second==1) {
                ++controlLines; integer(controls,2);
                for (int node: {edge.first.first,edge.first.second}) {
                    double xyz[3]={double(grid.NodeList(node).x()),
                                   double(grid.NodeList(node).y()), double(grid.NodeList(node).z())};
                    surface.RotateXYZPoint(xyz);
                    for (int k=0;k<3;++k) real(controls,xyz[k]);
                }
            }
        }
        integer(geometry,nodes); integer(geometry,triangles); integer(geometry,controlLines);
        for (int i=1;i<=grid.NumberOfNodes();++i) if (nodeMap[i]>=0) {
            real(geometry,double(grid.NodeList(i).x()));
            real(geometry,double(grid.NodeList(i).y()));
            real(geometry,double(grid.NodeList(i).z()));
        }
        for (int i=1;i<=grid.NumberOfLoops();++i) {
            auto& loop=grid.LoopList(i);
            if (loop.SurfaceID()==0) continue;
            for (int j=2;j<loop.NumberOfNodes();++j) {
                integer(geometry,nodeMap[loop.Node(1)]);
                integer(geometry,nodeMap[loop.Node(j)]);
                integer(geometry,nodeMap[loop.Node(j+1)]);
            }
        }
        geometry.insert(geometry.end(),controls.begin(),controls.end());
        uint64_t lines=0;
        for (int k=1;k<=geom.NumberOfVortexSheets();++k)
            lines+=geom.VortexSheet(k).NumberOfTrailingVortices();
        integer(wake,lines);
        for (int k=1;k<=geom.NumberOfVortexSheets();++k) {
            auto& sheet=geom.VortexSheet(k);
            for (int i=1;i<=sheet.NumberOfTrailingVortices();++i) {
                auto& trail=sheet.TrailingVortex(i);
                int n=trail.TE_Node_Region_Is_Concave() ? 1 : trail.NumberOfNodes();
                integer(wake,n);
                for (int j=1;j<=n;++j) {
                    real(wake,double(trail.WakeNodeX(j)));
                    real(wake,double(trail.WakeNodeY(j)));
                    real(wake,double(trail.WakeNodeZ(j)));
                }
            }
        }
        if (!file_ || chunk_ != row/chunkSize) {
            if (file_ && fclose(file_) != 0) fail("Could not close wake archive");
            char path[4096];
            snprintf(path,sizeof(path),"%s/wakes-%012llu-%012llu.bin",directory,
                     (unsigned long long)start_,(unsigned long long)(row/chunkSize));
            file_=fopen(path,"wb");
            if (!file_) fail("Could not open wake archive");
            if (fwrite("VDSWAK01",1,8,file_) != 8) fail("Could not write wake archive header");
            chunk_=row/chunkSize; geometry_.clear(); wake_.clear();
        }
        bool newGeometry=geometry!=geometry_, newWake=wake!=wake_;
        std::vector<unsigned char> header;
        integer(header,row);
        integer(header,newGeometry ? geometry.size() : 0);
        integer(header,newWake ? wake.size() : 0);
        write(header);
        if (newGeometry) write(geometry);
        if (newWake) write(wake);
        if (fwrite("ENDW",1,4,file_) != 4 || fflush(file_) != 0)
            fail("Could not flush wake archive");
        geometry_.swap(geometry); wake_.swap(wake);
    }
};
#endif
