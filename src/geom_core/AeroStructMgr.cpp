//
// This file is released under the terms of the NASA Open Source Agreement (NOSA)
// version 1.3 as detailed in the LICENSE file which accompanies this software.
//
//
// Rob McDonald
//////////////////////////////////////////////////////////////////////

#ifdef WIN32
#undef _HAS_STD_BYTE
#define _HAS_STD_BYTE 0
#endif

#include <filesystem>
#include <cstdlib>

#include "AeroStructMgr.h"
#include "Vehicle.h"
#include "MeshGeom.h"
#include "WingGeom.h"
#include "FileUtil.h"
#include "VSPAEROMgr.h"
#include "StructureMgr.h"

#ifdef WIN32
namespace
{
// Dependency discovery must not execute optional programs or share scratch
// files between OpenVSP instances. In particular, the old temp.txt probe could
// be deleted by another worker before fopen(), followed by fseek(nullptr).
bool ExecutableOnPath( const string & executable )
{
    const char *raw_path = std::getenv( "PATH" );
    if ( !raw_path )
    {
        return false;
    }
    string path_list( raw_path );
    size_t start = 0;
    do
    {
        size_t end = path_list.find( ';', start );
        string directory = path_list.substr( start, end - start );
        if ( directory.size() >= 2 && directory.front() == '"' && directory.back() == '"' )
        {
            directory = directory.substr( 1, directory.size() - 2 );
        }
        std::error_code error;
        if ( std::filesystem::is_regular_file( std::filesystem::path( directory ) / executable, error ) )
        {
            return true;
        }
        if ( end == string::npos )
        {
            break;
        }
        start = end + 1;
    } while ( start <= path_list.size() );
    return false;
}
}
#endif

AeroStructSingleton::AeroStructSingleton() : ParmContainer()
{
    m_Name = "AeroStructSettings";

    m_DynPress.Init( "DynamicPressure", "AeroStructure", this, 0, 0, 1e12 );

    m_CurrStructAssyIndex.Init( "CurrStructAssyIndex", "AeroStructure", this, -1, -1, 1e12 );
}

xmlNodePtr AeroStructSingleton::EncodeXml( xmlNodePtr & node )
{
    xmlNodePtr AeroStructnode = xmlNewChild( node, nullptr, BAD_CAST"AeroStructMgr", nullptr );

    ParmContainer::EncodeXml( AeroStructnode );


    return AeroStructnode;
}

xmlNodePtr AeroStructSingleton::DecodeXml( xmlNodePtr & node )
{
    xmlNodePtr AeroStructnode = XmlUtil::GetNode( node, "AeroStructMgr", 0 );

    if ( AeroStructnode )
    {
        ParmContainer::DecodeXml( AeroStructnode );
    }

    return AeroStructnode;
}

void AeroStructSingleton::Update()
{
    VSPAEROMgr.UpdateFilenames();

    m_ADBFile = VSPAEROMgr.m_AdbFile;
    m_ADBFileFound = FileExist( m_ADBFile );

    m_StructAssyFlagVec.clear();
    m_StructAssyIDVec.clear();

    vector< FeaStructure* > structVec = StructureMgr.GetAllFeaStructs();
    if ( structVec.size() > 0 )
    {
        for ( int i = 0; i < (int)structVec.size(); i++ )
        {
            m_StructAssyFlagVec.push_back( true );
            m_StructAssyIDVec.push_back( structVec[i]->GetID() );
        }
    }

    vector < FeaAssembly* > assyVec = StructureMgr.GetFeaAssemblyVec();
    if ( assyVec.size() > 0 )
    {
        for ( int i = 0; i < (int)assyVec.size(); i++ )
        {
            m_StructAssyFlagVec.push_back( false );
            m_StructAssyIDVec.push_back( assyVec[i]->GetID() );
        }
    }

    if ( m_StructAssyFlagVec.size() == 0 || ( m_CurrStructAssyIndex() >= m_StructAssyFlagVec.size() ) )
    {
        m_CurrStructAssyIndex.Set( -1 );
    }



    m_FEAMeshFile = string();
    m_FEAMeshFileFound = false;

    if ( m_CurrStructAssyIndex() >= 0 ) // Non-negative test is sufficient because of tests above.
    {
        string id = m_StructAssyIDVec[ m_CurrStructAssyIndex() ];

        if ( m_StructAssyFlagVec[ m_CurrStructAssyIndex() ] )                // Currently a structure
        {
            FeaStructure *fea_struct = StructureMgr.GetFeaStruct( id );
            if ( fea_struct )
            {
                vector < string > fnames = fea_struct->GetStructSettingsPtr()->GetExportFileNames();
                m_FEAMeshFile = fnames[ vsp::FEA_CALCULIX_FILE_NAME ];
            }
            m_FEAMeshFileFound = FileExist( m_FEAMeshFile );
        }
        else                                                                 // Currently an assembly.
        {
            FeaAssembly *fea_assy = StructureMgr.GetFeaAssembly( id );

            if ( fea_assy )
            {
                vector < string > fnames = fea_assy->m_AssemblySettings.GetExportFileNames();
                m_FEAMeshFile = fnames[ vsp::FEA_CALCULIX_FILE_NAME ];
            }
            m_FEAMeshFileFound = FileExist( m_FEAMeshFile );
        }
    }


    m_FEAInputFile = string();
    if ( m_FEAMeshFileFound )
    {
        m_FEAInputFile = GetBasename( m_FEAMeshFile ) + ".static.inp";
    }
    m_FEAInputFileFound = FileExist( m_FEAInputFile );


    m_FEASolutionFile = string();
    if ( m_FEAInputFileFound )
    {
        m_FEASolutionFile = GetBasename( m_FEAInputFile ) + ".frd";
    }
    m_FEASolutionFileFound = FileExist( m_FEASolutionFile );


}

