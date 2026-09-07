//
// This file is released under the terms of the NASA Open Source Agreement (NOSA)
// version 1.3 as detailed in the LICENSE file which accompanies this software.
//

#include "main.h"
#include "VehicleMgr.h"
#include "GuiInterface.h"
#include "common.h"
#include "MainThreadIDMgr.h"

using namespace vsp;
int main( int argc, char** argv )
{
    // Set up MainThreadID if this is entry point.
    MainThreadIDMgr.getInstance();

    //==== Get Vehicle Ptr ====//
    Vehicle* vPtr = VehicleMgr.GetVehicle();

    vPtr->CheckForVSPAERO( vPtr->GetVSPAEROPath() );
    vPtr->CheckForHelp( vPtr->GetHelpPath() );

    int ret;
    if ( batchMode( argc, argv, vPtr, ret ) )
    {
        vsp_exit( ret );
    }

    //==== Init Gui ====//
    GuiInterface::getInstance().InitGUI( vPtr );

    // This custom build does not report usage or check upstream releases.

    //==== Run Test Scripts =====//
#ifndef NDEBUG
    vPtr->RunTestScripts();
#endif

    //==== Start Gui - FLTK Now Control Process ====//
    GuiInterface::getInstance().StartGUI();
    return 0;
}
