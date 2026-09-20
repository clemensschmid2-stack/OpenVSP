#include "../../src/vsp_aero/Solver/StateSweepCheckpoint.H"
#include <iostream>

int main(int argc, char **argv)
{
    if ( argc != 2 ) return 2;
    unsigned long long next;
    while ( std::cin >> next ) {
        StateSweepWriteCheckpoint(argv[1],0xabc,next,1000);
        std::cout << "published " << next << std::endl;
    }
    return 0;
}