void AeroStructSingleton::LoadDrawObjs( vector< DrawObj* > &draw_obj_vec )
{
    Vehicle *veh = VehicleMgr.GetVehicle();
    if ( !veh )
    {
        assert( false );
        return;
    }


}

void AeroStructSingleton::FindCCX( const string & path )
{
    m_CalculiXFound = false;
    m_CalculiXCmd = "ccx";
    m_CalculiXPath = string();

    // Check specific location
#ifdef WIN32
    if ( CheckForFile( path, "ccx.exe" ) )
#else
    if ( CheckForFile( path, "ccx" ) )
#endif
    {
        m_CalculiXFound = true;
        m_CalculiXPath = path;
    }
    else // Check for ccx in path
    {
#ifdef WIN32
        if ( ExecutableOnPath( "ccx.exe" ) )
#else
        if ( !system( "which ccx > /dev/null 2>&1" ))
#endif
        {
            m_CalculiXFound = true;
        }
    }
}

void AeroStructSingleton::FindCGX( const string & path )
{
    m_CGXFound = false;
    m_CGXCmd = "cgx";
    m_CGXPath = string();

    // Check specific location
#ifdef WIN32
    if ( CheckForFile( path, "cgx.exe" ) )
#else
    if ( CheckForFile( path, "cgx" ) )
#endif
    {
        m_CGXFound = true;
        m_CGXPath = path;
    }
    else // Check for ccx in path
    {
#ifdef WIN32
        if ( ExecutableOnPath( "cgx.exe" ) )
#else
        if ( !system( "which cgx > /dev/null 2>&1" ))
#endif
        {
            m_CGXFound = true;
        }
    }
}

void AeroStructSingleton::TransferLoads( FILE * logFile )
{
    Vehicle* veh = VehicleMgr.GetVehicle();
    if ( !veh )
    {
        return;
    }

    //====== Send command to be executed by the system at the command prompt ======//
    vector<string> args;
    char str[512];

    args.push_back( "-interp" );

    args.push_back( GetBasename( m_ADBFile ) ); // adb base name.

    args.push_back( GetBasename( m_FEAMeshFile ) ); // FEA mesh base name.

    args.push_back( "-dynp" );
    snprintf( str, sizeof( str ), "%f", m_DynPress() );
    args.push_back( string( str ) );


    string cmdStr = ProcessUtil::PrettyCmd( veh->GetVSPAEROPath(), veh->GetLOADSCmd(), args );
    if( logFile )
    {
        fprintf( logFile, "%s", cmdStr.c_str() );
    }
    else
    {
        MessageData data;
        data.m_String = "AeroStructMessage";
        data.m_StringVec.push_back( cmdStr );
        MessageMgr::getInstance().Send( "ScreenMgr", nullptr, data );
    }

    m_LoadsProcess.ForkCmd( veh->GetVSPAEROPath(), veh->GetLOADSCmd(), args );

    // ==== MonitorSolverProcess ==== //
    MonitorProcess( logFile, &m_LoadsProcess, "AeroStructMessage" );
}

void AeroStructSingleton::ComputeStructure( FILE * logFile )
{
    Vehicle* veh = VehicleMgr.GetVehicle();
    if ( !veh )
    {
        return;
    }

    //====== Send command to be executed by the system at the command prompt ======//
    vector<string> args;

    args.push_back( GetBasename( m_FEAInputFile ) );


    string cmdStr = ProcessUtil::PrettyCmd( m_CalculiXPath, m_CalculiXCmd, args );
    if( logFile )
    {
        fprintf( logFile, "%s", cmdStr.c_str() );
    }
    else
    {
        MessageData data;
        data.m_String = "AeroStructMessage";
        data.m_StringVec.push_back( cmdStr );
        MessageMgr::getInstance().Send( "ScreenMgr", nullptr, data );
    }

    m_CalculiXProcess.ForkCmd( m_CalculiXPath, m_CalculiXCmd, args );


    // ==== MonitorSolverProcess ==== //
    MonitorProcess( logFile, &m_CalculiXProcess, "AeroStructMessage" );

}
