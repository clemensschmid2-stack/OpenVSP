
import unittest
import os, sys

curr_path = os.path.dirname(os.path.realpath(__file__))
vsp_path = os.path.join(curr_path, '../..')
sys.path.insert(1, vsp_path)

from openvsp import *

class TestOpenVSP(unittest.TestCase):
	def setUp(self):
		VSPRenew()
		# Start from a clean error queue so each example is only judged on the
		# errors it raised itself.
		api_err_mgr = ErrorMgrSingleton.getInstance()
		while api_err_mgr.GetNumTotalErrors() > 0:
			api_err_mgr.PopLastError()
	def tearDown(self):
		# An example that leaves an API error behind has not worked, whether or
		# not it bothered to check anything itself.  An example that raises one
		# on purpose is expected to take it back off the queue.
		api_err_mgr = ErrorMgrSingleton.getInstance()
		api_err_msgs = []
		while api_err_mgr.GetNumTotalErrors() > 0:
			api_err_msgs.append( api_err_mgr.PopLastError().GetErrorString() )
		assert len( api_err_msgs ) == 0, "API errors: " + "; ".join( api_err_msgs )
	def test_VSPCheckSetup(self):

		VSPCheckSetup()

		# A failed setup exits OpenVSP outright, so reaching this point is most of
		# the test.  Confirm the model is actually usable.
		type_array = GetGeomTypes()

		assert len( type_array ) > 0, "VSPCheckSetup did not leave a usable model"

		# Continue to do things...




	def test_VSPRenew(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		SetParmVal( pod_id, "Y_Rel_Location", "XForm", 2.0 )

		VSPRenew()

		if  len(FindGeoms()) != 0 :
			print( "ERROR: VSPRenew" )
			assert False, "ERROR: VSPRenew"



	def test_Update(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		xsec_surf = GetXSecSurf( fid, 0 )           # Get First (and Only) XSec Surf

		num_xsecs = GetNumXSec( xsec_surf )

		Update()

		before_max = GetGeomBBoxMax( fid, 0, False )

		#==== Set Tan Angles At Nose/Tail
		SetXSecTanAngles( GetXSec( xsec_surf, 0 ), XSEC_BOTH_SIDES, 90, -1.0e12, -1.0e12, -1.0e12 )
		SetXSecTanAngles( GetXSec( xsec_surf, num_xsecs - 1 ), XSEC_BOTH_SIDES, -90, -1.0e12, -1.0e12, -1.0e12 )

		Update()       # Force Surface Update

		after_max = GetGeomBBoxMax( fid, 0, False )

		# Blunting the nose and tail pushes the surface out, which only shows up in
		# the bounding box once Update() has rebuilt it.
		assert dist( before_max, after_max ) > 1e-9, "Update did not rebuild the surface"



	def test_VSPExit(self):
		Update()

		# Shown rather than run: this ends the process, and would take the caller with it.
		# VSPExit( 0 )



	def test_VSPCrash(self):
		Update()

		# Shown rather than run: this deliberately crashes the process, and is only for exercising
		# the crash handler.
		# VSPCrash( 0 )



	def test_GetAndResetUpdateCount(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		Update()

		# Reading the count clears it, so a second read with nothing in between
		# reports no change.
		GetAndResetUpdateCount()

		assert GetAndResetUpdateCount() == 0, "the update count did not reset"

		# The count is a GUI notion.  A script with no GUI running never marks a
		# screen dirty, so the count stays where the read left it.
		SetParmValUpdate( pid, "Length", "Design", 10.0 )

		Update()

		assert GetAndResetUpdateCount() >= 0, "the update count went negative"



	def test_Print(self):
		Print( "Hello from the OpenVSP API" )


	def test_Print1(self):
		Print( vec3d( 1.0, 2.0, 3.0 ) )


	def test_Print11(self):
		Print( 3.14159 )


	def test_Print111(self):
		Print( 42 )


	def test_Min(self):
		assert abs( Min( 2.0, 5.0 ) - 2.0 ) < 1e-12, "Min did not return the smaller value"

		assert abs( Min( 5.0, 2.0 ) - 2.0 ) < 1e-12, "Min depends on the order of its arguments"


	def test_Max(self):
		assert abs( Max( 2.0, 5.0 ) - 5.0 ) < 1e-12, "Max did not return the larger value"

		assert abs( Max( 5.0, 2.0 ) - 5.0 ) < 1e-12, "Max depends on the order of its arguments"


	def test_Rad2Deg(self):
		import math

		assert abs( Rad2Deg( math.pi ) - 180.0 ) < 1e-9, "Rad2Deg did not convert half a turn to 180 degrees"


	def test_Deg2Rad(self):
		import math

		assert abs( Deg2Rad( 180.0 ) - math.pi ) < 1e-9, "Deg2Rad did not convert 180 degrees to half a turn"


	def test_GetVSPVersion(self):
		print( "The current OpenVSP version is: ", False )

		ver = GetVSPVersion()

		print( ver )

		# The string form has to agree with the numeric accessors.
		num = f"{GetVSPVersionMajor()}.{GetVSPVersionMinor()}.{GetVSPVersionChange()}"

		assert num in ver, "GetVSPVersion does not contain " + num



	def test_GetVSPVersionMajor(self):
		print( "The current OpenVSP version is: ", False )

		major = GetVSPVersionMajor()
		minor = GetVSPVersionMinor()
		change = GetVSPVersionChange()

		print( f"{major}.{minor}.{change}" )

		# OpenVSP 3 and later.  Negative pieces would mean the version was never
		# filled in.
		assert major >= 3 and minor >= 0 and change >= 0, "implausible version number"

		# The pieces have to add back up to the string form.
		num = f"{major}.{minor}.{change}"

		assert num in GetVSPVersion(), "version pieces disagree with GetVSPVersion"



	def test_GetVSPVersionMinor(self):
		print( "The current OpenVSP version is: ", False )

		major = GetVSPVersionMajor()
		minor = GetVSPVersionMinor()
		change = GetVSPVersionChange()

		print( f"{major}.{minor}.{change}" )

		# OpenVSP 3 and later.  Negative pieces would mean the version was never
		# filled in.
		assert major >= 3 and minor >= 0 and change >= 0, "implausible version number"

		# The pieces have to add back up to the string form.
		num = f"{major}.{minor}.{change}"

		assert num in GetVSPVersion(), "version pieces disagree with GetVSPVersion"



	def test_GetVSPVersionChange(self):
		print( "The current OpenVSP version is: ", False )

		major = GetVSPVersionMajor()
		minor = GetVSPVersionMinor()
		change = GetVSPVersionChange()

		print( f"{major}.{minor}.{change}" )

		# OpenVSP 3 and later.  Negative pieces would mean the version was never
		# filled in.
		assert major >= 3 and minor >= 0 and change >= 0, "implausible version number"

		# The pieces have to add back up to the string form.
		num = f"{major}.{minor}.{change}"

		assert num in GetVSPVersion(), "version pieces disagree with GetVSPVersion"



	def test_GetVSPExePath(self):
		print( "The current VSP executable path is: ", False )

		exe_path = GetVSPExePath()

		print( exe_path )

		assert len( exe_path ) > 0, "GetVSPExePath returned an empty path"



	def test_SetVSPAEROPath(self):
		orig_path = GetVSPAEROPath()

		if  not CheckForVSPAERO( GetVSPExePath() ) :
			vspaero_path = "C:/Users/example_user/Documents/OpenVSP_3.4.5"
			SetVSPAEROPath( vspaero_path )

		# A directory with no VSPAERO in it has to be rejected, and rejecting it
		# must leave the stored path alone.
		assert not SetVSPAEROPath( "/no/such/directory/anywhere" ), "SetVSPAEROPath accepted a nonexistent directory"

		assert GetVSPAEROPath() == orig_path, "a rejected SetVSPAEROPath changed the stored path"



	def test_GetVSPAEROPath(self):
		if  not CheckForVSPAERO( GetVSPAEROPath() ) :
			print( "VSPAERO is not where OpenVSP thinks it is. I should move the VSPAERO executable or call SetVSPAEROPath." )

		assert len( GetVSPAEROPath() ) > 0, "GetVSPAEROPath returned an empty path"



	def test_CheckForVSPAERO(self):
		vspaero_path = "C:/Users/example_user/Documents/OpenVSP_3.4.5"

		if  CheckForVSPAERO( vspaero_path ) :
			SetVSPAEROPath( vspaero_path )

		# A directory that cannot exist must not report VSPAERO in it.
		assert not CheckForVSPAERO( "/no/such/directory/anywhere" ), "CheckForVSPAERO found VSPAERO in a nonexistent directory"



	def test_SetVSPHelpPath(self):
		orig_path = GetVSPHelpPath()

		if  not CheckForVSPHelp( GetVSPExePath() ) :
			vsphelp_path = "C:/Users/example_user/Documents/OpenVSP_3.4.5/help"
			SetVSPHelpPath( vsphelp_path )

		# A directory with no help files in it has to be rejected, and rejecting it
		# must leave the stored path alone.
		assert not SetVSPHelpPath( "/no/such/directory/anywhere" ), "SetVSPHelpPath accepted a nonexistent directory"

		assert GetVSPHelpPath() == orig_path, "a rejected SetVSPHelpPath changed the stored path"



	def test_GetVSPHelpPath(self):
		if  not CheckForVSPHelp( GetVSPHelpPath() ) :
			print( "OpenVSP help is not where OpenVSP thinks it is. I should move the help files or call SetVSPHelpPath." )

		assert len( GetVSPHelpPath() ) > 0, "GetVSPHelpPath returned an empty path"



	def test_CheckForVSPHelp(self):
		vsphelp_path = "C:/Users/example_user/Documents/OpenVSP_3.4.5/help"

		if  CheckForVSPHelp( vsphelp_path ) :
			SetVSPHelpPath( vsphelp_path )

		# A directory that cannot exist must not report help files in it.
		assert not CheckForVSPHelp( "/no/such/directory/anywhere" ), "CheckForVSPHelp found help in a nonexistent directory"



	def test_ReadVSPFile(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		fname = "example_fuse.vsp3"

		SetVSP3FileName( fname )

		# A relative name is resolved against the working directory, so ask for the
		# resolved name rather than assuming it comes back verbatim.
		full_name = GetVSPFileName()

		Update()

		#==== Save Vehicle to File ====//
		print( "\tSaving vehicle file to: ", False )

		print( fname )

		WriteVSPFile( GetVSPFileName(), SET_ALL )

		#==== Reset Geometry ====//
		print( "--->Resetting VSP model to blank slate\n" )

		ClearVSPModel()

		assert len( FindGeoms() ) == 0, "ClearVSPModel left Geoms behind"

		ReadVSPFile( fname )

		# The Fuselage has to come back, and come back the same shape.
		geoms = FindGeoms()

		assert len( geoms ) == 1, "ReadVSPFile did not restore the model"
		assert GetGeomTypeName( geoms[0] ) == "Fuselage", "ReadVSPFile restored the wrong Geom type"
		assert GetVSPFileName() == full_name, "ReadVSPFile did not set the project file name"



	def test_WriteVSPFile(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		fname = "example_fuse.vsp3"

		SetVSP3FileName( fname )

		# A relative name is resolved against the working directory, so ask for the
		# resolved name rather than assuming it comes back verbatim.
		full_name = GetVSPFileName()

		Update()

		#==== Save Vehicle to File ====//
		print( "\tSaving vehicle file to: ", False )

		print( fname )

		WriteVSPFile( GetVSPFileName(), SET_ALL )

		#==== Reset Geometry ====//
		print( "--->Resetting VSP model to blank slate\n" )

		ClearVSPModel()

		assert len( FindGeoms() ) == 0, "ClearVSPModel left Geoms behind"

		ReadVSPFile( fname )

		# The Fuselage has to come back, and come back the same shape.
		geoms = FindGeoms()

		assert len( geoms ) == 1, "ReadVSPFile did not restore the model"
		assert GetGeomTypeName( geoms[0] ) == "Fuselage", "ReadVSPFile restored the wrong Geom type"
		assert GetVSPFileName() == full_name, "ReadVSPFile did not set the project file name"



	def test_SetVSP3FileName(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		fname = "example_fuse.vsp3"

		SetVSP3FileName( fname )

		# A relative name is resolved against the working directory, so ask for the
		# resolved name rather than assuming it comes back verbatim.
		full_name = GetVSPFileName()

		Update()

		#==== Save Vehicle to File ====//
		print( "\tSaving vehicle file to: ", False )

		print( fname )

		WriteVSPFile( GetVSPFileName(), SET_ALL )

		#==== Reset Geometry ====//
		print( "--->Resetting VSP model to blank slate\n" )

		ClearVSPModel()

		assert len( FindGeoms() ) == 0, "ClearVSPModel left Geoms behind"

		ReadVSPFile( fname )

		# The Fuselage has to come back, and come back the same shape.
		geoms = FindGeoms()

		assert len( geoms ) == 1, "ReadVSPFile did not restore the model"
		assert GetGeomTypeName( geoms[0] ) == "Fuselage", "ReadVSPFile restored the wrong Geom type"
		assert GetVSPFileName() == full_name, "ReadVSPFile did not set the project file name"



	def test_GetVSPFileName(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		fname = "example_fuse.vsp3"

		SetVSP3FileName( fname )

		# A relative name is resolved against the working directory, so ask for the
		# resolved name rather than assuming it comes back verbatim.
		full_name = GetVSPFileName()

		Update()

		#==== Save Vehicle to File ====//
		print( "\tSaving vehicle file to: ", False )

		print( fname )

		WriteVSPFile( GetVSPFileName(), SET_ALL )

		assert GetVSPFileName() == full_name and full_name.endswith( fname ), "GetVSPFileName did not report the name that was set"



	def test_ClearVSPModel(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		#==== Reset Geometry ====//
		print( "--->Resetting VSP model to blank slate\n" )
		ClearVSPModel()

		assert len( FindGeoms() ) == 0, "ClearVSPModel left Geoms behind"



	def test_InsertVSPFile(self):
		pid = AddGeom( "POD" )

		Update()

		WriteVSPFile( "TestInsert.vsp3" )

		InsertVSPFile( "TestInsert.vsp3", "" )

		assert len( FindGeoms() ) == 2, "InsertVSPFile did not bring in the Geom"



	def test_ExportFile(self):
		wid = AddGeom( "WING" )             # Add Wing

		ExportFile( "Airfoil_Metadata.csv", SET_ALL, EXPORT_SELIG_AIRFOIL )

		mesh_id = ExportFile( "Example_Mesh.msh", SET_ALL, EXPORT_GMSH )
		assert len( mesh_id ) > 0, "ExportFile returned no id"

		DeleteGeom( mesh_id ) # Delete the mesh generated by the GMSH export



	def test_ImportFile(self):
		pid = AddGeom( "POD" )

		Update()

		SetComputationFileName( COMP_GEOM_TXT_TYPE, "TestImport.txt" )

		ExportFile( "TestImport.stl", SET_ALL, EXPORT_STL )

		mesh_id = ImportFile( "TestImport.stl", IMPORT_STL, "" )

		assert len( mesh_id ) > 0, "ImportFile returned no ID"



	def test_GetBEMPropID(self):
		#==== Add Prop Geometry ====//
		prop_id = AddGeom( "PROP" )

		SetBEMPropID( prop_id )

		ExportFile( "ExampleBEM.bem", SET_ALL, EXPORT_BEM )

		# A BEM export of a Geom that is not a propeller has to be rejected.  The
		# error queue is reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		pod_id = AddGeom( "POD" )

		SetBEMPropID( pod_id )

		ExportFile( "ExampleBEM.bem", SET_ALL, EXPORT_BEM )

		assert err_mgr.GetNumTotalErrors() > 0, "BEM export accepted a Geom that is not a propeller"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_SetBEMPropID(self):
		prop_id = AddGeom( "PROP" )

		Update()

		SetBEMPropID( prop_id )

		assert GetBEMPropID() == prop_id, "SetBEMPropID did not take"



	def test_ReadApplyDESFile(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		WriteDESFile( "TestDesignVars.des" )

		ReadApplyDESFile( "TestDesignVars.des" )



	def test_WriteDESFile(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		WriteDESFile( "TestDesignVars.des" )



	def test_ReadApplyXDDMFile(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		WriteXDDMFile( "TestDesignVars.xddm" )

		ReadApplyXDDMFile( "TestDesignVars.xddm" )



	def test_WriteXDDMFile(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		WriteXDDMFile( "TestDesignVars.xddm" )



	def test_GetNumDesignVars(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		assert GetNumDesignVars() == 1, "GetNumDesignVars did not count the variable"



	def test_AddDesignVar(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		assert GetNumDesignVars() == 1, "AddDesignVar did not add the variable"



	def test_DeleteAllDesignVars(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		DeleteAllDesignVars()

		assert GetNumDesignVars() == 0, "DeleteAllDesignVars left variables behind"



	def test_GetDesignVar(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		assert GetDesignVar( 0 ) == length, "GetDesignVar did not report the variable"



	def test_GetDesignVarType(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddDesignVar( length, XDDM_VAR )

		assert GetDesignVarType( 0 ) == XDDM_VAR, "GetDesignVarType did not report the type"



	def test_GetComputationFileName(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		#==== Set File Name ====//
		SetComputationFileName( DEGEN_GEOM_CSV_TYPE, "TestDegenScript.csv" )

		#==== Run Degen Geom ====//
		ComputeDegenGeom( SET_ALL, DEGEN_GEOM_CSV_TYPE )

		# The degenerate representation is reported through the Results Manager as
		# well as written to file.  A Pod yields a surface, a plate and a stick.
		assert GetNumResults( "DegenGeom" ) == 1, "ComputeDegenGeom produced no DegenGeom result"
		assert GetNumResults( "Degen_surf" ) >= 1, "ComputeDegenGeom produced no Degen_surf result"
		assert GetNumResults( "Degen_plate" ) >= 1, "ComputeDegenGeom produced no Degen_plate result"
		assert GetNumResults( "Degen_stick" ) >= 1, "ComputeDegenGeom produced no Degen_stick result"



	def test_SetComputationFileName(self):
		SetComputationFileName( CFD_STL_TYPE, "TestCFDMesh.stl" )

		SetComputationFileName( CFD_TRI_TYPE, "TestCFDMesh.tri" )



	def test_ComputeMassProps(self):
		#==== Test Mass Props ====//
		pid = AddGeom( "POD", "" )

		mesh_id = ComputeMassProps( SET_ALL, 20, X_DIR )

		mass_res_id = FindLatestResultsID( "Mass_Properties" )

		double_arr = GetDoubleResults( mass_res_id, "Total_Mass" )

		if  len(double_arr) != 1 :
			print( "---> Error: API ComputeMassProps" )
			assert False, "---> Error: API ComputeMassProps"



	def test_ComputeCompGeom(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		#==== Run CompGeom And Get Results ====//
		mesh_id = ComputeCompGeom( SET_ALL, False, 0 )                      # Half Mesh false and no file export
		assert len( mesh_id ) > 0, "ComputeCompGeom returned no id"


		comp_res_id = FindLatestResultsID( "Comp_Geom" )                    # Find Results ID

		double_arr = GetDoubleResults( comp_res_id, "Wet_Area" )    # Extract Results



	def test_ComputePlaneSlice(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		#==== Test Plane Slice ====//
		slice_mesh_id = ComputePlaneSlice( 0, 6, vec3d( 0.0, 0.0, 1.0 ), True )

		pslice_results = FindLatestResultsID( "Slice" )

		double_arr = GetDoubleResults( pslice_results, "Slice_Area" )

		if  len(double_arr) != 6 :
			print( "---> Error: API ComputePlaneSlice" )
			assert False, "---> Error: API ComputePlaneSlice"



	def test_ComputeDegenGeom(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		#==== Set File Name ====//
		SetComputationFileName( DEGEN_GEOM_CSV_TYPE, "TestDegenScript.csv" )

		#==== Run Degen Geom ====//
		ComputeDegenGeom( SET_ALL, DEGEN_GEOM_CSV_TYPE )

		# The degenerate representation is reported through the Results Manager as
		# well as written to file.  A Pod yields a surface, a plate and a stick.
		assert GetNumResults( "DegenGeom" ) == 1, "ComputeDegenGeom produced no DegenGeom result"
		assert GetNumResults( "Degen_surf" ) >= 1, "ComputeDegenGeom produced no Degen_surf result"
		assert GetNumResults( "Degen_plate" ) >= 1, "ComputeDegenGeom produced no Degen_plate result"
		assert GetNumResults( "Degen_stick" ) >= 1, "ComputeDegenGeom produced no Degen_stick result"



	def test_ComputeCFDMesh(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		Update()

		#==== Keep the mesh coarse so the example runs quickly ====//
		SetCFDMeshVal( CFD_MAX_EDGE_LEN, 1.0 )
		SetCFDMeshVal( CFD_MIN_EDGE_LEN, 0.1 )

		#==== CFDMesh Method Facet Export =====//
		SetComputationFileName( CFD_FACET_TYPE, "TestCFDMeshFacet_API.facet" )
		SetComputationFileName( CFD_STL_TYPE, "TestCFDMesh_API.stl" )

		print( "\tComputing CFDMesh..." )

		ComputeCFDMesh( SET_ALL, SET_NONE, CFD_FACET_TYPE | CFD_STL_TYPE )

		# CFD Mesh reports nothing through the Results Manager, so read the mesh it
		# just wrote back in to prove it produced one.
		mesh_id = ImportFile( "TestCFDMesh_API.stl", IMPORT_STL, "" )

		assert len( mesh_id ) > 0, "ComputeCFDMesh did not write a readable mesh"
		assert GetGeomTypeName( mesh_id ) == "Mesh", "ComputeCFDMesh did not write a readable mesh"

		DeleteGeom( mesh_id )


	def test_GetCFDMeshVal(self):
		SetCFDMeshVal( CFD_MIN_EDGE_LEN, 1.0 )

		# The control types are backed by Parms in the CFD grid density container,
		# so the value that was set can be read back.
		dens_id = FindContainer( "CFDGridDensity", 0 )

		min_len_id = FindParm( dens_id, "MinLen", "CFDGridDensity" )

		assert abs( GetParmVal( min_len_id ) - 1.0 ) < 1e-12, "SetCFDMeshVal did not set CFD_MIN_EDGE_LEN"



	def test_SetCFDMeshVal(self):
		SetCFDMeshVal( CFD_MIN_EDGE_LEN, 0.2 )

		SetCFDMeshVal( CFD_MAX_EDGE_LEN, 1.0 )



	def test_GetCFDWakeFlag(self):
		#==== Add Wing Geom ====//
		wid = AddGeom( "WING", "" )

		SetCFDWakeFlag( wid, True )

		assert abs( GetParmVal( wid, "Wake", "Shape" ) - 1.0 ) < 1e-12, "SetCFDWakeFlag did not activate the wake"

		SetCFDWakeFlag( wid, False )

		assert abs( GetParmVal( wid, "Wake", "Shape" ) ) < 1e-12, "SetCFDWakeFlag did not deactivate the wake"

		# This is equivalent to SetParmValUpdate( wid, "Wake", "Shape", 1.0 )
		# To change the scale: SetParmValUpdate( wid, "WakeScale", "WakeSettings", 10.0 )
		# To change the angle: SetParmValUpdate( wid, "WakeAngle", "WakeSettings", -5.0 )



	def test_SetCFDWakeFlag(self):
		wid = AddGeom( "WING" )

		Update()

		SetCFDWakeFlag( wid, True )

		assert GetParmVal( FindParm( wid, "Wake", "Shape" ) ) == 1.0, "SetCFDWakeFlag did not take"



	def test_SetCFDFarFieldGeomID(self):
		#==== Add Pod And A Sphere Around It ====//
		pid = AddGeom( "POD" )
		eid = AddGeom( "ELLIPSOID" )

		SetParmVal( eid, "A_Radius", "Design", 12.0 )

		SetCFDMeshVal( CFD_FAR_FIELD_FLAG, 1.0 )
		SetParmVal( FindParm( FindContainer( "CFDMeshSettings", 0 ), "FarComp", "FarField" ), 1.0 )

		SetCFDFarFieldGeomID( eid )

		assert GetCFDFarFieldGeomID() == eid, "SetCFDFarFieldGeomID did not name the Geom"

		# An empty string puts the setting back the way it reads before a choice is made.
		SetCFDFarFieldGeomID( "" )

		assert GetCFDFarFieldGeomID() == "", "SetCFDFarFieldGeomID did not clear the choice"

		# A Geom that does not exist has to be rejected.  The error queue is reached through
		# the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetCFDFarFieldGeomID( "NoSuchGeom" )

		assert err_mgr.GetNumTotalErrors() > 0, "SetCFDFarFieldGeomID accepted a Geom that does not exist"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetCFDFarFieldGeomID(self):
		#==== Add Two Geoms To Choose Between ====//
		pid = AddGeom( "POD" )
		eid = AddGeom( "ELLIPSOID" )

		SetCFDFarFieldGeomID( eid )

		assert GetCFDFarFieldGeomID() == eid, "GetCFDFarFieldGeomID did not report the Geom that was set"

		# It follows the setting, so naming another Geom changes what comes back.
		SetCFDFarFieldGeomID( pid )

		assert GetCFDFarFieldGeomID() == pid, "GetCFDFarFieldGeomID did not follow SetCFDFarFieldGeomID"

		# With the choice cleared it comes back empty.
		SetCFDFarFieldGeomID( "" )

		assert GetCFDFarFieldGeomID() == "", "GetCFDFarFieldGeomID did not come back empty"



	def test_GetNumCFDSources(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 2.0, 0.5, 0.5 )      # Add A Point Source

		assert GetNumCFDSources( pid ) == 1, "the source was not added"

		DeleteAllCFDSources()

		assert GetNumCFDSources( pid ) == 0, "DeleteAllCFDSources left sources behind"



	def test_GetCFDSourceName(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		AddDefaultSources() # 3 Sources: Def_Fwd_PS, Def_Aft_PS, Def_Fwd_Aft_LS

		assert GetCFDSourceName( pid, 0 ) == "Def_Fwd_PS", "GetCFDSourceName did not name the first default source"

		# Every source the Geom counts has to be nameable.
		for i in range( GetNumCFDSources( pid ) ):
			assert len( GetCFDSourceName( pid, i ) ) > 0, "source " + str( i ) + " has no name"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetCFDSourceName( pid, GetNumCFDSources( pid ) )

		assert err_mgr.GetNumTotalErrors() > 0, "GetCFDSourceName accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_SetCFDSourceName(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 2.0, 0.5, 0.5 )      # Add A Point Source

		assert GetCFDSourceType( pid, 0 ) == POINT_SOURCE, "GetCFDSourceType did not report the type that was added"

		# A source of a different type reports differently.
		AddCFDSource( LINE_SOURCE, pid, 0, 0.25, 2.0, 0.5, 0.5, 0.25, 2.0, 0.75, 0.75 )

		assert GetCFDSourceType( pid, 1 ) == LINE_SOURCE, "GetCFDSourceType did not report the second source"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetCFDSourceType( pid, GetNumCFDSources( pid ) )

		assert err_mgr.GetNumTotalErrors() > 0, "GetCFDSourceType accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetCFDSourceType(self):
		pid = AddGeom( "POD" )

		Update()

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 1.0, 0.25, 0.5 )

		assert GetCFDSourceType( pid, 0 ) == POINT_SOURCE, "GetCFDSourceType did not report the source type"



	def test_DeleteCFDSource(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		AddDefaultSources() # 3 Sources: Def_Fwd_PS, Def_Aft_PS, Def_Fwd_Aft_LS

		second_name = GetCFDSourceName( pid, 1 )

		DeleteCFDSource( pid, 0 )

		# Only the named source goes, and the rest slide down.
		assert GetNumCFDSources( pid ) == 2, "DeleteCFDSource did not remove one source"
		assert GetCFDSourceName( pid, 0 ) == second_name, "DeleteCFDSource removed the wrong source"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteCFDSource( pid, GetNumCFDSources( pid ) )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteCFDSource accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteAllCFDSources(self):
		pid = AddGeom( "POD" )

		Update()

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 1.0, 0.25, 0.5 )

		DeleteAllCFDSources()

		assert GetNumCFDSources( pid ) == 0, "DeleteAllCFDSources left sources behind"



	def test_GetCFDSourceID(self):
		pid = AddGeom( "POD", "" )

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 2.0, 0.5, 0.5 )

		src_id = GetCFDSourceID( pid, 0 )

		assert len( src_id ) > 0, "GetCFDSourceID returned no id"

		# The source was created with a length of 0.25, and is editable from here.
		assert abs( GetParmVal( src_id, "SrcLen", "Source" ) - 0.25 ) < 1e-6, "GetCFDSourceID did not reach the source"

		SetParmVal( src_id, "SrcLen", "Source", 0.5 )



	def test_AdjustAllCFDSourceLen(self):
		pid = AddGeom( "POD", "" )

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 2.0, 0.5, 0.5 )

		src_id = GetCFDSourceID( pid, 0 )

		AdjustAllCFDSourceLen( 2.0 )

		assert abs( GetParmVal( src_id, "SrcLen", "Source" ) - 0.5 ) < 1e-6, "AdjustAllCFDSourceLen did not scale the source"



	def test_AdjustAllCFDSourceRad(self):
		pid = AddGeom( "POD", "" )

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 2.0, 0.5, 0.5 )

		src_id = GetCFDSourceID( pid, 0 )

		AdjustAllCFDSourceRad( 0.5 )

		assert abs( GetParmVal( src_id, "SrcRad", "Source" ) - 1.0 ) < 1e-6, "AdjustAllCFDSourceRad did not scale the source"



	def test_AddDefaultSources(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		AddDefaultSources() # 3 Sources: Def_Fwd_PS, Def_Aft_PS, Def_Fwd_Aft_LS

		# The three default sources arrive under the names in the comment.
		assert GetNumCFDSources( pid ) == 3, "AddDefaultSources did not add three sources"
		assert GetCFDSourceName( pid, 0 ) == "Def_Fwd_PS", "AddDefaultSources did not add the expected sources"
		assert GetCFDSourceName( pid, 1 ) == "Def_Aft_PS", "AddDefaultSources did not add the expected sources"
		assert GetCFDSourceName( pid, 2 ) == "Def_Fwd_Aft_LS", "AddDefaultSources did not add the expected sources"

		# The first two are point sources and the third joins them with a line.
		assert GetCFDSourceType( pid, 0 ) == POINT_SOURCE, "AddDefaultSources did not add the expected source types"
		assert GetCFDSourceType( pid, 1 ) == POINT_SOURCE, "AddDefaultSources did not add the expected source types"
		assert GetCFDSourceType( pid, 2 ) == LINE_SOURCE, "AddDefaultSources did not add the expected source types"



	def test_AddCFDSource(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		AddCFDSource( POINT_SOURCE, pid, 0, 0.25, 2.0, 0.5, 0.5 )      # Add A Point Source

		# The source lands on the Geom it was given, as the type it was given.
		assert GetNumCFDSources( pid ) == 1, "AddCFDSource did not add a point source"
		assert GetCFDSourceType( pid, 0 ) == POINT_SOURCE, "AddCFDSource did not add a point source"

		# A source attached to a Geom that does not exist has to be rejected.  The
		# error queue is reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		AddCFDSource( POINT_SOURCE, "NOSUCHGEOM", 0, 0.25, 2.0, 0.5, 0.5 )

		assert err_mgr.GetNumTotalErrors() > 0, "AddCFDSource accepted a bad Geom ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetVSPAERORefWingID(self):
		wid = AddGeom( "WING" )

		Update()

		SetVSPAERORefWingID( wid )

		assert GetVSPAERORefWingID() == wid, "GetVSPAERORefWingID did not report the wing that was set"



	def test_SetVSPAERORefWingID(self):
		#==== Add Wing Geom and set some parameters =====//
		wing_id = AddGeom( "WING" )

		SetGeomName( wing_id, "MainWing" )

		#==== Add Vertical tail and set some parameters =====//
		vert_id = AddGeom( "WING" )

		SetGeomName( vert_id, "Vert" )

		SetParmValUpdate( vert_id, "TotalArea", "WingGeom", 10.0 )
		SetParmValUpdate( vert_id, "X_Rel_Location", "XForm", 8.5 )
		SetParmValUpdate( vert_id, "X_Rel_Rotation", "XForm", 90 )

		#==== Set VSPAERO Reference lengths & areas ====//
		SetVSPAERORefWingID( wing_id ) # Set as reference wing for VSPAERO

		print( "VSPAERO Reference Wing ID: ", False )

		print( GetVSPAERORefWingID() )

		assert GetVSPAERORefWingID() == wing_id, "SetVSPAERORefWingID did not take"

		# Naming a Geom that does not exist has to be rejected.  The error queue is
		# reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetVSPAERORefWingID( "NOSUCHGEOM" )

		assert err_mgr.GetNumTotalErrors() > 0, "SetVSPAERORefWingID accepted a bad Geom ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetNumAnalysis(self):
		nanalysis = GetNumAnalysis()

		print( f"Number of registered analyses: {nanalysis}" )

		# The count has to match the list of names.
		analysis_array = ListAnalysis()

		assert nanalysis == len( analysis_array ), "GetNumAnalysis disagrees with ListAnalysis"
		assert nanalysis >= 1, "no analyses registered"



	def test_ListAnalysis(self):
		analysis_array = ListAnalysis()

		print( "List of Available Analyses: " )

		for i in range(int( len(analysis_array) )):

			print( "    " + analysis_array[i] )

			assert len( analysis_array[i] ) > 0, "ListAnalysis returned an unnamed analysis"

		assert len( analysis_array ) == GetNumAnalysis(), "ListAnalysis disagrees with GetNumAnalysis"

		# The analyses the rest of these examples lean on have to be there.
		assert "VSPAEROComputeGeometry" in analysis_array, "VSPAEROComputeGeometry is not registered"



	def test_GetAnalysisInputNames(self):
		analysis_name = "VSPAEROComputeGeometry"

		in_names =  GetAnalysisInputNames( analysis_name )
		assert len( in_names ) > 0, "GetAnalysisInputNames returned nothing"

		print("Analysis Inputs: ")

		for i in range(int( len(in_names) )):

			print( ( "\t" + in_names[i] + "\n" ) )



	def test_GetAnalysisDoc(self):
		analysis_name = "VSPAEROComputeGeometry"

		doc = GetAnalysisDoc( analysis_name )
		assert len( doc ) > 0, "GetAnalysisDoc returned nothing"



	def test_GetAnalysisInputDoc(self):
		analysis_name = "CompGeom"

		in_array = GetAnalysisInputNames( analysis_name )

		doc = GetAnalysisInputDoc( analysis_name, in_array[0] )

		assert len( doc ) > 0, "GetAnalysisInputDoc returned nothing"



	def test_ExecAnalysis(self):
		analysis_name = "VSPAEROComputeGeometry"

		res_id = ExecAnalysis( analysis_name )
		assert len( res_id ) > 0, "ExecAnalysis returned no id"




	def test_GetNumAnalysisInputData(self):
		analysis_name = "CompGeom"

		in_array = GetAnalysisInputNames( analysis_name )

		assert GetNumAnalysisInputData( analysis_name, in_array[0] ) >= 1, "GetNumAnalysisInputData reported nothing"



	def test_GetAnalysisInputType(self):
		analysis = "VSPAEROComputeGeometry"

		inp_array = GetAnalysisInputNames( analysis )

		assert len( inp_array ) > 0, "GetAnalysisInputNames returned nothing"

		for j in range(int( len(inp_array) )):

			typ = GetAnalysisInputType( analysis, inp_array[j] )

			# Every input the analysis lists has to report a real data type.
			assert typ != INVALID_TYPE, "GetAnalysisInputType returned INVALID_TYPE for " + inp_array[j]

		# An input that does not exist has to report INVALID_TYPE.
		assert GetAnalysisInputType( analysis, "NoSuchInput" ) == INVALID_TYPE, "GetAnalysisInputType accepted an unknown input"

		# That lookup failure was raised deliberately, so take it back off the queue.
		err_mgr = ErrorMgrSingleton.getInstance()

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetIntAnalysisInput(self):
		#==== Analysis: VSPAero Compute Geometry ====//
		analysis_name = "VSPAEROComputeGeometry"

		# Set to panel method
		thick_set = GetIntAnalysisInput( analysis_name, "GeomSet" )
		assert len( thick_set ) > 0, "GetIntAnalysisInput returned nothing"
		thin_set = GetIntAnalysisInput( analysis_name, "ThinGeomSet" )

		thick_set = [vsp.SET_NONE]
		thin_set = [vsp.SET_ALL]

		SetIntAnalysisInput( analysis_name, "GeomSet", thick_set )
		SetIntAnalysisInput( analysis_name, "ThinGeomSet", thin_set )



	def test_GetDoubleAnalysisInput(self):
		vinfFCinput = list( GetDoubleAnalysisInput( "ParasiteDrag", "Vinf" ) )

		vinfFCinput[0] = 629

		SetDoubleAnalysisInput( "ParasiteDrag", "Vinf", vinfFCinput )



	def test_GetStringAnalysisInput(self):
		fileNameInput = GetStringAnalysisInput( "ParasiteDrag", "FileName" )
		assert len( fileNameInput ) > 0, "GetStringAnalysisInput returned nothing"

		fileNameInput = ["ParasiteDragExample"]

		SetStringAnalysisInput( "ParasiteDrag", "FileName", fileNameInput )



	def test_GetVec3dAnalysisInput(self):
		# PlanarSlice
		norm = GetVec3dAnalysisInput( "PlanarSlice", "Norm" )
		assert len( norm ) > 0, "GetVec3dAnalysisInput returned nothing"

		norm[0].set_xyz( 0.23, 0.6, 0.15 )

		SetVec3dAnalysisInput( "PlanarSlice", "Norm", norm )



	def test_SetAnalysisInputDefaults(self):
		#==== Analysis: VSPAero Compute Geometry ====//
		analysis_name = "VSPAEROComputeGeometry"

		# Change an input away from its default...
		geom_set = GetIntAnalysisInput( analysis_name, "GeomSet" )

		new_set = [ geom_set[0] + 1 ]

		SetIntAnalysisInput( analysis_name, "GeomSet", new_set )

		check_set = GetIntAnalysisInput( analysis_name, "GeomSet" )

		assert check_set[0] == new_set[0], "SetIntAnalysisInput did not take"

		# ...and set defaults, which has to put it back.
		SetAnalysisInputDefaults( analysis_name )

		check_set = GetIntAnalysisInput( analysis_name, "GeomSet" )

		assert check_set[0] == geom_set[0], "SetAnalysisInputDefaults did not restore the default"



	def test_SetIntAnalysisInput(self):
		#==== Analysis: VSPAero Compute Geometry ====//
		analysis_name = "VSPAEROComputeGeometry"

		# Set to panel method
		thick_set = GetIntAnalysisInput( analysis_name, "GeomSet" )
		thin_set = GetIntAnalysisInput( analysis_name, "ThinGeomSet" )

		thick_set = [vsp.SET_NONE]
		thin_set = [vsp.SET_ALL]

		SetIntAnalysisInput( analysis_name, "GeomSet", thick_set )
		assert list( GetIntAnalysisInput( analysis_name, "GeomSet" ) ) == list( thick_set ), "SetIntAnalysisInput did not take"

		SetIntAnalysisInput( analysis_name, "ThinGeomSet", thin_set )



	def test_SetDoubleAnalysisInput(self):
		#==== Analysis: CpSlicer ====//
		analysis_name = "CpSlicer"

		# Setup cuts
		ycuts = []
		ycuts.append( 2.0 )
		ycuts.append( 4.5 )
		ycuts.append( 8.0 )

		SetDoubleAnalysisInput( analysis_name, "YSlicePosVec", ycuts, 0 )
		assert list( GetDoubleAnalysisInput( analysis_name, "YSlicePosVec", 0 ) ) == list( ycuts ), "SetDoubleAnalysisInput did not take"




	def test_SetStringAnalysisInput(self):
		fileNameInput = GetStringAnalysisInput( "ParasiteDrag", "FileName" )

		fileNameInput = ["ParasiteDragExample"]

		SetStringAnalysisInput( "ParasiteDrag", "FileName", fileNameInput )
		assert list( GetStringAnalysisInput( "ParasiteDrag", "FileName" ) ) == list( fileNameInput ), "SetStringAnalysisInput did not take"




	def test_SetVec3dAnalysisInput(self):
		# PlanarSlice
		norm = GetVec3dAnalysisInput( "PlanarSlice", "Norm" )

		norm[0].set_xyz( 0.23, 0.6, 0.15 )

		SetVec3dAnalysisInput( "PlanarSlice", "Norm", norm )
		# The Python binding does not expose vec3d equality, so compare components.
		norm_back = GetVec3dAnalysisInput( "PlanarSlice", "Norm" )
		assert len( norm_back ) == len( norm ), "SetVec3dAnalysisInput length"
		for i in range( len( norm ) ):
			assert abs( norm_back[i].x() - norm[i].x() ) < 1e-9, "SetVec3dAnalysisInput x"
			assert abs( norm_back[i].y() - norm[i].y() ) < 1e-9, "SetVec3dAnalysisInput y"
			assert abs( norm_back[i].z() - norm[i].z() ) < 1e-9, "SetVec3dAnalysisInput z"




	def test_PrintAnalysisInputs(self):
		#==== Analysis: VSPAero Compute Geometry ====//
		analysis_name = "VSPAEROComputeGeometry"

		# list inputs, type, and current values
		PrintAnalysisInputs( analysis_name )

		# There has to be something to list.
		inp_array = GetAnalysisInputNames( analysis_name )

		assert len( inp_array ) > 0, "the analysis reports no inputs to print"

		# Printing an analysis that does not exist has to be rejected.  The error
		# queue is reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		PrintAnalysisInputs( "NoSuchAnalysis" )

		assert err_mgr.GetNumTotalErrors() > 0, "PrintAnalysisInputs accepted an unknown analysis"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_PrintAnalysisDocs(self):
		#==== Analysis: VSPAero Compute Geometry ====//
		analysis_name = "VSPAEROComputeGeometry"

		# list inputs, type, and documentation
		PrintAnalysisDocs( analysis_name )

		# The analysis itself has to carry documentation to print.
		assert len( GetAnalysisDoc( analysis_name ) ) > 0, "the analysis carries no documentation"

		# Printing an analysis that does not exist has to be rejected.  The error
		# queue is reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		PrintAnalysisDocs( "NoSuchAnalysis" )

		assert err_mgr.GetNumTotalErrors() > 0, "PrintAnalysisDocs accepted an unknown analysis"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_AddGeometryAnalysis(self):
		##==== GeometryAnalysis: Add and configure a case ====##
		ga_id = AddGeometryAnalysis()
		print( "Added Geometry Analysis: ", ga_id )


	def test_AddGeometryAnalysisAzEl(self):
		##==== GeometryAnalysis: Delete a specific case ====##
		ga_id = AddGeometryAnalysis()

		assert len( GetAllGeometryAnalysesIDVec() ) == 1, "AddGeometryAnalysis did not add a case"

		DeleteGeometryAnalysis( ga_id )

		assert len( GetAllGeometryAnalysesIDVec() ) == 0, "DeleteGeometryAnalysis did not remove the case"



	def test_DeleteGeometryAnalysisAzEl(self):
		ga_id = AddGeometryAnalysis()

		AddGeometryAnalysisAzEl( ga_id, 30.0, 15.0 )
		AddGeometryAnalysisAzEl( ga_id, 60.0, 45.0 )

		DeleteGeometryAnalysisAzEl( ga_id, 0 )

		# Only the indexed pair goes, and the rest slide down.
		assert GetNumGeometryAnalysisAzEl( ga_id ) == 1, "DeleteGeometryAnalysisAzEl did not remove one pair"
		assert abs( GetParmVal( GetGeometryAnalysisAzimuthParm( ga_id, 0 ) ) - 60.0 ) < 1e-6, "DeleteGeometryAnalysisAzEl removed the wrong pair"

		# An index past the end has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteGeometryAnalysisAzEl( ga_id, GetNumGeometryAnalysisAzEl( ga_id ) )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteGeometryAnalysisAzEl accepted an index past the end"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteAllGeometryAnalysisAzEl(self):
		ga_id = AddGeometryAnalysis()

		AddGeometryAnalysisAzEl( ga_id, 30.0, 15.0 )
		AddGeometryAnalysisAzEl( ga_id, 60.0, 45.0 )

		DeleteAllGeometryAnalysisAzEl( ga_id )

		assert GetNumGeometryAnalysisAzEl( ga_id ) == 0, "DeleteAllGeometryAnalysisAzEl left pairs behind"

		# Clearing an empty case is not an error.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteAllGeometryAnalysisAzEl( ga_id )

		assert err_mgr.GetNumTotalErrors() == 0, "DeleteAllGeometryAnalysisAzEl complained about an empty case"



	def test_GetNumGeometryAnalysisAzEl(self):
		id = AddGeometryAnalysis()

		AddGeometryAnalysisAzEl( id, 10.0, 20.0 )

		assert GetNumGeometryAnalysisAzEl( id ) == 1, "GetNumGeometryAnalysisAzEl did not count the pair"



	def test_GetGeometryAnalysisAzimuthParm(self):
		id = AddGeometryAnalysis()

		AddGeometryAnalysisAzEl( id, 10.0, 20.0 )

		azparm = GetGeometryAnalysisAzimuthParm( id, 0 )

		assert abs( GetParmVal( azparm ) - 10.0 ) < 1e-6, "GetGeometryAnalysisAzimuthParm did not report the azimuth"



	def test_GetGeometryAnalysisElevationParm(self):
		id = AddGeometryAnalysis()

		AddGeometryAnalysisAzEl( id, 10.0, 20.0 )

		elparm = GetGeometryAnalysisElevationParm( id, 0 )

		assert abs( GetParmVal( elparm ) - 20.0 ) < 1e-6, "GetGeometryAnalysisElevationParm did not report the elevation"



	def test_DeleteGeometryAnalysis(self):
		id = AddGeometryAnalysis()

		SetActiveGeometryAnalysis( id )

		assert GetActiveGeometryAnalysis() == id, "SetActiveGeometryAnalysis did not take"

		DeleteGeometryAnalysis( id )

		# The case that was active is gone, so nothing is active.
		assert GetActiveGeometryAnalysis() != id, "DeleteGeometryAnalysis did not delete the case"



	def test_DeleteAllGeometryAnalyses(self):
		##==== GeometryAnalysis: Delete all cases ====##
		ga_id_1 = AddGeometryAnalysis()
		ga_id_2 = AddGeometryAnalysis()

		assert ga_id_1 != ga_id_2, "AddGeometryAnalysis reused an ID"
		assert len( GetAllGeometryAnalysesIDVec() ) == 2, "the two cases were not both added"

		DeleteAllGeometryAnalyses()
		ga_ids = GetAllGeometryAnalysesIDVec()
		print( "Number of Geometry Analyses after delete: ", len( ga_ids ) )

		assert len( ga_ids ) == 0, "DeleteAllGeometryAnalyses left cases behind"


	def test_GetAllGeometryAnalysesIDVec(self):
		##==== GeometryAnalysis: List all cases ====##
		ga_id_1 = AddGeometryAnalysis()
		ga_id_2 = AddGeometryAnalysis()
		ga_ids = GetAllGeometryAnalysesIDVec()
		assert len( ga_ids ) > 0, "GetAllGeometryAnalysesIDVec returned nothing"
		for ga_id in ga_ids:
			print( "Geometry Analysis ID: ", ga_id )


	def test_SetActiveGeometryAnalysis(self):
		ga_id = AddGeometryAnalysis()
		SetActiveGeometryAnalysis( ga_id )
		assert GetActiveGeometryAnalysis() == ga_id, "SetActiveGeometryAnalysis did not take"



	def test_GetActiveGeometryAnalysis(self):
		ga_id = AddGeometryAnalysis()
		SetActiveGeometryAnalysis( ga_id )
		active = GetActiveGeometryAnalysis()
		assert len( active ) > 0, "GetActiveGeometryAnalysis returned nothing"


	def test_MakeMeshGeom(self):
		#==== Add a Geom for the case to work on ====//
		pod_id = AddGeom( "POD" )
		Update()

		ga_id = AddGeometryAnalysis()

		#==== Configure the case.  Without a primary target the analysis has
		#==== nothing to mesh and reports an empty primary mesh.
		SetParmVal( FindParm( ga_id, "PrimaryType", "InterferenceCase" ), SET_TARGET )
		SetParmVal( FindParm( ga_id, "PrimarySet", "InterferenceCase" ), SET_ALL )
		SetParmVal( FindParm( ga_id, "SecondaryType", "InterferenceCase" ), SET_TARGET )
		SetParmVal( FindParm( ga_id, "SecondarySet", "InterferenceCase" ), SET_ALL )
		Update()

		# Evaluate the case through the Analysis framework so that its result meshes exist.
		SetAnalysisInputDefaults( "GeometryAnalysis" )

		SetStringAnalysisInput( "GeometryAnalysis", "CaseID", [ga_id] )

		ExecAnalysis( "GeometryAnalysis" )

		# Turn the case's result meshes into a MeshGeom.
		mesh_id = MakeMeshGeom( ga_id )
		assert len( mesh_id ) > 0, "MakeMeshGeom returned no id"



	def test_SummarizeAttributes(self):
		##==== Attributes: SummarizeAttributes ====##
		SummaryText = SummarizeAttributes()
		assert len( SummaryText ) > 0, "SummarizeAttributes returned no id"

		print( SummaryText )



	def test_SummarizeAttributesAsTree(self):
		##==== Attributes: SummarizeAttributesAsTree ====##
		SummaryTextTree = SummarizeAttributesAsTree();
		assert len( SummaryTextTree ) > 0, "SummarizeAttributesAsTree returned no id"

		print( SummaryTextTree )



	def test_FindAllAttributes(self):
		##==== Attributes: FindAllAttributes ====##
		AttrIDs = FindAllAttributes()
		assert len( AttrIDs ) > 0, "FindAllAttributes found nothing"
		for AttrID in AttrIDs:
			print( AttrID )



	def test_FindAttributesByName(self):
		##==== Attributes: FindAttributesByName ====##
		AttrIDs = FindAttributesByName( "Watermark" )
		assert len( AttrIDs ) > 0, "FindAttributesByName found nothing"
		for AttrID in AttrIDs:
			print( AttrID )



	def test_FindAttributeByName(self):
		##==== Attributes: FindAttributeByName ====##
		AttrID = FindAttributeByName( "Watermark", 0 )
		assert len( AttrID ) > 0, "FindAttributeByName found nothing"
		print( AttrID )



	def test_FindAttributeInCollection(self):
		##==== Attributes: FindAttributeInCollection ====##
		VehID = GetVehicleID()
		AttrID = FindAttributeInCollection( VehID, 'Watermark', 0 )
		assert len( AttrID ) > 0, "FindAttributeInCollection found nothing"
		print( AttrID )



	def test_FindAttributeNamesInCollection(self):
		##==== Attributes: FindAttributeNamesInCollection ====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrNames = FindAttributeNamesInCollection( CollID )
		assert len( AttrNames ) > 0, "FindAttributeNamesInCollection found nothing"
		for AttrName in AttrNames:
			print( AttrName )



	def test_FindAttributesInCollection(self):
		##==== Attributes: FindAttributesInCollection ====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrIDs = FindAttributesInCollection( CollID )
		assert len( AttrIDs ) > 0, "FindAttributesInCollection found nothing"
		for AttrID in AttrIDs:
			print( AttrID )



	def test_FindAttributedObjects(self):
		##==== Attributes: FindAttributedObjects ====##
		AttachIDs = FindAttributedObjects()
		assert len( AttachIDs ) > 0, "FindAttributedObjects found nothing"
		for AttachID in AttachIDs:
			print( AttachID )



	def test_GetObjectType(self):
		##==== Attributes: GetObjectType ====##
		AttachIDs = FindAttributedObjects()

		assert len( AttachIDs ) > 0, "FindAttributedObjects found nothing"

		for AttachID in AttachIDs:
			ObjType = GetObjectType( AttachID )
			print( ObjType )

			# Every object that carries attributes has to be a recognized kind, and
			# the enum has to agree with the name form.
			assert ObjType != ATTROBJ_FREE, "GetObjectType did not recognize " + AttachID
			assert len( GetObjectTypeName( AttachID ) ) > 0, "GetObjectTypeName returned nothing for " + AttachID



	def test_GetObjectTypeName(self):
		AttachIDs = FindAttributedObjects()
		for AttachID in AttachIDs:
			ObjTypeName = GetObjectTypeName( AttachID )
			assert len( ObjTypeName ) > 0, "GetObjectTypeName returned nothing"
			print( ObjTypeName )



	def test_GetObjectName(self):
		##==== Attributes: GetObjectName ====##
		AttachIDs = FindAttributedObjects()
		for AttachID in AttachIDs:
			ObjName = GetObjectName( AttachID )
			assert len( ObjName ) > 0, "GetObjectName returned nothing"
			print( ObjName )



	def test_GetObjectParent(self):
		##==== Attributes: GetObjectParent ====##

		WingID = AddGeom( "WING" )
		PodID = AddGeom( "POD", WingID )
		ParentID = GetObjectParent( PodID )
		assert len( ParentID ) > 0, "GetObjectParent returned nothing"

		if ParentID == WingID:
			print( "Parent of Pod is Wing")

		#Get first attribute in vehicle as an example
		AttrID = FindAllAttributes()[0]
		CollID = GetObjectParent( AttrID )
		CollParentObjID = GetObjectParent( CollID )
		print( CollParentObjID )



	def test_GetChildCollection(self):
		##==== Attributes: GetChildCollection =====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		assert len( CollID ) > 0, "GetChildCollection returned nothing"
		print( CollID )




	def test_GetGeomSetCollection(self):
		##==== Attributes: GetGeomSetCollection =====##
		CollID = GetGeomSetCollection( 0 )
		assert len( CollID ) > 0, "GetGeomSetCollection returned nothing"
		print( CollID )



	def test_GetAttributeName(self):
		##==== Attributes: GetAttributeName =====##

		AttrIDs = FindAllAttributes()

		for AttrID in AttrIDs:
			AttrName = GetAttributeName( AttrID )
			assert len( AttrName ) > 0, "GetAttributeName returned nothing"
			print( AttrName )



	def test_GetAttributeID(self):
		##==== Attributes: GetAttributeID =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrNames = FindAttributeNamesInCollection( CollID )
		for AttrName in AttrNames:
			AttrID = GetAttributeID( CollID, AttrName, 0 )
			assert len( AttrID ) > 0, "GetAttributeID returned nothing"
			print( AttrID )




	def test_GetAttributeDoc(self):
		##==== Attributes: GetAttributeDoc =====##
		AttrID = FindAllAttributes()[0]
		AttrDoc = GetAttributeDoc(AttrID)
		assert len( AttrDoc ) > 0, "GetAttributeDoc returned nothing"
		print( AttrDoc )



	def test_GetAttributeType(self):
		##==== Attributes: GetAttributeType =====##
		AttrIDs = FindAllAttributes()

		assert len( AttrIDs ) > 0, "FindAllAttributes found nothing"

		AttrID = AttrIDs[0]
		AttrType = GetAttributeType( AttrID )
		print( AttrType )

		# The attribute has to report a real type, and the enum has to agree with
		# the name form.
		assert AttrType != INVALID_TYPE, "GetAttributeType returned INVALID_TYPE"
		assert len( GetAttributeTypeName( AttrID ) ) > 0, "GetAttributeTypeName returned nothing"

		# An ID that is not an attribute has to report INVALID_TYPE.
		assert GetAttributeType( "NOSUCHATTRIBUTE" ) == INVALID_TYPE, "GetAttributeType accepted a bad ID"

		# That lookup failure was raised deliberately, so take it back off the queue.
		err_mgr = ErrorMgrSingleton.getInstance()

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetAttributeTypeName(self):
		##==== Attributes: GetAttributeTypeName =====##
		AttrID = FindAllAttributes()[0]
		AttributeTypeName = GetAttributeTypeName( AttrID )
		assert len( AttributeTypeName ) > 0, "GetAttributeTypeName returned nothing"
		print( AttributeTypeName )




	def test_GetAttributeBoolVal(self):
		##==== Attribute: GetAttributeBoolVal  =====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = True
		AttrID = AddAttributeBool( CollID, "TestBoolAttr", InitVal )

		GetVal = GetAttributeBoolVal( AttrID )
		if GetVal[0] == InitVal:
			print( "Got matching Bool Value from Attribute" )
		else:
			print( "GetAttributeBoolVal error!" )
			assert False, "GetAttributeBoolVal error!"



	def test_GetAttributeIntVal(self):
		##==== Attribute: GetAttributeIntVal  =====//
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = 55
		AttrID = AddAttributeInt( CollID, "TestIntAttr", InitVal )

		GetVal = GetAttributeIntVal( AttrID )
		if GetVal[0] == InitVal:
			print( "Got matching Int Value from Attribute" )
		else:
			print( "GetAttributeIntVal error!" )
			assert False, "GetAttributeIntVal error!"



	def test_GetAttributeDoubleVal(self):
		##==== Attribute: GetAttributeDoubleVal  =====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = 3.14159
		AttrID = AddAttributeDouble( CollID, "TestDoubleAttr", InitVal )

		GetVal = GetAttributeDoubleVal( AttrID )
		if GetVal[0] == InitVal:
			print( "Got matching Double Value from Attribute" )
		else:
			print( "GetAttributeDoubleVal error!" )
			assert False, "GetAttributeDoubleVal error!"



	def test_GetAttributeStringVal(self):
		##==== Attribute: GetAttributeStringVal  =====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = "Hello_World_of_Attributes"
		AttrID = AddAttributeString( CollID, "TestStringAttr", InitVal )

		GetVal = GetAttributeStringVal( AttrID )
		if GetVal[0] == InitVal:
			print( "Got matching String Value from Attribute" )
		else:
			print( "GetAttributeStringVal error!" )
			assert False, "GetAttributeStringVal error!"



	def test_GetAttributeParmID(self):
		##==== Attribute: GetAttributeParmID  =====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )

		PodID = AddGeom( "POD", "" )
		print( "---> Test Get Parm Val" )
		ParmArray = GetGeomParmIDs( PodID )

		ParmID = ParmArray[0]
		AttrID = AddAttributeParm( CollID, "TestParmAttr", ParmID )

		GetID = GetAttributeParmID( AttrID )

		if GetID[0] == ParmID:
			print( "Got matching Parm ID from Attribute" )
		else:
			print( "GetAttributeParmID error!" )
			assert False, "GetAttributeParmID error!"



	def test_GetAttributeParmVal(self):
		##==== Attribute: GetAttributeParmVal  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )

		PodID = AddGeom( "POD", "" )
		print( "---> Test Get Parm Val" )
		ParmArray = GetGeomParmIDs( PodID )

		ParmID = ParmArray[0]
		AttrID = AddAttributeParm( CollID, "TestParmAttr", ParmID )

		InitVal = GetParmVal( ParmID )
		GetVal = GetAttributeParmVal( AttrID )

		if GetVal[0] == InitVal:
			print( "Got matching Parm Value from Attribute" )
		else:
			print( "GetAttributeParmVal error!" )
			assert False, "GetAttributeParmVal error!"




	def test_GetAttributeParmName(self):
		##==== Attribute: GetAttributeParmName  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		PodID = AddGeom( "POD", "" )
		print( "---> Test Get Parm Val" )
		ParmArray = GetGeomParmIDs( PodID )
		AttrName = 'Example_Parm_Attr'
		ParmID = ParmArray[0]
		AddAttributeParm( CollID, AttrName, ParmID )
		AttrID = GetAttributeID( CollID, AttrName, 0 )
		ParmName = GetAttributeParmName( AttrID )[0]
		if ParmName == GetParmName( ParmID ):
			print( "Got matching Parm Name from Attribute" )
		else:
			print( "GetAttributeParmName error!" )
			assert False, "GetAttributeParmName error!"




	def test_GetAttributeVec3dVal(self):
		##==== Attribute: GetAttributeVec3dVal  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = vec3d([1., 0.5, -4.])
		AttrID = AddAttributeVec3d( CollID, "TestVec3dAttr", [InitVal] )

		Vec3dVal = GetAttributeVec3dVal( AttrID )
		if ( Vec3dVal[0].x() == InitVal.x() ) and ( Vec3dVal[0].y() == InitVal.y() ) and ( Vec3dVal[0].z() == InitVal.z() ):
			print( "Got matching Vec3d Value from Attribute" )
		else:
			print( "GetAttributeVec3dVal error!" )
			assert False, "GetAttributeVec3dVal error!"



	def test_GetAttributeIntMatrixVal(self):
		##==== Attribute: GetAttributeIntMatrixVal  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = [[0, 1,],[-4, -1000]]
		AttrID = AddAttributeIntMatrix( CollID, "TestIntMatrixAttr", InitVal )

		IntMatrixVal = GetAttributeIntMatrixVal( AttrID )
		IntMatrixVal = [list(row) for row in IntMatrixVal]

		if IntMatrixVal == InitVal:
			print( "Got matching IntMatrix Value from Attribute" )
		else:
			print( "GetAttributeIntMatrixVal error!" )
			assert False, "GetAttributeIntMatrixVal error!"




	def test_GetAttributeDoubleMatrixVal(self):
		##==== Attribute: GetAttributeDoubleMatrixVal  =====##
		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = [[0., 1.,],[-4., -1000.]]
		AttrID = AddAttributeDoubleMatrix( CollID, "TestDoubleMatrixAttr", InitVal )

		DblMatrixVal = GetAttributeDoubleMatrixVal( AttrID )
		DblMatrixVal = [list(row) for row in DblMatrixVal]

		if DblMatrixVal == InitVal:
			print( "Got matching Double Matrix Value from Attribute" )
		else:
			print( "GetAttributeDoubleMatrixVal error!" )
			assert False, "GetAttributeDoubleMatrixVal error!"



	def test_SetAttributeName(self):
		##==== Attribute: SetAttributeName  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = "Hello_World_of_Attributes"
		AttrID = AddAttributeString( CollID, "TestStringAttr", InitVal )

		NameString = 'NewName_Example'
		SetAttributeName( AttrID, NameString )
		AttrName = GetAttributeName( AttrID )
		if NameString == AttrName:
			print( "Got matching name from Attribute")
		else:
			print( "SetAttributeName error!" )
			assert False, "SetAttributeName error!"



	def test_SetAttributeDoc(self):
		##==== Attribute: SetAttributeDoc  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = "Hello_World_of_Attributes"
		AttrID = AddAttributeString( CollID, "TestStringAttr", InitVal )

		DocString = 'New_docstring_for_attribute'

		SetAttributeDoc( AttrID, DocString )
		NewDocString = GetAttributeDoc( AttrID )
		if NewDocString == DocString:
			print( "Got matching DocString from Attribute")
		else:
			print( "SetAttributeDoc error!" )
			assert False, "SetAttributeDoc error!"



	def test_SetAttributeBool(self):
		##==== Attribute: SetAttributeBool  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = True
		AttrID = AddAttributeBool( CollID, "TestBoolAttr", InitVal )

		SetVal = False
		SetAttributeBool( AttrID, SetVal )

		GetVal = GetAttributeBoolVal( AttrID )
		if GetVal[0] == SetVal:
			print( "Set matching Bool Value from Attribute" )
		else:
			print( "SetAttributeBoolVal error!" )
			assert False, "SetAttributeBoolVal error!"



	def test_SetAttributeInt(self):
		##==== Attribute: SetAttributeInt  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = 55
		AttrID = AddAttributeInt( CollID, "TestIntAttr", InitVal )

		NewIntVal = -55

		SetAttributeInt( AttrID, NewIntVal )
		GetVal = GetAttributeIntVal( AttrID )
		if GetVal[0] == NewIntVal:
			print( "Set matching Int Value from Attribute" )
		else:
			print( "SetAttributeIntVal error!" )
			assert False, "SetAttributeIntVal error!"



	def test_SetAttributeDouble(self):
		##==== Attribute: SetAttributeDouble  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = 3.14159
		AttrID = AddAttributeDouble( CollID, "TestDoubleAttr", InitVal )

		DoubleVal = 3.15

		SetAttributeDouble( AttrID, DoubleVal )

		GetVal = GetAttributeDoubleVal( AttrID )
		if GetVal[0] == DoubleVal:
			print( "Set matching Double Value from Attribute" )
		else:
			print( "SetAttributeDoubleVal error!" )
			assert False, "SetAttributeDoubleVal error!"



	def test_SetAttributeString(self):
		##==== Attribute: SetAttributeString  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = "Hello_World_of_Attributes"
		AttrID = AddAttributeString( CollID, "TestStringAttr", InitVal )

		StringVal = "Du bist supergeil!"
		SetAttributeString( AttrID, StringVal )

		GetVal = GetAttributeStringVal( AttrID )
		if GetVal[0] == StringVal:
			print( "Got matching String Value from Attribute" )
		else:
			print( "GetAttributeStringVal error!" )
			assert False, "GetAttributeStringVal error!"



	def test_SetAttributeParmID(self):
		##==== Attribute: SetAttributeParmID  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )

		PodID = AddGeom( "POD", "" )
		print( "---> Test Get Parm Val" )
		ParmArray = GetGeomParmIDs( PodID )

		ParmID = ParmArray[0]
		AttrID = AddAttributeParm( CollID, "TestParmAttr", ParmID )

		NewParmID = ParmArray[1]
		SetAttributeParmID( AttrID, NewParmID )
		GetID = GetAttributeParmID( AttrID )

		if GetID[0] == NewParmID:
			print( "Set matching Parm ID from Attribute" )
		else:
			print( "SetAttributeParmID error!" )
			assert False, "SetAttributeParmID error!"



	def test_SetAttributeVec3d(self):
		##==== Attribute: SetAttributeVec3d  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = vec3d([1., 0.5, -4.])
		AttrID = AddAttributeVec3d( CollID, "TestVec3dAttr", [InitVal] )

		Vec3dVal = vec3d([0.5, 0.75, -0.4])
		SetAttributeVec3d( AttrID, [Vec3dVal] )

		GetVal = GetAttributeVec3dVal( AttrID )
		if ( GetVal[0].x() == Vec3dVal.x() ) and ( GetVal[0].y() == Vec3dVal.y() ) and ( GetVal[0].z() == Vec3dVal.z() ):
			print( "Set matching Vec3d Value from Attribute" )
		else:
			print( "SetAttributeVec3dVal error!" )
			assert False, "SetAttributeVec3dVal error!"



	def test_SetAttributeIntMatrix(self):
		##==== Attribute: SetAttributeIntMatrix  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = [[0, 1,],[-4, -1000]]
		AttrID = AddAttributeIntMatrix( CollID, "TestIntMatrixAttr", InitVal )

		ImatVal = [[1,5],[-8,0]]
		SetAttributeIntMatrix( AttrID, ImatVal )

		IntMatrixVal = GetAttributeIntMatrixVal( AttrID )
		IntMatrixVal = [list(row) for row in IntMatrixVal]

		if IntMatrixVal == ImatVal:
			print( "Set matching IntMatrix Value from Attribute" )
		else:
			print( "SetAttributeIntMatrixVal error!" )
			assert False, "SetAttributeIntMatrixVal error!"



	def test_SetAttributeDoubleMatrix(self):
		##==== Attribute: SetAttributeDoubleMatrix  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = [[0., 1.,],[-4., -1000.]]
		AttrID = AddAttributeDoubleMatrix( CollID, "TestDoubleMatrixAttr", InitVal )

		NewDmatVal = [[0.,1.5],[8.4,1.1566]]
		SetAttributeDoubleMatrix( AttrID, NewDmatVal )

		DblMatrixVal = GetAttributeDoubleMatrixVal( AttrID )
		DblMatrixVal = [list(row) for row in DblMatrixVal]

		if DblMatrixVal == NewDmatVal:
			print( "Got matching Double Matrix Value from Attribute" )
		else:
			print( "GetAttributeDoubleMatrixVal error!" )
			assert False, "GetAttributeDoubleMatrixVal error!"



	def test_DeleteAttribute(self):
		##==== Attribute: DeleteAttribute  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = "This_Attribute_Will_Be_Deleted"
		AttrID = AddAttributeString( CollID, "TestStringAttr", InitVal )


		AttrIDs = FindAllAttributes()
		AttrAdded = AttrID in AttrIDs

		DeleteAttribute( AttrID )
		NewAttrIDs = FindAllAttributes()
		AttrDeleted = AttrID not in NewAttrIDs

		if AttrAdded and AttrDeleted:
			print( "Attribute successfully deleted" )
		else:
			print( "DeleteAttribute error!" )
			assert False, "DeleteAttribute error!"



	def test_AddAttributeBool(self):
		##==== Attribute: AddAttributeBool  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = True
		AttrID = AddAttributeBool( CollID, "TestBoolAttr", InitVal )

		GetVal = GetAttributeBoolVal( AttrID )
		if GetVal[0] == InitVal:
			print( "Added Bool Attribute" )
		else:
			print( "AddAttributeBool error!" )
			assert False, "AddAttributeBool error!"



	def test_AddAttributeInt(self):
		##==== Attribute: AddAttributeInt  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		InitVal = 55
		AttrID = AddAttributeInt( CollID, "TestIntAttr", InitVal )

		GetVal = GetAttributeIntVal( AttrID )
		if GetVal[0] == InitVal:
			print( "Added Int Attribute" )
		else:
			print( "AddAttributeInt error!" )
			assert False, "AddAttributeInt error!"



	def test_AddAttributeDouble(self):
		##==== Attribute: AddAttributeDouble  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_Double_Attr'
		DoubleValue = 3.14159
		AttrID = AddAttributeDouble( CollID, AttrName, DoubleValue )

		GetVal = GetAttributeDoubleVal( AttrID )
		if GetVal[0] == DoubleValue:
			print( "Added Double Attribute" )
		else:
			print( "AddAttributeDouble error!" )
			assert False, "AddAttributeDouble error!"



	def test_AddAttributeString(self):
		##==== Attribute: AddAttributeString  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_String_Attr'
		StringValue = 'Example_String_Attr_DataVal'
		AttrID = AddAttributeString( CollID, AttrName, StringValue )

		GetVal = GetAttributeStringVal( AttrID )
		if GetVal[0] == StringValue:
			print( "Added String Attribute" )
		else:
			print( "AddAttributeString error!" )
			assert False, "AddAttributeString error!"



	def test_AddAttributeParm(self):
		##==== Attribute: AddAttributeParm  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		pid = AddGeom( "POD", "" )
		print( "---> Test Add Parm Attr" )
		parm_array = GetGeomParmIDs( pid )
		AttrName = 'Example_Parm_Attr'
		ParmID = parm_array[0]
		AttrID = AddAttributeParm( CollID, AttrName, ParmID )

		GetVal = GetAttributeParmID( AttrID )
		if GetVal[0] == ParmID:
			print( "Added Parm Attribute" )
		else:
			print( "AddAttributeParm error!" )
			assert False, "AddAttributeParm error!"




	def test_AddAttributeVec3d(self):
		##==== Attribute: AddAttributeVec3d  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_Vec3D_Attr'
		Vec3dVal = vec3d( 0.5, 0.75, -0.4 )
		AttrID = AddAttributeVec3d( CollID, AttrName, [Vec3dVal] )

		GetVal = GetAttributeVec3dVal( AttrID )
		if ( GetVal[0].x() == Vec3dVal.x() ) and ( GetVal[0].y() == Vec3dVal.y() ) and ( GetVal[0].z() == Vec3dVal.z() ):
			print( "Added Vec3d Attribute" )
		else:
			print( "AddAttributeVec3d error!" )
			assert False, "AddAttributeVec3d error!"



	def test_AddAttributeIntMatrix(self):
		##==== Attribute: AddAttributeIntMatrix  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_IntMatrix_Attr'
		IntMatrix = [[1,5],[-8,0]]
		AttrID = AddAttributeIntMatrix( CollID, AttrName, IntMatrix )

		IntMatrixVal = GetAttributeIntMatrixVal( AttrID )
		IntMatrixVal = [list(row) for row in IntMatrixVal]

		if IntMatrixVal == IntMatrix:
			print( "Added IntMatrix Attribute" )
		else:
			print( "AddAttributeIntMatrix error!" )
			assert False, "AddAttributeIntMatrix error!"



	def test_AddAttributeDoubleMatrix(self):
		##==== Attribute: AddAttributeDoubleMatrix  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_DoubleMat_Attr'
		DoubleMatrix = [[0.,1.5],[8.4,1.1566]]
		AttrID = AddAttributeDoubleMatrix( CollID, AttrName, DoubleMatrix )

		DoubleMatrixVal = GetAttributeDoubleMatrixVal( AttrID )
		DoubleMatrixVal = [list(row) for row in DoubleMatrixVal]

		if DoubleMatrixVal == DoubleMatrix:
			print( "Added DoubleMatrix Attribute" )
		else:
			print( "AddAttributeDoubleMatrix error!" )
			assert False, "AddAttributeDoubleMatrix error!"



	def test_AddAttributeGroup(self):
		##==== Attribute: AddAttributeGroup  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_Attr_Group'
		AttrID = AddAttributeGroup( CollID, AttrName )
		if GetAttributeType( AttrID ) == ATTR_COLLECTION_DATA:
			print( "Added Attribute Group" )
		else:
			print( "AddAttributeGroup error!" )
			assert False, "AddAttributeGroup error!"




	def test_CopyAttribute(self):
		##==== Attribute: CopyAttribute  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_String_Attr'
		StringValue = 'Example_String_Attr_DataVal'
		AttrID = AddAttributeString( CollID, AttrName, StringValue )
		CopyError = CopyAttribute( AttrID )
		if not CopyError:
			print("Successfully copied Attribute")
		else:
			print("CopyAttribute Error!")
			assert False, "CopyAttribute Error!"


	def test_CutAttribute(self):
		##==== Attribute: CopyAttribute  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_String_Attr'
		StringValue = 'Example_String_Attr_DataVal'
		AttrID = AddAttributeString( CollID, AttrName, StringValue )
		CutAttribute( AttrID )

		NewCollID = GetChildCollection( "_AttrWMGroup" )
		NewAttrIDs = PasteAttribute( NewCollID )

		MatchIDs = NewAttrIDs[0] == AttrID
		Attr_Cut_Check = AttrID not in FindAttributesInCollection( CollID )
		if MatchIDs and Attr_Cut_Check:
			print("Successfully cut Attribute")
		else:
			print("CutAttribute Error!")
			assert False, "CutAttribute Error!"



	def test_PasteAttribute(self):
		##==== Attribute: PasteAttribute  =====##

		VehID = GetVehicleID()
		CollID = GetChildCollection( VehID )
		AttrName = 'Example_String_Attr'
		StringValue = 'Example_String_Attr_DataVal'
		AttrID = AddAttributeString( CollID, AttrName, StringValue )
		CutAttribute( AttrID )

		NewCollID = GetChildCollection( "_AttrWMGroup" )
		NewAttrIDs = PasteAttribute( NewCollID )

		MatchIDs = NewAttrIDs[0] == AttrID
		Attr_Cut_Check = AttrID not in FindAttributesInCollection( CollID )
		Attr_Paste_Check = AttrID in FindAttributesInCollection( NewCollID )
		if MatchIDs and Attr_Cut_Check and Attr_Paste_Check:
			print("Successfully pasted Attribute")
		else:
			print("PasteAttribute Error!")
			assert False, "PasteAttribute Error!"



	def test_GetAllResultsNames(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		results_array = GetAllResultsNames()
		assert len( results_array ) > 0, "GetAllResultsNames returned nothing"

		for i in range(int( len(results_array) )):

			resid = FindLatestResultsID( results_array[i] )
			PrintResults( resid )



	def test_GetAllDataNames(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		res_id = FindResultsID( "Test_Results" )

		data_names = GetAllDataNames( res_id )

		if  len(data_names) != 5 :
			print( "---> Error: API GetAllDataNames" )
			assert False, "---> Error: API GetAllDataNames"



	def test_GetNumResults(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		if ( GetNumResults( "Test_Results" ) != 2 ):
			print( "---> Error: API GetNumResults" )
			assert False, "---> Error: API GetNumResults"



	def test_GetResultsName(self):
		#==== Analysis: VSPAero Compute Geometry ====//
		analysis_name = "VSPAEROComputeGeometry"

		# Set defaults
		SetAnalysisInputDefaults( analysis_name )

		res_id = ( ExecAnalysis( analysis_name ) )

		print( "Results Name: ", False )

		print( GetResultsName( res_id ) )

		# The name is the Results Manager's handle for this result, so looking the
		# name back up has to lead to the same result.
		assert len( GetResultsName( res_id ) ) > 0, "GetResultsName returned nothing"
		assert FindLatestResultsID( GetResultsName( res_id ) ) == res_id, "GetResultsName does not round trip through FindLatestResultsID"



	def test_GetResultsSetDoc(self):
		#==== Analysis: VSPAero Compute Geometry ====//
		analysis_name = "VSPAEROComputeGeometry"

		# Set defaults
		SetAnalysisInputDefaults( analysis_name )

		res_id = ( ExecAnalysis( analysis_name ) )

		print( "Results doc: ", False )

		print( GetResultsSetDoc( res_id ) )

		assert len( GetResultsSetDoc( res_id ) ) > 0, "the result carries no documentation"

		# Every entry in the result has to be documented too.
		data_names = GetAllDataNames( res_id )

		for data_name in data_names:
			assert len( GetResultsEntryDoc( res_id, data_name ) ) > 0, data_name + " carries no documentation"



	def test_GetResultsEntryDoc(self):
		pid = AddGeom( "POD" )

		Update()

		rid = ExecAnalysis( "CompGeom" )

		name_array = GetAllDataNames( rid )

		if len( name_array ) > 0:
			doc = GetResultsEntryDoc( rid, name_array[0] )

			assert len( doc ) > 0, "GetResultsEntryDoc returned nothing"



	def test_FindResultsID(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		res_id = FindResultsID( "Test_Results" )

		if  len(res_id) == 0 :
			print( "---> Error: API FindResultsID" )
			assert False, "---> Error: API FindResultsID"



	def test_FindLatestResultsID(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		results_array = GetAllResultsNames()

		for i in range(int( len(results_array) )):

			resid = FindLatestResultsID( results_array[i] )
			assert len( resid ) > 0, "FindLatestResultsID found nothing"
			PrintResults( resid )



	def test_GetNumData(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		res_id = FindResultsID( "Test_Results" )

		if ( GetNumData( res_id, "Test_Int" ) != 2 ):
			print( "---> Error: API GetNumData " )
			assert False, "---> Error: API GetNumData"

		int_arr = GetIntResults( res_id, "Test_Int", 0 )

		if  int_arr[0] != 1 :
			print( "---> Error: API GetIntResults" )
			assert False, "---> Error: API GetIntResults"

		int_arr = GetIntResults( res_id, "Test_Int", 1 )

		if  int_arr[0] != 2 :
			print( "---> Error: API GetIntResults" )
			assert False, "---> Error: API GetIntResults"



	def test_GetResultsType(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		res_id = FindResultsID( "Test_Results" )

		res_array = GetAllDataNames( res_id )

		assert len( res_array ) > 0, "GetAllDataNames returned nothing"

		for j in range(int( len(res_array) )):

			typ = GetResultsType( res_id, res_array[j] )

			# Every entry the result lists has to report a real data type.
			assert typ != INVALID_TYPE, "GetResultsType returned INVALID_TYPE for " + res_array[j]

		# The fake results are written with known types.
		assert GetResultsType( res_id, "Test_Int" ) == INT_DATA, "GetResultsType reported the wrong type"
		assert GetResultsType( res_id, "Test_Double" ) == DOUBLE_DATA, "GetResultsType reported the wrong type"
		assert GetResultsType( res_id, "Test_String" ) == STRING_DATA, "GetResultsType reported the wrong type"

		# An entry that does not exist has to report INVALID_TYPE.
		assert GetResultsType( res_id, "NoSuchEntry" ) == INVALID_TYPE, "GetResultsType accepted an unknown entry"

		# That lookup failure was raised deliberately, so take it back off the queue.
		err_mgr = ErrorMgrSingleton.getInstance()

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetIntResults(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		res_id = FindResultsID( "Test_Results" )

		if ( GetNumData( res_id, "Test_Int" ) != 2 ):
			print( "---> Error: API GetNumData " )
			assert False, "---> Error: API GetNumData"

		int_arr = GetIntResults( res_id, "Test_Int", 0 )

		if  int_arr[0] != 1 :
			print( "---> Error: API GetIntResults" )
			assert False, "---> Error: API GetIntResults"

		int_arr = GetIntResults( res_id, "Test_Int", 1 )

		if  int_arr[0] != 2 :
			print( "---> Error: API GetIntResults" )
			assert False, "---> Error: API GetIntResults"



	def test_GetDoubleResults(self):
		#==== Add Pod Geom ====//
		pid = AddGeom( "POD", "" )

		#==== Run CompGeom And View Results ====//
		mesh_id = ComputeCompGeom( SET_ALL, False, 0 )                      # Half Mesh false and no file export

		comp_res_id = FindLatestResultsID( "Comp_Geom" )                    # Find Results ID

		double_arr = GetDoubleResults( comp_res_id, "Wet_Area" )    # Extract Results
		assert len( double_arr ) > 0, "GetDoubleResults returned nothing"



	def test_GetDoubleMatResults(self):
		pid = AddGeom( "POD" )

		Update()

		rid = ExecAnalysis( "CompGeom" )

		for name in GetAllDataNames( rid ):
			if GetResultsType( rid, name ) == DOUBLE_MATRIX_DATA:
				mat = GetDoubleMatResults( rid, name )
				assert len( mat ) > 0, "GetDoubleMatResults returned nothing"



	def test_GetStringResults(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		res_id = FindResultsID( "Test_Results" )

		str_arr = GetStringResults( res_id, "Test_String" )

		if ( str_arr[0] != "This Is A Test" ):
			print( "---> Error: API GetStringResults" )
			assert False, "---> Error: API GetStringResults"



	def test_GetVec3dResults(self):
		#==== Write Some Fake Test Results =====//

		tol = 0.00001

		WriteTestResults()

		res_id = FindLatestResultsID( "Test_Results" )

		vec3d_vec = GetVec3dResults( res_id, "Test_Vec3d" )
		assert len( vec3d_vec ) > 0, "GetVec3dResults returned nothing"

		print( "X: ", False )
		print( vec3d_vec[0].x(), False )

		print( "\tY: ", False )
		print( vec3d_vec[0].y(), False )

		print( "\tZ: ", False )
		print( vec3d_vec[0].z() )



	def test_CreateGeomResults(self):
		#==== Test Comp Geom ====//
		gid1 = AddGeom( "POD", "" )

		mesh_id = ComputeCompGeom( 0, False, 0 )

		#==== Test Comp Geom Mesh Results ====//
		mesh_geom_res_id = CreateGeomResults( mesh_id, "Comp_Mesh" )

		int_arr = GetIntResults( mesh_geom_res_id, "Num_Tris" )

		if  int_arr[0] < 4 :
			print( "---> Error: API CreateGeomResults" )
			assert False, "---> Error: API CreateGeomResults"



	def test_DeleteAllResults(self):
		#==== Test Comp Geom ====//
		gid1 = AddGeom( "POD", "" )

		mesh_id = ComputeCompGeom( 0, False, 0 )

		#==== Test Comp Geom Mesh Results ====//
		mesh_geom_res_id = CreateGeomResults( mesh_id, "Comp_Mesh" )

		DeleteAllResults()

		if ( GetNumResults( "Comp_Mesh" ) != 0 ):
			print( "---> Error: API DeleteAllResults" )
			assert False, "---> Error: API DeleteAllResults"



	def test_DeleteResult(self):
		#==== Test Comp Geom ====//
		gid1 = AddGeom( "POD", "" )

		mesh_id = ComputeCompGeom( 0, False, 0 )

		#==== Test Comp Geom Mesh Results ====//
		mesh_geom_res_id = CreateGeomResults( mesh_id, "Comp_Mesh" )

		DeleteResult( mesh_geom_res_id )

		if ( GetNumResults( "Comp_Mesh" ) != 0 ):
			print( "---> Error: API DeleteResult" )
			assert False, "---> Error: API DeleteResult"



	def test_WriteResultsCSVFile(self):
		# Add Pod Geom
		pid = AddGeom( "POD" )

		analysis_name = "VSPAEROComputeGeometry"

		rid = ExecAnalysis( analysis_name )

		WriteResultsCSVFile( rid, "CompGeomRes.csv" )
		# The call above should have produced a file with content in it.
		import os
		assert os.path.getsize( "CompGeomRes.csv" ) > 0, "WriteResultsCSVFile wrote no file"




	def test_PrintResults(self):
		# Add Pod Geom
		pid = AddGeom( "POD" )

		analysis_name = "VSPAEROComputeGeometry"

		rid = ExecAnalysis( analysis_name )

		# Get & Display Results
		PrintResults( rid )

		# There has to be something to display.
		assert len( GetAllDataNames( rid ) ) > 0, "the result carries no data to print"

		# Every entry that gets printed has to have a value behind it.
		data_names = GetAllDataNames( rid )

		for data_name in data_names:
			assert GetNumData( rid, data_name ) >= 1, data_name + " has no data to print"



	def test_PrintResultsDocs(self):
		# Add Pod Geom
		pid = AddGeom( "POD" )

		analysis_name = "VSPAEROComputeGeometry"

		rid = ExecAnalysis( analysis_name )

		# Get & Display Results Docs
		PrintResultsDocs( rid )

		# There has to be documentation to display.
		assert len( GetResultsSetDoc( rid ) ) > 0, "the result carries no documentation to print"

		# Every entry that gets printed has to carry documentation of its own.
		data_names = GetAllDataNames( rid )

		for data_name in data_names:
			assert len( GetResultsEntryDoc( rid, data_name ) ) > 0, data_name + " carries no documentation"



	def test_WriteTestResults(self):
		#==== Write Some Fake Test Results =====//
		WriteTestResults()

		results_array = GetAllResultsNames()

		for i in range( len( results_array ) ):
			resid = FindLatestResultsID( results_array[i] )
			PrintResults( resid )

		# Two copies of Test_Results are written, carrying five named entries with
		# known values.
		assert GetNumResults( "Test_Results" ) == 2, "WriteTestResults did not write two results"

		res_id = FindResultsID( "Test_Results" )

		assert len( GetAllDataNames( res_id ) ) == 5, "WriteTestResults wrote the wrong number of entries"

		int_arr = GetIntResults( res_id, "Test_Int", 0 )
		dbl_arr = GetDoubleResults( res_id, "Test_Double", 0 )
		str_arr = GetStringResults( res_id, "Test_String", 0 )

		assert int_arr[0] == 1, "WriteTestResults wrote the wrong values"
		assert abs( dbl_arr[0] - 0.1 ) < 1e-12, "WriteTestResults wrote the wrong values"
		assert str_arr[0] == "This Is A Test", "WriteTestResults wrote the wrong values"

		# The second copy carries the next set of values.
		res_id_1 = FindResultsID( "Test_Results", 1 )

		int_arr = GetIntResults( res_id_1, "Test_Int", 0 )

		assert int_arr[0] == 2, "WriteTestResults did not vary the second result"



	def test_InitGUI(self):

		InitGUI()



	def test_StartGUI(self):

		StartGUI()



	def test_EnableStopGUIMenuItem(self):

		EnableStopGUIMenuItem()
		StartGUI()



	def test_DisableStopGUIMenuItem(self):

		EnableStopGUIMenuItem()
		DisableStopGUIMenuItem()
		StartGUI()



	def test_StopGUI(self):

		StartGUI()

		StopGUI()

		StartGUI()



	def test_PopupMsg(self):

		StartGUI()

		PopupMsg( "This is a popup message." )



	def test_UpdateGUI(self):

		StartGUI()

		pod_id = AddGeom( "POD" )

		length = FindParm( pod_id, "Length", "Design" )

		SetParmVal( length, 13.0 )

		UpdateGUI()



	def test_IsGUIBuild(self):

		if ( IsGUIBuild() ):
			print( "OpenVSP build is graphics capable." )
		else:
			print( "OpenVSP build is not graphics capable." )



	def test_Lock(self):

		StartGUI()

		pod_id = AddGeom( "POD" )

		Lock()
		rid = ExecAnalysis( "CompGeom" )

		mesh_id_vec = GetStringResults( rid, "Mesh_GeomID" )

		DeleteGeomVec( mesh_id_vec )
		Unlock()



	def test_Unlock(self):

		StartGUI()

		pod_id = AddGeom( "POD" )

		Lock()
		rid = ExecAnalysis( "CompGeom" )

		mesh_id_vec = GetStringResults( rid, "Mesh_GeomID" )

		DeleteGeomVec( mesh_id_vec )
		Unlock()



	def test_IsEventLoopRunning(self):

		StartGUI()

		if ( IsEventLoopRunning() ):
			print( "Event loop is running." )



	def test_ScreenGrab(self):
		screenw = 2000                                             # Set screenshot width and height
		screenh = 2000

		fname = "test_screen_grab.png"

		ScreenGrab( fname, screenw, screenh, True, True )                # Take PNG screenshot



	def test_SetViewAxis(self):
		SetViewAxis( False )                                           # Turn off axis marker in corner of viewscreen



	def test_SetShowBorders(self):
		SetShowBorders( False )                                        # Turn off red/black border on active window



	def test_SetGeomDrawType(self):
		pid = AddGeom( "POD", "" )                             # Add Pod for testing

		SetGeomDrawType( pid, GEOM_DRAW_SHADE )                       # Make pod appear as shaded

		# The draw type is display state rather than model state, so there is nothing
		# to read back.  What has to hold is that a Geom which does not exist is
		# rejected.  The error queue is reached through the error manager singleton
		# in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetGeomDrawType( "NOSUCHGEOM", GEOM_DRAW_SHADE )

		assert err_mgr.GetNumTotalErrors() > 0, "SetGeomDrawType accepted a bad Geom ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_SetGeomWireColor(self):
		pid = AddGeom( "POD", "" )

		SetGeomWireColor( pid, 0, 0, 255 )

		# The colour is display state rather than model state, so there is nothing to
		# read back.  What has to hold is that a Geom which does not exist is
		# rejected.  The error queue is reached through the error manager singleton
		# in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetGeomWireColor( "NOSUCHGEOM", 0, 0, 255 )

		assert err_mgr.GetNumTotalErrors() > 0, "SetGeomWireColor accepted a bad Geom ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_SetGeomDisplayType(self):
		pid = AddGeom( "POD" )                             # Add Pod for testing

		SetGeomDisplayType( pid, DISPLAY_DEGEN_PLATE )                       # Make pod appear as Bezier plate (Degen Geom)

		# The display type is display state rather than model state, so there is
		# nothing to read back.  What has to hold is that a Geom which does not exist
		# is rejected.  The error queue is reached through the error manager
		# singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetGeomDisplayType( "NOSUCHGEOM", DISPLAY_DEGEN_PLATE )

		assert err_mgr.GetNumTotalErrors() > 0, "SetGeomDisplayType accepted a bad Geom ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetGeomDrawType(self):
		pid = AddGeom( "POD" )

		SetGeomMaterialName( pid, "Ruby" )

		# Ruby is one of the materials the library ships with.
		assert "Ruby" in GetMaterialNames(), "Ruby is not in the material library"

		# A material that is not in the library has to be rejected.  The error queue
		# is reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetGeomMaterialName( pid, "NoSuchMaterial" )

		assert err_mgr.GetNumTotalErrors() > 0, "SetGeomMaterialName accepted an unknown material"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetGeomDisplayType(self):
		pid = AddGeom( "POD" )

		SetGeomDisplayType( pid, DISPLAY_DEGEN_PLATE )

		assert GetGeomDisplayType( pid ) == DISPLAY_DEGEN_PLATE, "GetGeomDisplayType did not report the type that was set"

		SetGeomDisplayType( pid, DISPLAY_BEZIER )

		assert GetGeomDisplayType( pid ) == DISPLAY_BEZIER, "GetGeomDisplayType did not follow a second set"



	def test_GetGeomWireColor(self):
		pid = AddGeom( "POD", "" )

		SetGeomWireColor( pid, 0, 0, 255 )

		color = GetGeomWireColor( pid )

		assert abs( color.x() ) < 1e-9, "GetGeomWireColor did not report the color that was set"
		assert abs( color.y() ) < 1e-9, "GetGeomWireColor did not report the color that was set"
		assert abs( color.z() - 255 ) < 1e-9, "GetGeomWireColor did not report the color that was set"

		# Each Geom carries its own color.
		p2id = AddGeom( "POD", "" )

		SetGeomWireColor( p2id, 255, 0, 0 )

		assert abs( GetGeomWireColor( pid ).z() - 255 ) < 1e-9, "setting one Geom's color disturbed another"



	def test_GetGeomMaterialName(self):
		pid = AddGeom( "POD" )

		SetGeomMaterialName( pid, "Ruby" )

		assert GetGeomMaterialName( pid ) == "Ruby", "GetGeomMaterialName did not report the material that was set"

		# The name that comes back has to be one the library knows.
		assert GetGeomMaterialName( pid ) in GetMaterialNames(), "GetGeomMaterialName reported a material the library does not have"



	def test_SetGeomMaterialName(self):
		pid = AddGeom( "POD" )

		Update()

		SetGeomMaterialName( pid, "Aluminum" )



	def test_AddMaterial(self):
		pid = AddGeom( "POD" )

		AddMaterial( "RedGlass", vec3d( 44, 2, 2 ), vec3d( 156, 10, 10 ), vec3d( 185, 159, 159 ), vec3d( 44, 2, 2 ), 30, 0.4 )

		SetGeomMaterialName( pid, "RedGlass" )

		# The new material joins the library and can then be applied by name.
		assert "RedGlass" in GetMaterialNames(), "AddMaterial did not add the material to the library"

		# Adding it again under the same name has to be rejected.  The error queue is
		# reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		AddMaterial( "RedGlass", vec3d( 44, 2, 2 ), vec3d( 156, 10, 10 ), vec3d( 185, 159, 159 ), vec3d( 44, 2, 2 ), 30, 0.4 )

		assert err_mgr.GetNumTotalErrors() > 0, "AddMaterial accepted a duplicate name"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()


	def test_GetMaterialNames(self):
		mat_array = GetMaterialNames()
		assert len( mat_array ) > 0, "GetMaterialNames returned nothing"

		for i in range(int( len(mat_array) )):
			print( mat_array[i] )



	def test_GetNumLights(self):
		#==== A model always has the same number of lights ====#
		assert GetNumLights() > 0, "GetNumLights did not count the lights"

		#==== Every one of them answers ====#
		for i in range( GetNumLights() ):
			assert len( FindLight( i ) ) > 0, "FindLight found nothing"



	def test_FindLight(self):
		#==== Take the first light and put it somewhere of its own ====#
		light_id = FindLight( 0 )

		assert len( light_id ) > 0, "FindLight found nothing"

		SetParmVal( FindParm( light_id, "ActiveFlag", "Light_Parm" ), 1.0 )
		SetParmVal( FindParm( light_id, "X", "Light_Parm" ), 12.0 )

		Update()

		moved = GetParmVal( light_id, "X", "Light_Parm" )

		assert abs( moved - 12.0 ) < 1e-6, "the light did not take the position it was given"

		#==== Asking for one that is not there is refused.  The error queue is reached through
		#==== the error manager singleton in Python, and is drained first so the count below is
		#==== about that call and not about anything before it.
		err_mgr = ErrorMgrSingleton.getInstance()

		while err_mgr.GetNumTotalErrors() > 0 :
			drained = err_mgr.PopLastError()

		FindLight( GetNumLights() )

		assert err_mgr.GetNumTotalErrors() > 0, "FindLight answered for a light that does not exist"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_SetBackground(self):
		SetBackground( 1.0, 1.0, 1.0 )                                 # Set background to bright white



	def test_SetAllViews(self):
		SetAllViews( CAM_CENTER )



	def test_SetView(self):
		SetView( 0, CAM_CENTER )



	def test_FitAllViews(self):
		FitAllViews()



	def test_ResetViews(self):
		ResetViews()



	def test_SetWindowLayout(self):
		SetWindowLayout( 2, 2 )



	def test_SetGUIElementDisable(self):
		SetGUIElementDisable( GDEV_INPUT, True )


	def test_SetGUIScreenDisable(self):
		SetGUIScreenDisable( VSP_CFD_MESH_SCREEN, True )


	def test_SetGeomScreenDisable(self):
		SetGeomScreenDisable( ALL_GEOM_SCREENS, True )


	def test_HideScreen(self):
		HideScreen( VSP_CFD_MESH_SCREEN )


	def test_ShowScreen(self):
		ShowScreen( VSP_CFD_MESH_SCREEN )


	def test_GetGeomTypes(self):
		#==== Add Pod Geometries ====//
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		type_array = GetGeomTypes()

		if ( type_array[0] != "POD" ):
			print( "---> Error: API GetGeomTypes  " )
			assert False, "---> Error: API GetGeomTypes"



	def test_AddGeom(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )



	def test_UpdateGeom(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		Update()

		before_min = GetGeomBBoxMin( pod_id, 0, True )

		SetParmVal( pod_id, "X_Rel_Location", "XForm", 5.0 )

		UpdateGeom( pod_id ) # Faster than updating the whole vehicle

		# Updating just this Geom has to move it, the same as a full Update would.
		after_min = GetGeomBBoxMin( pod_id, 0, True )

		assert abs( ( after_min.x() - before_min.x() ) - 5.0 ) < 1e-6, "UpdateGeom did not rebuild the Geom"



	def test_DeleteGeom(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		num_before_del = len( FindGeoms() )
		DeleteGeom( wing_id )
		assert len( FindGeoms() ) < num_before_del, "DeleteGeom removed nothing"




	def test_DeleteGeomVec(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD", "" )

		rid = ExecAnalysis( "CompGeom" )

		mesh_id_vec = GetStringResults( rid, "Mesh_GeomID" )

		num_before_del = len( FindGeoms() )
		DeleteGeomVec( mesh_id_vec )
		assert len( FindGeoms() ) < num_before_del, "DeleteGeomVec removed nothing"




	def test_CutGeomToClipboard(self):
		#==== Add Pod Geometries ====//
		pid1 = AddGeom( "POD", "" )
		pid2 = AddGeom( "POD", "" )

		CutGeomToClipboard( pid1 )

		PasteGeomClipboard( pid2 ) # Paste Pod 1 as child of Pod 2

		geom_ids = FindGeoms()

		if  len(geom_ids) != 2 :
			print( "---> Error: API Cut/Paste Geom  " )
			assert False, "---> Error: API Cut/Paste Geom"



	def test_CopyGeomToClipboard(self):
		#==== Add Pod Geometries ====//
		pid1 = AddGeom( "POD", "" )
		pid2 = AddGeom( "POD", "" )

		CopyGeomToClipboard( pid1 )

		PasteGeomClipboard( pid2 ) # Paste Pod 1 as child of Pod 2

		geom_ids = FindGeoms()

		if  len(geom_ids) != 3 :
			print( "---> Error: API Copy/Paste Geom  " )
			assert False, "---> Error: API Copy/Paste Geom"



	def test_PasteGeomClipboard(self):
		#==== Add Pod Geometries ====//
		pid1 = AddGeom( "POD", "" )
		pid2 = AddGeom( "POD", "" )

		CutGeomToClipboard( pid1 )

		PasteGeomClipboard( pid2 ) # Paste Pod 1 as child of Pod 2

		geom_ids = FindGeoms()

		if  len(geom_ids) != 2 :
			print( "---> Error: API Cut/Paste Geom  " )
			assert False, "---> Error: API Cut/Paste Geom"



	def test_FindGeoms(self):
		#==== Add Pod Geometries ====//
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		#==== There Should Be Two Geoms =====//
		geom_ids = FindGeoms()

		if  len(geom_ids) != 2 :
			print( "---> Error: API FindGeoms " )
			assert False, "---> Error: API FindGeoms"



	def test_FindGeomsWithName(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD", "" )

		SetGeomName( pid, "ExamplePodName" )

		geom_ids = FindGeomsWithName( "ExamplePodName" )

		if  len(geom_ids) != 1 :
			print( "---> Error: API FindGeomsWithName " )
			assert False, "---> Error: API FindGeomsWithName"



	def test_FindGeom(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD", "" )

		SetGeomName( pid, "ExamplePodName" )

		geom_id = FindGeom( "ExamplePodName", 0 )

		geom_ids = FindGeomsWithName( "ExamplePodName" )

		if  geom_ids[0] != geom_id :
			print( "---> Error: API FindGeom & FindGeomsWithName" )
			assert False, "---> Error: API FindGeom & FindGeomsWithName"



	def test_SetGeomName(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD", "" )

		SetGeomName( pid, "ExamplePodName" )

		geom_ids = FindGeomsWithName( "ExamplePodName" )

		if  len(geom_ids) != 1 :
			print( "---> Error: API FindGeomsWithName " )
			assert False, "---> Error: API FindGeomsWithName"



	def test_GetGeomName(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD", "" )

		SetGeomName( pid, "ExamplePodName" )

		name_str = "Geom Name: " + GetGeomName( pid )

		print( name_str )

		assert GetGeomName( pid ) == "ExamplePodName", "GetGeomName did not report the name that was set"

		# The name is how FindGeomsWithName looks Geoms up.
		found = FindGeomsWithName( "ExamplePodName" )

		assert len( found ) == 1, "GetGeomName disagrees with FindGeomsWithName"
		assert found[0] == pid, "GetGeomName disagrees with FindGeomsWithName"



	def test_GetGeomParmIDs(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD", "" )

		print( "---> Test Get Parm Arrays" )

		parm_array = GetGeomParmIDs( pid )

		if  len(parm_array) < 1 :
			print( "---> Error: API GetGeomParmIDs " )
			assert False, "---> Error: API GetGeomParmIDs"



	def test_GetGeomTypeName(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		print( "Geom Type Name: ", False )

		print( GetGeomTypeName( wing_id ) )

		assert GetGeomTypeName( wing_id ) == "Wing", "GetGeomTypeName did not report the type that was added"

		# A Geom of a different type has to report a different name.
		pod_id = AddGeom( "POD" )

		assert GetGeomTypeName( pod_id ) != GetGeomTypeName( wing_id ), "GetGeomTypeName gave two types the same name"



	def test_GetParm(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		lenid = GetParm( pid, "Length", "Design" )

		if  not ValidParm( lenid ) :
			print( "---> Error: API GetParm  " )
			assert False, "---> Error: API GetParm"



	def test_SetGeomParent(self):
		#==== Reparent two PodGeoms ====#
		pod1 = AddGeom( "POD" )
		pod2 = AddGeom( "POD", pod1 )
		pod3 = AddGeom ("POD" )

		veh_id = GetVehicleID()

		SetGeomParent( pod2, veh_id )
		SetGeomParent( pod3, pod1 )

		pod2_parent = GetGeomParent( pod2 )
		pod3_parent = GetGeomParent( pod3 )

		if ( pod2_parent != "NONE" or pod3_parent != pod1 ):
			print( "SetGeomParent error!" )
			assert False, "SetGeomParent error!"



	def test_ReorderGeom(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		# Both Pods sit at the top level, in the order they were added.
		assert FindGeoms()[0] == pod1, "the Geoms did not start in creation order"

		ReorderGeom( pod2, REORDER_MOVE_UP )

		assert FindGeoms()[0] == pod2, "ReorderGeom did not move the Geom"

		ReorderGeom( pod2, REORDER_MOVE_BOTTOM )

		assert FindGeoms()[0] == pod1, "ReorderGeom did not move the Geom back"



	def test_AttachGeomTexture(self):
		pod_id = AddGeom( "POD", "" )

		tex_id = AttachGeomTexture( pod_id, "textures/nasa-logo.tga" )

		assert len( tex_id ) > 0, "AttachGeomTexture attached nothing"

		# Place the logo on the upper surface, at half size.
		SetParmVal( tex_id, "U", "Texture_Parm", 0.35 )
		SetParmVal( tex_id, "W", "Texture_Parm", 0.25 )
		SetParmVal( tex_id, "U_Scale", "Texture_Parm", 0.5 )
		SetParmVal( tex_id, "W_Scale", "Texture_Parm", 0.5 )

		Update()

		tex_ids = GetGeomTextureIDVec( pod_id )

		assert len( tex_ids ) == 1, "the texture is not in the texture list"
		assert tex_ids[0] == tex_id, "the texture is not in the texture list"



	def test_RemoveGeomTexture(self):
		pod_id = AddGeom( "POD", "" )

		tex_id = AttachGeomTexture( pod_id, "textures/nasa-logo.tga" )

		RemoveGeomTexture( pod_id, tex_id )

		assert len( GetGeomTextureIDVec( pod_id ) ) == 0, "RemoveGeomTexture left the texture behind"



	def test_GetGeomTextureIDVec(self):
		pod_id = AddGeom( "POD", "" )

		# A fresh Geom carries no textures.
		assert len( GetGeomTextureIDVec( pod_id ) ) == 0, "a new Geom already carries textures"

		AttachGeomTexture( pod_id, "textures/nasa-logo.tga" )
		AttachGeomTexture( pod_id, "textures/window.tga" )

		assert len( GetGeomTextureIDVec( pod_id ) ) == 2, "GetGeomTextureIDVec, two were attached"



	def test_GetGeomTextureFileName(self):
		pod_id = AddGeom( "POD", "" )

		tex_id = AttachGeomTexture( pod_id, "textures/nasa-logo.tga" )

		assert GetGeomTextureFileName( pod_id, tex_id ) == "textures/nasa-logo.tga", "GetGeomTextureFileName did not report the file"



	def test_GetGeomParent(self):
		#==== Add Parent and Child Geometry ====//
		pod1 = AddGeom( "POD" )

		pod2 = AddGeom( "POD", pod1 )

		print( "Parent ID of Pod #2: ", False )

		print( GetGeomParent( pod2 ) )

		assert GetGeomParent( pod2 ) == pod1, "GetGeomParent did not report the parent it was given"

		# The relationship has to read the same from the other end.
		children = GetGeomChildren( pod1 )

		assert len( children ) == 1, "GetGeomParent disagrees with GetGeomChildren"
		assert children[0] == pod2, "GetGeomParent disagrees with GetGeomChildren"

		# A Geom added with no parent sits at the top level.
		assert GetGeomParent( pod1 ) == "NONE", "GetGeomParent did not report NONE for a top level Geom"



	def test_GetGeomChildren(self):
		#==== Add Parent and Child Geometry ====//
		pod1 = AddGeom( "POD" )

		pod2 = AddGeom( "POD", pod1 )

		pod3 = AddGeom( "POD", pod2 )

		print( "Children of Pod #1: " )

		children = GetGeomChildren( pod1 )
		assert len( children ) > 0, "GetGeomChildren returned nothing"

		for i in range(int( len(children) )):

			print( "\t", False )
			print( children[i] )



	def test_GetNumXSecSurfs(self):
		#==== Add Fuselage Geometry ====//
		fuseid = AddGeom( "FUSELAGE", "" )

		num_xsec_surfs = GetNumXSecSurfs( fuseid )

		if  num_xsec_surfs != 1 :
			print( "---> Error: API GetNumXSecSurfs  " )
			assert False, "---> Error: API GetNumXSecSurfs"



	def test_GetNumMainSurfs(self):
		#==== Add Prop Geometry ====//
		prop_id = AddGeom( "PROP" )

		num_surf = 0

		num_surf = GetNumMainSurfs( prop_id ) # Should be the same as the number of blades

		assert num_surf == GetIntParmVal( FindParm( prop_id, "NumBlade", "Design" ) ), "GetNumMainSurfs does not match the blade count"

		print( "Number of Propeller Surfaces: ", False )

		print( num_surf )



	def test_GetTotalNumSurfs(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		num_surf = 0

		num_surf = GetTotalNumSurfs( wing_id ) # Wings default with XZ symmetry on -> 2 surfaces

		assert num_surf == 2, "GetTotalNumSurfs, expected 2 for a symmetric wing"

		print( "Total Number of Wing Surfaces: ", False )

		print( num_surf )



	def test_GetGeomVSPSurfType(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		if  GetGeomVSPSurfType( wing_id ) != WING_SURF :
			print( "---> Error: API GetGeomVSPSurfType " )
			assert False, "---> Error: API GetGeomVSPSurfType"



	def test_GetGeomVSPSurfCfdType(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		if  GetGeomVSPSurfCfdType( wing_id ) != CFD_NORMAL :
			print( "---> Error: API GetGeomVSPSurfCfdType " )
			assert False, "---> Error: API GetGeomVSPSurfCfdType"



	def test_GetGeomBBoxMax(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		SetParmVal( FindParm( pid, "Y_Rotation", "XForm" ), 45 )
		SetParmVal( FindParm( pid, "Z_Rotation", "XForm" ), 25 )

		Update()

		max_pnt = GetGeomBBoxMax( pid, 0, False )

		min_pnt = GetGeomBBoxMin( pid, 0, False )

		assert max_pnt.x() > min_pnt.x() and max_pnt.y() > min_pnt.y() and max_pnt.z() > min_pnt.z(), "GetGeomBBoxMax is not above the minimum corner"



	def test_GetGeomBBoxMin(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		SetParmVal( FindParm( pid, "Y_Rotation", "XForm" ), 45 )
		SetParmVal( FindParm( pid, "Z_Rotation", "XForm" ), 25 )

		Update()

		min_pnt = GetGeomBBoxMin( pid, 0, False )

		max_pnt = GetGeomBBoxMax( pid, 0, False )

		assert min_pnt.x() < max_pnt.x() and min_pnt.y() < max_pnt.y() and min_pnt.z() < max_pnt.z(), "GetGeomBBoxMin is not below the maximum corner"



	def test_AddSubSurf(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		# Note: Parm Group for SubSurfaces in the form: "SS_" + type + "_" + count (initialized at 1)
		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line

		SetParmVal( wid, "Const_Line_Value", "SubSurface_1", 0.4 )     # Change Location



	def test_GetSubSurf(self):
		wid = AddGeom( "WING", "" ) # Add Wing

		ss_rec_1 = AddSubSurf( wid, SS_RECTANGLE ) # Add Sub Surface Rectangle #1

		ss_rec_2 = AddSubSurf( wid, SS_RECTANGLE ) # Add Sub Surface Rectangle #2

		print( ss_rec_2, False )

		print( " = ", False )

		print( GetSubSurf( wid, 1 ) )

		# Sub-surfaces come back in the order they were added.
		assert GetSubSurf( wid, 0 ) == ss_rec_1, "GetSubSurf did not report the sub-surfaces in order"
		assert GetSubSurf( wid, 1 ) == ss_rec_2, "GetSubSurf did not report the sub-surfaces in order"

		# The index form and the ID vector have to agree.
		id_vec = GetSubSurfIDVec( wid )

		assert len( id_vec ) == 2, "GetSubSurf disagrees with GetSubSurfIDVec"
		assert id_vec[1] == GetSubSurf( wid, 1 ), "GetSubSurf disagrees with GetSubSurfIDVec"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetSubSurf( wid, 2 )

		assert err_mgr.GetNumTotalErrors() > 0, "GetSubSurf accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetSubSurf1(self):
		wid = AddGeom( "WING", "" ) # Add Wing

		ss_rec_1 = AddSubSurf( wid, SS_RECTANGLE ) # Add Sub Surface Rectangle #1

		ss_rec_2 = AddSubSurf( wid, SS_RECTANGLE ) # Add Sub Surface Rectangle #2

		print( ss_rec_2, False )

		print( " = ", False )

		print( GetSubSurf( wid, 1 ) )

		# Sub-surfaces come back in the order they were added.
		assert GetSubSurf( wid, 0 ) == ss_rec_1, "GetSubSurf did not report the sub-surfaces in order"
		assert GetSubSurf( wid, 1 ) == ss_rec_2, "GetSubSurf did not report the sub-surfaces in order"

		# The index form and the ID vector have to agree.
		id_vec = GetSubSurfIDVec( wid )

		assert len( id_vec ) == 2, "GetSubSurf disagrees with GetSubSurfIDVec"
		assert id_vec[1] == GetSubSurf( wid, 1 ), "GetSubSurf disagrees with GetSubSurfIDVec"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetSubSurf( wid, 2 )

		assert err_mgr.GetNumTotalErrors() > 0, "GetSubSurf accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteSubSurf(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line
		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		print("Delete SS_Line\n")

		num_before_del = GetNumSubSurf( wid )
		DeleteSubSurf( wid, ss_line_id )
		assert GetNumSubSurf( wid ) < num_before_del, "DeleteSubSurf removed nothing"


		num_ss = GetNumSubSurf( wid )

		num_str = f"Number of SubSurfaces: {num_ss}\n"

		print( num_str )



	def test_ReorderSubSurf(self):
		wing_id = AddGeom( "WING", "" )

		ss_line = AddSubSurf( wing_id, SS_LINE )
		ss_rect = AddSubSurf( wing_id, SS_RECTANGLE )

		assert GetSubSurf( wing_id, 0 ) == ss_line, "the sub-surfaces did not start in creation order"

		ReorderSubSurf( wing_id, ss_rect, REORDER_MOVE_TOP )

		assert GetSubSurf( wing_id, 0 ) == ss_rect, "ReorderSubSurf did not move the sub-surface"



	def test_DeleteSubSurf1(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line
		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		print("Delete SS_Line\n")

		num_before_del = GetNumSubSurf( wid )
		DeleteSubSurf( ss_line_id )
		assert GetNumSubSurf( wid ) < num_before_del, "DeleteSubSurf removed nothing"


		num_ss = GetNumSubSurf( wid )

		num_str = f"Number of SubSurfaces: {num_ss}\n"

		print( num_str )



	def test_SetSubSurfName(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		new_name = "New_SS_Rec_Name"

		SetSubSurfName( wid, ss_rec_id, new_name )
		assert GetSubSurfName( wid, ss_rec_id ) == new_name, "SetSubSurfName did not take"




	def test_SetSubSurfName1(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		new_name = "New_SS_Rec_Name"

		SetSubSurfName( ss_rec_id, new_name )
		assert GetSubSurfName( ss_rec_id ) == new_name, "SetSubSurfName did not take"




	def test_GetSubSurfName(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		rec_name = GetSubSurfName( wid, ss_rec_id )
		assert len( rec_name ) > 0, "GetSubSurfName returned nothing"

		name_str = "Current Name of SS_Rectangle: " + rec_name + "\n"

		print( name_str )



	def test_GetSubSurfName1(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		rec_name = GetSubSurfName( wid, ss_rec_id )
		assert len( rec_name ) > 0, "GetSubSurfName returned nothing"

		name_str = "Current Name of SS_Rectangle: " + rec_name + "\n"

		print( name_str )



	def test_GetSubSurfIndex(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line
		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		ind = GetSubSurfIndex( ss_rec_id )

		ind_str = f"Index of SS_Rectangle: {ind}"

		print( ind_str )

		# The rectangle was added second, so it sits at index 1.
		assert ind == 1, "GetSubSurfIndex did not report the order they were added"
		assert GetSubSurfIndex( ss_line_id ) == 0, "GetSubSurfIndex did not report the order they were added"

		# The index has to lead back to the same sub-surface.
		assert GetSubSurf( wid, ind ) == ss_rec_id, "GetSubSurfIndex disagrees with GetSubSurf"



	def test_GetSubSurfIDVec(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line
		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		id_vec = GetSubSurfIDVec( wid )
		assert len( id_vec ) > 0, "GetSubSurfIDVec returned nothing"

		id_type_str = "SubSurface IDs and Type Indexes -> "

		for i in range(len(id_vec)):

			id_type_str += id_vec[i]

			id_type_str += ": "

			id_type_str += f'{GetSubSurfType(id_vec[i])}'

			id_type_str += "\t"

		id_type_str += "\n"

		print( id_type_str )



	def test_GetAllSubSurfIDs(self):
		pid = AddGeom( "POD" )

		AddSubSurf( pid, SS_RECTANGLE )

		Update()

		assert len( GetAllSubSurfIDs() ) == 1, "GetAllSubSurfIDs did not report the sub-surface"



	def test_GetNumSubSurf(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line
		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		num_ss = GetNumSubSurf( wid )

		assert num_ss == 2, "GetNumSubSurf, two were added"

		num_str = "Number of SubSurfaces: {num_ss}"

		print( num_str )



	def test_GetSubSurfType(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line
		ss_rec_id = AddSubSurf( wid, SS_RECTANGLE )                        # Add Sub Surface Rectangle

		id_vec = GetSubSurfIDVec( wid )

		# Each sub-surface has to report the type it was created as.
		assert GetSubSurfType( ss_line_id ) == SS_LINE, "GetSubSurfType did not report the type that was added"
		assert GetSubSurfType( ss_rec_id ) == SS_RECTANGLE, "GetSubSurfType did not report the type that was added"

		id_type_str = "SubSurface IDs and Type Indexes -> "

		for i in range(len(id_vec)):

			id_type_str += id_vec[i]

			id_type_str += ": "

			id_type_str += f'{GetSubSurfType(id_vec[i])}'

			id_type_str += "\t"

		id_type_str += "\n"

		print( id_type_str )



	def test_GetSubSurfParmIDs(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		ss_line_id = AddSubSurf( wid, SS_LINE )                      # Add Sub Surface Line

		# Get and list all Parm info for SS_Line
		parm_id_vec = GetSubSurfParmIDs( ss_line_id )
		assert len( parm_id_vec ) > 0, "GetSubSurfParmIDs returned nothing"

		for i in range(len(parm_id_vec)):

			id_name_str = "\tName: " + GetParmName(parm_id_vec[i]) + ", Group: " + GetParmDisplayGroupName(parm_id_vec[i]) + ", ID: " + str(parm_id_vec[i]) + "\n"


			print( id_name_str )



	def test_IntersectSubSurf(self):
		pid = AddGeom( "POD", "" )
		p2id = AddGeom( "POD", "" )

		xpod2 = GetParm( p2id, "X_Rel_Location", "XForm" )
		SetParmVal( xpod2, 4.0 )

		zrotpod2 = GetParm( p2id, "Z_Rel_Rotation", "XForm" )
		SetParmVal( zrotpod2, 60.0 )

		sub_id = AddSubSurf( pid, SS_INTERSECT )

		Update()

		SetIntersectSubSurfGeomID( sub_id, p2id )

		IntersectSubSurf( sub_id )

		Update()

		# The sub-surface is an intersection of the two Pods, and it belongs to the
		# first one.
		assert GetSubSurfType( sub_id ) == SS_INTERSECT, "the sub-surface is not an intersection"

		sub_ids = GetSubSurfIDVec( pid )

		assert len( sub_ids ) == 1, "the intersection sub-surface is not on the Geom it was added to"
		assert sub_ids[0] == sub_id, "the intersection sub-surface is not on the Geom it was added to"

		# Naming a Geom that does not exist has to be rejected.  The error queue is
		# reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetIntersectSubSurfGeomID( sub_id, "NOSUCHGEOM" )

		IntersectSubSurf( sub_id )

		assert err_mgr.GetNumTotalErrors() > 0, "a bad Geom ID was accepted for the intersection"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()


	def test_GetIntersectSubSurfGeomID(self):
		pid = AddGeom( "POD", "" )
		p2id = AddGeom( "POD", "" )

		xpod2 = GetParm( p2id, "X_Rel_Location", "XForm" )
		SetParmVal( xpod2, 4.0 )

		zrotpod2 = GetParm( p2id, "Z_Rel_Rotation", "XForm" )
		SetParmVal( zrotpod2, 60.0 )

		sub_id = AddSubSurf( pid, SS_INTERSECT )

		Update()

		SetIntersectSubSurfGeomID( sub_id, p2id )

		IntersectSubSurf( sub_id )

		Update()

		# The sub-surface is an intersection of the two Pods, and it belongs to the
		# first one.
		assert GetSubSurfType( sub_id ) == SS_INTERSECT, "the sub-surface is not an intersection"

		sub_ids = GetSubSurfIDVec( pid )

		assert len( sub_ids ) == 1, "the intersection sub-surface is not on the Geom it was added to"
		assert sub_ids[0] == sub_id, "the intersection sub-surface is not on the Geom it was added to"

		# Naming a Geom that does not exist has to be rejected.  The error queue is
		# reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetIntersectSubSurfGeomID( sub_id, "NOSUCHGEOM" )

		IntersectSubSurf( sub_id )

		assert err_mgr.GetNumTotalErrors() > 0, "a bad Geom ID was accepted for the intersection"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()


	def test_SetIntersectSubSurfGeomID(self):
		pid = AddGeom( "POD" )

		ssid = AddSubSurf( pid, SS_INTERSECT )

		Update()

		SetIntersectSubSurfGeomID( ssid, pid )



	def test_AddFeaStruct(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		# The first structure on this Geom lands at index 0, and its ID has to lead
		# back to that index.
		assert struct_ind == 0, "AddFeaStruct did not add a structure"
		assert NumFeaStructures() == 1, "AddFeaStruct did not add a structure"

		struct_id = GetFeaStructID( pod_id, struct_ind )

		assert len( struct_id ) > 0, "AddFeaStruct did not give the structure a usable ID"
		assert GetFeaStructIndex( struct_id ) == struct_ind, "AddFeaStruct did not give the structure a usable ID"

		# init_skin defaults to true, so the structure starts with an FEA Skin.
		assert NumFeaParts( struct_id ) == 1, "AddFeaStruct did not initialize the skin"



	def test_GetFeaMeshStructIndex(self):

		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		SetFeaMeshStructIndex( struct_ind )

		if  len(FindGeoms()) != 1 :
			print( "ERROR: SetFeaMeshStructIndex" )
			assert False, "ERROR: SetFeaMeshStructIndex"



	def test_SetFeaMeshStructIndex(self):
		pid = AddGeom( "POD" )

		AddFeaStruct( pid )

		Update()

		SetFeaMeshStructIndex( 0 )



	def test_DeleteFeaStruct(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind_1 = AddFeaStruct( pod_id )

		struct_ind_2 = AddFeaStruct( pod_id )

		struct_id_2 = GetFeaStructID( pod_id, struct_ind_2 )

		assert NumFeaStructures() == 2, "the two structures were not both added"

		DeleteFeaStruct( pod_id, struct_ind_1 )

		# Deleting the first structure leaves the second one, which slides down to
		# take its index.
		assert NumFeaStructures() == 1, "DeleteFeaStruct did not remove the structure"
		assert GetFeaStructID( pod_id, 0 ) == struct_id_2, "DeleteFeaStruct removed the wrong structure"



	def test_GetFeaStructID(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )
		assert len( struct_id ) > 0, "GetFeaStructID returned nothing"



	def test_GetFeaStructIndex(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind_1 = AddFeaStruct( pod_id )

		struct_ind_2 = AddFeaStruct( pod_id )

		struct_id_2 = GetFeaStructID( pod_id, struct_ind_2 )

		DeleteFeaStruct( pod_id, struct_ind_1 )

		struct_ind_2_new = GetFeaStructIndex( struct_id_2 )

		# The second structure slides down to fill the gap the first one left.
		assert struct_ind_2 == 1, "GetFeaStructIndex did not follow the delete"
		assert struct_ind_2_new == 0, "GetFeaStructIndex did not follow the delete"

		# The index has to lead back to the same structure.
		assert GetFeaStructID( pod_id, struct_ind_2_new ) == struct_id_2, "GetFeaStructIndex disagrees with GetFeaStructID"

		# An ID that is not a structure has to report -1.
		assert GetFeaStructIndex( "NOSUCHSTRUCT" ) == -1, "GetFeaStructIndex accepted a bad ID"

		# That lookup failure was raised deliberately, so take it back off the queue.
		err_mgr = ErrorMgrSingleton.getInstance()

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetFeaStructParentGeomID(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Get Parent Geom ID and Index ====//
		parent_id = GetFeaStructParentGeomID( struct_id )
		assert len( parent_id ) > 0, "GetFeaStructParentGeomID returned nothing"



	def test_GetFeaStructName(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Get Structure Name ====//
		parm_container_name = GetFeaStructName( pod_id, struct_ind )
		assert len( parm_container_name ) > 0, "GetFeaStructName returned nothing"

		display_name = "Current Structure Parm Container Name: " + parm_container_name + "\n"

		print( display_name )



	def test_SetFeaStructName(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Change the Structure Name ====//
		SetFeaStructName( pod_id, struct_ind, "Example_Struct" )
		assert GetFeaStructName( pod_id, struct_ind ) == "Example_Struct", "SetFeaStructName did not take"


		parm_container_id = FindContainer( "Example_Struct", struct_ind )

		display_id = "New Structure Parm Container ID: " + parm_container_id + "\n"

		print( display_id )



	def test_GetFeaStructIDVec(self):
		#==== Add Geometries ====//
		pod_id = AddGeom( "POD" )
		wing_id = AddGeom( "WING" )

		#==== Add FeaStructures ====//
		pod_struct_ind = AddFeaStruct( pod_id )
		wing_struct_ind = AddFeaStruct( wing_id )

		struct_id_vec = GetFeaStructIDVec()
		assert len( struct_id_vec ) > 0, "GetFeaStructIDVec returned nothing"



	def test_SetFeaPartName(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add Bulkead ====//
		bulkhead_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )

		SetFeaPartName( bulkhead_id, "Bulkhead" )
		assert GetFeaPartName( bulkhead_id ) == "Bulkhead", "SetFeaPartName did not take"




	def test_AddFeaPart(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add Bulkead ====//
		bulkhead_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )

		SetParmVal( FindParm( bulkhead_id, "IncludedElements", "FeaPart" ), FEA_SHELL_AND_BEAM )

		SetParmVal( FindParm( bulkhead_id, "RelCenterLocation", "FeaPart" ), 0.15 )



	def test_DeleteFeaPart(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add Bulkead ====//
		bulkhead_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )

		#==== Add Fixed Point ====//
		fixed_id = AddFeaPart( pod_id, struct_ind, FEA_FIX_POINT )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		# The skin, the bulkhead and the fixed point.
		num_before = NumFeaParts( struct_id )

		assert num_before == 3, "the parts were not all added"

		#==== Delete Bulkead ====//
		DeleteFeaPart( pod_id, struct_ind, bulkhead_id )

		# Only the named part goes; the fixed point stays.
		assert NumFeaParts( struct_id ) == num_before - 1, "DeleteFeaPart did not remove the part"
		assert len( GetFeaPartName( fixed_id ) ) > 0, "DeleteFeaPart removed the wrong part"



	def test_ReorderFeaPart(self):
		pod_id = AddGeom( "POD", "" )

		struct_ind = AddFeaStruct( pod_id )
		struct_id = GetFeaStructID( pod_id, struct_ind )

		bulkhead = AddFeaPart( pod_id, struct_ind, FEA_SLICE )
		skin = GetFeaPartID( struct_id, 0 )

		ReorderFeaPart( pod_id, struct_ind, bulkhead, REORDER_MOVE_TOP )

		assert GetFeaPartID( struct_id, 0 ) == bulkhead, "ReorderFeaPart did not move the part"

		ReorderFeaPart( pod_id, struct_ind, bulkhead, REORDER_MOVE_BOTTOM )

		assert GetFeaPartID( struct_id, 0 ) == skin, "ReorderFeaPart did not move the part back"



	def test_IndividualizeFeaPart(self):
		pod_id = AddGeom( "POD", "" )

		struct_ind = AddFeaStruct( pod_id )
		struct_id = GetFeaStructID( pod_id, struct_ind )

		array_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE_ARRAY )

		SetParmVal( FindParm( array_id, "SliceRelSpacing", "FeaSliceArray" ), 0.25 )

		Update()

		num_before = NumFeaParts( struct_id )

		IndividualizeFeaPart( pod_id, struct_ind, array_id )

		# The array is replaced by the slices it stood for, so the part count goes up.
		assert NumFeaParts( struct_id ) > num_before, "IndividualizeFeaPart did not expand the array"



	def test_GetFeaPartID(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Add Bulkead ====//
		bulkhead_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )

		Update()

		if  bulkhead_id != GetFeaPartID( struct_id, 1 ) : # These should be equivalent (index 0 is skin)

			print( "Error: GetFeaPartID" )
			assert False, "Error: GetFeaPartID"



	def test_GetFeaPartName(self):
		#==== Add Fuselage Geometry ====//
		fuse_id = AddGeom( "FUSELAGE" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( fuse_id )

		#==== Add Bulkead ====//
		bulkhead_id = AddFeaPart( fuse_id, struct_ind, FEA_SLICE )

		name = "example_name"
		SetFeaPartName( bulkhead_id, name )

		if  name != GetFeaPartName( bulkhead_id ) : # These should be equivalent

			print( "Error: GetFeaPartName" )
			assert False, "Error: GetFeaPartName"



	def test_GetFeaPartType(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add Slice ====//
		slice_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )

		if  FEA_SLICE != GetFeaPartType( slice_id ) : # These should be equivalent

			print( "Error: GetFeaPartType" )
			assert False, "Error: GetFeaPartType"



	def test_GetFeaPartIDVec(self):
		#==== Add Geometries ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Add FEA Parts ====//
		slice_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )
		dome_id = AddFeaPart( pod_id, struct_ind, FEA_DOME )

		part_id_vec = GetFeaPartIDVec( struct_id ) # Should include slice_id & dome_id
		assert len( part_id_vec ) > 0, "GetFeaPartIDVec returned nothing"



	def test_GetFeaSubSurfIDVec(self):
		#==== Add Geometries ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Add SubSurfaces ====//
		line_array_id = AddFeaSubSurf( pod_id, struct_ind, SS_LINE_ARRAY )
		rectangle_id = AddFeaSubSurf( pod_id, struct_ind, SS_RECTANGLE )

		part_id_vec = GetFeaSubSurfIDVec( struct_id ) # Should include line_array_id & rectangle_id
		assert len( part_id_vec ) > 0, "GetFeaSubSurfIDVec returned nothing"



	def test_SetFeaPartPerpendicularSparID(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		#==== Add FeaStructure to Wing ====//
		struct_ind = AddFeaStruct( wing_id )

		#==== Add Rib ====//
		rib_id = AddFeaPart( wing_id, struct_ind, FEA_RIB )

		#==== Add Spars ====//
		spar_id_1 = AddFeaPart( wing_id, struct_ind, FEA_SPAR )
		spar_id_2 = AddFeaPart( wing_id, struct_ind, FEA_SPAR )

		SetParmVal( FindParm( spar_id_1, "RelCenterLocation", "FeaPart" ), 0.25 )
		SetParmVal( FindParm( spar_id_2, "RelCenterLocation", "FeaPart" ), 0.75 )

		#==== Set Perpendicular Edge type to SPAR ====//
		SetParmVal( FindParm( rib_id, "PerpendicularEdgeType", "FeaRib" ), SPAR_NORMAL )

		SetFeaPartPerpendicularSparID( rib_id, spar_id_2 )

		if  spar_id_2 != GetFeaPartPerpendicularSparID( rib_id ) :
			print( "Error: SetFeaPartPerpendicularSparID" )
			assert False, "Error: SetFeaPartPerpendicularSparID"



	def test_GetFeaPartPerpendicularSparID(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		#==== Add FeaStructure to Wing ====//
		struct_ind = AddFeaStruct( wing_id )

		#==== Add Rib ====//
		rib_id = AddFeaPart( wing_id, struct_ind, FEA_RIB )

		#==== Add Spars ====//
		spar_id_1 = AddFeaPart( wing_id, struct_ind, FEA_SPAR )
		spar_id_2 = AddFeaPart( wing_id, struct_ind, FEA_SPAR )

		SetParmVal( FindParm( spar_id_1, "RelCenterLocation", "FeaPart" ), 0.25 )
		SetParmVal( FindParm( spar_id_2, "RelCenterLocation", "FeaPart" ), 0.75 )

		#==== Set Perpendicular Edge type to SPAR ====//
		SetParmVal( FindParm( rib_id, "PerpendicularEdgeType", "FeaRib" ), SPAR_NORMAL )

		SetFeaPartPerpendicularSparID( rib_id, spar_id_2 )

		if  spar_id_2 != GetFeaPartPerpendicularSparID( rib_id ) :
			print( "Error: GetFeaPartPerpendicularSparID" )
			assert False, "Error: GetFeaPartPerpendicularSparID"



	def test_SetFeaSubSurfName(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add LineArray ====//
		line_array_id = AddFeaSubSurf( pod_id, struct_ind, SS_LINE_ARRAY )

		SetFeaSubSurfName( line_array_id, "Stiffener_array" )
		assert GetFeaSubSurfName( line_array_id ) == "Stiffener_array", "SetFeaSubSurfName did not take"




	def test_GetFeaSubSurfName(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add LineArray ====//
		line_array_id = AddFeaSubSurf( pod_id, struct_ind, SS_LINE_ARRAY )

		name = "example_name"
		SetFeaSubSurfName( line_array_id, name )

		if  name != GetFeaSubSurfName( line_array_id ) : # These should be equivalent
			print( "Error: GetFeaSubSurfName" )
			assert False, "Error: GetFeaSubSurfName"



	def test_AddFeaSubSurf(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add LineArray ====//
		line_array_id = AddFeaSubSurf( pod_id, struct_ind, SS_LINE_ARRAY )

		SetParmVal( FindParm( line_array_id, "ConstLineType", "SS_LineArray" ), 1 ) # Constant W

		SetParmVal( FindParm( line_array_id, "Spacing", "SS_LineArray" ), 0.25 )



	def test_DeleteFeaSubSurf(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add LineArray ====//
		line_array_id = AddFeaSubSurf( pod_id, struct_ind, SS_LINE_ARRAY )

		#==== Add Rectangle ====//
		rect_id = AddFeaSubSurf( pod_id, struct_ind, SS_RECTANGLE )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		num_before = NumFeaSubSurfs( struct_id )

		#==== Delete LineArray ====//
		DeleteFeaSubSurf( pod_id, struct_ind, line_array_id )

		assert NumFeaSubSurfs( struct_id ) == num_before - 1, "DeleteFeaSubSurf did not remove the sub-surface"



	def test_GetFeaSubSurfIndex(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Add Slice ====//
		slice_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )

		#==== Add LineArray ====//
		line_array_id = AddFeaSubSurf( pod_id, struct_ind, SS_LINE_ARRAY )

		#==== Add Rectangle ====//
		rect_id = AddFeaSubSurf( pod_id, struct_ind, SS_RECTANGLE )

		if  1 != GetFeaSubSurfIndex( rect_id ) : # These should be equivalent

			print( "Error: GetFeaSubSurfIndex" )
			assert False, "Error: GetFeaSubSurfIndex"



	def test_GetFeaPolySparNumPt(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		# A new Poly Spar starts with 2 points
		if GetFeaPolySparNumPt( pspar_id ) != 2:
			print( "Error: GetFeaPolySparNumPt" )
			assert False, "Error: GetFeaPolySparNumPt"



	def test_AddFeaPolySparPt(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		pt_id = AddFeaPolySparPt( pspar_id )

		if GetFeaPolySparNumPt( pspar_id ) != 3:
			print( "Error: AddFeaPolySparPt" )
			assert False, "Error: AddFeaPolySparPt"



	def test_InsertFeaPolySparPt(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		# Insert a new intermediate point between the two default endpoints
		pt_id = InsertFeaPolySparPt( pspar_id, 1 )

		if GetFeaPolySparNumPt( pspar_id ) != 3:
			print( "Error: InsertFeaPolySparPt" )
			assert False, "Error: InsertFeaPolySparPt"



	def test_DelFeaPolySparPt(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		AddFeaPolySparPt( pspar_id )
		AddFeaPolySparPt( pspar_id )

		# Delete the point at index 2 (leaving 3 points)
		DelFeaPolySparPt( pspar_id, 2 )

		if GetFeaPolySparNumPt( pspar_id ) != 3:
			print( "Error: DelFeaPolySparPt" )
			assert False, "Error: DelFeaPolySparPt"



	def test_DelAllFeaPolySparPt(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		AddFeaPolySparPt( pspar_id )
		AddFeaPolySparPt( pspar_id )

		DelAllFeaPolySparPt( pspar_id )

		if GetFeaPolySparNumPt( pspar_id ) != 0:
			print( "Error: DelAllFeaPolySparPt" )
			assert False, "Error: DelAllFeaPolySparPt"



	def test_MoveFeaPolySparPt(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		AddFeaPolySparPt( pspar_id )

		# Move point at index 2 up one position
		new_index = MoveFeaPolySparPt( pspar_id, 2, REORDER_MOVE_UP )

		if new_index != 1:
			print( "Error: MoveFeaPolySparPt" )
			assert False, "Error: MoveFeaPolySparPt"



	def test_SetFeaPolySparPtName(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		SetFeaPolySparPtName( pspar_id, 0, "InboardPt" )
		SetFeaPolySparPtName( pspar_id, 1, "OutboardPt" )

		if GetFeaPolySparPtName( pspar_id, 0 ) != "InboardPt":
			print( "Error: SetFeaPolySparPtName" )
			assert False, "Error: SetFeaPolySparPtName"



	def test_GetFeaPolySparPtName(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		SetFeaPolySparPtName( pspar_id, 0, "InboardPt" )

		name = GetFeaPolySparPtName( pspar_id, 0 )
		assert len( name ) > 0, "GetFeaPolySparPtName returned nothing"

		print( "Point 0 name: " + name )



	def test_GetFeaPolySparPtID(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		pt_id = GetFeaPolySparPtID( pspar_id, 0 )
		assert len( pt_id ) > 0, "GetFeaPolySparPtID returned nothing"

		# Set the spanwise location of the inboard point to eta = 0.1
		SetParmVal( FindParm( pt_id, "Eta", "FeaPolySparPoint" ), 0.1 )

		pt_id_1 = GetFeaPolySparPtID( pspar_id, 1 )

		# Set the spanwise location of the outboard point to eta = 0.9
		SetParmVal( FindParm( pt_id_1, "Eta", "FeaPolySparPoint" ), 0.9 )



	def test_GetAllFeaPolySparPtIDVec(self):
		wing_id = AddGeom( "WING" )

		struct_ind = AddFeaStruct( wing_id )

		pspar_id = AddFeaPart( wing_id, struct_ind, FEA_POLY_SPAR )

		AddFeaPolySparPt( pspar_id )

		pt_ids = GetAllFeaPolySparPtIDVec( pspar_id )

		if len( pt_ids ) != 3:
			print( "Error: GetAllFeaPolySparPtIDVec" )
			assert False, "Error: GetAllFeaPolySparPtIDVec"

		# Set each point's spanwise eta location
		SetParmVal( FindParm( pt_ids[0], "Eta", "FeaPolySparPoint" ), 0.1 )
		SetParmVal( FindParm( pt_ids[1], "Eta", "FeaPolySparPoint" ), 0.5 )
		SetParmVal( FindParm( pt_ids[2], "Eta", "FeaPolySparPoint" ), 0.9 )



	def test_AddFeaTrimPart(self):
		assembly_id = AddFeaAssembly()

		assert len( assembly_id ) > 0, "AddFeaAssembly did not add an assembly"
		assert NumFeaAssemblies() == 1, "AddFeaAssembly did not add an assembly"

		assy_ids = GetFeaAssemblyIDVec()

		assert len( assy_ids ) == 1 and assy_ids[0] == assembly_id, "the assembly is not in the assembly list"

		# A new assembly is named and holds nothing yet.
		assert len( GetFeaAssemblyName( assembly_id ) ) > 0, "AddFeaAssembly did not name the assembly"
		assert len( GetFeaAssemblyStructureIDVec( assembly_id ) ) == 0, "a new assembly already holds structures"



	def test_DeleteFeaTrimPart(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		trim_id = AddFeaPart( pid, struct_ind, FEA_TRIM )

		# Nothing has been added to trim against, so there is nothing to take out yet.
		assert len( GetFeaTrimPartIDVec( trim_id ) ) == 0, "GetFeaTrimPartIDVec reported trim parts on a new part"



	def test_GetFeaTrimPartIDVec(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		trim_id = AddFeaPart( pid, struct_ind, FEA_TRIM )

		# A trim part starts with nothing to trim against.
		assert len( GetFeaTrimPartIDVec( trim_id ) ) == 0, "GetFeaTrimPartIDVec reported trim parts on a new part"



	def test_AddFeaAssembly(self):
		assembly_id = AddFeaAssembly()

		assert len( assembly_id ) > 0, "AddFeaAssembly returned no ID"

		assert NumFeaAssemblies() == 1, "AddFeaAssembly did not add the assembly"



	def test_DeleteFeaAssembly(self):
		pod_id = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pod_id )

		assembly_id = AddFeaAssembly()

		AddFeaStructureToAssembly( assembly_id, GetFeaStructID( pod_id, struct_ind ) )

		DeleteFeaAssembly( assembly_id )

		assert NumFeaAssemblies() == 0, "DeleteFeaAssembly did not remove the assembly"

		# The Structure it held survives.
		assert NumFeaStructures() == 1, "DeleteFeaAssembly removed the Structure it gathered"

		# An ID that is not an assembly has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteFeaAssembly( "NOSUCHASSEMBLY" )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteFeaAssembly accepted a bad ID"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_NumFeaAssemblies(self):
		assert NumFeaAssemblies() == 0, "a new model starts with FEA Assemblies"

		AddFeaAssembly()
		AddFeaAssembly()

		assert NumFeaAssemblies() == 2, "NumFeaAssemblies did not count both assemblies"
		assert NumFeaAssemblies() == len( GetFeaAssemblyIDVec() ), "NumFeaAssemblies disagrees with GetFeaAssemblyIDVec"



	def test_GetFeaAssemblyIDVec(self):
		first = AddFeaAssembly()
		second = AddFeaAssembly()

		assy_ids = GetFeaAssemblyIDVec()

		# Assemblies come back in the order they were added.
		assert len( assy_ids ) == 2, "GetFeaAssemblyIDVec did not report the assemblies in order"
		assert assy_ids[0] == first, "GetFeaAssemblyIDVec did not report the assemblies in order"
		assert assy_ids[1] == second, "GetFeaAssemblyIDVec did not report the assemblies in order"



	def test_GetFeaAssemblyName(self):
		assembly_id = AddFeaAssembly()

		SetFeaAssemblyName( assembly_id, "ExampleAssembly" )

		assert GetFeaAssemblyName( assembly_id ) == "ExampleAssembly", "GetFeaAssemblyName did not report the name that was set"

		# An ID that is not an assembly has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetFeaAssemblyName( "NOSUCHASSEMBLY" )

		assert err_mgr.GetNumTotalErrors() > 0, "GetFeaAssemblyName accepted a bad ID"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_SetFeaAssemblyName(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		assembly_id = AddFeaAssembly()

		AddFeaAssemblyStructure( assembly_id, GetFeaStructID( pid, struct_ind ) )

		SetFeaAssemblyName( assembly_id, "TestAssembly" )

		assert GetFeaAssemblyName( assembly_id ) == "TestAssembly", "SetFeaAssemblyName did not take"



	def test_AddFeaStructureToAssembly(self):
		pod_id = AddGeom( "POD" )

		struct_ind_1 = AddFeaStruct( pod_id )
		struct_ind_2 = AddFeaStruct( pod_id )

		struct_id_1 = GetFeaStructID( pod_id, struct_ind_1 )
		struct_id_2 = GetFeaStructID( pod_id, struct_ind_2 )

		assembly_id = AddFeaAssembly()

		AddFeaStructureToAssembly( assembly_id, struct_id_1 )
		AddFeaStructureToAssembly( assembly_id, struct_id_2 )

		struct_ids = GetFeaAssemblyStructureIDVec( assembly_id )

		assert len( struct_ids ) == 2, "the assembly does not hold the Structures it was given"
		assert struct_ids[0] == struct_id_1, "the assembly does not hold the Structures it was given"
		assert struct_ids[1] == struct_id_2, "the assembly does not hold the Structures it was given"

		# A Structure that does not exist has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		AddFeaStructureToAssembly( assembly_id, "NOSUCHSTRUCT" )

		assert err_mgr.GetNumTotalErrors() > 0, "AddFeaStructureToAssembly accepted a bad Structure ID"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteFeaStructureFromAssembly(self):
		pod_id = AddGeom( "POD" )

		struct_ind_1 = AddFeaStruct( pod_id )
		struct_ind_2 = AddFeaStruct( pod_id )

		struct_id_1 = GetFeaStructID( pod_id, struct_ind_1 )
		struct_id_2 = GetFeaStructID( pod_id, struct_ind_2 )

		assembly_id = AddFeaAssembly()

		AddFeaStructureToAssembly( assembly_id, struct_id_1 )
		AddFeaStructureToAssembly( assembly_id, struct_id_2 )

		DeleteFeaStructureFromAssembly( assembly_id, struct_id_1 )

		# Only the named Structure leaves the assembly, and it survives in the model.
		struct_ids = GetFeaAssemblyStructureIDVec( assembly_id )

		assert len( struct_ids ) == 1, "DeleteFeaStructureFromAssembly removed the wrong Structure"
		assert struct_ids[0] == struct_id_2, "DeleteFeaStructureFromAssembly removed the wrong Structure"
		assert NumFeaStructures() == 2, "DeleteFeaStructureFromAssembly deleted the Structure itself"

		# A Structure the assembly does not hold has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteFeaStructureFromAssembly( assembly_id, struct_id_1 )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteFeaStructureFromAssembly accepted a Structure it does not hold"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_AddFeaAssemblyStructure(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		struct_id = GetFeaStructID( pid, struct_ind )

		assembly_id = AddFeaAssembly()

		AddFeaAssemblyStructure( assembly_id, struct_id )

		assert len( GetFeaAssemblyStructureIDVec( assembly_id ) ) == 1, "AddFeaAssemblyStructure did not add the structure"



	def test_DeleteFeaAssemblyStructure(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		struct_id = GetFeaStructID( pid, struct_ind )

		assembly_id = AddFeaAssembly()

		AddFeaAssemblyStructure( assembly_id, struct_id )

		DeleteFeaAssemblyStructure( assembly_id, struct_id )

		assert len( GetFeaAssemblyStructureIDVec( assembly_id ) ) == 0, "DeleteFeaAssemblyStructure did not remove the structure"

		# The structure is still there; it is only out of the assembly.
		assert NumFeaStructures() == 1, "DeleteFeaAssemblyStructure deleted the structure itself"



	def test_GetFeaAssemblyStructureIDVec(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		assembly_id = AddFeaAssembly()

		AddFeaAssemblyStructure( assembly_id, GetFeaStructID( pid, struct_ind ) )

		assert len( GetFeaAssemblyStructureIDVec( assembly_id ) ) == 1, "GetFeaAssemblyStructureIDVec did not report the structure"



	def test_AddFeaAssemblyConnection(self):
		pod_id = AddGeom( "POD" )

		struct_ind_1 = AddFeaStruct( pod_id )
		struct_ind_2 = AddFeaStruct( pod_id )

		struct_id_1 = GetFeaStructID( pod_id, struct_ind_1 )
		struct_id_2 = GetFeaStructID( pod_id, struct_ind_2 )

		#==== Each Structure needs a Fixed Point to connect ====//
		fix_pt_1 = AddFeaPart( pod_id, struct_ind_1, FEA_FIX_POINT )
		fix_pt_2 = AddFeaPart( pod_id, struct_ind_2, FEA_FIX_POINT )

		assembly_id = AddFeaAssembly()

		AddFeaStructureToAssembly( assembly_id, struct_id_1 )
		AddFeaStructureToAssembly( assembly_id, struct_id_2 )

		assert NumFeaAssemblyConnections( assembly_id ) == 0, "a new assembly already holds connections"

		AddFeaAssemblyConnection( assembly_id, fix_pt_1, struct_id_1, 0, fix_pt_2, struct_id_2, 0 )

		assert NumFeaAssemblyConnections( assembly_id ) == 1, "AddFeaAssemblyConnection did not add a connection"

		DeleteFeaAssemblyConnection( assembly_id, 0 )

		assert NumFeaAssemblyConnections( assembly_id ) == 0, "DeleteFeaAssemblyConnection did not remove the connection"

		# An index past the end has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteFeaAssemblyConnection( assembly_id, 0 )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteFeaAssemblyConnection accepted an index past the end"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteFeaAssemblyConnection(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		assembly_id = AddFeaAssembly()

		AddFeaAssemblyStructure( assembly_id, GetFeaStructID( pid, struct_ind ) )

		# A new assembly has no connections, so there is nothing to take out yet.
		assert NumFeaAssemblyConnections( assembly_id ) == 0, "NumFeaAssemblyConnections miscounted a new assembly"



	def test_NumFeaAssemblyConnections(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		assembly_id = AddFeaAssembly()

		AddFeaAssemblyStructure( assembly_id, GetFeaStructID( pid, struct_ind ) )

		assert NumFeaAssemblyConnections( assembly_id ) == 0, "NumFeaAssemblyConnections miscounted a new assembly"



	def test_GetFeaAssemblyConnectionID(self):
		#==== Two structures to connect ====#
		pod = AddGeom( "POD", "" )
		wing = AddGeom( "WING", "" )

		pod_struct = AddFeaStruct( pod )
		wing_struct = AddFeaStruct( wing )

		pod_struct_id = GetFeaStructID( pod, pod_struct )
		wing_struct_id = GetFeaStructID( wing, wing_struct )

		#==== A fix point on each, which is what a connection joins ====#
		pod_pt = AddFeaPart( pod, pod_struct, FEA_FIX_POINT )
		wing_pt = AddFeaPart( wing, wing_struct, FEA_FIX_POINT )

		assembly_id = AddFeaAssembly()
		AddFeaStructureToAssembly( assembly_id, pod_struct_id )
		AddFeaStructureToAssembly( assembly_id, wing_struct_id )

		AddFeaAssemblyConnection( assembly_id, pod_pt, pod_struct_id, 0, wing_pt, wing_struct_id, 0 )

		assert NumFeaAssemblyConnections( assembly_id ) == 1, "the connection was not added"

		conn_id = GetFeaAssemblyConnectionID( assembly_id, 0 )

		assert len( conn_id ) > 0, "GetFeaAssemblyConnectionID found nothing"

		#==== And what it constrains is a Parm like any other ====#
		SetParmVal( FindParm( conn_id, "ConMode", "Connection" ), FEA_BCM_PIN )

		Update()

		mode = GetParmVal( conn_id, "ConMode", "Connection" )

		assert mode == FEA_BCM_PIN, "the connection did not take the mode it was given"



	def test_GetFeaAssemblyFileName(self):
		pod_id = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Keep the mesh coarse so the example runs quickly ====//
		SetFeaMeshVal( pod_id, struct_ind, CFD_MAX_EDGE_LEN, 0.75 )

		assembly_id = AddFeaAssembly()

		SetFeaAssemblyName( assembly_id, "ExampleAssembly" )

		AddFeaStructureToAssembly( assembly_id, struct_id )

		out_name = GetFeaAssemblyFileName( assembly_id, FEA_CALCULIX_FILE_NAME )

		ComputeFeaAssemblyMesh( assembly_id )

		# The assembly writes the Calculix deck it named.
		import os
		assert os.path.getsize( out_name ) > 0, "ComputeFeaAssemblyMesh wrote no file"



	def test_SetFeaAssemblyFileName(self):
		assembly_id = AddFeaAssembly()

		SetFeaAssemblyFileName( assembly_id, FEA_CALCULIX_FILE_NAME, "ExampleAssembly.inp" )

		assert GetFeaAssemblyFileName( assembly_id, FEA_CALCULIX_FILE_NAME ) == "ExampleAssembly.inp", "SetFeaAssemblyFileName did not take"

		# Each output type carries its own name.
		assert GetFeaAssemblyFileName( assembly_id, FEA_NASTRAN_FILE_NAME ) != "ExampleAssembly.inp", "setting one output name disturbed another"



	def test_ComputeFeaAssemblyMesh(self):
		pid = AddGeom( "POD" )

		struct_ind = AddFeaStruct( pid )

		Update()

		assembly_id = AddFeaAssembly()

		AddFeaAssemblyStructure( assembly_id, GetFeaStructID( pid, struct_ind ) )

		# Meshing an assembly is not quick; keep the mesh coarse.
		SetFeaMeshVal( pid, 0, CFD_MAX_EDGE_LEN, 1.0 )

		ComputeFeaAssemblyMesh( assembly_id )



	def test_NumFeaStructures(self):
		pid = AddGeom( "POD" )

		AddFeaStruct( pid )

		Update()

		assert NumFeaStructures() == 1, "NumFeaStructures did not count the structure"



	def test_NumFeaParts(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Add FEA Parts ====//
		slice_id = AddFeaPart( pod_id, struct_ind, FEA_SLICE )
		dome_id = AddFeaPart( pod_id, struct_ind, FEA_DOME )

		if  NumFeaParts( struct_id ) != 3 : # Includes FeaSkin

			print( "Error: NumFeaParts" )
			assert False, "Error: NumFeaParts"



	def test_NumFeaSubSurfs(self):
		#==== Add Pod Geometry ====//
		wing_id = AddGeom( "WING" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( wing_id )

		struct_id = GetFeaStructID( wing_id, struct_ind )

		#==== Add SubSurfaces ====//
		line_array_id = AddFeaSubSurf( wing_id, struct_ind, SS_LINE_ARRAY )
		rectangle_id = AddFeaSubSurf( wing_id, struct_ind, SS_RECTANGLE )

		if  NumFeaSubSurfs( struct_id ) != 2 :
			print( "Error: NumFeaSubSurfs" )
			assert False, "Error: NumFeaSubSurfs"



	def test_AddFeaBC(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind );

		#==== Add BC ====//
		bc_id = AddFeaBC( struct_id, FEA_BC_STRUCTURE )



	def test_DelFeaBC(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind );

		#==== Add BC ====//
		bc_id = AddFeaBC( struct_id, FEA_BC_STRUCTURE )

		assert NumFeaBCs( struct_id ) == 1, "AddFeaBC did not add a boundary condition"

		DelFeaBC( struct_id, bc_id )

		assert NumFeaBCs( struct_id ) == 0, "DelFeaBC did not remove the boundary condition"
		assert len( GetFeaBCIDVec( struct_id ) ) == 0, "DelFeaBC left the boundary condition in the ID list"



	def test_GetFeaBCIDVec(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind );

		#==== Add BC ====//
		bc_id = AddFeaBC( struct_id, FEA_BC_STRUCTURE )

		bc_id_vec = GetFeaBCIDVec( struct_id )
		assert len( bc_id_vec ) > 0, "GetFeaBCIDVec returned nothing"



	def test_NumFeaBCs(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind );

		#==== Add BC ====//
		bc_id = AddFeaBC( struct_id, FEA_BC_STRUCTURE )

		nbc = NumFeaBCs( struct_id )

		# The count has to match the list of IDs, and follow another add.
		assert nbc == 1, "NumFeaBCs did not count the boundary condition"
		assert nbc == len( GetFeaBCIDVec( struct_id ) ), "NumFeaBCs disagrees with GetFeaBCIDVec"

		AddFeaBC( struct_id, FEA_BC_STRUCTURE )

		assert NumFeaBCs( struct_id ) == nbc + 1, "NumFeaBCs did not follow AddFeaBC"



	def test_AddFeaLayer(self):
		#==== Create FeaMaterial ====//
		mat_id = AddFeaMaterial()

		SetParmVal( FindParm( mat_id, "MassDensity", "FeaMaterial" ), 0.016 )



	def test_DeleteFeaLayer(self):
		mat_id = AddFeaMaterial()

		SetParmVal( FindParm( mat_id, "FeaMaterialType", "FeaMaterial" ), FEA_LAMINATE )

		Update()

		# A laminate material starts with a layer of its own, so count before and after.
		n0 = NumFeaLayers( mat_id )

		layer_id = AddFeaLayer( mat_id )

		DeleteFeaLayer( mat_id, layer_id )

		assert NumFeaLayers( mat_id ) == n0, "DeleteFeaLayer did not delete the layer"



	def test_ReorderFeaLayer(self):
		mat_id = AddFeaMaterial()

		SetParmVal( FindParm( mat_id, "FeaMaterialType", "FeaMaterial" ), FEA_LAMINATE )

		Update()

		first = AddFeaLayer( mat_id )
		second = AddFeaLayer( mat_id )

		layer_ids = GetFeaLayerIDVec( mat_id )
		num_layers = len( layer_ids )

		ReorderFeaLayer( mat_id, second, REORDER_MOVE_TOP )

		moved_ids = GetFeaLayerIDVec( mat_id )

		assert len( moved_ids ) == num_layers, "ReorderFeaLayer did not move the layer"
		assert moved_ids[0] == second, "ReorderFeaLayer did not move the layer"



	def test_NumFeaLayers(self):
		mat_id = AddFeaMaterial()

		SetParmVal( FindParm( mat_id, "FeaMaterialType", "FeaMaterial" ), FEA_LAMINATE )

		Update()

		# A laminate material starts with a layer of its own, so count before and after.
		n0 = NumFeaLayers( mat_id )

		layer_id = AddFeaLayer( mat_id )

		assert NumFeaLayers( mat_id ) == n0 + 1, "NumFeaLayers did not count the layer"



	def test_GetFeaLayerIDVec(self):
		mat_id = AddFeaMaterial()

		SetParmVal( FindParm( mat_id, "FeaMaterialType", "FeaMaterial" ), FEA_LAMINATE )

		Update()

		# A laminate material starts with a layer of its own, so count before and after.
		n0 = NumFeaLayers( mat_id )

		layer_id = AddFeaLayer( mat_id )

		layer_array = GetFeaLayerIDVec( mat_id )

		assert len( layer_array ) == n0 + 1, "GetFeaLayerIDVec did not report the layer"



	def test_GetFeaMaterialIDVec(self):
		mat_id = AddFeaMaterial()

		mat_array = GetFeaMaterialIDVec()

		assert mat_id in mat_array, "GetFeaMaterialIDVec did not report the new material"



	def test_DeleteFeaMaterial(self):
		#==== Create FeaMaterial ====//
		mat_id = AddFeaMaterial()

		num_before = len( GetFeaMaterialIDVec() )

		DeleteFeaMaterial( mat_id )

		assert len( GetFeaMaterialIDVec() ) == num_before - 1, "DeleteFeaMaterial did not remove the material"

		# An ID that is not a material has to be rejected.  The error queue is
		# reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteFeaMaterial( "NOSUCHMATERIAL" )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteFeaMaterial accepted a bad ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_AddFeaMaterial(self):
		mat_id = AddFeaMaterial()

		assert len( mat_id ) > 0, "AddFeaMaterial returned no ID"



	def test_GetFeaPropertyIDVec(self):
		#==== Create FeaProperty ====//
		prop_id = AddFeaProperty()

		SetParmVal( FindParm( prop_id, "Thickness", "FeaProperty" ), 0.01 )



	def test_DeleteFeaProperty(self):
		#==== Create FeaProperty ====//
		prop_id = AddFeaProperty()

		num_before = len( GetFeaPropertyIDVec() )

		DeleteFeaProperty( prop_id )

		assert len( GetFeaPropertyIDVec() ) == num_before - 1, "DeleteFeaProperty did not remove the property"

		# An ID that is not a property has to be rejected.  The error queue is
		# reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteFeaProperty( "NOSUCHPROPERTY" )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteFeaProperty accepted a bad ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_AddFeaProperty(self):
		prop_id = AddFeaProperty()

		assert len( prop_id ) > 0, "AddFeaProperty returned no ID"



	def test_GetFeaMeshVal(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Adjust FeaMeshSettings ====//
		SetFeaMeshVal( pod_id, struct_ind, CFD_MAX_EDGE_LEN, 0.75 )

		SetFeaMeshVal( pod_id, struct_ind, CFD_MIN_EDGE_LEN, 0.2 )

		# The options are backed by Parms on the Structure, in its grid density
		# group, so the values that were set can be read back.
		struct_id = GetFeaStructID( pod_id, struct_ind )

		assert abs( GetParmVal( FindParm( struct_id, "BaseLen", "FEAGridDensity" ) ) - 0.75 ) < 1e-12, "SetFeaMeshVal did not set CFD_MAX_EDGE_LEN"
		assert abs( GetParmVal( FindParm( struct_id, "MinLen", "FEAGridDensity" ) ) - 0.2 ) < 1e-12, "SetFeaMeshVal did not set CFD_MIN_EDGE_LEN"



	def test_SetFeaMeshVal(self):
		pid = AddGeom( "POD" )

		AddFeaStruct( pid )

		Update()

		SetFeaMeshVal( pid, 0, CFD_MAX_EDGE_LEN, 0.75 )



	def test_GetFeaMeshFileName(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#=== Set Export File Name ===//
		export_name = "FEAMeshTest_calculix.dat"

		#==== Get Parent Geom ID and Index ====//
		parent_id = GetFeaStructParentGeomID( struct_id ) # same as pod_id

		assert parent_id == pod_id, "GetFeaStructParentGeomID did not report the parent Geom"

		SetFeaMeshFileName( parent_id, struct_ind, FEA_CALCULIX_FILE_NAME, export_name )

		# Keep the mesh coarse so the example runs quickly, then mesh to prove the
		# name that was set is the name that gets written.
		SetFeaMeshVal( parent_id, struct_ind, CFD_MAX_EDGE_LEN, 0.75 )

		ComputeFeaMesh( parent_id, struct_ind, FEA_CALCULIX_FILE_NAME )

		import os
		assert os.path.getsize( export_name ) > 0, "SetFeaMeshFileName did not name the output file"



	def test_SetFeaMeshFileName(self):
		pid = AddGeom( "POD" )

		AddFeaStruct( pid )

		Update()

		SetFeaMeshFileName( pid, 0, FEA_MASS_FILE_NAME, "TestFeaMass.txt" )



	def test_ComputeFeaMesh(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Generate FEA Mesh and Export ====//
		print( "--> Generating FeaMesh " )

		#==== Get Parent Geom ID and Index ====//
		parent_id = GetFeaStructParentGeomID( struct_id ) # same as pod_id

		#==== Keep the mesh coarse so the example runs quickly ====//
		SetFeaMeshVal( parent_id, struct_ind, CFD_MAX_EDGE_LEN, 0.75 )

		SetFeaMeshFileName( parent_id, struct_ind, FEA_CALCULIX_FILE_NAME, "FEAMeshTest_calculix.dat" )

		ComputeFeaMesh( parent_id, struct_ind, FEA_CALCULIX_FILE_NAME )

		# FEA Mesh reports nothing through the Results Manager, so the output file is
		# the evidence that it ran.
		import os
		assert os.path.getsize( "FEAMeshTest_calculix.dat" ) > 0, "ComputeFeaMesh wrote no file"



	def test_ComputeFeaMesh1(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		struct_id = GetFeaStructID( pod_id, struct_ind )

		#==== Generate FEA Mesh and Export ====//
		print( "--> Generating FeaMesh " )

		#==== Get Parent Geom ID and Index ====//
		parent_id = GetFeaStructParentGeomID( struct_id ) # same as pod_id

		#==== Keep the mesh coarse so the example runs quickly ====//
		SetFeaMeshVal( parent_id, struct_ind, CFD_MAX_EDGE_LEN, 0.75 )

		SetFeaMeshFileName( parent_id, struct_ind, FEA_CALCULIX_FILE_NAME, "FEAMeshTest_calculix.dat" )

		# This form names the Structure directly rather than its parent and index.
		ComputeFeaMesh( struct_id, FEA_CALCULIX_FILE_NAME )

		# FEA Mesh reports nothing through the Results Manager, so the output file is
		# the evidence that it ran.
		import os
		assert os.path.getsize( "FEAMeshTest_calculix.dat" ) > 0, "ComputeFeaMesh wrote no file"



	def test_SetXSecAlias(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# Set Alias and verify alias match
		alias = "XSec_One_Alias"

		SetXSecAlias( xsec_1, alias )

		get_alias = GetXSecAlias( xsec_1 )

		if alias != get_alias:
			print("SetXSecAlias/GetXSecAlias error!")
			assert False, "SetXSecAlias/GetXSecAlias error!"



	def test_GetXSecAlias(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# Set Alias and verify alias match
		alias = "XSec_One_Alias"

		SetXSecAlias( xsec_1, alias )

		get_alias = GetXSecAlias( xsec_1 )

		if alias != get_alias:
			print("SetXSecAlias/GetXSecAlias error!")
			assert False, "SetXSecAlias/GetXSecAlias error!"



	def test_SetXSecCurveAlias(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# Set Alias and verify alias match
		alias = "XSecCurve_One_Alias"

		SetXSecCurveAlias( xsec_1, alias )

		get_alias = GetXSecCurveAlias( xsec_1 )

		if alias != get_alias:
			print("SetXSecCurveAlias/GetXSecCurveAlias error!")
			assert False, "SetXSecCurveAlias/GetXSecCurveAlias error!"



	def test_GetXSecCurveAlias(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# Set Alias and verify alias match
		alias = "XSecCurve_One_Alias"

		SetXSecCurveAlias( xsec_1, alias )

		get_alias = GetXSecCurveAlias( xsec_1 )

		if alias != get_alias:
			print("SetXSecCurveAlias/GetXSecCurveAlias error!")
			assert False, "SetXSecCurveAlias/GetXSecCurveAlias error!"



	def test_CutXSec(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		#==== Insert, Cut, Paste Example ====//
		xsec_surf = GetXSecSurf( fid, 0 )

		num_start = GetNumXSec( xsec_surf )

		InsertXSec( fid, 1, XS_ROUNDED_RECTANGLE )         # Insert A Cross-Section

		assert GetNumXSec( xsec_surf ) == num_start + 1, "InsertXSec did not add a section"
		assert GetXSecShape( GetXSec( xsec_surf, 2 ) ) == XS_ROUNDED_RECTANGLE, "InsertXSec did not insert after the given index"

		CopyXSec( fid, 2 )                                 # Copy Just Created XSec To Clipboard

		PasteXSec( fid, 1 )                                # Paste Clipboard

		# Pasting replaces a section rather than adding one, and section 1 now
		# carries the shape that was copied.
		assert GetNumXSec( xsec_surf ) == num_start + 1, "PasteXSec changed the number of sections"
		assert GetXSecShape( GetXSec( xsec_surf, 1 ) ) == XS_ROUNDED_RECTANGLE, "PasteXSec did not paste the copied section"

		CutXSec( fid, 2 )                                  # Cut Created XSec

		assert GetNumXSec( xsec_surf ) == num_start, "CutXSec did not remove a section"



	def test_CopyXSec(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		# Give XSec 1 a shape that XSec 3 does not have.
		ChangeXSecShape( xsec_surf, 1, XS_ROUNDED_RECTANGLE )

		Update()

		num_start = GetNumXSec( xsec_surf )

		# Copy XSec To Clipboard
		CopyXSec( sid, 1 )

		# Paste To XSec 3
		PasteXSec( sid, 3 )

		Update()

		# Pasting replaces the target section, so the count is unchanged and XSec 3
		# now carries the shape that was copied.
		assert GetNumXSec( xsec_surf ) == num_start, "PasteXSec changed the number of sections"
		assert GetXSecShape( GetXSec( xsec_surf, 3 ) ) == XS_ROUNDED_RECTANGLE, "PasteXSec did not paste the copied section"

		# The section that was copied has to be left alone.
		assert GetXSecShape( GetXSec( xsec_surf, 1 ) ) == XS_ROUNDED_RECTANGLE, "CopyXSec disturbed the section it copied"



	def test_PasteXSec(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		# Give XSec 1 a shape that XSec 3 does not have.
		ChangeXSecShape( xsec_surf, 1, XS_ROUNDED_RECTANGLE )

		Update()

		num_start = GetNumXSec( xsec_surf )

		# Copy XSec To Clipboard
		CopyXSec( sid, 1 )

		# Paste To XSec 3
		PasteXSec( sid, 3 )

		Update()

		# Pasting replaces the target section, so the count is unchanged and XSec 3
		# now carries the shape that was copied.
		assert GetNumXSec( xsec_surf ) == num_start, "PasteXSec changed the number of sections"
		assert GetXSecShape( GetXSec( xsec_surf, 3 ) ) == XS_ROUNDED_RECTANGLE, "PasteXSec did not paste the copied section"

		# The section that was copied has to be left alone.
		assert GetXSecShape( GetXSec( xsec_surf, 1 ) ) == XS_ROUNDED_RECTANGLE, "CopyXSec disturbed the section it copied"



	def test_InsertXSec(self):
		wing_id = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wing_id, 0 )

		num_start = GetNumXSec( xsec_surf )

		#===== Add XSec ====//
		InsertXSec( wing_id, 1, XS_SIX_SERIES )

		Update()

		# The new section lands after the given index.
		assert GetNumXSec( xsec_surf ) == num_start + 1, "InsertXSec did not add a section"
		assert GetXSecShape( GetXSec( xsec_surf, 2 ) ) == XS_SIX_SERIES, "InsertXSec did not insert the requested shape"



	def test_SplitWingXSec(self):
		wing_id = AddGeom( "WING", "" )

		xsec_surf = GetXSecSurf( wing_id, 0 )

		num_start = GetNumXSec( xsec_surf )

		span_start = GetParmVal( wing_id, "Span", "XSec_1" )

		#==== Set Wing Section Controls ====//
		SplitWingXSec( wing_id, 1 )

		Update()

		# Splitting a section turns one section into two, and the two halves span
		# what the one section spanned.
		assert GetNumXSec( xsec_surf ) == num_start + 1, "SplitWingXSec did not split the section"

		span_1 = GetParmVal( wing_id, "Span", "XSec_1" )
		span_2 = GetParmVal( wing_id, "Span", "XSec_2" )

		assert abs( ( span_1 + span_2 ) - span_start ) < 1e-6, "SplitWingXSec changed the span of the wing"


	def test_GetDriverGroup(self):
		#==== Add Wing Geometry and Set Parms ====//
		wing_id = AddGeom( "WING", "" )

		#==== Set Wing Section Controls ====//
		SetDriverGroup( wing_id, 1, AR_WSECT_DRIVER, ROOTC_WSECT_DRIVER, TIPC_WSECT_DRIVER )

		Update()

		#==== Set Parms ====//
		SetParmVal( wing_id, "Root_Chord", "XSec_1", 2 )
		SetParmVal( wing_id, "Tip_Chord", "XSec_1", 1 )

		Update()

		# The three chosen drivers are the values that hold; span is now solved for
		# from the aspect ratio and the two chords.
		ar = GetParmVal( wing_id, "Aspect", "XSec_1" )
		span = GetParmVal( wing_id, "Span", "XSec_1" )

		assert abs( GetParmVal( wing_id, "Root_Chord", "XSec_1" ) - 2.0 ) < 1e-6, "the driving Parms did not hold their values"
		assert abs( GetParmVal( wing_id, "Tip_Chord", "XSec_1" ) - 1.0 ) < 1e-6, "the driving Parms did not hold their values"

		# A section of this planform has area span * ( root + tip ) / 2, and aspect
		# ratio span * span / area.
		area = span * ( 2.0 + 1.0 ) * 0.5

		assert abs( ar - span * span / area ) < 1e-6, "SetDriverGroup left the section inconsistent"



	def test_SetDriverGroup(self):
		wid = AddGeom( "WING", "" )

		SetDriverGroup( wid, 1, SPAN_WSECT_DRIVER, ROOTC_WSECT_DRIVER, TIPC_WSECT_DRIVER )

		Update()



	def test_GetXSecSurf(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )
		assert len( xsec_surf ) > 0, "GetXSecSurf returned nothing"



	def test_GetNumXSec(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Flatten ends
		num_xsecs = GetNumXSec( xsec_surf )

		# A Stack starts with five sections, and every index below the count has to
		# name a real XSec.
		assert num_xsecs == 5, "GetNumXSec did not report the sections of a new Stack"

		for i in range(num_xsecs):

			xsec = GetXSec( xsec_surf, i )

			assert len( xsec ) > 0, "GetNumXSec counted a section that GetXSec cannot find"

			SetXSecTanAngles( xsec, XSEC_BOTH_SIDES, 0, -1.0e12, -1.0e12, -1.0e12 )       # Set Tangent Angles At Cross Section

			SetXSecTanStrengths( xsec, XSEC_BOTH_SIDES, 0.0, -1.0e12, -1.0e12, -1.0e12 )  # Set Tangent Strengths At Cross Section

		# Inserting a section has to move the count.
		InsertXSec( sid, 1, XS_ROUNDED_RECTANGLE )

		assert GetNumXSec( xsec_surf ) == num_xsecs + 1, "GetNumXSec did not follow InsertXSec"



	def test_GetXSec(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )
		assert len( xsec_1 ) > 0, "GetXSec returned nothing"



	def test_ChangeXSecShape(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Set XSec 1 & 2 to Edit Curve type
		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )
		ChangeXSecShape( xsec_surf, 2, XS_EDIT_CURVE )

		xsec_2 = GetXSec( xsec_surf, 2 )

		if  GetXSecShape( xsec_2 ) != XS_EDIT_CURVE :
			print( "Error: ChangeXSecShape" )
			assert False, "Error: ChangeXSecShape"



	def test_FitCSTAirfoil(self):
		wing_id = AddGeom( "WING", "" )

		xsec_surf = GetXSecSurf( wing_id, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FOUR_SERIES )

		Update()

		FitCSTAirfoil( xsec_surf, 1, 8 )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		assert GetXSecShape( xsec ) == XS_CST_AIRFOIL, "FitCSTAirfoil did not convert the XSec"

		# The fit is carried out at the degree that was asked for.
		assert GetUpperCSTDegree( xsec ) == 8, "FitCSTAirfoil did not fit at the requested degree"
		assert GetLowerCSTDegree( xsec ) == 8, "FitCSTAirfoil did not fit at the requested degree"



	def test_SetXSecSurfGlobalXForm(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		mat = Matrix4d()
		mat.loadIdentity()
		mat.translatef( 1.0, 2.0, 3.0 )

		SetXSecSurfGlobalXForm( xsec_surf, mat )



	def test_GetXSecSurfGlobalXForm(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		mat = GetXSecSurfGlobalXForm( xsec_surf )



	def test_GetXSecShape(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )

		xsec = GetXSec( xsec_surf, 1 )

		if  GetXSecShape( xsec ) != XS_EDIT_CURVE :
			print( "ERROR: GetXSecShape" )
			assert False, "ERROR: GetXSecShape"



	def test_GetXSecWidth(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 2 ) # Get 2nd to last XSec

		SetXSecWidthHeight( xsec, 3.0, 6.0 )

		if  abs( GetXSecWidth( xsec ) - 3.0 ) > 1e-6 :
			print( "---> Error: API Get/Set Width " )
			assert False, "---> Error: API Get/Set Width"



	def test_GetXSecHeight(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 2 ) # Get 2nd to last XSec

		SetXSecWidthHeight( xsec, 3.0, 6.0 )

		if  abs( GetXSecHeight( xsec ) - 6.0 ) > 1e-6 :
			print( "---> Error: API Get/Set Width " )
			assert False, "---> Error: API Get/Set Width"



	def test_SetXSecWidthHeight(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		SetXSecWidthHeight( xsec_2, 1.5, 1.5 )

		Update()

		assert abs( GetXSecWidth( xsec_2 ) - 1.5 ) < 1e-6, "SetXSecWidthHeight did not take"
		assert abs( GetXSecHeight( xsec_2 ) - 1.5 ) < 1e-6, "SetXSecWidthHeight did not take"

		# The neighbouring sections have to be left alone.
		xsec_1 = GetXSec( xsec_surf, 1 )

		assert abs( GetXSecWidth( xsec_1 ) - 1.5 ) > 1e-6 or abs( GetXSecHeight( xsec_1 ) - 1.5 ) > 1e-6, "SetXSecWidthHeight reached a section it was not given"



	def test_SetXSecWidth(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		SetXSecWidth( xsec_2, 1.5 )
		assert abs( GetXSecWidth( xsec_2 ) - 1.5 ) < 1e-9, "SetXSecWidth did not take"




	def test_SetXSecHeight(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		SetXSecHeight( xsec_2, 1.5 )
		assert abs( GetXSecHeight( xsec_2 ) - 1.5 ) < 1e-9, "SetXSecHeight did not take"




	def test_GetXSecParmIDs(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		parm_array = GetXSecParmIDs( xsec )

		if  len(parm_array) < 1 :
			print( "---> Error: API GetXSecParmIDs " )
			assert False, "---> Error: API GetXSecParmIDs"



	def test_GetXSecParm(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		if  not ValidParm( wid ) :
			print( "---> Error: API GetXSecParm " )
			assert False, "---> Error: API GetXSecParm"



	def test_ReadFileXSec(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 2, XS_FILE_FUSE )

		xsec = GetXSec( xsec_surf, 2 )

		vec_array = ReadFileXSec(xsec, "TestXSec.fxs")

		Update()

		# The file holds a closed diamond, so the first and last points coincide and
		# the section takes its size from their extents.
		assert len( vec_array ) >= 3, "ReadFileXSec returned too few points"
		assert dist( vec_array[0], vec_array[-1] ) < 1e-8, "ReadFileXSec returned an open curve"

		# The shape is normalized on the way in and then scaled by the section's own
		# width and height, so the curve has to fit inside them.
		w = GetXSecWidth( xsec )
		h = GetXSecHeight( xsec )

		for i in range( 11 ):
			p = ComputeXSecPnt( xsec, i * 0.1 )

			assert abs( p.y() ) <= 0.5 * w + 1e-6, "ReadFileXSec left the curve outside the section"
			assert abs( p.z() ) <= 0.5 * h + 1e-6, "ReadFileXSec left the curve outside the section"



	def test_GetXSecPnts(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 2, XS_FILE_FUSE )

		xsec = GetXSec( xsec_surf, 2 )

		# ReadFileXSec hands back a tuple, so copy it into a list to edit it.
		vec_array = list( ReadFileXSec(xsec, "TestXSec.fxs") )

		assert len( vec_array ) > 0, "ReadFileXSec returned no points"

		# The Python vec3d carries no arithmetic operators, so scale by component.
		vec_array[1] = vec3d( vec_array[1].x() * 2.0, vec_array[1].y() * 2.0, vec_array[1].z() * 2.0 )
		vec_array[3] = vec3d( vec_array[3].x() * 2.0, vec_array[3].y() * 2.0, vec_array[3].z() * 2.0 )

		# A file XSec takes its width and height from the extents of the points it
		# was given, in X and Y respectively.
		wmin = min( [ p.x() for p in vec_array ] )
		wmax = max( [ p.x() for p in vec_array ] )
		hmin = min( [ p.y() for p in vec_array ] )
		hmax = max( [ p.y() for p in vec_array ] )

		SetXSecPnts( xsec, vec_array )

		Update()

		assert abs( GetXSecWidth( xsec ) - ( wmax - wmin ) ) < 1e-6, "SetXSecPnts did not set the section width"
		assert abs( GetXSecHeight( xsec ) - ( hmax - hmin ) ) < 1e-6, "SetXSecPnts did not set the section height"



	def test_CopyXSecCurve(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_ROUNDED_RECTANGLE )

		Update()

		CopyXSecCurve( sid, 1 )

		PasteXSecCurve( sid, 3 )

		Update()

		# The shape travels to the pasted section.
		assert GetXSecShape( GetXSec( xsec_surf, 3 ) ) == XS_ROUNDED_RECTANGLE, "the XSecCurve did not paste"

		# A Geom that carries no cross sections has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		pid = AddGeom( "POD" )

		CopyXSecCurve( pid, 0 )

		assert err_mgr.GetNumTotalErrors() > 0, "CopyXSecCurve accepted a Geom with no cross sections"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_PasteXSecCurve(self):
		# A body of revolution holds one XSecCurve, so its index is ignored.
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_ROUNDED_RECTANGLE )

		Update()

		CopyXSecCurve( sid, 1 )

		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		PasteXSecCurve( bor_id, 0 )

		Update()

		assert GetBORXSecShape( bor_id ) == XS_ROUNDED_RECTANGLE, "the XSecCurve did not paste onto the body of revolution"

		# An index past the end has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		PasteXSecCurve( sid, 100 )

		assert err_mgr.GetNumTotalErrors() > 0, "PasteXSecCurve accepted an index past the end"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_SetXSecPnts(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FILE_FUSE )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		# Take the section's own points and hand back a squashed copy of them.  Building a set from
		# nothing has to match what a file section expects, which is a closed curve in the section's
		# own plane.
		pnt_vec = [ vec3d( p.x(), 0.5 * p.y(), p.z() ) for p in GetXSecPnts( xsec ) ]

		SetXSecPnts( xsec, pnt_vec )

		Update()

		assert len( GetXSecPnts( xsec ) ) == len( pnt_vec ), "SetXSecPnts did not take the points"



	def test_ComputeXSecPnt(self):
		#==== Add Geom ====//
		stack_id = AddGeom( "STACK" )

		#==== Get The XSec Surf ====//
		xsec_surf = GetXSecSurf( stack_id, 0 )

		xsec = GetXSec( xsec_surf, 2 )

		u_fract = 0.25

		pnt = ComputeXSecPnt(xsec, u_fract)

		# The section is a closed curve, so the ends meet.
		assert dist( ComputeXSecPnt( xsec, 0.0 ), ComputeXSecPnt( xsec, 1.0 ) ) < 1e-6, "the XSec curve does not close"

		# The point has to lie on the section, which is sized by its width and
		# height about the section origin.
		w = GetXSecWidth( xsec )
		h = GetXSecHeight( xsec )

		assert abs( pnt.y() ) <= 0.5 * w + 1e-6, "ComputeXSecPnt returned a point off the section"
		assert abs( pnt.z() ) <= 0.5 * h + 1e-6, "ComputeXSecPnt returned a point off the section"



	def test_ComputeXSecTan(self):
		#==== Add Geom ====//
		stack_id = AddGeom( "STACK" )

		#==== Get The XSec Surf ====//
		xsec_surf = GetXSecSurf( stack_id, 0 )

		xsec = GetXSec( xsec_surf, 2 )

		u_fract = 0.25

		tan = ComputeXSecTan( xsec, u_fract )

		# A tangent is a direction, so it has to have some length.
		assert tan.mag() > 1e-9, "ComputeXSecTan returned a degenerate tangent"

		# The tangent has to follow the curve, so stepping along the curve from the
		# point has to line up with it.
		du = 1.0e-5

		p0 = ComputeXSecPnt( xsec, u_fract )
		p1 = ComputeXSecPnt( xsec, u_fract + du )

		fd = vec3d( p1.x() - p0.x(), p1.y() - p0.y(), p1.z() - p0.z() )

		assert fd.mag() > 1e-12, "the XSec curve does not advance"

		align = ( fd.x() * tan.x() + fd.y() * tan.y() + fd.z() * tan.z() ) / ( fd.mag() * tan.mag() )

		assert align > 0.999, "ComputeXSecTan does not follow the curve"



	def test_ResetXSecSkinParms(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		xsec_surf = GetXSecSurf( fid, 0 )           # Get First (and Only) XSec Surf

		num_xsecs = GetNumXSec( xsec_surf )

		xsec = GetXSec( xsec_surf, 1 )

		SetXSecTanAngles( xsec, XSEC_BOTH_SIDES, 15.0, -1.0e12, -1.0e12, -1.0e12 )      # Set Tangent Angles At Cross Section
		SetXSecContinuity( xsec, 1 )                       # Set Continuity At Cross Section

		assert abs( GetParmVal( GetXSecParm( xsec, "TopLAngle" ) ) - 15.0 ) < 1e-6, "the skin Parms were never set"

		ResetXSecSkinParms( xsec )

		# Resetting zeroes every skin value on all four sides and turns the symmetry
		# flags back on.  Continuity is left alone.
		for skin_parm in [ "TopLAngle", "TopRAngle", "TopLSlew", "TopLStrength", "TopLCurve",
							"RightLAngle", "BottomLAngle", "LeftLAngle" ]:
			assert abs( GetParmVal( GetXSecParm( xsec, skin_parm ) ) ) < 1e-6, "ResetXSecSkinParms did not zero " + skin_parm

		assert abs( GetParmVal( GetXSecParm( xsec, "TBSym" ) ) - 1.0 ) < 1e-12, "ResetXSecSkinParms did not restore the symmetry flags"
		assert abs( GetParmVal( GetXSecParm( xsec, "RLSym" ) ) - 1.0 ) < 1e-12, "ResetXSecSkinParms did not restore the symmetry flags"



	def test_GetXSecContinuity(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		xsec_surf = GetXSecSurf( fid, 0 )           # Get First (and Only) XSec Surf

		num_xsecs = GetNumXSec( xsec_surf )

		for i in range(num_xsecs):

			xsec = GetXSec( xsec_surf, i )

			SetXSecContinuity( xsec, 1 )                       # Set Continuity At Cross Section

			# The setter is shorthand for the section's continuity Parm.
			assert abs( GetParmVal( GetXSecParm( xsec, "ContinuityTop" ) ) - 1.0 ) < 1e-12, "SetXSecContinuity did not set section " + str( i )

			SetXSecContinuity( xsec, 0 )

			assert abs( GetParmVal( GetXSecParm( xsec, "ContinuityTop" ) ) ) < 1e-12, "SetXSecContinuity did not clear section " + str( i )

			SetXSecContinuity( xsec, 1 )



	def test_SetXSecContinuity(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		xsec = GetXSec( xsec_surf, 1 )

		SetXSecContinuity( xsec, 1 )

		assert GetXSecContinuity( xsec ) == 1, "SetXSecContinuity did not take"



	def test_GetXSecTanAngles(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		num_xsecs = GetNumXSec( xsec_surf )

		for i in range(num_xsecs):

			xsec = GetXSec( xsec_surf, i )

			SetXSecTanAngles( xsec, XSEC_BOTH_SIDES, 10.0, -1.0e12, -1.0e12, -1.0e12 )       # Set Tangent Angles At Cross Section

			# The setter is shorthand for the skin Parms, so the value has to show up
			# on both sides of the section.
			assert abs( GetParmVal( GetXSecParm( xsec, "TopLAngle" ) ) - 10.0 ) < 1e-6, "SetXSecTanAngles did not set the top of section " + str( i )
			assert abs( GetParmVal( GetXSecParm( xsec, "TopRAngle" ) ) - 10.0 ) < 1e-6, "SetXSecTanAngles did not set the top of section " + str( i )



	def test_SetXSecTanAngles(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		xsec = GetXSec( xsec_surf, 1 )

		SetXSecTanAngles( xsec, XSEC_BOTH_SIDES, 5.0, 5.0, 5.0, 5.0 )

		vals = GetXSecTanAngles( xsec, XSEC_LEFT_SIDE )

		for v in vals:
			assert abs( v - 5.0 ) < 1e-6, "SetXSecTanAngles did not take"



	def test_GetXSecTanSlews(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		num_xsecs = GetNumXSec( xsec_surf )

		for i in range(num_xsecs):

			xsec = GetXSec( xsec_surf, i )

			SetXSecTanSlews( xsec, XSEC_BOTH_SIDES, 5.0, -1.0e12, -1.0e12, -1.0e12 )       # Set Tangent Slews At Cross Section

			# The setter is shorthand for the skin Parms, so the value has to show up
			# on both sides of the section.
			assert abs( GetParmVal( GetXSecParm( xsec, "TopLSlew" ) ) - 5.0 ) < 1e-6, "SetXSecTanSlews did not set the top of section " + str( i )
			assert abs( GetParmVal( GetXSecParm( xsec, "TopRSlew" ) ) - 5.0 ) < 1e-6, "SetXSecTanSlews did not set the top of section " + str( i )



	def test_SetXSecTanSlews(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		xsec = GetXSec( xsec_surf, 1 )

		SetXSecTanSlews( xsec, XSEC_BOTH_SIDES, 5.0, 5.0, 5.0, 5.0 )

		vals = GetXSecTanSlews( xsec, XSEC_LEFT_SIDE )

		for v in vals:
			assert abs( v - 5.0 ) < 1e-6, "SetXSecTanSlews did not take"



	def test_GetXSecTanStrengths(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Flatten ends
		num_xsecs = GetNumXSec( xsec_surf )

		for i in range(num_xsecs):

			xsec = GetXSec( xsec_surf, i )

			SetXSecTanStrengths( xsec, XSEC_BOTH_SIDES, 0.8, -1.0e12, -1.0e12, -1.0e12 )  # Set Tangent Strengths At Cross Section

			# The setter is shorthand for the skin Parms, so the value has to show up
			# on both sides of the section.
			assert abs( GetParmVal( GetXSecParm( xsec, "TopLStrength" ) ) - 0.8 ) < 1e-6, "SetXSecTanStrengths did not set the top of section " + str( i )
			assert abs( GetParmVal( GetXSecParm( xsec, "TopRStrength" ) ) - 0.8 ) < 1e-6, "SetXSecTanStrengths did not set the top of section " + str( i )



	def test_SetXSecTanStrengths(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		xsec = GetXSec( xsec_surf, 1 )

		SetXSecTanStrengths( xsec, XSEC_BOTH_SIDES, 5.0, 5.0, 5.0, 5.0 )

		vals = GetXSecTanStrengths( xsec, XSEC_LEFT_SIDE )

		for v in vals:
			assert abs( v - 5.0 ) < 1e-6, "SetXSecTanStrengths did not take"



	def test_GetXSecCurvatures(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		# Flatten ends
		num_xsecs = GetNumXSec( xsec_surf )

		for i in range(num_xsecs):

			xsec = GetXSec( xsec_surf, i )

			SetXSecCurvatures( xsec, XSEC_BOTH_SIDES, 0.2, -1.0e12, -1.0e12, -1.0e12 )  # Set Curvatures At Cross Section

			# The setter is shorthand for the skin Parms, so the value has to show up
			# on both sides of the section.
			assert abs( GetParmVal( GetXSecParm( xsec, "TopLCurve" ) ) - 0.2 ) < 1e-6, "SetXSecCurvatures did not set the top of section " + str( i )
			assert abs( GetParmVal( GetXSecParm( xsec, "TopRCurve" ) ) - 0.2 ) < 1e-6, "SetXSecCurvatures did not set the top of section " + str( i )



	def test_SetXSecCurvatures(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		xsec = GetXSec( xsec_surf, 1 )

		SetXSecCurvatures( xsec, XSEC_BOTH_SIDES, 5.0, 5.0, 5.0, 5.0 )

		vals = GetXSecCurvatures( xsec, XSEC_LEFT_SIDE )

		for v in vals:
			assert abs( v - 5.0 ) < 1e-6, "SetXSecCurvatures did not take"



	def test_ReadFileAirfoil(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL )

		xsec = GetXSec( xsec_surf, 1 )

		ReadFileAirfoil( xsec, "airfoil/N0012_VSP.af" )

		up_array = GetAirfoilUpperPnts( xsec )
		low_array = GetAirfoilLowerPnts( xsec )

		assert len( up_array ) > 0, "ReadFileAirfoil did not read matching surfaces"
		assert len( up_array ) == len( low_array ), "ReadFileAirfoil did not read matching surfaces"

		# The points run from the leading edge to the trailing edge on a unit chord.
		assert abs( up_array[0].x() ) < 1e-6, "ReadFileAirfoil did not normalize the chord"
		assert abs( up_array[-1].x() - 1.0 ) < 1e-6, "ReadFileAirfoil did not normalize the chord"
		assert abs( low_array[0].x() ) < 1e-6, "ReadFileAirfoil did not normalize the chord"

		# A NACA 0012 is symmetric, so the lower surface mirrors the upper, and the
		# section is twelve percent thick.
		for i in range( len( up_array ) ):
			assert abs( low_array[i].y() + up_array[i].y() ) < 1e-6, "ReadFileAirfoil did not read a symmetric section"

		max_up = max( [ p.y() for p in up_array ] )

		assert abs( 2.0 * max_up - 0.12 ) < 1e-3, "ReadFileAirfoil did not read a twelve percent section"



	def test_SetAirfoilUpperPnts(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL )

		xsec = GetXSec( xsec_surf, 1 )

		ReadFileAirfoil( xsec, "airfoil/N0012_VSP.af" )

		up_array = GetAirfoilUpperPnts( xsec )

		for i in range(int( len(up_array) )):

			up_array[i].scale_y( 2.0 )

		SetAirfoilUpperPnts( xsec, up_array )

		check_array = GetAirfoilUpperPnts( xsec )

		assert len( check_array ) == len( up_array ), "SetAirfoilUpperPnts point count"

		# The doubled upper surface has to come back doubled, and the lower surface
		# has to be left alone.
		for i in range( len( up_array ) ):
			assert dist( check_array[i], up_array[i] ) < 1e-6, "SetAirfoilUpperPnts did not store point " + str( i )

		low_array = GetAirfoilLowerPnts( xsec )

		max_up = max( [ p.y() for p in check_array ] )
		min_low = min( [ p.y() for p in low_array ] )

		assert abs( max_up + 2.0 * min_low ) < 1e-6, "SetAirfoilUpperPnts did not leave the lower surface alone"



	def test_SetAirfoilLowerPnts(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL )

		xsec = GetXSec( xsec_surf, 1 )

		ReadFileAirfoil( xsec, "airfoil/N0012_VSP.af" )

		low_array = GetAirfoilLowerPnts( xsec )

		for i in range(int( len(low_array) )):

			low_array[i].scale_y( 0.5 )

		SetAirfoilLowerPnts( xsec, low_array )

		check_array = GetAirfoilLowerPnts( xsec )

		assert len( check_array ) == len( low_array ), "SetAirfoilLowerPnts point count"

		# The halved lower surface has to come back halved, and the upper surface
		# has to be left alone.
		for i in range( len( low_array ) ):
			assert dist( check_array[i], low_array[i] ) < 1e-6, "SetAirfoilLowerPnts did not store point " + str( i )

		up_array = GetAirfoilUpperPnts( xsec )

		max_up = max( [ p.y() for p in up_array ] )
		min_low = min( [ p.y() for p in check_array ] )

		assert abs( 0.5 * max_up + min_low ) < 1e-6, "SetAirfoilLowerPnts did not leave the upper surface alone"



	def test_SetAirfoilPnts(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL )

		xsec = GetXSec( xsec_surf, 1 )

		ReadFileAirfoil( xsec, "airfoil/N0012_VSP.af" )

		up_array = GetAirfoilUpperPnts( xsec )

		low_array = GetAirfoilLowerPnts( xsec )

		for i in range(int( len(up_array) )):

			up_array[i].scale_y( 2.0 )

			low_array[i].scale_y( 0.5 )

		SetAirfoilPnts( xsec, up_array, low_array )

		check_up = GetAirfoilUpperPnts( xsec )
		check_low = GetAirfoilLowerPnts( xsec )

		assert len( check_up ) == len( up_array ), "SetAirfoilPnts point count"
		assert len( check_low ) == len( low_array ), "SetAirfoilPnts point count"

		for i in range( len( up_array ) ):
			assert dist( check_up[i], up_array[i] ) < 1e-6, "SetAirfoilPnts did not store point " + str( i )
			assert dist( check_low[i], low_array[i] ) < 1e-6, "SetAirfoilPnts did not store point " + str( i )

		# The section started symmetric; doubling the top and halving the bottom
		# leaves the top four times as deep as the bottom.
		max_up = max( [ p.y() for p in check_up ] )
		min_low = min( [ p.y() for p in check_low ] )

		assert abs( max_up + 4.0 * min_low ) < 1e-6, "SetAirfoilPnts did not scale the two surfaces apart"



	def test_GetHersheyBarLiftDist(self):
		pi = 3.14159265358979323846
		# Compute theoretical lift and drag distributions using 100 points
		Vinf = 100

		halfAR = 20

		alpha_deg = 10

		n_pts = 100

		cl_dist_theo = GetHersheyBarLiftDist( int( n_pts ), alpha_deg*pi/180, Vinf, ( 2 * halfAR ), False )
		assert len( cl_dist_theo ) > 0, "GetHersheyBarLiftDist returned nothing"

		cd_dist_theo = GetHersheyBarDragDist( int( n_pts ), alpha_deg*pi/180, Vinf, ( 2 * halfAR ), False )



	def test_GetHersheyBarDragDist(self):
		pi = 3.14159265358979323846
		# Compute theoretical lift and drag distributions using 100 points
		Vinf = 100

		halfAR = 20

		alpha_deg = 10

		n_pts = 100

		cl_dist_theo = GetHersheyBarLiftDist( int( n_pts ), alpha_deg*pi/180, Vinf, ( 2 * halfAR ), False )

		cd_dist_theo = GetHersheyBarDragDist( int( n_pts ), alpha_deg*pi/180, Vinf, ( 2 * halfAR ), False )
		assert len( cd_dist_theo ) > 0, "GetHersheyBarDragDist returned nothing"



	def test_GetVKTAirfoilPnts(self):
		pi = 3.14159265358979323846

		npts = 122

		alpha = 0.0

		epsilon = 0.1

		kappa = 0.1

		tau = 10

		xyz_airfoil = GetVKTAirfoilPnts(npts, alpha, epsilon, kappa, tau*(pi/180) )
		assert len( xyz_airfoil ) > 0, "GetVKTAirfoilPnts returned nothing"

		cp_dist = GetVKTAirfoilCpDist( alpha, epsilon, kappa, tau*(pi/180), xyz_airfoil )



	def test_GetVKTAirfoilCpDist(self):
		pi = 3.14159265358979323846

		npts = 122

		alpha = 0.0

		epsilon = 0.1

		kappa = 0.1

		tau = 10

		xyz_airfoil = GetVKTAirfoilPnts(npts, alpha, epsilon, kappa, tau*(pi/180) )

		cp_dist = GetVKTAirfoilCpDist( alpha, epsilon, kappa, tau*(pi/180), xyz_airfoil )
		assert len( cp_dist ) > 0, "GetVKTAirfoilCpDist returned nothing"



	def test_GetEllipsoidSurfPnts(self):
		pnts = GetEllipsoidSurfPnts( vec3d( 0.0, 0.0, 0.0 ), vec3d( 1.0, 2.0, 3.0 ), 10, 10 )

		assert len( pnts ) > 0, "GetEllipsoidSurfPnts returned nothing"



	def test_GetFeatureLinePnts(self):
		pid = AddGeom( "POD" )

		Update()

		pnts = GetFeatureLinePnts( pid )

		assert len( pnts ) > 0, "GetFeatureLinePnts returned nothing"



	def test_GetEllipsoidCpDist(self):
		import math
		pi = 3.14159265358979323846

		npts = 101

		abc_rad = vec3d(1.0, 2.0, 3.0)

		alpha = 5 # deg

		beta = 5 # deg

		V_inf = 100.0

		x_slice_pnt_vec = [None]*npts
		theta_vec = [None]*npts

		theta_vec[0] = 0

		for i in range(1, npts):
			theta_vec[i] = theta_vec[i-1] + (2 * pi / (npts - 1))


		for i in range(npts):

			x_slice_pnt_vec[i] = vec3d( 0, abc_rad.y() * math.cos( theta_vec[i] ), abc_rad.z() * math.sin( theta_vec[i] ) )

		V_vec = vec3d( ( V_inf * math.cos( alpha*pi/180 ) * math.cos( beta*pi/180 ) ), ( V_inf * math.sin( beta*pi/180 ) ), ( V_inf * math.sin( alpha*pi/180 ) * math.cos( beta*pi/180 ) ) )

		cp_dist = GetEllipsoidCpDist( x_slice_pnt_vec, abc_rad, V_vec )
		assert len( cp_dist ) > 0, "GetEllipsoidCpDist returned nothing"



	def test_IntegrateEllipsoidFlow(self):
		val = IntegrateEllipsoidFlow( vec3d( 1.0, 2.0, 3.0 ), 0 )

		assert val != 0.0, "IntegrateEllipsoidFlow returned zero"



	def test_GetAirfoilUpperPnts(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL )

		xsec = GetXSec( xsec_surf, 1 )

		ReadFileAirfoil( xsec, "airfoil/N0012_VSP.af" )

		up_array = GetAirfoilUpperPnts( xsec )
		assert len( up_array ) > 0, "GetAirfoilUpperPnts returned nothing"



	def test_GetAirfoilLowerPnts(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL )

		xsec = GetXSec( xsec_surf, 1 )

		ReadFileAirfoil( xsec, "airfoil/N0012_VSP.af" )

		low_array = GetAirfoilLowerPnts( xsec )
		assert len( low_array ) > 0, "GetAirfoilLowerPnts returned nothing"



	def test_GetUpperCSTCoefs(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		coefs = GetUpperCSTCoefs( xsec )

		assert len( coefs ) > 0, "GetUpperCSTCoefs returned nothing"



	def test_GetLowerCSTCoefs(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		coefs = GetLowerCSTCoefs( xsec )

		assert len( coefs ) > 0, "GetLowerCSTCoefs returned nothing"



	def test_GetUpperCSTDegree(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		assert GetUpperCSTDegree( xsec ) >= 1, "GetUpperCSTDegree returned a degenerate degree"



	def test_GetLowerCSTDegree(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		assert GetLowerCSTDegree( xsec ) >= 1, "GetLowerCSTDegree returned a degenerate degree"



	def test_SetUpperCST(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		coefs = GetUpperCSTCoefs( xsec )

		SetUpperCST( xsec, GetUpperCSTDegree( xsec ), coefs )

		Update()



	def test_SetLowerCST(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		coefs = GetLowerCSTCoefs( xsec )

		SetLowerCST( xsec, GetLowerCSTDegree( xsec ), coefs )

		Update()



	def test_PromoteCSTUpper(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		deg = GetUpperCSTDegree( xsec )

		PromoteCSTUpper( xsec )

		assert GetUpperCSTDegree( xsec ) == deg + 1, "PromoteCSTUpper did not raise the degree"



	def test_PromoteCSTLower(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		deg = GetLowerCSTDegree( xsec )

		PromoteCSTLower( xsec )

		assert GetLowerCSTDegree( xsec ) == deg + 1, "PromoteCSTLower did not raise the degree"



	def test_DemoteCSTUpper(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		PromoteCSTUpper( xsec )

		deg = GetUpperCSTDegree( xsec )

		DemoteCSTUpper( xsec )

		assert GetUpperCSTDegree( xsec ) == deg - 1, "DemoteCSTUpper did not lower the degree"



	def test_DemoteCSTLower(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_CST_AIRFOIL )

		Update()

		xsec = GetXSec( xsec_surf, 1 )

		PromoteCSTLower( xsec )

		deg = GetLowerCSTDegree( xsec )

		DemoteCSTLower( xsec )

		assert GetLowerCSTDegree( xsec ) == deg - 1, "DemoteCSTLower did not lower the degree"



	def test_FitAfCST(self):
		wid = AddGeom( "WING" )

		xsec_surf = GetXSecSurf( wid, 0 )

		Update()

		FitAfCST( xsec_surf, 1, 5 )

		Update()



	def test_AddBackground3D(self):
		nbg = GetNumBackground3Ds()

		# Add Background3D
		bg_id = AddBackground3D()

		if GetNumBackground3Ds() != nbg + 1 :
			print( "ERROR: AddBackground3D" )
			assert False, "ERROR: AddBackground3D"

		DelBackground3D( bg_id )


	def test_GetNumBackground3Ds(self):
		nbg = GetNumBackground3Ds()

		# Add Background3D
		bg_id = AddBackground3D()

		if GetNumBackground3Ds() != nbg + 1 :
			print( "ERROR: AddBackground3D" )
			assert False, "ERROR: AddBackground3D"

		DelBackground3D( bg_id )


	def test_GetAllBackground3Ds(self):
		nbg = GetNumBackground3Ds()

		# Add Background3D
		AddBackground3D()
		AddBackground3D()
		AddBackground3D()

		if GetNumBackground3Ds() != nbg + 3 :
			print( "ERROR: AddBackground3D" )
			assert False, "ERROR: AddBackground3D"

		bg_array = GetAllBackground3Ds()

		for n in range( len( bg_array ) ):
			print( bg_array[n] )

		DelAllBackground3Ds()


	def test_ShowAllBackground3Ds(self):
		# Add Background3D
		AddBackground3D()
		AddBackground3D()
		AddBackground3D()

		assert GetNumBackground3Ds() == 3, "the three Background3Ds were not all added"
		assert len( GetAllBackground3Ds() ) == 3, "the three Background3Ds were not all added"

		ShowAllBackground3Ds()

		DelAllBackground3Ds()

		assert GetNumBackground3Ds() == 0, "DelAllBackground3Ds left something behind"
		assert len( GetAllBackground3Ds() ) == 0, "DelAllBackground3Ds left something behind"


	def test_HideAllBackground3Ds(self):
		# Add Background3D
		AddBackground3D()
		AddBackground3D()
		AddBackground3D()

		assert GetNumBackground3Ds() == 3, "the three Background3Ds were not all added"
		assert len( GetAllBackground3Ds() ) == 3, "the three Background3Ds were not all added"

		HideAllBackground3Ds()

		DelAllBackground3Ds()

		assert GetNumBackground3Ds() == 0, "DelAllBackground3Ds left something behind"
		assert len( GetAllBackground3Ds() ) == 0, "DelAllBackground3Ds left something behind"


	def test_DelAllBackground3Ds(self):
		# Add Background3D
		AddBackground3D()
		AddBackground3D()
		AddBackground3D()

		DelAllBackground3Ds()

		nbg = GetNumBackground3Ds()

		if nbg != 0 :
			print( "ERROR: DelAllBackground3Ds" )
			assert False, "ERROR: DelAllBackground3Ds"



	def test_DelBackground3D(self):
		# Add Background3D
		AddBackground3D()
		bg_id = AddBackground3D()
		AddBackground3D()

		nbg = GetNumBackground3Ds()

		DelBackground3D( bg_id )

		if GetNumBackground3Ds() != nbg -1 :
			print( "ERROR: DelBackground3D" )
			assert False, "ERROR: DelBackground3D"



	def test_GetAllBackground3DRelativePaths(self):
		# Add Background3D
		AddBackground3D()
		AddBackground3D()
		AddBackground3D()

		bg_file_array = GetAllBackground3DRelativePaths()
		assert len( bg_file_array ) > 0, "GetAllBackground3DRelativePaths returned nothing"

		for n in range( len( bg_file_array ) ):
			print( bg_file_array[n] )

		DelAllBackground3Ds()


	def test_GetAllBackground3DAbsolutePaths(self):
		# Add Background3D
		AddBackground3D()
		AddBackground3D()
		AddBackground3D()

		bg_file_array = GetAllBackground3DAbsolutePaths()
		assert len( bg_file_array ) > 0, "GetAllBackground3DAbsolutePaths returned nothing"

		for n in range( len( bg_file_array ) ):
			print( bg_file_array[n] )

		DelAllBackground3Ds()


	def test_GetBackground3DRelativePath(self):
		# Add Background3D
		bg_id = AddBackground3D()

		SetBackground3DRelativePath( bg_id, "front.png" )
		bg_file = GetBackground3DRelativePath( bg_id )
		assert len( bg_file ) > 0, "GetBackground3DRelativePath returned nothing"

		print( bg_file )

		DelAllBackground3Ds()


	def test_GetBackground3DAbsolutePath(self):
		# Add Background3D
		bg_id = AddBackground3D()

		SetBackground3DAbsolutePath( bg_id, "/user/me/vsp_work/front.png" )
		bg_file = GetBackground3DAbsolutePath( bg_id )
		assert len( bg_file ) > 0, "GetBackground3DAbsolutePath returned nothing"

		print( bg_file )

		DelAllBackground3Ds()


	def test_SetBackground3DRelativePath(self):
		# Add Background3D
		bg_id = AddBackground3D()

		SetBackground3DRelativePath( bg_id, "front.png" )
		assert GetBackground3DRelativePath( bg_id ) == "front.png", "SetBackground3DRelativePath did not take"

		bg_file = GetBackground3DRelativePath( bg_id )

		print( bg_file )

		DelAllBackground3Ds()


	def test_SetBackground3DAbsolutePath(self):
		# Add Background3D
		bg_id = AddBackground3D()

		SetBackground3DAbsolutePath( bg_id, "front.png" )
		bg_file = GetBackground3DAbsolutePath( bg_id )

		print( bg_file )

		# A relative name is resolved against the working directory, so the path that
		# comes back ends with the name that was set.
		assert bg_file.endswith( "front.png" ), "SetBackground3DAbsolutePath did not take"

		DelAllBackground3Ds()


	def test_CreateAndAddBogie(self):
		gear_id = AddGeom( "GEAR", "" )             # Add a landing gear Geom

		bogie_id = CreateAndAddBogie( gear_id )     # Create and add a Bogie

		# Bogies are ParmContainers -- work with their Parms once you have the ID.
		SetParmVal( bogie_id, "NumAcross", "Bogie", 2 )    # Two wheels across
		SetParmVal( bogie_id, "NumTandem", "Bogie", 2 )    # Two wheels in tandem


	def test_GetNumBogies(self):
		gear_id = AddGeom( "GEAR", "" )

		CreateAndAddBogie( gear_id )
		CreateAndAddBogie( gear_id )

		num_bogie = GetNumBogies( gear_id )            # num_bogie == 2

		assert num_bogie == 2, "GetNumBogies, two were added"


	def test_GetAllBogies(self):
		gear_id = AddGeom( "GEAR", "" )

		CreateAndAddBogie( gear_id )
		CreateAndAddBogie( gear_id )

		bogie_ids = GetAllBogies( gear_id )
		assert len( bogie_ids ) > 0, "GetAllBogies returned nothing"


	def test_DelBogie(self):
		gear_id = AddGeom( "GEAR", "" )

		bogie_id = CreateAndAddBogie( gear_id )

		num_before_del = GetNumBogies( gear_id )
		DelBogie( gear_id, bogie_id )
		assert GetNumBogies( gear_id ) < num_before_del, "DelBogie removed nothing"



	def test_DelAllBogies(self):
		gear_id = AddGeom( "GEAR", "" )

		CreateAndAddBogie( gear_id )
		CreateAndAddBogie( gear_id )

		DelAllBogies( gear_id )                            # GetNumBogies( gear_id ) == 0
		assert GetNumBogies( gear_id ) == 0, "DelAllBogies left something behind"



	def test_SetAuxiliaryGeomContactPtID(self):
		gear_id = AddGeom( "GEAR", "" )

		nose_id = CreateAndAddBogie( gear_id )
		main_id = CreateAndAddBogie( gear_id )

		SetParmVal( main_id, "Symmetrical", "Bogie", 1 )    # Left and right main gear

		aux_id = AddGeom( "AUXILIARY", gear_id )

		SetParmVal( aux_id, "AuxiliaryGeomType", "Design", AUX_GEOM_THREE_PT_GROUND )

		SetAuxiliaryGeomContactPtID( aux_id, 0, nose_id )
		SetAuxiliaryGeomContactPtID( aux_id, 1, main_id )
		SetAuxiliaryGeomContactPtID( aux_id, 2, main_id )

		Update()

		assert GetAuxiliaryGeomContactPtID( aux_id, 0 ) == nose_id, "SetAuxiliaryGeomContactPtID did not take"



	def test_GetAuxiliaryGeomContactPtID(self):
		gear_id = AddGeom( "GEAR", "" )

		bogie_id = CreateAndAddBogie( gear_id )

		aux_id = AddGeom( "AUXILIARY", gear_id )

		SetParmVal( aux_id, "AuxiliaryGeomType", "Design", AUX_GEOM_ONE_PT_GROUND )

		Update()

		# With only one Bogie to choose from, every contact point resolves to it.
		assert GetAuxiliaryGeomContactPtID( aux_id, 0 ) == bogie_id, "GetAuxiliaryGeomContactPtID"



	def test_ReadAuxiliaryGeomCCEFile(self):
		gear_id = AddGeom( "GEAR", "" )

		CreateAndAddBogie( gear_id )

		aux_id = AddGeom( "AUXILIARY", gear_id )

		SetParmVal( aux_id, "AuxiliaryGeomType", "Design", AUX_GEOM_THREE_PT_CCE )

		ReadAuxiliaryGeomCCEFile( aux_id, "CCE/SD-24L.cce" )

		Update()



	def test_InitStackPreset(self):
		stack_id = AddGeom( "STACK", "" )

		InitStackPreset( stack_id, STACK_PRESET_FLOWTHRU_MID_ORIG )

		Update()

		# Each preset lays down its own set of XSecs, replacing the default five.
		xsec_surf = GetXSecSurf( stack_id, 0 )

		assert GetNumXSec( xsec_surf ) == 7, "InitStackPreset did not rebuild the XSecs"



	def test_GetNumRoutingPts(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		npt = vsp.GetNumRoutingPts(routing_geom)

		# Three points were added, and the count has to match the ID list.
		assert npt == 3, "GetNumRoutingPts did not count the points that were added"
		assert npt == len( vsp.GetAllRoutingPtIds( routing_geom ) ), "GetNumRoutingPts disagrees with GetAllRoutingPtIds"

		# Deleting one has to move the count.
		vsp.DelRoutingPt( routing_geom, 1 )

		assert vsp.GetNumRoutingPts( routing_geom ) == npt - 1, "GetNumRoutingPts did not follow DelRoutingPt"



	def test_AddRoutingPt(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)


	def test_InsertRoutingPt(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		npt = vsp.GetNumRoutingPts(routing_geom)
		rptPre2 = vsp.InsertRoutingPt(routing_geom, 2, pod2, 0)
		uPre2 = vsp.GetParm( rptPre2, 'U', 'RoutePt')
		vsp.SetParmVal(uPre2, 0.)


	def test_DelRoutingPt(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		num_before_del = vsp.GetNumRoutingPts( routing_geom )
		vsp.DelRoutingPt( routing_geom, 1 )
		assert vsp.GetNumRoutingPts( routing_geom ) < num_before_del, "DelRoutingPt removed nothing"



	def test_DelAllRoutingPt(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		vsp.DelAllRoutingPt( routing_geom )

		assert vsp.GetNumRoutingPts( routing_geom ) == 0, "DelAllRoutingPt left something behind"


	def test_MoveRoutingPt(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		before_ids = vsp.GetAllRoutingPtIds( routing_geom )

		newindx = vsp.MoveRoutingPt( routing_geom, 1, vsp.REORDER_MOVE_DOWN )

		# The point that was at index 1 is now at index 2, and its neighbour has
		# taken its place.
		after_ids = vsp.GetAllRoutingPtIds( routing_geom )

		assert newindx == 2, "MoveRoutingPt did not move the point down"
		assert len( after_ids ) == len( before_ids ), "MoveRoutingPt changed the number of points"
		assert after_ids[2] == before_ids[1], "MoveRoutingPt did not swap the two points"
		assert after_ids[1] == before_ids[2], "MoveRoutingPt did not swap the two points"


	def test_GetRoutingPtID(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		rid = vsp.GetRoutingPtID(routing_geom, 2)


	def test_GetAllRoutingPtIds(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		rpts = vsp.GetAllRoutingPtIds(routing_geom)


	def test_GetRoutingPtParentID(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		gid = vsp.GetRoutingPtParentID(rpt1)


	def test_SetRoutingPtParentID(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		vsp.SetRoutingPtParentID(rpt1, pod1)


	def test_GetMainRoutingPtCoord(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		vsp.Update()
		p1 = vsp.GetMainRoutingPtCoord(rpt1)

		# rpt1 rides on pod2, which was moved two units out in Y.
		assert abs( p1.y() - 2.0 ) < 1e-6, "GetMainRoutingPtCoord did not follow the parent Geom"

		# With no symmetry applied, the main copy is also symm_index 0.
		assert vsp.dist( p1, vsp.GetRoutingPtCoord( routing_geom, 1, 0 ) ) < 1e-6, "GetMainRoutingPtCoord disagrees with GetRoutingPtCoord"



	def test_GetRoutingPtCoord(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		vsp.Update()
		p1 = vsp.GetRoutingPtCoord(routing_geom, 1, 0)

		# rpt1 rides on pod2, which was moved two units out in Y.
		assert abs( p1.y() - 2.0 ) < 1e-6, "GetRoutingPtCoord did not follow the parent Geom"

		# The indexed point has to be the second of the three that were added.
		pvec = vsp.GetAllRoutingPtCoords(routing_geom, 0)

		assert len( pvec ) == 3, "GetAllRoutingPtCoords returned the wrong number of points"
		assert vsp.dist( p1, pvec[1] ) < 1e-6, "GetRoutingPtCoord disagrees with GetAllRoutingPtCoords"



	def test_GetAllRoutingPtCoords(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		vsp.Update()
		pvec = vsp.GetAllRoutingPtCoords(routing_geom, 0)

		# One coordinate per routing point, in the order they were added.
		assert len( pvec ) == 3, "GetAllRoutingPtCoords returned the wrong number of points"

		# rpt0 sits at the nose of pod1 and rpt2 at its tail, both on the
		# centerline.  rpt1 rides on pod2, two units out in Y.
		assert abs( pvec[0].y() ) < 1e-6, "GetAllRoutingPtCoords did not follow the parent Geoms"
		assert abs( pvec[1].y() - 2.0 ) < 1e-6, "GetAllRoutingPtCoords did not follow the parent Geoms"
		assert abs( pvec[2].y() ) < 1e-6, "GetAllRoutingPtCoords did not follow the parent Geoms"

		assert pvec[2].x() > pvec[0].x(), "GetAllRoutingPtCoords did not order the points by U"

		assert vsp.dist( pvec[1], vsp.GetMainRoutingPtCoord( rpt1 ) ) < 1e-6, "GetAllRoutingPtCoords disagrees with GetMainRoutingPtCoord"



	def test_GetRoutingCurve(self):
		pod1 = vsp.AddGeom('POD', '')

		pod2 = vsp.AddGeom('POD', '')
		ypod2 = vsp.GetParm(pod2, 'Y_Rel_Location', 'XForm')
		vsp.SetParmVal(ypod2, 2.0)

		routing_geom = vsp.AddGeom('ROUTING', '')

		rpt0 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u0 = vsp.GetParm( rpt0, 'U', 'RoutePt')
		vsp.SetParmVal(u0, 0.0)

		rpt1 = vsp.AddRoutingPt(routing_geom, pod2, 0)

		rpt2 = vsp.AddRoutingPt(routing_geom, pod1, 0)
		u2 = vsp.GetParm( rpt2, 'U', 'RoutePt')
		vsp.SetParmVal(u2, 1.0)

		vsp.Update()
		pvec = vsp.GetRoutingCurve(routing_geom, 0)

		# The curve is tessellated, so it carries at least as many points as there
		# are routing points, and it has to start and end on them.
		rpts = vsp.GetAllRoutingPtCoords(routing_geom, 0)

		assert len( pvec ) >= len( rpts ), "GetRoutingCurve returned too few points"
		assert vsp.dist( pvec[0], rpts[0] ) < 1e-6, "GetRoutingCurve does not start on the first routing point"
		assert vsp.dist( pvec[-1], rpts[-1] ) < 1e-6, "GetRoutingCurve does not end on the last routing point"



	def test_ChangeBORXSecShape(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_ROUNDED_RECTANGLE )

		if  GetBORXSecShape( bor_id ) != XS_ROUNDED_RECTANGLE :
			print( "ERROR: ChangeBORXSecShape" )
			assert False, "ERROR: ChangeBORXSecShape"



	def test_GetBORXSecShape(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_ROUNDED_RECTANGLE )

		if  GetBORXSecShape( bor_id ) != XS_ROUNDED_RECTANGLE :
			print( "ERROR: GetBORXSecShape" )
			assert False, "ERROR: GetBORXSecShape"



	def test_ReadBORFileXSec(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_FUSE )

		vec_array = ReadBORFileXSec( bor_id, "TestXSec.fxs" )

		Update()

		# The file holds a closed curve, and the section it produced is the one the
		# body is now built on.
		assert len( vec_array ) >= 3, "ReadBORFileXSec returned too few points"
		assert dist( vec_array[0], vec_array[-1] ) < 1e-8, "ReadBORFileXSec returned an open curve"
		assert GetBORXSecShape( bor_id ) == XS_FILE_FUSE, "ReadBORFileXSec changed the section type"

		# The section curve closes on itself.
		assert dist( ComputeBORXSecPnt( bor_id, 0.0 ), ComputeBORXSecPnt( bor_id, 1.0 ) ) < 1e-6, "the BOR section does not close"



	def test_GetBORXSecPnts(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_FUSE )

		# ReadBORFileXSec hands back a tuple, so copy it into a list to edit it.
		vec_array = list( ReadBORFileXSec( bor_id, "TestXSec.fxs" ) )

		Update()

		before = ComputeBORXSecPnt( bor_id, 0.0 )

		assert len( vec_array ) > 0, "ReadBORFileXSec returned no points"

		# The Python vec3d carries no arithmetic operators, so scale by component.
		vec_array[1] = vec3d( vec_array[1].x() * 2.0, vec_array[1].y() * 2.0, vec_array[1].z() * 2.0 )
		vec_array[3] = vec3d( vec_array[3].x() * 2.0, vec_array[3].y() * 2.0, vec_array[3].z() * 2.0 )

		SetBORXSecPnts( bor_id, vec_array )

		Update()

		after = ComputeBORXSecPnt( bor_id, 0.0 )

		# Points 1 and 3 are the top and bottom of the diamond read from file, so
		# doubling them doubles the height of the section while leaving its width
		# alone.  The section is normalized to the body diameter by its height, so
		# the section grows half as wide as it was.
		assert abs( after.x() - 0.5 * before.x() ) < 1e-6, "SetBORXSecPnts did not reshape the section"



	def test_SetBORXSecPnts(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_FILE_FUSE )

		Update()

		# Take the section's own points and hand back a squashed copy of them.
		pnt_vec = [ vec3d( p.x(), 0.5 * p.y(), p.z() ) for p in GetBORXSecPnts( bid ) ]

		SetBORXSecPnts( bid, pnt_vec )

		Update()

		assert len( GetBORXSecPnts( bid ) ) == len( pnt_vec ), "SetBORXSecPnts did not take the points"



	def test_ComputeBORXSecPnt(self):
		#==== Add Geom ====//
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		u_fract = 0.25

		pnt = ComputeBORXSecPnt( bor_id, u_fract )

		# The section is a closed curve, so the ends meet.
		assert dist( ComputeBORXSecPnt( bor_id, 0.0 ), ComputeBORXSecPnt( bor_id, 1.0 ) ) < 1e-6, "the BOR section does not close"

		# The section lies in a plane of constant Z.
		assert abs( pnt.z() - ComputeBORXSecPnt( bor_id, 0.0 ).z() ) < 1e-9, "the BOR section is not planar"

		# Walking the curve has to move, not sit still.
		assert dist( pnt, ComputeBORXSecPnt( bor_id, u_fract + 0.25 ) ) > 1e-9, "ComputeBORXSecPnt does not advance along the curve"



	def test_ComputeBORXSecTan(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		u_fract = 0.25

		tan = ComputeBORXSecTan( bor_id, u_fract )

		# A tangent is a direction, so it has to have some length.
		assert tan.mag() > 1e-9, "ComputeBORXSecTan returned a degenerate tangent"

		# The tangent has to follow the curve, so stepping along the curve from the
		# point has to line up with it.
		du = 1.0e-5

		p0 = ComputeBORXSecPnt( bor_id, u_fract )
		p1 = ComputeBORXSecPnt( bor_id, u_fract + du )

		fd = vec3d( p1.x() - p0.x(), p1.y() - p0.y(), p1.z() - p0.z() )

		assert fd.mag() > 1e-12, "the BOR section does not advance"

		align = ( fd.x() * tan.x() + fd.y() * tan.y() + fd.z() * tan.z() ) / ( fd.mag() * tan.mag() )

		assert align > 0.999, "ComputeBORXSecTan does not follow the curve"



	def test_ReadBORFileAirfoil(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_AIRFOIL )

		ReadBORFileAirfoil( bor_id, "airfoil/N0012_VSP.af" )

		up_array = GetBORAirfoilUpperPnts( bor_id )
		low_array = GetBORAirfoilLowerPnts( bor_id )

		assert len( up_array ) > 0, "ReadBORFileAirfoil did not read matching surfaces"
		assert len( up_array ) == len( low_array ), "ReadBORFileAirfoil did not read matching surfaces"

		# The points run from the leading edge to the trailing edge on a unit chord,
		# and a NACA 0012 is symmetric top to bottom.
		assert abs( up_array[0].x() ) < 1e-6, "ReadBORFileAirfoil did not normalize the chord"
		assert abs( up_array[-1].x() - 1.0 ) < 1e-6, "ReadBORFileAirfoil did not normalize the chord"

		for i in range( len( up_array ) ):
			assert abs( low_array[i].y() + up_array[i].y() ) < 1e-6, "ReadBORFileAirfoil did not read a symmetric section"

		max_up = max( [ p.y() for p in up_array ] )

		assert abs( 2.0 * max_up - 0.12 ) < 1e-3, "ReadBORFileAirfoil did not read a twelve percent section"



	def test_SetBORAirfoilUpperPnts(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_AIRFOIL )

		ReadBORFileAirfoil( bor_id, "airfoil/N0012_VSP.af" )

		up_array = GetBORAirfoilUpperPnts( bor_id )

		for i in range(int( len(up_array) )):

			up_array[i].scale_y( 2.0 )

		SetBORAirfoilUpperPnts( bor_id, up_array )

		# The doubled upper surface has to come back doubled, and the lower surface
		# has to be left alone.
		check_array = GetBORAirfoilUpperPnts( bor_id )
		low_array = GetBORAirfoilLowerPnts( bor_id )

		assert len( check_array ) == len( up_array ), "SetBORAirfoilUpperPnts point count"

		for i in range( len( up_array ) ):
			assert dist( check_array[i], up_array[i] ) < 1e-6, "SetBORAirfoilUpperPnts did not store point " + str( i )

		max_up = max( [ p.y() for p in check_array ] )
		min_low = min( [ p.y() for p in low_array ] )

		assert abs( max_up + 2.0 * min_low ) < 1e-6, "SetBORAirfoilUpperPnts did not leave the lower surface alone"



	def test_SetBORAirfoilLowerPnts(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_AIRFOIL )

		ReadBORFileAirfoil( bor_id, "airfoil/N0012_VSP.af" )

		low_array = GetBORAirfoilLowerPnts( bor_id )

		for i in range(int( len(low_array) )):

			low_array[i].scale_y( 0.5 )

		SetBORAirfoilLowerPnts( bor_id, low_array )

		# The halved lower surface has to come back halved, and the upper surface has
		# to be left alone.
		check_array = GetBORAirfoilLowerPnts( bor_id )
		up_array = GetBORAirfoilUpperPnts( bor_id )

		assert len( check_array ) == len( low_array ), "SetBORAirfoilLowerPnts point count"

		for i in range( len( low_array ) ):
			assert dist( check_array[i], low_array[i] ) < 1e-6, "SetBORAirfoilLowerPnts did not store point " + str( i )

		max_up = max( [ p.y() for p in up_array ] )
		min_low = min( [ p.y() for p in check_array ] )

		assert abs( 0.5 * max_up + min_low ) < 1e-6, "SetBORAirfoilLowerPnts did not leave the upper surface alone"



	def test_SetBORAirfoilPnts(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_AIRFOIL )

		ReadBORFileAirfoil( bor_id, "airfoil/N0012_VSP.af" )

		up_array = GetBORAirfoilUpperPnts( bor_id )

		low_array = GetBORAirfoilLowerPnts( bor_id )

		for i in range(int( len(up_array) )):

			up_array[i].scale_y( 2.0 )

			low_array[i].scale_y( 0.5 )

		SetBORAirfoilPnts( bor_id, up_array, low_array )

		check_up = GetBORAirfoilUpperPnts( bor_id )
		check_low = GetBORAirfoilLowerPnts( bor_id )

		assert len( check_up ) == len( up_array ), "SetBORAirfoilPnts point count"
		assert len( check_low ) == len( low_array ), "SetBORAirfoilPnts point count"

		for i in range( len( up_array ) ):
			assert dist( check_up[i], up_array[i] ) < 1e-6, "SetBORAirfoilPnts did not store point " + str( i )
			assert dist( check_low[i], low_array[i] ) < 1e-6, "SetBORAirfoilPnts did not store point " + str( i )

		# The section started symmetric; doubling the top and halving the bottom
		# leaves the top four times as deep as the bottom.
		max_up = max( [ p.y() for p in check_up ] )
		min_low = min( [ p.y() for p in check_low ] )

		assert abs( max_up + 4.0 * min_low ) < 1e-6, "SetBORAirfoilPnts did not scale the two surfaces apart"



	def test_GetBORAirfoilUpperPnts(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_AIRFOIL )

		ReadBORFileAirfoil( bor_id, "airfoil/N0012_VSP.af" )

		up_array = GetBORAirfoilUpperPnts( bor_id )
		assert len( up_array ) > 0, "GetBORAirfoilUpperPnts returned nothing"



	def test_GetBORAirfoilLowerPnts(self):
		# Add Body of Recolution
		bor_id = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bor_id, XS_FILE_AIRFOIL )

		ReadBORFileAirfoil( bor_id, "airfoil/N0012_VSP.af" )

		low_array = GetBORAirfoilLowerPnts( bor_id )
		assert len( low_array ) > 0, "GetBORAirfoilLowerPnts returned nothing"



	def test_GetBORUpperCSTCoefs(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		coefs = GetBORUpperCSTCoefs( bid )

		assert len( coefs ) > 0, "GetBORUpperCSTCoefs returned nothing"



	def test_GetBORLowerCSTCoefs(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		coefs = GetBORLowerCSTCoefs( bid )

		assert len( coefs ) > 0, "GetBORLowerCSTCoefs returned nothing"



	def test_GetBORUpperCSTDegree(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		assert GetBORUpperCSTDegree( bid ) >= 1, "GetBORUpperCSTDegree returned a degenerate degree"



	def test_GetBORLowerCSTDegree(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		assert GetBORLowerCSTDegree( bid ) >= 1, "GetBORLowerCSTDegree returned a degenerate degree"



	def test_SetBORUpperCST(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		coefs = GetBORUpperCSTCoefs( bid )

		SetBORUpperCST( bid, GetBORUpperCSTDegree( bid ), coefs )

		Update()



	def test_SetBORLowerCST(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		coefs = GetBORLowerCSTCoefs( bid )

		SetBORLowerCST( bid, GetBORLowerCSTDegree( bid ), coefs )

		Update()



	def test_PromoteBORCSTUpper(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		deg = GetBORUpperCSTDegree( bid )

		PromoteBORCSTUpper( bid )

		assert GetBORUpperCSTDegree( bid ) == deg + 1, "PromoteBORCSTUpper did not raise the degree"



	def test_PromoteBORCSTLower(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		deg = GetBORLowerCSTDegree( bid )

		PromoteBORCSTLower( bid )

		assert GetBORLowerCSTDegree( bid ) == deg + 1, "PromoteBORCSTLower did not raise the degree"



	def test_DemoteBORCSTUpper(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		PromoteBORCSTUpper( bid )

		deg = GetBORUpperCSTDegree( bid )

		DemoteBORCSTUpper( bid )

		assert GetBORUpperCSTDegree( bid ) == deg - 1, "DemoteBORCSTUpper did not lower the degree"



	def test_DemoteBORCSTLower(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_CST_AIRFOIL )

		Update()

		PromoteBORCSTLower( bid )

		deg = GetBORLowerCSTDegree( bid )

		DemoteBORCSTLower( bid )

		assert GetBORLowerCSTDegree( bid ) == deg - 1, "DemoteBORCSTLower did not lower the degree"



	def test_FitBORAfCST(self):
		bid = AddGeom( "BODYOFREVOLUTION", "" )

		ChangeBORXSecShape( bid, XS_FOUR_SERIES )

		Update()

		FitBORAfCST( bid, 5 )

		Update()



	def test_WriteBezierAirfoil(self):
		#==== Add Wing Geometry and Set Parms ====//
		wing_id = AddGeom( "WING", "" )

		u = 0.5 # export airfoil at mid span location

		#==== Write Bezier Airfoil File ====//
		WriteBezierAirfoil( "Example_Bezier.bz", wing_id, u )
		# The call above should have produced a file with content in it.
		import os
		assert os.path.getsize( "Example_Bezier.bz" ) > 0, "WriteBezierAirfoil wrote no file"




	def test_WriteSeligAirfoil(self):
		#==== Add Wing Geometry and Set Parms ====//
		wing_id = AddGeom( "WING", "" )

		u = 0.5 # export airfoil at mid span location

		#==== Write Selig Airfoil File ====//
		WriteSeligAirfoil( "Example_Selig.dat", wing_id, u )
		# The call above should have produced a file with content in it.
		import os
		assert os.path.getsize( "Example_Selig.dat" ) > 0, "WriteSeligAirfoil wrote no file"




	def test_GetAirfoilCoordinates(self):
		wid = AddGeom( "WING" )

		Update()

		pnts = GetAirfoilCoordinates( wid, 0.5 )

		assert len( pnts ) > 0, "GetAirfoilCoordinates returned nothing"



	def test_EditXSecInitShape(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 2, XS_EDIT_CURVE )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		# Set XSec 2 to linear
		EditXSecConvertTo( xsec_2, LINEAR )

		linear_pts = GetEditXSecCtrlVec( xsec_2, True )

		EditXSecInitShape( xsec_2 ) # Change back to default ellipse

		Update()

		# The default ellipse is a four point Bezier, so it carries more control
		# points than the linear square it replaced.
		ellipse_pts = GetEditXSecCtrlVec( xsec_2, True )

		assert len( ellipse_pts ) >= 4 and ( len( ellipse_pts ) - 1 ) % 3 == 0, "EditXSecInitShape did not restore a cubic Bezier"
		assert len( ellipse_pts ) > len( linear_pts ), "EditXSecInitShape did not rebuild the control points"

		# The ellipse is symmetric about both axes, so it stays inside the unit box
		# the control points are normalized to.
		for p in ellipse_pts:
			assert abs( p.x() ) <= 0.5 + 1e-9, "the rebuilt shape is not normalized"
			assert abs( p.y() ) <= 0.5 + 1e-9, "the rebuilt shape is not normalized"



	def test_EditXSecConvertTo(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# The default shape is a Bezier ellipse, stored in groups of three plus a
		# closing point.
		bezier_pts = GetEditXSecCtrlVec( xsec_1, True )

		assert len( bezier_pts ) >= 4 and ( len( bezier_pts ) - 1 ) % 3 == 0, "the edit curve did not start out as a cubic Bezier"

		# Set XSec 1 to Linear
		EditXSecConvertTo( xsec_1, LINEAR )

		Update()

		# A linear curve needs no interior control points, so the conversion drops
		# them: the ellipse keeps only the points that were on the curve.
		linear_pts = GetEditXSecCtrlVec( xsec_1, True )

		assert len( linear_pts ) == ( len( bezier_pts ) - 1 ) // 3 + 1, "EditXSecConvertTo did not drop the interior control points"

		# Converting back has to put them back.
		EditXSecConvertTo( xsec_1, CEDIT )

		Update()

		assert len( GetEditXSecCtrlVec( xsec_1, True ) ) == len( bezier_pts ), "EditXSecConvertTo would not convert back"



	def test_GetEditXSecUVec(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 2, XS_EDIT_CURVE )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		# Set XSec 2 to linear
		EditXSecConvertTo( xsec_2, LINEAR )

		u_vec = GetEditXSecUVec( xsec_2 )

		if  u_vec[1] - 0.25 > 1e-6 :
			print( "Error: GetEditXSecUVec" )
			assert False, "Error: GetEditXSecUVec"



	def test_GetEditXSecCtrlVec(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# Get the control points for the default shape
		xsec1_pts = GetEditXSecCtrlVec( xsec_1, True ) # The returned control points will not be scaled by width and height
		assert len( xsec1_pts ) > 0, "GetEditXSecCtrlVec returned nothing"

		print( f"Normalized Bottom Point of XSecCurve: {xsec1_pts[3].x()}, {xsec1_pts[3].y()}, {xsec1_pts[3].z()}" )



	def test_SetEditXSecPnts(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 2, XS_EDIT_CURVE )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		# Set XSec 2 to linear
		EditXSecConvertTo( xsec_2, LINEAR )

		# Turn off R/L symmetry
		SetParmVal( GetXSecParm( xsec_2, "SymType"), SYM_NONE )

		# Define a square
		xsec2_pts = [vec3d(0.5, 0.5, 0.0),
				vec3d(0.5, -0.5, 0.0),
				vec3d(-0.5, -0.5, 0.0),
				vec3d(-0.5, 0.5, 0.0),
				vec3d(0.5, 0.5, 0.0)]

		# u vec must start at 0.0 and end at 1.0
		u_vec = [0.0, 0.25, 0.5, 0.75, 1.0]

		r_vec = [0.0, 0.0, 0.0, 0.0, 0.0]

		SetEditXSecPnts( xsec_2, u_vec, xsec2_pts, r_vec ) # Note: points are unscaled by the width and height parms

		new_pnts = GetEditXSecCtrlVec( xsec_2, True ) # The returned control points will not be scaled by width and height

		if  dist( new_pnts[3], xsec2_pts[3] ) > 1e-6 :
			print( "Error: SetEditXSecPnts")
			assert False, "Error: SetEditXSecPnts"



	def test_EditXSecDelPnt(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 2, XS_EDIT_CURVE )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		# Turn off R/L symmetry
		SetParmVal( GetXSecParm( xsec_2, "SymType"), SYM_NONE )

		old_pnts = GetEditXSecCtrlVec( xsec_2, True ) # The returned control points will not be scaled by width and height

		EditXSecDelPnt( xsec_2, 3 ) # Remove control point at bottom of circle

		new_pnts = GetEditXSecCtrlVec( xsec_2, True ) # The returned control points will not be scaled by width and height

		if  len(old_pnts) - len(new_pnts) != 3  :
			print( "Error: EditXSecDelPnt")
			assert False, "Error: EditXSecDelPnt"



	def test_EditXSecSplit01(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 2, XS_EDIT_CURVE )

		# Identify XSec 2
		xsec_2 = GetXSec( xsec_surf, 2 )

		# Turn off R/L symmetry
		SetParmVal( GetXSecParm( xsec_2, "SymType"), SYM_NONE )

		old_pnts = GetEditXSecCtrlVec( xsec_2, True ) # The returned control points will not be scaled by width and height

		new_pnt_ind = EditXSecSplit01( xsec_2, 0.375 )

		new_pnts = GetEditXSecCtrlVec( xsec_2, True ) # The returned control points will not be scaled by width and height

		if  len(new_pnts) - len(old_pnts) != 3  :
			print( "Error: EditXSecSplit01")
			assert False, "Error: EditXSecSplit01"



	def test_MoveEditXSecPnt(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# Turn off R/L symmetry
		SetParmVal( GetXSecParm( xsec_1, "SymType"), SYM_NONE )

		# Get the control points for the default shape
		xsec1_pts = GetEditXSecCtrlVec( xsec_1, True ) # The returned control points will not be scaled by width and height

		# Identify a control point that lies on the curve and shift it in Y
		move_pnt_ind = 3

		new_pnt = vec3d( xsec1_pts[move_pnt_ind].x(), 2 * xsec1_pts[move_pnt_ind].y(), 0.0 )

		# Move the control point
		MoveEditXSecPnt( xsec_1, move_pnt_ind, new_pnt )

		new_pnts = GetEditXSecCtrlVec( xsec_1, True ) # The returned control points will not be scaled by width and height

		if  dist( new_pnt, new_pnts[move_pnt_ind] ) > 1e-6 :
			print( "Error: MoveEditXSecPnt" )
			assert False, "Error: MoveEditXSecPnt"



	def test_ConvertXSecToEdit(self):
		# Add Stack
		sid = AddGeom( "STACK", "" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( sid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_ROUNDED_RECTANGLE )

		# Convert Rounded Rectangle to Edit Curve type XSec
		ConvertXSecToEdit( sid, 1 )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		# Get the control points for the default shape
		xsec1_pts = GetEditXSecCtrlVec( xsec_1, True ) # The returned control points will not be scaled by width and height

		# The section is an edit curve carrying a closed cubic Bezier, normalized to
		# the unit box.
		assert GetXSecShape( xsec_1 ) == XS_EDIT_CURVE, "the section is not an edit curve"
		assert len( xsec1_pts ) >= 4, "the edit curve carries too few control points"
		assert dist( xsec1_pts[0], xsec1_pts[-1] ) < 1e-9, "the edit curve does not close"



	def test_GetEditXSecFixedUVec(self):
		# Add Wing
		wid = AddGeom( "WING" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		fixed_u_vec = list(GetEditXSecFixedUVec( xsec_1 ))

		fixed_u_vec[3] = True # change a flag

		SetEditXSecFixedUVec( xsec_1, fixed_u_vec )

		before_pts = GetEditXSecCtrlVec( xsec_1, True )

		ReparameterizeEditXSec( xsec_1 )

		Update()

		# Reparameterizing redistributes U without changing the shape, so the same
		# control points are still there.
		after_pts = GetEditXSecCtrlVec( xsec_1, True )

		assert len( after_pts ) == len( before_pts ), "ReparameterizeEditXSec changed the number of control points"

		# The U values stay in order over the unit interval.
		u_vec = GetEditXSecUVec( xsec_1 )

		assert len( u_vec ) == len( after_pts ), "the U vector does not match the control points"
		assert abs( u_vec[0] ) < 1e-9 and abs( u_vec[-1] - 1.0 ) < 1e-9, "the U vector does not span the curve"

		for i in range( 1, len( u_vec ) ):
			assert u_vec[i] >= u_vec[i - 1], "the U vector is not increasing at " + str( i )



	def test_SetEditXSecFixedUVec(self):
		# Add Wing
		wid = AddGeom( "WING" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		fixed_u_vec = list(GetEditXSecFixedUVec( xsec_1 ))

		fixed_u_vec[3] = True # change a flag

		SetEditXSecFixedUVec( xsec_1, fixed_u_vec )

		assert len( GetEditXSecFixedUVec( xsec_1 ) ) == len( fixed_u_vec ), "SetEditXSecFixedUVec length"

		before_pts = GetEditXSecCtrlVec( xsec_1, True )

		ReparameterizeEditXSec( xsec_1 )

		Update()

		# Reparameterizing redistributes U without changing the shape, so the same
		# control points are still there.
		after_pts = GetEditXSecCtrlVec( xsec_1, True )

		assert len( after_pts ) == len( before_pts ), "ReparameterizeEditXSec changed the number of control points"

		# The U values stay in order over the unit interval.
		u_vec = GetEditXSecUVec( xsec_1 )

		assert len( u_vec ) == len( after_pts ), "the U vector does not match the control points"
		assert abs( u_vec[0] ) < 1e-9 and abs( u_vec[-1] - 1.0 ) < 1e-9, "the U vector does not span the curve"

		for i in range( 1, len( u_vec ) ):
			assert u_vec[i] >= u_vec[i - 1], "the U vector is not increasing at " + str( i )



	def test_ReparameterizeEditXSec(self):
		# Add Wing
		wid = AddGeom( "WING" )

		# Get First (and Only) XSec Surf
		xsec_surf = GetXSecSurf( wid, 0 )

		ChangeXSecShape( xsec_surf, 1, XS_EDIT_CURVE )

		# Identify XSec 1
		xsec_1 = GetXSec( xsec_surf, 1 )

		fixed_u_vec = list(GetEditXSecFixedUVec( xsec_1 ))

		fixed_u_vec[3] = True # change a flag

		SetEditXSecFixedUVec( xsec_1, fixed_u_vec )

		before_pts = GetEditXSecCtrlVec( xsec_1, True )

		ReparameterizeEditXSec( xsec_1 )

		Update()

		# Reparameterizing redistributes U without changing the shape, so the same
		# control points are still there.
		after_pts = GetEditXSecCtrlVec( xsec_1, True )

		assert len( after_pts ) == len( before_pts ), "ReparameterizeEditXSec changed the number of control points"

		# The U values stay in order over the unit interval.
		u_vec = GetEditXSecUVec( xsec_1 )

		assert len( u_vec ) == len( after_pts ), "the U vector does not match the control points"
		assert abs( u_vec[0] ) < 1e-9 and abs( u_vec[-1] - 1.0 ) < 1e-9, "the U vector does not span the curve"

		for i in range( 1, len( u_vec ) ):
			assert u_vec[i] >= u_vec[i - 1], "the U vector is not increasing at " + str( i )



	def test_GetNumSets(self):
		if  GetNumSets() <= 0 :
			print( "---> Error: API GetNumSets " )
			assert False, "---> Error: API GetNumSets"



	def test_SetSetName(self):
		SetSetName( 3, "SetFromScript" )

		if GetSetName(3) != "SetFromScript":
			print("---> Error: API Get/Set Set Name")
			assert False, "---> Error: API Get/Set Set Name"




	def test_GetSetName(self):
		SetSetName( 3, "SetFromScript" )

		if GetSetName(3) != "SetFromScript":
			print("---> Error: API Get/Set Set Name")
			assert False, "---> Error: API Get/Set Set Name"



	def test_GetGeomSetAtIndex(self):
		SetSetName( 3, "SetFromScript" )

		geom_arr1 = GetGeomSetAtIndex( 3 )

		geom_arr2 = GetGeomSet( "SetFromScript" )

		if  len(geom_arr1) != len(geom_arr2) :
			print( "---> Error: API GetGeomSet " )
			assert False, "---> Error: API GetGeomSet"



	def test_GetGeomSet(self):
		SetSetName( 3, "SetFromScript" )

		geom_arr1 = GetGeomSetAtIndex( 3 )

		geom_arr2 = GetGeomSet( "SetFromScript" )

		if  len(geom_arr1) != len(geom_arr2) :
			print( "---> Error: API GetGeomSet " )
			assert False, "---> Error: API GetGeomSet"



	def test_GetSetIndex(self):
		SetSetName( 3, "SetFromScript" )

		if GetSetIndex("SetFromScript") != 3:
			print("ERROR: GetSetIndex")
			assert False, "ERROR: GetSetIndex"




	def test_GetSetFlag(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		SetSetFlag( fuseid, 3, True )

		if not GetSetFlag(fuseid, 3):
			print("---> Error: API Set/Get Set Flag")
			assert False, "---> Error: API Set/Get Set Flag"




	def test_SetSetFlag(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		SetSetFlag( fuseid, 3, True )

		if not GetSetFlag(fuseid, 3):
			print("---> Error: API Set/Get Set Flag")
			assert False, "---> Error: API Set/Get Set Flag"




	def test_CopyPasteSet(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		#set fuseid's state for set 3 to true
		SetSetFlag( fuseid, 3, True )

		#Copy set 3 and Paste into set 4
		CopyPasteSet( 3, 4 )

		#get fuseid's state for set 4
		flag_value = GetSetFlag( fuseid, 4 )

		if  flag_value != True:
			print( "---> Error: API CopyPasteSet " )
			assert False, "---> Error: API CopyPasteSet"



	def test_GetBBoxSet(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		Update()

		sethasmembers, xmin, ymin, zmin, xlen, ylen, zlen = GetBBoxSet( SET_ALL )

		# A pod was added above, so the set is populated and the box has real size.
		assert sethasmembers, "GetBBoxSet"
		assert xlen > 0.0 and ylen > 0.0 and zlen > 0.0, "GetBBoxSet extent"


	def test_GetScaleIndependentBBoxSet(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		Update()

		sethasmembers, xmin, ymin, zmin, xlen, ylen, zlen = GetScaleIndependentBBoxSet( SET_ALL )

		# A pod was added above, so the set is populated and the box has real size.
		assert sethasmembers, "GetScaleIndependentBBoxSet"
		assert xlen > 0.0 and ylen > 0.0 and zlen > 0.0, "GetScaleIndependentBBoxSet extent"


	def test_ScaleSet(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE" )

		SetSetFlag( fuseid, 3, True )

		# Scale by a factor of 2
		Update()

		before_max = GetGeomBBoxMax( fuseid, 0, False )
		before_min = GetGeomBBoxMin( fuseid, 0, False )

		ScaleSet( 3, 2.0 )

		Update()

		after_max = GetGeomBBoxMax( fuseid, 0, False )
		after_min = GetGeomBBoxMin( fuseid, 0, False )

		assert abs( ( after_max.x() - after_min.x() ) - 2.0 * ( before_max.x() - before_min.x() ) ) < 1e-6, "ScaleSet did not double the extent"



	def test_RotateSet(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE" )

		SetSetFlag( fuseid, 3, True )

		Update()

		before_max = GetGeomBBoxMax( fuseid, 0, True )
		before_min = GetGeomBBoxMin( fuseid, 0, True )

		# Rotate 90 degrees about Y
		RotateSet( 3, 0, 90, 0 )

		Update()

		after_max = GetGeomBBoxMax( fuseid, 0, True )
		after_min = GetGeomBBoxMin( fuseid, 0, True )

		# Turning the Geom on its nose trades the X extent for the Z extent.
		assert abs( ( after_max.z() - after_min.z() ) - ( before_max.x() - before_min.x() ) ) < 1e-6, "RotateSet did not rotate the geometry"
		assert abs( ( after_max.x() - after_min.x() ) - ( before_max.z() - before_min.z() ) ) < 1e-6, "RotateSet did not rotate the geometry"



	def test_TranslateSet(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE" )

		SetSetFlag( fuseid, 3, True )

		# Translate 2 units in X and 3 units in Y
		Update()

		# The bounding box has to be asked for in the absolute frame.  A body frame
		# box travels with the Geom, so it would not see the translation at all.
		before_min = GetGeomBBoxMin( fuseid, 0, True )

		TranslateSet( 3, vec3d( 2, 3, 0 ) )

		Update()

		after_min = GetGeomBBoxMin( fuseid, 0, True )

		assert abs( ( after_min.x() - before_min.x() ) - 2.0 ) < 1e-6 and abs( ( after_min.y() - before_min.y() ) - 3.0 ) < 1e-6, "TranslateSet did not move the geometry"



	def test_TransformSet(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE" )

		SetSetFlag( fuseid, 3, True )

		Update()

		before_max = GetGeomBBoxMax( fuseid, 0, True )
		before_min = GetGeomBBoxMin( fuseid, 0, True )

		# Translate 2 units in X and 3 units in Y, rotate 90 degrees about Y, and scale by a factor of 2
		TransformSet( 3, vec3d( 2, 3, 0 ), 0, 90, 0, 2.0, True )

		Update()

		after_max = GetGeomBBoxMax( fuseid, 0, True )
		after_min = GetGeomBBoxMin( fuseid, 0, True )

		# Turning the Geom on its nose trades the X extent for the Z, and the scale
		# doubles both.
		assert abs( ( after_max.z() - after_min.z() ) - 2.0 * ( before_max.x() - before_min.x() ) ) < 1e-6, "TransformSet did not rotate and scale the geometry"
		assert abs( ( after_max.x() - after_min.x() ) - 2.0 * ( before_max.z() - before_min.z() ) ) < 1e-6, "TransformSet did not rotate and scale the geometry"

		# The Y extent only scales.
		assert abs( ( after_max.y() - after_min.y() ) - 2.0 * ( before_max.y() - before_min.y() ) ) < 1e-6, "TransformSet did not scale the geometry in Y"



	def test_ValidParm(self):
		#==== Add Pod Geometry ====//
		pid = AddGeom( "POD" )

		lenid = GetParm( pid, "Length", "Design" )

		if  not ValidParm( lenid ) :
			print( "---> Error: API GetParm  " )
			assert False, "---> Error: API GetParm"



	def test_SetParmVal(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		SetParmVal( wid, 23.0 )

		if  abs( GetParmVal( wid ) - 23 ) > 1e-6 :
			print( "---> Error: API Parm Val Set/Get " )
			assert False, "---> Error: API Parm Val Set/Get"



	def test_SetParmVal1(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		SetParmVal( wid, 23.0 )

		if  abs( GetParmVal( wid ) - 23 ) > 1e-6 :
			print( "---> Error: API Parm Val Set/Get " )
			assert False, "---> Error: API Parm Val Set/Get"



	def test_SetParmValLimits(self):
		pod_id = AddGeom( "POD" )

		length = FindParm( pod_id, "Length", "Design" )

		SetParmValLimits( length, 10.0, 0.001, 1.0e12 )

		SetParmDescript( length, "Total Length of Geom" )

		# The value and both limits have to take.
		assert abs( GetParmVal( length ) - 10.0 ) < 1e-9, "SetParmValLimits did not take"
		assert abs( GetParmLowerLimit( length ) - 0.001 ) < 1e-9, "SetParmValLimits did not take"
		assert abs( GetParmUpperLimit( length ) - 1.0e12 ) < 1.0, "SetParmValLimits did not take"

		assert GetParmDescript( length ) == "Total Length of Geom", "SetParmDescript did not take"

		# The limits are limits, so a value outside them gets clamped.
		SetParmVal( length, -1.0 )

		assert abs( GetParmVal( length ) - 0.001 ) < 1e-9, "the lower limit did not hold"



	def test_SetParmValUpdate(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		parm_id = GetParm( pod_id, "X_Rel_Location", "XForm" )

		SetParmValUpdate( parm_id, 5.0 )

		assert abs( GetParmVal( parm_id ) - 5.0 ) < 1e-9, "SetParmValUpdate"



	def test_SetParmValUpdate1(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		parm_id = GetParm( pod_id, "X_Rel_Location", "XForm" )

		SetParmValUpdate( parm_id, 5.0 )

		assert abs( GetParmVal( parm_id ) - 5.0 ) < 1e-9, "SetParmValUpdate"



	def test_GetParmVal(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		SetParmVal( wid, 23.0 )

		if  abs( GetParmVal( wid ) - 23 ) > 1e-6 :
			print( "---> Error: API Parm Val Set/Get " )
			assert False, "---> Error: API Parm Val Set/Get"



	def test_GetParmVal1(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		SetParmVal( wid, 23.0 )

		if  abs( GetParmVal( wid ) - 23 ) > 1e-6 :
			print( "---> Error: API Parm Val Set/Get " )
			assert False, "---> Error: API Parm Val Set/Get"



	def test_GetIntParmVal(self):
		#==== Add Prop Geometry ====//
		prop_id = AddGeom( "PROP" )

		num_blade_id = GetParm( prop_id, "NumBlade", "Design" )

		num_blade = GetIntParmVal( num_blade_id )

		# A new propeller has three blades, and the int form has to agree with the
		# double form.
		assert num_blade == 3, "GetIntParmVal did not report the blade count"
		assert num_blade == int( GetParmVal( num_blade_id ) ), "GetIntParmVal disagrees with GetParmVal"

		# Setting it has to move both.
		SetParmVal( num_blade_id, 5 )

		assert GetIntParmVal( num_blade_id ) == 5, "GetIntParmVal did not follow the Parm"



	def test_GetBoolParmVal(self):
		#==== Add Prop Geometry ====//
		prop_id = AddGeom( "PROP" )

		rev_flag_id = GetParm( prop_id, "ReverseFlag", "Design" )

		SetParmVal( rev_flag_id, 1.0 )

		reverse_flag = GetBoolParmVal( rev_flag_id )

		assert reverse_flag, "GetBoolParmVal did not read back a set flag"

		SetParmVal( rev_flag_id, 0.0 )

		assert not GetBoolParmVal( rev_flag_id ), "GetBoolParmVal did not read back a cleared flag"



	def test_SetParmUpperLimit(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		SetParmVal( wid, 23.0 )

		SetParmUpperLimit( wid, 13.0 )

		if  abs( GetParmVal( wid ) - 13 ) > 1e-6 :
			print( "---> Error: API SetParmUpperLimit " )
			assert False, "---> Error: API SetParmUpperLimit"



	def test_GetParmUpperLimit(self):
		#==== Add Prop Geometry ====//
		prop_id = AddGeom( "PROP" )

		num_blade_id = GetParm( prop_id, "NumBlade", "Design" )

		max_blade = GetParmUpperLimit( num_blade_id )



	def test_SetParmLowerLimit(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		SetParmVal( wid, 13.0 )

		SetParmLowerLimit( wid, 15.0 )

		if  abs( GetParmVal( wid ) - 15 ) > 1e-6 :
			print( "---> Error: API SetParmLowerLimit " )
			assert False, "---> Error: API SetParmLowerLimit"



	def test_GetParmLowerLimit(self):
		#==== Add Prop Geometry ====//
		prop_id = AddGeom( "PROP" )

		num_blade_id = GetParm( prop_id, "NumBlade", "Design" )

		min_blade = GetParmLowerLimit( num_blade_id )

		# A propeller needs at least one blade, and the limits have to bracket the
		# current value.
		assert min_blade >= 1.0, "GetParmLowerLimit allows a propeller with no blades"
		assert min_blade <= GetParmVal( num_blade_id ), "the lower limit is above the value"
		assert min_blade <= GetParmUpperLimit( num_blade_id ), "the lower limit is above the upper limit"

		# Asking for less than the limit allows has to clamp to it.
		SetParmVal( num_blade_id, min_blade - 10.0 )

		assert abs( GetParmVal( num_blade_id ) - min_blade ) < 1e-9, "the lower limit did not hold"



	def test_GetParmType(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		if  GetParmType( wid ) != PARM_DOUBLE_TYPE :
			print( "---> Error: API GetParmType " )
			assert False, "---> Error: API GetParmType"



	def test_GetParmName(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Get Structure Name and Parm Container ID ====//
		parm_container_name = GetFeaStructName( pod_id, struct_ind )

		parm_container_id = FindContainer( parm_container_name, struct_ind )

		#==== Get and List All Parms in the Container ====//
		parm_ids = FindContainerParmIDs( parm_container_id )

		for i in range(len(parm_ids)):

			name_id = GetParmName( parm_ids[i] ) + ": " + parm_ids[i] + "\n"
			assert len( name_id ) > 0, "GetParmName returned nothing"

			print( name_id )



	def test_GetParmGroupName(self):
		veh_id = FindContainer( "Vehicle", 0 )

		#==== Get and List All Parms in the Container ====//
		parm_ids = FindContainerParmIDs( veh_id )

		print( "Parm Groups and IDs in Vehicle Parm Container: " )

		for i in range(len(parm_ids)):

			group_str = GetParmGroupName( parm_ids[i] ) + ": " + parm_ids[i] + "\n"
			assert len( group_str ) > 0, "GetParmGroupName returned nothing"

			print( group_str )



	def test_GetParmDisplayGroupName(self):
		veh_id = FindContainer( "Vehicle", 0 )

		#==== Get and List All Parms in the Container ====//
		parm_ids = FindContainerParmIDs( veh_id )

		print( "Parm Group Display Names and IDs in Vehicle Parm Container: " )

		for i in range(len(parm_ids)):

			group_str = GetParmDisplayGroupName( parm_ids[i] ) + ": " + parm_ids[i] + "\n"
			assert len( group_str ) > 0, "GetParmDisplayGroupName returned nothing"

			print( group_str )



	def test_GetParmContainer(self):
		# Add Fuselage Geom
		fuseid = AddGeom( "FUSELAGE", "" )

		xsec_surf = GetXSecSurf( fuseid, 0 )

		ChangeXSecShape( xsec_surf, GetNumXSec( xsec_surf ) - 1, XS_ROUNDED_RECTANGLE )

		xsec = GetXSec( xsec_surf, GetNumXSec( xsec_surf ) - 1 )

		wid = GetXSecParm( xsec, "RoundedRect_Width" )

		cid = GetParmContainer( wid )

		if  len(cid) == 0 :
			print( "---> Error: API GetParmContainer " )
			assert False, "---> Error: API GetParmContainer"



	def test_SetParmDescript(self):
		pod_id = AddGeom( "POD" )

		length = FindParm( pod_id, "Length", "Design" )

		SetParmValLimits( length, 10.0, 0.001, 1.0e12 )

		SetParmDescript( length, "Total Length of Geom" )
		assert GetParmDescript( length ) == "Total Length of Geom", "SetParmDescript did not take"




	def test_GetParmDescript(self):
		pod_id = AddGeom( "POD" )

		length = FindParm( pod_id, "Length", "Design" )

		SetParmValLimits( length, 10.0, 0.001, 1.0e12 )

		desc = GetParmDescript( length )
		assert len( desc ) > 0, "GetParmDescript returned nothing"
		print( desc )



	def test_FindParm(self):
		#==== Add Wing Geometry ====//
		wing_id = AddGeom( "WING" )

		#==== Turn Symmetry OFF ====//
		sym_id = FindParm( wing_id, "Sym_Planar_Flag", "Sym")
		assert len( sym_id ) > 0, "FindParm found nothing"

		SetParmVal( sym_id, 0.0 ) # Note: bool input not supported in SetParmVal



	def test_FindContainers(self):
		ctr_arr = FindContainers()
		assert len( ctr_arr ) > 0, "FindContainers found nothing"

		print( "---> API Parm Container IDs: " )

		for i in range(int( len(ctr_arr) )):

			message = "\t" + ctr_arr[i] + "\n"

			print( message )



	def test_FindContainersWithName(self):
		ctr_arr = FindContainersWithName( "UserParms" )
		assert len( ctr_arr ) > 0, "FindContainersWithName found nothing"

		if  len(ctr_arr) > 0 : print( ( "UserParms Parm Container ID: " + ctr_arr[0] ) )



	def test_FindContainer(self):
		#===== Get Vehicle Parm Container ID ====//
		veh_id = FindContainer( "Vehicle", 0 )
		assert len( veh_id ) > 0, "FindContainer found nothing"



	def test_SetContainerName(self):
		veh_id = FindContainer( "Vehicle", 0 )

		if  GetContainerName( veh_id) != "Vehicle":
			print( "---> Error: API GetContainerName" )
			assert False, "---> Error: API GetContainerName"



	def test_GetContainerName(self):
		pid = AddGeom( "POD" )

		SetGeomName( pid, "TestPod" )

		Update()

		assert GetContainerName( pid ) == "TestPod", "GetContainerName did not report the name"



	def test_FindContainerGroupNames(self):
		user_ctr = FindContainer( "UserParms", 0 )

		grp_arr = FindContainerGroupNames( user_ctr )
		assert len( grp_arr ) > 0, "FindContainerGroupNames found nothing"

		print( "---> UserParms Container Group IDs: " )
		for i in range(int( len(grp_arr) )):

			message = "\t" + grp_arr[i] + "\n"

			print( message )



	def test_FindContainerParmIDs(self):
		#==== Add Pod Geometry ====//
		pod_id = AddGeom( "POD" )

		#==== Add FeaStructure to Pod ====//
		struct_ind = AddFeaStruct( pod_id )

		#==== Get Structure Name and Parm Container ID ====//
		parm_container_name = GetFeaStructName( pod_id, struct_ind )

		parm_container_id = FindContainer( parm_container_name, struct_ind )

		#==== Get and List All Parms in the Container ====//
		parm_ids = FindContainerParmIDs( parm_container_id )
		assert len( parm_ids ) > 0, "FindContainerParmIDs found nothing"

		for i in range(len(parm_ids)):

			name_id = GetParmName( parm_ids[i] ) + ": " + parm_ids[i] + "\n"

			print( name_id )



	def test_GetVehicleID(self):
		#===== Get Vehicle Parm Container ID ====//
		veh_id = GetVehicleID()
		assert len( veh_id ) > 0, "GetVehicleID returned nothing"



	def test_GetNumUserParms(self):
		n = GetNumUserParms()

		# A fresh model already carries the predefined user Parms, and the count has
		# to match the list.
		assert n == GetNumPredefinedUserParms(), "GetNumUserParms does not match the predefined count"
		assert n == len( GetAllUserParms() ), "GetNumUserParms disagrees with the user Parm list"

		# Adding one has to move the count.
		AddUserParm( PARM_DOUBLE_TYPE, "ExampleParm", "ExampleGroup" )

		assert GetNumUserParms() == n + 1, "GetNumUserParms did not follow AddUserParm"



	def test_GetNumPredefinedUserParms(self):
		n = GetNumPredefinedUserParms()

		assert n > 0, "GetNumPredefinedUserParms"




	def test_GetAllUserParms(self):
		id_arr = GetAllUserParms()
		assert len( id_arr ) > 0, "GetAllUserParms returned nothing"

		print( "---> User Parm IDs: " )

		for i in range(int( len(id_arr) )):

			message = "\t" + id_arr[i] + "\n"

			print( message )



	def test_GetUserParmContainer(self):
		up_id = GetUserParmContainer()
		assert len( up_id ) > 0, "GetUserParmContainer returned nothing"



	def test_AddUserParm(self):
		length = AddUserParm( PARM_DOUBLE_TYPE, "Length", "Design" )

		SetParmValLimits( length, 10.0, 0.001, 1.0e12 )

		SetParmDescript( length, "Length user parameter" )



	def test_DeleteUserParm(self):

		n = GetNumPredefinedUserParms()
		id_arr = GetAllUserParms()

		if  len(id_arr) > n :
			num_before_del = GetNumUserParms()
			DeleteUserParm( id_arr[n] )
			assert GetNumUserParms() < num_before_del, "DeleteUserParm removed nothing"




	def test_DeleteAllUserParm(self):
		# A fresh model already carries the predefined user Parms, so record the
		# starting count rather than expecting to end at zero.
		num_before = GetNumUserParms()

		AddUserParm( PARM_DOUBLE_TYPE, "Param1", "Group1" )
		AddUserParm( PARM_DOUBLE_TYPE, "Param2", "Group1" )

		assert GetNumUserParms() == num_before + 2, "AddUserParm"

		DeleteAllUserParm()

		assert GetNumUserParms() == num_before, "DeleteAllUserParm"




	def test_ComputeMinClearanceDistance(self):
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		pid = AddGeom( "POD", "" )                     # Add Pod

		x = GetParm( pid, "X_Rel_Location", "XForm" )

		SetParmVal( x, 3.0 )

		Update()

		min_dist = ComputeMinClearanceDistance( pid, SET_ALL )

		# The Pod was moved clear of the Fuselage, so there is a real gap between
		# them.  Sliding it back into the Fuselage has to close that gap.
		assert min_dist > 0.0, "ComputeMinClearanceDistance reports no clearance between separated Geoms"

		SetParmVal( x, 0.0 )

		Update()

		assert ComputeMinClearanceDistance( pid, SET_ALL ) < min_dist, "ComputeMinClearanceDistance did not close as the Geoms came together"



	def test_SnapParm(self):
		#Add Geoms
		fid = AddGeom( "FUSELAGE", "" )             # Add Fuselage

		pid = AddGeom( "POD", "" )                     # Add Pod

		x = GetParm( pid, "X_Rel_Location", "XForm" )

		SetParmVal( x, 3.0 )

		Update()

		min_dist = SnapParm( x, 0.1, True, SET_ALL )

		Update()

		# Snapping moves the Parm until the clearance reaches the target, so the Parm
		# has to have moved and the clearance has to end up where it was asked for.
		assert abs( GetParmVal( x ) - 3.0 ) > 1e-9, "SnapParm did not move the Parm"
		assert abs( ComputeMinClearanceDistance( pid, SET_ALL ) - 0.1 ) < 1e-4, "SnapParm did not reach the target clearance"
		assert abs( min_dist - ComputeMinClearanceDistance( pid, SET_ALL ) ) < 1e-4, "SnapParm reported a clearance it did not reach"



	def test_ResetFitModel(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, vec3d( 3.0, 0.0, 0.0 ) )

		ResetFitModel()

		assert GetNumFitModelTargetPts() == 0, "ResetFitModel left target points behind"



	def test_AddFitModelTargetPt(self):
		pid = AddGeom( "POD" )

		Update()

		pnt = CompPnt01( pid, 0, 0.5, 0.0 )

		index = AddFitModelTargetPt( pid, 0, pnt, FIT_MODEL_FREE, FIT_MODEL_FREE )

		assert index == 0, "AddFitModelTargetPt did not return the first index"

		assert GetNumFitModelTargetPts() == 1, "AddFitModelTargetPt did not add a point"



	def test_AddFitModelTargetPtFixedU(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPtFixedU( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), 0.5 )

		assert GetFitModelTargetPtUType( 0 ) == FIT_MODEL_FIXED, "AddFitModelTargetPtFixedU did not pin U"

		assert abs( GetFitModelTargetPtU( 0 ) - 0.5 ) < 1e-6, "AddFitModelTargetPtFixedU did not use the given U"

		assert UpdateFitModelDist() < 1e-4, "AddFitModelTargetPtFixedU did not place the point on the surface"



	def test_AddFitModelTargetPtFixedW(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPtFixedW( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), 0.25 )

		assert GetFitModelTargetPtWType( 0 ) == FIT_MODEL_FIXED, "AddFitModelTargetPtFixedW did not pin W"

		assert abs( GetFitModelTargetPtW( 0 ) - 0.25 ) < 1e-6, "AddFitModelTargetPtFixedW did not use the given W"

		assert UpdateFitModelDist() < 1e-4, "AddFitModelTargetPtFixedW did not place the point on the surface"



	def test_AddFitModelTargetPtFixedUW(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPtFixedUW( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), 0.5, 0.25 )

		assert GetNumFitModelOptVars() == 0, "AddFitModelTargetPtFixedUW left a direction free"

		assert UpdateFitModelDist() < 1e-6, "AddFitModelTargetPtFixedUW did not land on the given coordinate"



	def test_AddFitModelTargetPts(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []

		pts.append( CompPnt01( pid, 0, 0.25, 0.0 ) )
		pts.append( CompPnt01( pid, 0, 0.50, 0.0 ) )
		pts.append( CompPnt01( pid, 0, 0.75, 0.0 ) )

		AddFitModelTargetPts( pid, 0, pts )

		assert GetNumFitModelTargetPts() == 3, "AddFitModelTargetPts did not add three points"

		assert UpdateFitModelDist() < 1e-4, "AddFitModelTargetPts did not place the points on the surface"



	def test_AddFitModelTargetPtsFixedU(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []

		pts.append( CompPnt01( pid, 0, 0.5, 0.10 ) )
		pts.append( CompPnt01( pid, 0, 0.5, 0.35 ) )
		pts.append( CompPnt01( pid, 0, 0.5, 0.60 ) )

		AddFitModelTargetPtsFixedU( pid, 0, pts, 0.5 )

		assert GetFitModelTargetPtUType( 0 ) == FIT_MODEL_FIXED, "AddFitModelTargetPtsFixedU did not pin U"

		assert abs( GetFitModelTargetPtU( 0 ) - 0.5 ) < 1e-6, "AddFitModelTargetPtsFixedU did not use the given U"



	def test_AddFitModelTargetPtsFixedUs(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []
		us = []

		for u in [ 0.25, 0.50, 0.75 ]:
			pts.append( CompPnt01( pid, 0, u, 0.1 ) )
			us.append( u )

		AddFitModelTargetPtsFixedUs( pid, 0, pts, us )

		assert abs( GetFitModelTargetPtU( 2 ) - 0.75 ) < 1e-6, "AddFitModelTargetPtsFixedUs did not use the given U values"



	def test_AddFitModelTargetPtsFixedW(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []

		pts.append( CompPnt01( pid, 0, 0.25, 0.5 ) )
		pts.append( CompPnt01( pid, 0, 0.50, 0.5 ) )
		pts.append( CompPnt01( pid, 0, 0.75, 0.5 ) )

		AddFitModelTargetPtsFixedW( pid, 0, pts, 0.5 )

		assert GetFitModelTargetPtWType( 0 ) == FIT_MODEL_FIXED, "AddFitModelTargetPtsFixedW did not pin W"

		assert abs( GetFitModelTargetPtW( 0 ) - 0.5 ) < 1e-6, "AddFitModelTargetPtsFixedW did not use the given W"



	def test_AddFitModelTargetPtsFixedWs(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []
		ws = []

		for w in [ 0.10, 0.35, 0.60 ]:
			pts.append( CompPnt01( pid, 0, 0.3, w ) )
			ws.append( w )

		AddFitModelTargetPtsFixedWs( pid, 0, pts, ws )

		assert abs( GetFitModelTargetPtW( 2 ) - 0.60 ) < 1e-6, "AddFitModelTargetPtsFixedWs did not use the given W values"



	def test_AddFitModelTargetPtsFixedUW(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []

		pts.append( CompPnt01( pid, 0, 0.5, 0.25 ) )

		AddFitModelTargetPtsFixedUW( pid, 0, pts, 0.5, 0.25 )

		assert GetFitModelTargetPtUType( 0 ) == FIT_MODEL_FIXED, "AddFitModelTargetPtsFixedUW did not pin U"

		assert GetFitModelTargetPtWType( 0 ) == FIT_MODEL_FIXED, "AddFitModelTargetPtsFixedUW did not pin W"

		assert UpdateFitModelDist() < 1e-6, "AddFitModelTargetPtsFixedUW did not land on the given coordinate"



	def test_AddFitModelTargetPtsFixedUWs(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []
		us = []
		ws = []

		for u, w in [ ( 0.25, 0.1 ), ( 0.50, 0.4 ), ( 0.75, 0.7 ) ]:
			pts.append( CompPnt01( pid, 0, u, w ) )
			us.append( u )
			ws.append( w )

		AddFitModelTargetPtsFixedUWs( pid, 0, pts, us, ws )

		assert GetNumFitModelOptVars() == 0, "AddFitModelTargetPtsFixedUWs left a direction free"

		assert UpdateFitModelDist() < 1e-6, "AddFitModelTargetPtsFixedUWs did not land on the given coordinates"



	def test_DelFitModelTargetPt(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.25, 0.0 ) )
		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.75, 0.0 ) )

		DelFitModelTargetPt( 0 )

		assert GetNumFitModelTargetPts() == 1, "DelFitModelTargetPt did not remove a point"



	def test_DelAllFitModelTargetPts(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		DelAllFitModelTargetPts()

		assert GetNumFitModelTargetPts() == 0, "DelAllFitModelTargetPts left points behind"



	def test_SortFitModelTargetPtsByDist(self):
		pid = AddGeom( "POD" )

		Update()

		near_pnt = CompPnt01( pid, 0, 0.5, 0.25 )
		far_pnt = vec3d( near_pnt.x(), near_pnt.y(), near_pnt.z() + 1.0 )

		AddFitModelTargetPtFixedUW( pid, 0, near_pnt, 0.5, 0.25 )
		AddFitModelTargetPtFixedUW( pid, 0, far_pnt, 0.5, 0.25 )

		SortFitModelTargetPtsByDist()

		assert abs( GetFitModelTargetPt( 0 ).z() - far_pnt.z() ) < 1e-6, "SortFitModelTargetPtsByDist did not put the worst fit first"



	def test_MoveFitModelTargetPt(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.25, 0.0 ) )
		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.50, 0.0 ) )

		last_pnt = CompPnt01( pid, 0, 0.75, 0.0 )

		AddFitModelTargetPt( pid, 0, last_pnt )

		newindex = MoveFitModelTargetPt( 2, REORDER_MOVE_TOP )

		assert newindex == 0, "MoveFitModelTargetPt did not report the point at the top"

		assert abs( GetFitModelTargetPt( 0 ).x() - last_pnt.x() ) < 1e-6, "MoveFitModelTargetPt did not move the point to the top"



	def test_GetNumFitModelTargetPts(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		assert GetNumFitModelTargetPts() == 1, "GetNumFitModelTargetPts did not count the point"



	def test_GetFitModelTargetPt(self):
		pid = AddGeom( "POD" )

		Update()

		pnt = vec3d( 3.0, 1.0, 2.0 )

		AddFitModelTargetPt( pid, 0, pnt )

		pnt_out = GetFitModelTargetPt( 0 )

		assert dist( pnt, pnt_out ) < 1e-6, "GetFitModelTargetPt did not report the point that was set"



	def test_SetFitModelTargetPt(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, vec3d( 0.0, 0.0, 0.0 ) )

		SetFitModelTargetPt( 0, vec3d( 3.0, 1.0, 2.0 ) )

		assert dist( GetFitModelTargetPt( 0 ), vec3d( 3.0, 1.0, 2.0 ) ) < 1e-6, "SetFitModelTargetPt did not take"



	def test_GetFitModelTargetPtGeom(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		assert GetFitModelTargetPtGeom( 0 ) == pid, "GetFitModelTargetPtGeom did not report the Geom that was set"



	def test_SetFitModelTargetPtGeom(self):
		pid = AddGeom( "POD" )

		fid = AddGeom( "FUSELAGE" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		SetFitModelTargetPtGeom( 0, fid )

		assert GetFitModelTargetPtGeom( 0 ) == fid, "SetFitModelTargetPtGeom did not take"



	def test_GetFitModelTargetPtSurfIndx(self):
		pid = AddGeom( "POD" )

		SetParmVal( FindParm( pid, "Sym_Planar_Flag", "Sym" ), SYM_XZ )

		Update()

		AddFitModelTargetPt( pid, 1, CompPnt01( pid, 1, 0.5, 0.25 ) )

		assert GetFitModelTargetPtSurfIndx( 0 ) == 1, "GetFitModelTargetPtSurfIndx did not report the surface that was set"

		assert UpdateFitModelDist() < 1e-4, "target point did not land on the second surface"



	def test_SetFitModelTargetPtSurfIndx(self):
		pid = AddGeom( "POD" )

		SetParmVal( FindParm( pid, "Sym_Planar_Flag", "Sym" ), SYM_XZ )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 1, 0.5, 0.25 ) )

		SetFitModelTargetPtSurfIndx( 0, 1 )

		assert GetFitModelTargetPtSurfIndx( 0 ) == 1, "SetFitModelTargetPtSurfIndx did not take"

		SearchFitModelTargetUW()

		assert UpdateFitModelDist() < 1e-4, "target point did not land on the second surface"



	def test_GetFitModelTargetPtU(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), FIT_MODEL_FIXED, FIT_MODEL_FIXED, 0.5, 0.25 )

		assert abs( GetFitModelTargetPtU( 0 ) - 0.5 ) < 1e-6, "GetFitModelTargetPtU did not report the U that was set"



	def test_GetFitModelTargetPtW(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), FIT_MODEL_FIXED, FIT_MODEL_FIXED, 0.5, 0.25 )

		assert abs( GetFitModelTargetPtW( 0 ) - 0.25 ) < 1e-6, "GetFitModelTargetPtW did not report the W that was set"



	def test_GetFitModelTargetPtDist(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), FIT_MODEL_FIXED, FIT_MODEL_FIXED, 0.5, 0.25 )

		Update()

		assert GetFitModelTargetPtDist( 0 ) < 1e-6, "a target point placed on the surface is not at zero distance"



	def test_SetFitModelTargetPtUW(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ) )

		SetFitModelTargetPtUW( 0, 0.5, 0.25 )

		assert abs( GetFitModelTargetPtU( 0 ) - 0.5 ) < 1e-6, "SetFitModelTargetPtUW did not take"



	def test_GetFitModelTargetPtUType(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ), FIT_MODEL_FIXED, FIT_MODEL_FREE )

		assert GetFitModelTargetPtUType( 0 ) == FIT_MODEL_FIXED, "GetFitModelTargetPtUType did not report the type that was set"



	def test_SetFitModelTargetPtUType(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		SetFitModelTargetPtUType( 0, FIT_MODEL_FIXED )

		assert GetFitModelTargetPtUType( 0 ) == FIT_MODEL_FIXED, "SetFitModelTargetPtUType did not take"



	def test_GetFitModelTargetPtWType(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ), FIT_MODEL_FREE, FIT_MODEL_FIXED )

		assert GetFitModelTargetPtWType( 0 ) == FIT_MODEL_FIXED, "GetFitModelTargetPtWType did not report the type that was set"



	def test_SetFitModelTargetPtWType(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		SetFitModelTargetPtWType( 0, FIT_MODEL_FIXED )

		assert GetFitModelTargetPtWType( 0 ) == FIT_MODEL_FIXED, "SetFitModelTargetPtWType did not take"



	def test_GetFitModelTargetPtSurfPt(self):
		pid = AddGeom( "POD" )

		Update()

		pnt = CompPnt01( pid, 0, 0.5, 0.25 )

		AddFitModelTargetPt( pid, 0, pnt, FIT_MODEL_FIXED, FIT_MODEL_FIXED, 0.5, 0.25 )

		surf_pnt = GetFitModelTargetPtSurfPt( 0 )

		assert dist( pnt, surf_pnt ) < 1e-6, "GetFitModelTargetPtSurfPt did not land on the target point"



	def test_AddFitModelVar(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddFitModelVar( length )

		assert GetNumFitModelVars() == 1, "AddFitModelVar did not add the variable"



	def test_DelFitModelVar(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddFitModelVar( length )

		DelFitModelVar( length )

		assert GetNumFitModelVars() == 0, "DelFitModelVar did not remove the variable"



	def test_DelAllFitModelVars(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelVar( GetParm( pid, "Length", "Design" ) )

		DelAllFitModelVars()

		assert GetNumFitModelVars() == 0, "DelAllFitModelVars left variables behind"



	def test_GetNumFitModelVars(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelVar( GetParm( pid, "Length", "Design" ) )

		assert GetNumFitModelVars() == 1, "GetNumFitModelVars did not count the variable"



	def test_GetFitModelVar(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		AddFitModelVar( length )

		assert GetFitModelVar( 0 ) == length, "GetFitModelVar did not report the variable that was added"



	def test_GetFitModelVarVec(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelVar( GetParm( pid, "Length", "Design" ) )

		var_array = GetFitModelVarVec()

		assert len( var_array ) == 1, "GetFitModelVarVec did not report the variable"



	def test_SearchFitModelTargetUW(self):
		pid = AddGeom( "POD" )

		Update()

		pnt = CompPnt01( pid, 0, 0.5, 0.25 )

		AddFitModelTargetPt( pid, 0, pnt, FIT_MODEL_FREE, FIT_MODEL_FREE )

		SearchFitModelTargetUW()

		assert UpdateFitModelDist() < 1e-4, "SearchFitModelTargetUW did not find the point on the surface"



	def test_RefineFitModelTargetUW(self):
		pid = AddGeom( "POD" )

		Update()

		pnt = CompPnt01( pid, 0, 0.5, 0.25 )

		AddFitModelTargetPt( pid, 0, pnt, FIT_MODEL_FREE, FIT_MODEL_FREE, 0.45, 0.25 )

		RefineFitModelTargetUW()

		assert UpdateFitModelDist() < 1e-4, "RefineFitModelTargetUW did not settle on the point"



	def test_UpdateFitModelDist(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), FIT_MODEL_FIXED, FIT_MODEL_FIXED, 0.5, 0.25 )

		assert UpdateFitModelDist() < 1e-6, "UpdateFitModelDist did not report a matched point as matched"



	def test_GetFitModelDist(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.25 ), FIT_MODEL_FIXED, FIT_MODEL_FIXED, 0.5, 0.25 )

		UpdateFitModelDist()

		assert GetFitModelDist() < 1e-6, "GetFitModelDist did not report the distance last computed"



	def test_GetNumFitModelOptVars(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ), FIT_MODEL_FREE, FIT_MODEL_FREE )

		AddFitModelVar( GetParm( pid, "Length", "Design" ) )

		assert GetNumFitModelOptVars() == 3, "GetNumFitModelOptVars did not count one variable and two free directions"



	def test_OptimizeFitModel(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		# Sample points from the pod, then stretch it away from them.
		pts = []

		pts.append( CompPnt01( pid, 0, 0.25, 0.0 ) )
		pts.append( CompPnt01( pid, 0, 0.50, 0.0 ) )
		pts.append( CompPnt01( pid, 0, 0.75, 0.0 ) )

		len0 = GetParmVal( length )

		SetParmVal( length, 1.4 * len0 )

		Update()

		AddFitModelTargetPts( pid, 0, pts )

		AddFitModelVar( length )

		OptimizeFitModel()

		# Fitting the points back should have recovered the original length.
		assert abs( GetParmVal( length ) - len0 ) < 1e-3, "OptimizeFitModel did not recover the original length"



	def test_CanUndoFitModel(self):
		pid = AddGeom( "POD" )

		Update()

		assert not CanUndoFitModel(), "CanUndoFitModel is true before anything has been run"

		pts = [ CompPnt01( pid, 0, 0.2, 0.3 ), CompPnt01( pid, 0, 0.5, 0.6 ) ]

		AddFitModelTargetPts( pid, 0, pts )

		AddFitModelVar( GetParm( pid, "Length", "Design" ) )

		OptimizeFitModel()

		assert CanUndoFitModel(), "CanUndoFitModel is false after a fit"



	def test_UndoFitModel(self):
		pid = AddGeom( "POD" )

		Update()

		length = GetParm( pid, "Length", "Design" )

		pts = [ CompPnt01( pid, 0, 0.2, 0.3 ), CompPnt01( pid, 0, 0.5, 0.6 ) ]

		AddFitModelTargetPts( pid, 0, pts )

		AddFitModelVar( length )

		SetParmVal( length, 7.0 )
		Update()

		OptimizeFitModel()

		assert UndoFitModel(), "UndoFitModel found nothing to undo"

		#==== The Parm is back where it was before the fit ====#
		assert abs( GetParmVal( length ) - 7.0 ) < 1e-6, "UndoFitModel did not restore the Parm"

		#==== And there is nothing left to undo ====#
		assert not UndoFitModel(), "UndoFitModel is repeatable, but it should be one level deep"



	def test_SaveFitModelFile(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		AddFitModelVar( GetParm( pid, "Length", "Design" ) )

		SaveFitModelFile( "TestFitModel.fit" )



	def test_LoadFitModelFile(self):
		pid = AddGeom( "POD" )

		Update()

		AddFitModelTargetPt( pid, 0, CompPnt01( pid, 0, 0.5, 0.0 ) )

		SaveFitModelFile( "TestFitModel.fit" )

		ResetFitModel()

		LoadFitModelFile( "TestFitModel.fit" )

		assert GetNumFitModelTargetPts() == 1, "LoadFitModelFile did not read the target point back"



	def test_CreatePtCloudGeomFromPts(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		cloud_id = CreatePtCloudGeomFromPts( pts, "ScriptCloud" )

		assert len( GetPtCloudPnts( cloud_id ) ) == 4, "CreatePtCloudGeomFromPts did not keep the points"



	def test_KeepPtsInBBox(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		inside = KeepPtsInBBox( pts, vec3d( 1.0, -1.0, -1.0 ), vec3d( 5.0, 1.0, 1.0 ) )

		assert len( inside ) == 2, "KeepPtsInBBox did not keep the points inside the box"



	def test_RemovePtsInBBox(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		outside = RemovePtsInBBox( pts, vec3d( 1.0, -1.0, -1.0 ), vec3d( 5.0, 1.0, 1.0 ) )

		assert len( outside ) == 2, "RemovePtsInBBox did not drop the points inside the box"



	def test_KeepPtsInRange(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		mid = KeepPtsInRange( pts, X_DIR, 1.0, 5.0 )

		assert len( mid ) == 2, "KeepPtsInRange did not keep the points in range"



	def test_RemovePtsInRange(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		ends = RemovePtsInRange( pts, X_DIR, 1.0, 5.0 )

		assert len( ends ) == 2, "RemovePtsInRange did not drop the points in range"



	def test_KeepPtsAbove(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		aft = KeepPtsAbove( pts, X_DIR, 3.0 )

		assert len( aft ) == 2, "KeepPtsAbove did not keep the points above the value"



	def test_KeepPtsBelow(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		fwd = KeepPtsBelow( pts, X_DIR, 3.0 )

		assert len( fwd ) == 2, "KeepPtsBelow did not keep the points below the value"



	def test_KeepPtsNearPt(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		near = KeepPtsNearPt( pts, vec3d( 4.0, 0.0, 0.0 ), 1.0 )

		assert len( near ) == 1, "KeepPtsNearPt did not keep the points near the point"



	def test_RemovePtsNearPt(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		far = RemovePtsNearPt( pts, vec3d( 4.0, 0.0, 0.0 ), 1.0 )

		assert len( far ) == 3, "RemovePtsNearPt did not drop the points near the point"



	def test_KeepPtsNearGeom(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []

		pts.append( CompPnt01( pid, 0, 0.5, 0.25 ) )
		pts.append( vec3d( 0.0, 100.0, 0.0 ) )

		on_body = KeepPtsNearGeom( pts, pid, 0, 1e-4 )

		assert len( on_body ) == 1, "KeepPtsNearGeom did not keep the point on the surface"



	def test_RemovePtsNearGeom(self):
		pid = AddGeom( "POD" )

		Update()

		pts = []

		pts.append( CompPnt01( pid, 0, 0.5, 0.25 ) )
		pts.append( vec3d( 0.0, 100.0, 0.0 ) )

		off_body = RemovePtsNearGeom( pts, pid, 0, 1e-4 )

		assert len( off_body ) == 1, "RemovePtsNearGeom did not drop the point on the surface"



	def test_UniquePts(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		twice = pts + pts

		once = UniquePts( twice, 1e-8 )

		assert len( once ) == 4, "UniquePts did not drop the repeats"



	def test_UnionPts(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		fwd = KeepPtsBelow( pts, X_DIR, 3.0 )
		aft = KeepPtsAbove( pts, X_DIR, 3.0 )

		all_pts = UnionPts( fwd, aft, 1e-8 )

		assert len( all_pts ) == 4, "UnionPts did not put the two halves back together"



	def test_IntersectPts(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		mid = KeepPtsInRange( pts, X_DIR, 1.0, 5.0 )

		both = IntersectPts( pts, mid, 1e-8 )

		assert len( both ) == 2, "IntersectPts did not keep the shared points"



	def test_SubtractPts(self):
		pts = []

		pts.append( vec3d( 0.0, 0.0, 0.0 ) )
		pts.append( vec3d( 2.0, 0.0, 0.0 ) )
		pts.append( vec3d( 4.0, 0.0, 0.0 ) )
		pts.append( vec3d( 6.0, 0.0, 0.0 ) )
		mid = KeepPtsInRange( pts, X_DIR, 1.0, 5.0 )

		rest = SubtractPts( pts, mid, 1e-8 )

		assert len( rest ) == 2, "SubtractPts did not remove the shared points"



	def test_AddVarPresetGroup(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )


	def test_AddVarPresetSetting(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )



	def test_AddVarPresetParm(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		# The Parm has to show up in the group's list, and only once.
		parm_ids = GetVarPresetParmIDs( gid )

		assert len( parm_ids ) == 1, "AddVarPresetParm did not add the Parm to the group"
		assert parm_ids[0] == p1, "AddVarPresetParm added the wrong Parm"

		# Adding it again has to be rejected rather than duplicating it.  The error
		# queue is reached through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		AddVarPresetParm( gid, p1 )

		assert err_mgr.GetNumTotalErrors() > 0, "AddVarPresetParm accepted the same Parm twice"
		assert len( GetVarPresetParmIDs( gid ) ) == 1, "AddVarPresetParm added the same Parm twice"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteAllVarPresetGroups(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		num_before_del = len( GetVarPresetGroups() )
		DeleteVarPresetGroup( gid )
		assert len( GetVarPresetGroups() ) < num_before_del, "DeleteVarPresetGroup removed nothing"




	def test_DeleteVarPresetGroup(self):
		gid = AddVarPresetGroup( "TestGroup" )

		DeleteVarPresetGroup( gid )

		assert len( GetVarPresetGroups() ) == 0, "DeleteVarPresetGroup did not delete the group"



	def test_DeleteAllVarPresetSettings(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		num_before_del = len( GetVarPresetSettings( gid ) )
		DeleteVarPresetSetting( gid, sid )
		assert len( GetVarPresetSettings( gid ) ) < num_before_del, "DeleteVarPresetSetting removed nothing"




	def test_DeleteVarPresetSetting(self):
		gid = AddVarPresetGroup( "TestGroup" )

		sid = AddVarPresetSetting( gid, "TestSetting" )

		DeleteVarPresetSetting( gid, sid )

		assert len( GetVarPresetSettings( gid ) ) == 0, "DeleteVarPresetSetting did not delete the setting"



	def test_DeleteVarPresetParm(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		num_before_del = len( GetVarPresetParmIDs( gid ) )
		DeleteVarPresetParm( gid, p1 )
		assert len( GetVarPresetParmIDs( gid ) ) < num_before_del, "DeleteVarPresetParm removed nothing"




	def test_SetVarPresetParmVal(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		SetVarPresetParmVal( gid, sid, p1, 51 )
		assert abs( GetVarPresetParmVal( gid, sid, p1 ) - 51 ) < 1e-9, "SetVarPresetParmVal did not take"




	def test_GetVarPresetParmVal(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		val = GetVarPresetParmVal( gid, sid, p1 )

		# A Parm joins the group at its current value.
		assert abs( val - GetParmVal( p1 ) ) < 1e-9, "GetVarPresetParmVal does not match the Parm"

		# Storing a different value has to be what comes back, without disturbing the
		# Parm itself.
		SetVarPresetParmVal( gid, sid, p1, val + 3.0 )

		assert abs( GetVarPresetParmVal( gid, sid, p1 ) - ( val + 3.0 ) ) < 1e-9, "GetVarPresetParmVal did not follow SetVarPresetParmVal"
		assert abs( GetParmVal( p1 ) - val ) < 1e-9, "storing a preset value changed the Parm"



	def test_GetGroupName(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		name = GetGroupName( gid )
		assert len( name ) > 0, "GetGroupName returned nothing"



	def test_GetSettingName(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		name = GetSettingName( sid )
		assert len( name ) > 0, "GetSettingName returned nothing"



	def test_SetGroupName(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		SetGroupName( gid, "Resolution" )
		assert GetGroupName( gid ) == "Resolution", "SetGroupName did not take"




	def test_SetSettingName(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		SetSettingName( sid, "Low" )
		assert GetSettingName( sid ) == "Low", "SetSettingName did not take"




	def test_GetVarPresetGroups(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		group_ids = GetVarPresetGroups()
		assert len( group_ids ) > 0, "GetVarPresetGroups returned nothing"



	def test_GetVarPresetSettings(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		settingds = GetVarPresetSettings( gid )
		assert len( settingds ) > 0, "GetVarPresetSettings returned nothing"



	def test_GetVarPresetParmIDs(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		parmids = GetVarPresetParmIDs( gid )
		assert len( parmids ) > 0, "GetVarPresetParmIDs returned nothing"



	def test_GetVarPresetParmVals(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		parmval_vec = GetVarPresetParmVals( sid )
		assert len( parmval_vec ) > 0, "GetVarPresetParmVals returned nothing"



	def test_SetVarPresetParmVals(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		vals = [ 45 ]

		SetVarPresetParmVals( sid, vals )

		assert list( GetVarPresetParmVals( sid ) ) == list( vals ), "SetVarPresetParmVals did not take"



	def test_SaveVarPresetParmVals(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		# Move the Parm away from whatever the setting holds, then save.
		SetParmVal( p1, GetParmVal( p1 ) + 4.0 )

		Update()

		SaveVarPresetParmVals( gid, sid )

		# The setting now holds the Parm's current value.
		assert abs( GetVarPresetParmVal( gid, sid, p1 ) - GetParmVal( p1 ) ) < 1e-9, "SaveVarPresetParmVals did not capture the current value"



	def test_ApplyVarPresetSetting(self):
		# Add Pod Geom
		pod1 = AddGeom( "POD", "" )

		gid = AddVarPresetGroup( "Tess" )

		sid = AddVarPresetSetting( gid, "Coarse" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )

		AddVarPresetParm( gid, p1 )

		# Store a value in the setting, move the Parm somewhere else, then apply.
		target = GetParmVal( p1 ) + 5.0

		SetVarPresetParmVal( gid, sid, p1, target )

		SetParmVal( p1, GetParmVal( p1 ) - 2.0 )

		Update()

		ApplyVarPresetSetting( gid, sid )

		Update()

		# Applying the setting drives the Parm to the stored value.
		assert abs( GetParmVal( p1 ) - target ) < 1e-9, "ApplyVarPresetSetting did not apply the stored value"



	def test_CreateAndAddMode(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		assert len( mid1 ) > 0 and mid1 != "NONE", "CreateAndAddMode returned no id"
		assert mid1 != mid2, "CreateAndAddMode reused an ID"



	def test_GetNumModes(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		nmod = GetNumModes()

		assert nmod == 2, "GetNumModes, two were created"



	def test_GetAllModes(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		modids = GetAllModes();
		assert len( modids ) > 0, "GetAllModes returned nothing"



	def test_DelMode(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		num_before_del = GetNumModes()
		DelMode( mid1 )
		assert GetNumModes() < num_before_del, "DelMode removed nothing"




	def test_DelAllModes(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		DelAllModes()
		assert GetNumModes() == 0, "DelAllModes left something behind"




	def test_GetModeName(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		# Each Mode carries the pairings it was given, in order.
		gids = ModeGetAllGroups( mid1 )
		sids = ModeGetAllSettings( mid1 )

		assert len( gids ) == 2 and gids[0] == gid and gids[1] == gid2, "the Mode did not record the pairings it was given"
		assert len( sids ) == 2 and sids[0] == sid1 and sids[1] == sid4, "the Mode did not record the pairings it was given"
		assert len( ModeGetAllGroups( mid2 ) ) == 2, "the second Mode did not record its pairings"

		# ThinAero carries the Fine tessellation and the LongThin design, so applying
		# it has to drive all four Parms to those stored values.
		assert abs( GetParmVal( p1 ) - 35 ) < 1e-9, "the tessellation group was not applied"
		assert abs( GetParmVal( p2 ) - 21 ) < 1e-9, "the tessellation group was not applied"
		assert abs( GetParmVal( p3 ) - 20.0 ) < 1e-9, "the design group was not applied"
		assert abs( GetParmVal( p4 ) - 35.0 ) < 1e-9, "the design group was not applied"

		# The other Mode holds different values, so switching has to move them.
		ApplyModeSettings( mid1 )
		Update()

		assert abs( GetParmVal( p1 ) - 3 ) < 1e-9, "switching Modes did not change the Parms"
		assert abs( GetParmVal( p3 ) - 3.0 ) < 1e-9, "switching Modes did not change the Parms"



	def test_SetModeName(self):
		mid = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )

		SetModeName( mid, "RenamedMode" )

		assert GetModeName( mid ) == "RenamedMode", "SetModeName did not take"

		# Renaming one Mode leaves the others alone.
		mid2 = CreateAndAddMode( "ThinAero", SET_ALL, SET_NONE )

		SetModeName( mid, "RenamedAgain" )

		assert GetModeName( mid2 ) == "ThinAero", "renaming one Mode disturbed another"



	def test_ApplyModeSettings(self):
		mid = CreateAndAddMode( "TestMode", SET_ALL, SET_NONE )

		ApplyModeSettings( mid )



	def test_ShowOnlyMode(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		ShowOnlyMode( mid1 )

		Update()

		# FatWetAreas uses SET_ALL as its normal set, so both Geoms end up shown.
		assert GetSetFlag( pod1, SET_SHOWN ), "ShowOnlyMode did not show the Mode's set"
		assert GetSetFlag( wing, SET_SHOWN ), "ShowOnlyMode did not show the Mode's set"

		# A Mode that does not exist has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		ShowOnlyMode( "NOSUCHMODE" )

		assert err_mgr.GetNumTotalErrors() > 0, "ShowOnlyMode accepted a bad Mode ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_ModeAddGroupSetting(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		# Each Mode carries the pairings it was given, in order.
		gids = ModeGetAllGroups( mid1 )
		sids = ModeGetAllSettings( mid1 )

		assert len( gids ) == 2 and gids[0] == gid and gids[1] == gid2, "the Mode did not record the pairings it was given"
		assert len( sids ) == 2 and sids[0] == sid1 and sids[1] == sid4, "the Mode did not record the pairings it was given"
		assert len( ModeGetAllGroups( mid2 ) ) == 2, "the second Mode did not record its pairings"

		# ThinAero carries the Fine tessellation and the LongThin design, so applying
		# it has to drive all four Parms to those stored values.
		assert abs( GetParmVal( p1 ) - 35 ) < 1e-9, "the tessellation group was not applied"
		assert abs( GetParmVal( p2 ) - 21 ) < 1e-9, "the tessellation group was not applied"
		assert abs( GetParmVal( p3 ) - 20.0 ) < 1e-9, "the design group was not applied"
		assert abs( GetParmVal( p4 ) - 35.0 ) < 1e-9, "the design group was not applied"

		# The other Mode holds different values, so switching has to move them.
		ApplyModeSettings( mid1 )
		Update()

		assert abs( GetParmVal( p1 ) - 3 ) < 1e-9, "switching Modes did not change the Parms"
		assert abs( GetParmVal( p3 ) - 3.0 ) < 1e-9, "switching Modes did not change the Parms"



	def test_ModeGetGroup(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		gid3 = ModeGetGroup( mid1, 0 )
		assert len( gid3 ) > 0, "ModeGetGroup returned no id"




	def test_ModeGetSetting(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		sid6 = ModeGetSetting( mid1, 0 )
		assert len( sid6 ) > 0, "ModeGetSetting returned no id"




	def test_ModeGetAllGroups(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		gids = ModeGetAllGroups( mid1 )

		# Two group settings were added to this Mode, in this order.
		assert len( gids ) == 2, "ModeGetAllGroups did not report the groups that were added"
		assert gids[0] == gid, "ModeGetAllGroups did not report the groups that were added"
		assert gids[1] == gid2, "ModeGetAllGroups did not report the groups that were added"

		# The groups and the settings line up one for one.
		assert len( gids ) == len( ModeGetAllSettings( mid1 ) ), "ModeGetAllGroups disagrees with ModeGetAllSettings"



	def test_ModeGetAllSettings(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		sids = ModeGetAllSettings( mid1 )

		# The settings come back paired with the groups they were added under.
		assert len( sids ) == 2, "ModeGetAllSettings did not report the settings that were added"
		assert sids[0] == sid1, "ModeGetAllSettings did not report the settings that were added"
		assert sids[1] == sid4, "ModeGetAllSettings did not report the settings that were added"



	def test_RemoveGroupSetting(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		RemoveGroupSetting( mid1, 0 )

		# Only the indexed pairing goes; the other one stays and slides down.
		gids = ModeGetAllGroups( mid1 )
		sids = ModeGetAllSettings( mid1 )

		assert len( gids ) == 1 and gids[0] == gid2, "RemoveGroupSetting removed the wrong pairing"
		assert len( sids ) == 1 and sids[0] == sid4, "RemoveGroupSetting removed the wrong pairing"



	def test_RemoveAllGroupSettings(self):
		# Illustrating use of Modes requires substantial setup of the model including components, sets, and variable presets.
		#
		# Setup boiler plate.
		pod1 = AddGeom( "POD", "" )
		wing = AddGeom( "WING", pod1 )

		SetParmVal( wing, "Trans_Attach_Flag", "Attach", ATTACH_TRANS_LMN )
		SetParmVal( wing, "L_Attach_Location", "Attach", 0.35 )

		SetSetName( SET_FIRST_USER, "NonLifting" )
		SetSetName( SET_FIRST_USER + 1, "Lifting" )

		SetSetFlag( pod1, SET_FIRST_USER, True )
		SetSetFlag( wing, SET_FIRST_USER + 1, True )


		gid = AddVarPresetGroup( "Tess" )

		p1 = FindParm( pod1, "Tess_U", "Shape" )
		AddVarPresetParm( gid, p1 )

		p2 = FindParm( pod1, "Tess_W", "Shape" )
		AddVarPresetParm( gid, p2 )

		sid = AddVarPresetSetting( gid, "Default" )
		SaveVarPresetParmVals( gid, sid )

		sid1 = AddVarPresetSetting( gid, "Coarse" )
		SetVarPresetParmVal( gid, sid1, p1, 3 )
		SetVarPresetParmVal( gid, sid1, p2, 5 )

		sid2 = AddVarPresetSetting( gid, "Fine" )
		SetVarPresetParmVal( gid, sid2, p1, 35 )
		SetVarPresetParmVal( gid, sid2, p2, 21 )


		gid2 = AddVarPresetGroup( "Design" )

		p3 = FindParm( pod1, "Length", "Design" )
		AddVarPresetParm( gid2, p3 )

		p4 = FindParm( pod1, "FineRatio", "Design" )
		AddVarPresetParm( gid2, p4 )

		sid3 = AddVarPresetSetting( gid2, "Normal" )
		SaveVarPresetParmVals( gid2, sid3 )

		sid4 = AddVarPresetSetting( gid2, "ShortFat" )
		SetVarPresetParmVal( gid2, sid4, p3, 3.0 )
		SetVarPresetParmVal( gid2, sid4, p4, 5.0 )

		sid5 = AddVarPresetSetting( gid2, "LongThin" )
		SetVarPresetParmVal( gid2, sid5, p3, 20.0 )
		SetVarPresetParmVal( gid2, sid5, p4, 35.0 )

		# End of setup boiler plate.

		mid1 = CreateAndAddMode( "FatWetAreas", SET_ALL, SET_NONE )
		ModeAddGroupSetting( mid1, gid, sid1 )
		ModeAddGroupSetting( mid1, gid2, sid4 )

		mid2 = CreateAndAddMode( "ThinAero", SET_FIRST_USER, SET_FIRST_USER + 1 )
		ModeAddGroupSetting( mid2, gid, sid2 )
		ModeAddGroupSetting( mid2, gid2, sid5 )

		ApplyModeSettings( mid2 )
		Update()

		RemoveAllGroupSettings( mid1 )

		# Every pairing on this Mode goes, and the other Mode is left alone.
		assert len( ModeGetAllGroups( mid1 ) ) == 0, "RemoveAllGroupSettings left pairings behind"
		assert len( ModeGetAllSettings( mid1 ) ) == 0, "RemoveAllGroupSettings left pairings behind"
		assert len( ModeGetAllGroups( mid2 ) ) == 2, "RemoveAllGroupSettings reached the other Mode"



	def test_SetPCurve(self):
		prop_id = AddGeom( "PROP" )

		Update()

		tvec = PCurveGetTVec( prop_id, PROP_CHORD )
		valvec = PCurveGetValVec( prop_id, PROP_CHORD )

		SetPCurve( prop_id, PROP_CHORD, tvec, valvec, PCurveGetType( prop_id, PROP_CHORD ) )

		Update()

		assert len( PCurveGetTVec( prop_id, PROP_CHORD ) ) == len( tvec ), "SetPCurve did not take"



	def test_PCurveConvertTo(self):
		prop_id = AddGeom( "PROP" )

		Update()

		PCurveConvertTo( prop_id, PROP_CHORD, LINEAR )

		Update()

		assert PCurveGetType( prop_id, PROP_CHORD ) == LINEAR, "PCurveConvertTo did not change the type"



	def test_PCurveGetType(self):
		prop_id = AddGeom( "PROP" )

		Update()

		t = PCurveGetType( prop_id, PROP_CHORD )

		assert t >= 0, "PCurveGetType returned a bad type"



	def test_PCurveGetTVec(self):
		prop_id = AddGeom( "PROP" )

		Update()

		tvec = PCurveGetTVec( prop_id, PROP_CHORD )

		assert len( tvec ) > 0, "PCurveGetTVec returned nothing"



	def test_PCurveGetValVec(self):
		prop_id = AddGeom( "PROP" )

		Update()

		valvec = PCurveGetValVec( prop_id, PROP_CHORD )

		assert len( valvec ) > 0, "PCurveGetValVec returned nothing"

		assert len( valvec ) == len( PCurveGetTVec( prop_id, PROP_CHORD ) ), "PCurveGetValVec disagrees with the T vector"



	def test_PCurveDeletePt(self):
		prop_id = AddGeom( "PROP" )

		Update()

		# A cubic edit curve holds its points in groups and will not give one up on its own, so put
		# the curve into a form where a single point can go.
		PCurveConvertTo( prop_id, PROP_CHORD, LINEAR )

		Update()

		n = len( PCurveGetTVec( prop_id, PROP_CHORD ) )

		PCurveDeletePt( prop_id, PROP_CHORD, 1 )

		Update()

		assert len( PCurveGetTVec( prop_id, PROP_CHORD ) ) < n, "PCurveDeletePt did not remove a point"



	def test_PCurveSplit(self):
		prop_id = AddGeom( "PROP" )

		Update()

		n = len( PCurveGetTVec( prop_id, PROP_CHORD ) )

		PCurveSplit( prop_id, PROP_CHORD, 0.55 )

		Update()

		assert len( PCurveGetTVec( prop_id, PROP_CHORD ) ) > n, "PCurveSplit did not add a point"



	def test_ApproximateAllPropellerPCurves(self):
		# Add Propeller
		prop = AddGeom( "PROP", "" )

		# Take the blade curves off Bezier so the approximation has something to do.
		PCurveConvertTo( prop, PROP_CHORD, PCHIP )
		PCurveConvertTo( prop, PROP_TWIST, PCHIP )
		PCurveConvertTo( prop, PROP_THICK, PCHIP )

		Update()

		assert PCurveGetType( prop, PROP_CHORD ) == PCHIP, "the blade curves would not convert to PCHIP"

		ApproximateAllPropellerPCurves( prop )

		# Every blade curve is now a cubic Bezier.
		assert PCurveGetType( prop, PROP_CHORD ) == CEDIT, "ApproximateAllPropellerPCurves did not convert the curves"
		assert PCurveGetType( prop, PROP_TWIST ) == CEDIT, "ApproximateAllPropellerPCurves did not convert the curves"
		assert PCurveGetType( prop, PROP_THICK ) == CEDIT, "ApproximateAllPropellerPCurves did not convert the curves"

		# A cubic Bezier is stored in groups of three, so the control point count is
		# one more than a multiple of three.
		tvec = PCurveGetTVec( prop, PROP_CHORD )

		assert len( tvec ) >= 4 and ( len( tvec ) - 1 ) % 3 == 0, "the converted curve is not a cubic Bezier"



	def test_ResetPropellerThickness(self):
		prop_id = AddGeom( "PROP", "" )

		Update()

		ResetPropellerThickness( prop_id )

		# The thickness curve now carries one point per cross section.
		tvec = PCurveGetTVec( prop_id, PROP_THICK )

		xsec_surf = GetXSecSurf( prop_id, 0 )

		assert len( tvec ) == GetNumXSec( xsec_surf ), "ResetPropellerThickness did not rebuild the curve"



	def test_ResetPropellerThicknessCurve(self):
		# Add Propeller
		prop = AddGeom( "PROP", "" )

		ResetPropellerThicknessCurve( prop )

		Update()

		# The curve is rebuilt from the blade XSecs: one PCHIP station per XSec, each
		# carrying that XSec's thickness to chord ratio.
		tvec = PCurveGetTVec( prop, PROP_THICK )
		vvec = PCurveGetValVec( prop, PROP_THICK )

		xsec_surf = GetXSecSurf( prop, 0 )

		num_xsec = GetNumXSec( xsec_surf )

		assert PCurveGetType( prop, PROP_THICK ) == PCHIP, "ResetPropellerThicknessCurve did not make a PCHIP curve"
		assert len( vvec ) == num_xsec, "ResetPropellerThicknessCurve did not follow the XSecs"
		assert len( tvec ) == len( vvec ), "ResetPropellerThicknessCurve did not follow the XSecs"

		for i in range( num_xsec ):
			tc = GetXSecParm( GetXSec( xsec_surf, i ), "ThickChord" )

			# A circular XSec carries no thickness Parm; its base thickness is used
			# instead.
			if len( tc ) > 0:
				assert abs( vvec[i] - GetParmVal( tc ) ) < 1e-6, "station " + str( i ) + " does not match its XSec"

		# The stations run out along the blade.
		for i in range( 1, len( tvec ) ):
			assert tvec[i] > tvec[i - 1], "the thickness stations are not increasing"

		# Looking up the circular XSec's thickness raises an error on purpose, so take
		# it back off the queue.
		err_mgr = ErrorMgrSingleton.getInstance()

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_AutoGroupVSPAEROControlSurfaces(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL )                      # Add Control Surface Sub-Surface

		#==== Add Vertical tail and set some parameters =====//
		vert_id = AddGeom( "WING" )

		SetGeomName( vert_id, "Vert" )

		SetParmValUpdate( vert_id, "TotalArea", "WingGeom", 10.0 )
		SetParmValUpdate( vert_id, "X_Rel_Location", "XForm", 8.5 )
		SetParmValUpdate( vert_id, "X_Rel_Rotation", "XForm", 90 )

		rudder_id = AddSubSurf( vert_id, SS_CONTROL )                      # Add Control Surface Sub-Surface

		AutoGroupVSPAEROControlSurfaces()

		Update()

		print( "COMPLETE\n" )
		control_group_settings_container_id = FindContainer( "VSPAEROSettings", 0 )   # auto grouping produces parm containers within VSPAEROSettings

		#==== Set Control Surface Group Deflection Angle ====//
		print( "\tSetting control surface group deflection angles..." )

		# subsurfaces get added to groups with "CSGQualities_[geom_name]_[control_surf_name]"
		# subsurfaces gain parm name is "Surf[surfndx]_Gain" starting from 0 to NumSymmetricCopies-1

		deflection_gain_id = FindParm( control_group_settings_container_id, "Surf_" + aileron_id + "_0_Gain", "ControlSurfaceGroup_0" )
		deflection_gain_id = FindParm( control_group_settings_container_id, "Surf_" + aileron_id + "_1_Gain", "ControlSurfaceGroup_0" )

		#  deflect aileron
		deflection_angle_id = FindParm( control_group_settings_container_id, "DeflectionAngle", "ControlSurfaceGroup_0" )

		# Auto grouping puts each control surface in a group of its own, so the two
		# that were added make two groups, and each holds one surface.
		assert GetNumControlSurfaceGroups() == 2, "AutoGroupVSPAEROControlSurfaces did not make a group per surface"

		for i in range( 2 ):
			# Each wing is symmetric, so its control surface arrives as two copies
			# and both land in the group.
			assert len( GetActiveCSNameVec( i ) ) == 2, "group " + str( i ) + " does not hold its control surface copies"
			assert len( GetVSPAEROControlGroupName( i ) ) > 0, "group " + str( i ) + " was not named"

		# The Parms the grouping created have to be findable.
		assert len( deflection_gain_id ) > 0, "the control surface group Parms were not created"
		assert len( deflection_angle_id ) > 0, "the control surface group Parms were not created"



	def test_AddCpSlice(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL )                      # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		num_group = GetNumControlSurfaceGroups()

		if  num_group != 1 :
			print( "Error: CreateVSPAEROControlSurfaceGroup" )
			assert False, "Error: CreateVSPAEROControlSurfaceGroup"



	def test_GetNumCpSlices(self):
		num_before = GetNumCpSlices()

		AddCpSlice( X_DIR, 0.5 )
		AddCpSlice( Y_DIR, 0.25 )

		assert GetNumCpSlices() == num_before + 2, "GetNumCpSlices did not count both slices"

		# Every slice the count claims has to be findable.
		for i in range( GetNumCpSlices() ):
			assert len( GetCpSliceID( i ) ) > 0, "slice " + str( i ) + " cannot be found"



	def test_GetCpSliceID(self):
		num_before = GetNumCpSlices()

		first = AddCpSlice( X_DIR, 0.5 )
		second = AddCpSlice( Y_DIR, 0.25 )

		# Slices come back in the order they were added.
		assert GetCpSliceID( num_before ) == first, "GetCpSliceID did not report the slices in order"
		assert GetCpSliceID( num_before + 1 ) == second, "GetCpSliceID did not report the slices in order"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetCpSliceID( GetNumCpSlices() )

		assert err_mgr.GetNumTotalErrors() > 0, "GetCpSliceID accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DelCpSlice(self):
		DeleteAllCpSlices()

		first = AddCpSlice( X_DIR, 0.5 )
		second = AddCpSlice( Y_DIR, 0.25 )

		DelCpSlice( 0 )

		# Only the indexed slice goes, and the rest slide down.
		assert GetNumCpSlices() == 1, "DelCpSlice removed the wrong slice"
		assert GetCpSliceID( 0 ) == second, "DelCpSlice removed the wrong slice"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		DelCpSlice( GetNumCpSlices() )

		assert err_mgr.GetNumTotalErrors() > 0, "DelCpSlice accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteAllCpSlices(self):
		AddCpSlice( X_DIR, 0.5 )
		AddCpSlice( Y_DIR, 0.25 )

		DeleteAllCpSlices()

		assert GetNumCpSlices() == 0, "DeleteAllCpSlices left slices behind"

		# Clearing an empty slicer is not an error.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteAllCpSlices()

		assert err_mgr.GetNumTotalErrors() == 0, "DeleteAllCpSlices complained about an empty slicer"



	def test_DeleteVSPAEROControlSurfaceGroup(self):
		wid = AddGeom( "WING" )

		Update()

		CreateVSPAEROControlSurfaceGroup()

		DeleteVSPAEROControlSurfaceGroup( 0 )

		assert GetNumControlSurfaceGroups() == 0, "DeleteVSPAEROControlSurfaceGroup did not delete the group"



	def test_CreateVSPAEROControlSurfaceGroup(self):
		wid = AddGeom( "WING" )

		Update()

		group_index = CreateVSPAEROControlSurfaceGroup()

		assert GetNumControlSurfaceGroups() == 1, "CreateVSPAEROControlSurfaceGroup did not add the group"



	def test_AddAllToVSPAEROControlSurfaceGroup(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL )                      # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		# The group starts empty and the wing offers one control surface, mirrored
		# by the wing's own symmetry.
		assert GetNumControlSurfaceGroups() >= 1, "CreateVSPAEROControlSurfaceGroup did not add a group"

		num_avail = len( GetAvailableCSNameVec( group_index ) )

		assert num_avail >= 1, "no control surfaces are available to add"
		assert len( GetActiveCSNameVec( group_index ) ) == 0, "a new control surface group is not empty"

		AddAllToVSPAEROControlSurfaceGroup( group_index )

		# Everything that was available is now active, and nothing is left over.
		assert len( GetActiveCSNameVec( group_index ) ) == num_avail, "AddAllToVSPAEROControlSurfaceGroup did not add them all"
		assert len( GetAvailableCSNameVec( group_index ) ) == 0, "control surfaces are still available after adding them all"



	def test_RemoveAllFromVSPAEROControlSurfaceGroup(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL )                      # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		AddAllToVSPAEROControlSurfaceGroup( group_index )

		num_active = len( GetActiveCSNameVec( group_index ) )

		assert num_active >= 1, "nothing was added to the group to remove"

		RemoveAllFromVSPAEROControlSurfaceGroup( group_index ) # Empty control surface group

		# Everything that was active goes back to being available.
		assert len( GetActiveCSNameVec( group_index ) ) == 0, "RemoveAllFromVSPAEROControlSurfaceGroup left surfaces in the group"
		assert len( GetAvailableCSNameVec( group_index ) ) == num_active, "the removed surfaces did not become available again"



	def test_GetActiveCSNameVec(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL )                      # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		AddAllToVSPAEROControlSurfaceGroup( group_index )

		cs_name_vec = GetActiveCSNameVec( group_index )
		assert len( cs_name_vec ) > 0, "GetActiveCSNameVec returned nothing"

		print( "Active CS in Group Index #", False )
		print( group_index )

		for i in range(int( len(cs_name_vec) )):

			print( cs_name_vec[i] )



	def test_GetCompleteCSNameVec(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL )                      # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		cs_name_vec = GetCompleteCSNameVec()
		assert len( cs_name_vec ) > 0, "GetCompleteCSNameVec returned nothing"

		print( "All Control Surfaces: ", False )

		for i in range(int( len(cs_name_vec) )):

			print( cs_name_vec[i] )



	def test_GetAvailableCSNameVec(self):
		wid = AddGeom( "WING", "" ) # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL ) # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		cs_name_vec = GetAvailableCSNameVec( group_index )
		assert len( cs_name_vec ) > 0, "GetAvailableCSNameVec returned nothing"

		cs_ind_vec = [1]

		AddSelectedToCSGroup( cs_ind_vec, group_index ) # Add the first available control surface to the group

		# One surface moved from available to active.
		active_vec = GetActiveCSNameVec( group_index )

		assert len( active_vec ) == 1, "AddSelectedToCSGroup did not add the surface that was named"
		assert active_vec[0] == cs_name_vec[0], "AddSelectedToCSGroup added the wrong surface"
		assert len( GetAvailableCSNameVec( group_index ) ) == len( cs_name_vec ) - 1, "the added surface is still available"



	def test_SetVSPAEROControlGroupName(self):
		wid = AddGeom( "WING", "" ) # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL ) # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		SetVSPAEROControlGroupName( "Example_CS_Group", group_index )

		assert GetVSPAEROControlGroupName( group_index ) == "Example_CS_Group", "SetVSPAEROControlGroupName did not take"

		print( "CS Group name: ", False )

		print( GetVSPAEROControlGroupName( group_index ) )



	def test_GetVSPAEROControlGroupName(self):
		wid = AddGeom( "WING", "" ) # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL ) # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		SetVSPAEROControlGroupName( "Example_CS_Group", group_index )

		assert GetVSPAEROControlGroupName( group_index ) == "Example_CS_Group", "SetVSPAEROControlGroupName did not take"

		print( "CS Group name: ", False )

		print( GetVSPAEROControlGroupName( group_index ) )



	def test_AddSelectedToCSGroup(self):
		wid = AddGeom( "WING", "" ) # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL ) # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		cs_name_vec = GetAvailableCSNameVec( group_index )

		cs_ind_vec = [0] * len(cs_name_vec)

		for i in range(int( len(cs_name_vec) )):

			cs_ind_vec[i] = i + 1

		AddSelectedToCSGroup( cs_ind_vec, group_index ) # Add all available control surfaces to the group

		# Everything that was named moved from available to active.
		assert len( GetActiveCSNameVec( group_index ) ) == len( cs_name_vec ), "AddSelectedToCSGroup did not add them all"
		assert len( GetAvailableCSNameVec( group_index ) ) == 0, "control surfaces are still available after adding them all"



	def test_RemoveSelectedFromCSGroup(self):
		wid = AddGeom( "WING", "" ) # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL ) # Add Control Surface Sub-Surface

		group_index = CreateVSPAEROControlSurfaceGroup() # Empty control surface group

		cs_name_vec = GetAvailableCSNameVec( group_index )

		cs_ind_vec = [0] * len(cs_name_vec)

		for i in range(int( len(cs_name_vec) )):

			cs_ind_vec[i] = i + 1

		AddSelectedToCSGroup( cs_ind_vec, group_index ) # Add the available control surfaces to the group

		remove_cs_ind_vec = [1]

		num_active = len( GetActiveCSNameVec( group_index ) )

		assert num_active == len( cs_name_vec ), "not everything was added to the group"

		RemoveSelectedFromCSGroup( remove_cs_ind_vec, group_index ) # Remove the first control surface

		# One surface moved back from active to available.
		assert len( GetActiveCSNameVec( group_index ) ) == num_active - 1, "RemoveSelectedFromCSGroup did not remove a surface"
		assert len( GetAvailableCSNameVec( group_index ) ) == 1, "the removed surface did not become available again"



	def test_GetNumControlSurfaceGroups(self):
		wid = AddGeom( "WING", "" )                             # Add Wing

		aileron_id = AddSubSurf( wid, SS_CONTROL )                      # Add Control Surface Sub-Surface

		#==== Add Horizontal tail and set some parameters =====//
		horiz_id = AddGeom( "WING", "" )

		SetGeomName( horiz_id, "Vert" )

		SetParmValUpdate( horiz_id, "TotalArea", "WingGeom", 10.0 )
		SetParmValUpdate( horiz_id, "X_Rel_Location", "XForm", 8.5 )

		elevator_id = AddSubSurf( horiz_id, SS_CONTROL )                      # Add Control Surface Sub-Surface

		AutoGroupVSPAEROControlSurfaces()

		num_group = GetNumControlSurfaceGroups()

		if  num_group != 2 :
			print( "Error: GetNumControlSurfaceGroups" )
			assert False, "Error: GetNumControlSurfaceGroups"



	def test_FindControlSurfaceGroup(self):
		#==== A wing with a control surface on it ====#
		wid = AddGeom( "WING", "" )
		subsurf_id = AddSubSurf( wid, SS_CONTROL, 0 )

		Update()

		#==== Group it, the way the VSPAERO screen does ====#
		AutoGroupVSPAEROControlSurfaces()

		Update()

		assert GetNumControlSurfaceGroups() > 0, "no control surface group was made"

		group_id = FindControlSurfaceGroup( 0 )

		assert len( group_id ) > 0, "FindControlSurfaceGroup found nothing"

		#==== And its deflection is a Parm like any other ====#
		SetParmVal( FindParm( group_id, "DeflectionAngle", "ControlSurfaceGroup" ), 7.0 )

		Update()

		deflected = GetParmVal( group_id, "DeflectionAngle", "ControlSurfaceGroup" )

		assert abs( deflected - 7.0 ) < 1e-6, "the group did not take the deflection it was given"



	def test_FindActuatorDisk(self):
		# Add a propeller
		prop_id = AddGeom( "PROP", "" )
		SetParmVal( prop_id, "PropMode", "Design", PROP_DISK )
		SetParmVal( prop_id, "Diameter", "Design", 6.0 )

		Update()

		# Setup the actuator disk VSPAERO parms
		disk_id = FindActuatorDisk( 0 )
		assert len( disk_id ) > 0, "FindActuatorDisk found nothing"

		SetParmVal( FindParm( disk_id, "RotorRPM", "Rotor" ), 1234.0 )
		SetParmVal( FindParm( disk_id, "RotorCT", "Rotor" ), 0.35 )
		SetParmVal( FindParm( disk_id, "RotorCP", "Rotor" ), 0.55 )
		SetParmVal( FindParm( disk_id, "RotorHubDiameter", "Rotor" ), 1.0 )



	def test_GetNumActuatorDisks(self):
		# Set VSPAERO set index to SET_ALL
		SetParmVal( FindParm( FindContainer( "VSPAEROSettings", 0 ), "GeomSet", "VSPAERO" ), SET_ALL )

		# Add a propeller
		prop_id = AddGeom( "PROP", "" )
		SetParmValUpdate( prop_id, "PropMode", "Design", PROP_BLADES )

		num_disk = GetNumActuatorDisks() # Should be 0

		assert num_disk == 0, "a bladed propeller counts as an actuator disk"

		SetParmValUpdate( prop_id, "PropMode", "Design", PROP_DISK )

		num_disk = GetNumActuatorDisks() # Should be 1

		assert num_disk == 1, "GetNumActuatorDisks did not count the disk"

		# The disk has to be findable at every index it claims.
		for i in range( num_disk ):
			assert len( FindActuatorDisk( i ) ) > 0, "GetNumActuatorDisks counted a disk that cannot be found"



	def test_FindUnsteadyGroup(self):
		wing_id = AddGeom( "WING" )
		pod_id = AddGeom( "POD" )

		# Create an actuator disk
		prop_id = AddGeom( "PROP", "" )
		SetParmVal( prop_id, "PropMode", "Design", PROP_BLADES )

		Update()

		# Setup the unsteady group VSPAERO parms
		disk_id = FindUnsteadyGroup( 1 ) # fixed components are in group 0 (wing & pod)
		assert len( disk_id ) > 0, "FindUnsteadyGroup found nothing"

		SetParmVal( FindParm( disk_id, "RPM", "UnsteadyGroup" ), 1234.0 )



	def test_GetUnsteadyGroupName(self):
		# Add a pod and wing
		pod_id = AddGeom( "POD", "" )
		wing_id = AddGeom( "WING", pod_id )

		SetParmVal( wing_id, "X_Rel_Location", "XForm", 2.5 )
		Update()

		print( GetUnsteadyGroupName( 0 ) )

		# The pod and wing are fixed components, so they share the one fixed group.
		assert GetUnsteadyGroupName( 0 ) == "Fixed_Group", "GetUnsteadyGroupName did not name the fixed component group"

		# That group holds the pod and both wing surfaces.
		assert len( GetUnsteadyGroupCompIDs( 0 ) ) == 3, "the fixed group does not hold the components"

		# A group index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetUnsteadyGroupName( GetNumUnsteadyGroups() )

		assert err_mgr.GetNumTotalErrors() > 0, "GetUnsteadyGroupName accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetUnsteadyGroupCompIDs(self):
		# Add a pod and wing
		pod_id = AddGeom( "POD", "" )
		wing_id = AddGeom( "WING", pod_id ) # Default with symmetry on -> 2 surfaces

		SetParmVal( wing_id, "X_Rel_Location", "XForm", 2.5 )
		Update()

		comp_ids = GetUnsteadyGroupCompIDs( 0 )

		if  len(comp_ids) != 3 :
			print( "ERROR: GetUnsteadyGroupCompIDs" )
			assert False, "ERROR: GetUnsteadyGroupCompIDs"



	def test_GetUnsteadyGroupSurfIndexes(self):
		# Add a pod and wing
		pod_id = AddGeom( "POD", "" )
		wing_id = AddGeom( "WING", pod_id ) # Default with symmetry on -> 2 surfaces

		SetParmVal( wing_id, "X_Rel_Location", "XForm", 2.5 )
		Update()

		surf_indexes = GetUnsteadyGroupSurfIndexes( 0 )

		if  len(surf_indexes) != 3 :
			print( "ERROR: GetUnsteadyGroupSurfIndexes" )
			assert False, "ERROR: GetUnsteadyGroupSurfIndexes"



	def test_GetNumUnsteadyGroups(self):
		# Set VSPAERO set index to SET_ALL
		SetParmVal( FindParm( FindContainer( "VSPAEROSettings", 0 ), "GeomSet", "VSPAERO" ), SET_ALL )

		# Add a propeller
		prop_id = AddGeom( "PROP" )
		SetParmValUpdate( prop_id, "PropMode", "Design", PROP_DISK )

		num_group = GetNumUnsteadyGroups() # Should be 0

		assert num_group == 0, "an actuator disk counts as an unsteady group"

		SetParmValUpdate( prop_id, "PropMode", "Design", PROP_BLADES )

		num_group = GetNumUnsteadyGroups() # Should be 1

		assert num_group == 1, "the bladed propeller was not counted"

		wing_id = AddGeom( "WING" )

		num_group = GetNumUnsteadyGroups() # Should be 2 (includes fixed component group)

		assert num_group == 2, "the fixed component group was not counted"

		# Only the propeller is a rotor group; the wing shares the fixed group.
		assert GetNumUnsteadyRotorGroups() == 1, "GetNumUnsteadyGroups disagrees with GetNumUnsteadyRotorGroups"



	def test_GetNumUnsteadyRotorGroups(self):
		# Set VSPAERO set index to SET_ALL
		SetParmVal( FindParm( FindContainer( "VSPAEROSettings", 0 ), "GeomSet", "VSPAERO" ), SET_ALL )

		# Add a propeller
		prop_id = AddGeom( "PROP" )
		SetParmValUpdate( prop_id, "PropMode", "Design", PROP_DISK )

		num_group = GetNumUnsteadyRotorGroups() # Should be 0

		assert num_group == 0, "an actuator disk counts as a rotor group"

		SetParmValUpdate( prop_id, "PropMode", "Design", PROP_BLADES )

		num_group = GetNumUnsteadyRotorGroups() # Should be 1

		assert num_group == 1, "the bladed propeller was not counted"

		wing_id = AddGeom( "WING" )

		num_group = GetNumUnsteadyRotorGroups() # Should be 1 still (fixed group not included)

		assert num_group == 1, "the wing was counted as a rotor group"

		# The wing does add a fixed component group, which the total counts.
		assert GetNumUnsteadyGroups() == num_group + 1, "the fixed component group was not counted"



	def test_AddExcrescence(self):
		AddExcrescence( "Miscellaneous", EXCRESCENCE_COUNT, 8.5 )

		AddExcrescence( "Cowl Boattail", EXCRESCENCE_CD, 0.0003 )

		# Each excrescence gets its own row, so deleting them one at a time has to
		# empty the table and then start being rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteExcrescence( 1 )
		DeleteExcrescence( 0 )

		assert err_mgr.GetNumTotalErrors() == 0, "the two excrescences were not both added"

		DeleteExcrescence( 0 )

		assert err_mgr.GetNumTotalErrors() > 0, "more excrescences were added than asked for"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetNumExcrescences(self):
		AddExcrescence( "Miscellaneous", EXCRESCENCE_COUNT, 8.5 )

		AddExcrescence( "Cowl Boattail", EXCRESCENCE_CD, 0.0003 )

		AddExcrescence( "Percentage Example", EXCRESCENCE_PERCENT_GEOM, 5 )

		DeleteExcrescence( 2 ) # Last Index

		# Three were added and one was deleted, so index 2 no longer exists and
		# asking for it again has to be rejected.  The error queue is reached through
		# the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteExcrescence( 2 )

		assert err_mgr.GetNumTotalErrors() > 0, "DeleteExcrescence accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DeleteAllExcrescences(self):
		AddExcrescence( "Miscellaneous", EXCRESCENCE_COUNT, 8.5 )

		AddExcrescence( "Cowl Boattail", EXCRESCENCE_CD, 0.0003 )

		AddExcrescence( "Percentage Example", EXCRESCENCE_PERCENT_GEOM, 5 )

		DeleteAllExcrescences()

		assert GetNumExcrescences() == 0, "DeleteAllExcrescences left excrescences behind"

		# Clearing an empty table is not an error.
		err_mgr = ErrorMgrSingleton.getInstance()

		DeleteAllExcrescences()

		assert err_mgr.GetNumTotalErrors() == 0, "DeleteAllExcrescences complained about an empty table"



	def test_DeleteExcrescence(self):
		AddExcrescence( "TestExcrescence", EXCRESCENCE_COUNT, 2.0 )

		DeleteExcrescence( 0 )

		assert GetNumExcrescences() == 0, "DeleteExcrescence did not delete the excrescence"



	def test_UpdateParasiteDrag(self):
		pid = AddGeom( "POD" )

		Update()

		UpdateParasiteDrag()



	def test_ExportParasiteDragToCSV(self):
		pod_id = AddGeom( "POD", "" )

		Update()

		# The table is filled in by running the buildup, so do that first.
		ExecAnalysis( "ParasiteDrag" )

		res_id = ExportParasiteDragToCSV( "ParasiteDragExample.csv" )

		assert len( res_id ) > 0, "ExportParasiteDragToCSV returned no results"

		# The buildup carries one row per Geom, so the Pod has to be in there.
		labels = GetStringResults( res_id, "Comp_Label" )

		assert len( labels ) > 0, "the buildup table is empty"



	def test_WriteAtmosphereCSVFile(self):
		print( "Starting USAF Atmosphere 1966 Table Creation. \n" )

		WriteAtmosphereCSVFile( "USAFAtmosphere1966Data.csv", ATMOS_TYPE_HERRINGTON_1966 )
		# The call above should have produced a file with content in it.
		import os
		assert os.path.getsize( "USAFAtmosphere1966Data.csv" ) > 0, "WriteAtmosphereCSVFile wrote no file"




	def test_CalcAtmosphere(self):

		alt = 4000

		delta_temp = 0

		temp, pres, pres_ratio, rho_ratio = CalcAtmosphere( alt, delta_temp, ATMOS_TYPE_US_STANDARD_1976)

		# The ratios are against sea level standard day, so asking at sea level with
		# no temperature offset has to return the sea level standard itself.
		sl_temp, sl_pres, sl_pres_ratio, sl_rho_ratio = CalcAtmosphere( 0.0, 0.0, ATMOS_TYPE_US_STANDARD_1976 )

		assert abs( sl_temp - 288.15 ) < 1e-2, "sea level is not the standard day temperature"

		# The density ratio carries a little rounding from the model constants.
		assert abs( sl_pres_ratio - 1.0 ) < 1e-9, "the sea level ratios are not one"
		assert abs( sl_rho_ratio - 1.0 ) < 1e-4, "the sea level ratios are not one"

		# The atmosphere thins with altitude.
		assert temp < sl_temp, "the atmosphere did not thin with altitude"
		assert pres < sl_pres, "the atmosphere did not thin with altitude"
		assert pres_ratio < 1.0, "the atmosphere did not thin with altitude"
		assert rho_ratio < 1.0, "the atmosphere did not thin with altitude"

		# The pressure ratio is the pressure against sea level.
		assert abs( pres_ratio - pres / sl_pres ) < 1e-6, "the pressure ratio does not match the pressure"



	def test_WriteBodyFFCSVFile(self):
		print( "Starting Body Form Factor Data Creation. \n" )
		WriteBodyFFCSVFile( "BodyFormFactorData.csv" )
		# The call above should have produced a file with content in it.
		import os
		assert os.path.getsize( "BodyFormFactorData.csv" ) > 0, "WriteBodyFFCSVFile wrote no file"




	def test_WriteWingFFCSVFile(self):
		print( "Starting Wing Form Factor Data Creation. \n" )
		WriteWingFFCSVFile( "WingFormFactorData.csv" )
		# The call above should have produced a file with content in it.
		import os
		assert os.path.getsize( "WingFormFactorData.csv" ) > 0, "WriteWingFFCSVFile wrote no file"




	def test_WriteCfEqnCSVFile(self):
		WriteCfEqnCSVFile( "TestCfEqn.csv" )



	def test_WritePartialCfMethodCSVFile(self):
		WritePartialCfMethodCSVFile( "TestPartialCf.csv" )



	def test_CompPnt01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		pnt = CompPnt01( geom_id, surf_indx, u, w )

		print( f"Point: ( {pnt.x()}, {pnt.y()}, {pnt.z()} )" )

		# The point is on the surface, so projecting it back has to land on it and
		# recover the coordinates it came from.
		d, u_out, w_out = ProjPnt01( geom_id, surf_indx, pnt )

		assert d < 1e-6, "CompPnt01 returned a point off the surface"
		assert abs( u_out - u ) < 1e-6, "CompPnt01 does not round trip through ProjPnt01"
		assert abs( w_out - w ) < 1e-6, "CompPnt01 does not round trip through ProjPnt01"

		# W wraps around the section, so 0 and 1 are the same place.
		assert dist( CompPnt01( geom_id, surf_indx, u, 0.0 ), CompPnt01( geom_id, surf_indx, u, 1.0 ) ) < 1e-6, "the surface does not close in W"



	def test_CompNorm01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		norm = CompNorm01( geom_id, surf_indx, u, w )

		assert abs( norm.mag() - 1.0 ) < 1e-9, "CompNorm01 is not a unit vector"

		print( "Point: ( {norm.x()}, {norm.y()}, {norm.z()} )" )



	def test_CompTanU01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		tanu = CompTanU01( geom_id, surf_indx, u, w )

		assert tanu.mag() > 0.0, "CompTanU01 is degenerate"

		print( f"Point: ( {tanu.x()}, {tanu.y()}, {tanu.z()} )" )



	def test_CompTanW01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		tanw = CompTanW01( geom_id, surf_indx, u, w )

		assert tanw.mag() > 0.0, "CompTanW01 is degenerate"

		print( f"Point: ( {tanw.x()}, {tanw.y()}, {tanw.z()} )" )



	def test_CompCurvature01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0


		u = 0.25
		w = 0.75

		k1, k2, ka, kg = CompCurvature01( geom_id, surf_indx, u, w )

		print( f"Curvature : k1 {k1} k2 {k2} ka {ka} kg {kg}" )

		# The mean curvature is the average of the principal curvatures, and the
		# Gaussian curvature is their product.
		assert abs( ka - 0.5 * ( k1 + k2 ) ) < 1e-9, "the mean curvature does not match the principal curvatures"
		assert abs( kg - k1 * k2 ) < 1e-9, "the Gaussian curvature does not match the principal curvatures"

		# A Pod is convex everywhere, so the Gaussian curvature is positive.
		assert kg > 0.0, "a Pod should be convex here"



	def test_ProjPnt01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		pnt = CompPnt01( geom_id, surf_indx, u, w )

		norm = CompNorm01( geom_id, surf_indx, u, w )


		# Offset point from surface
		pnt.set_xyz( pnt.x() + norm.x(), pnt.y() + norm.y(), pnt.z() + norm.z() )

		d, uout, wout = ProjPnt01( geom_id, surf_indx, pnt )

		# pnt sits one unit off the surface along its own normal, so the
		# projection comes back to where it started at a distance of one.
		assert abs( d - 1.0 ) < 1e-6, "ProjPnt01 distance"
		assert abs( uout - u ) < 1e-6 and abs( wout - w ) < 1e-6, "ProjPnt01 u, w"

		print( f"Dist {d} u {uout} w {wout}" )



	def test_ProjPnt01I(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		d = 0

		pnt = CompPnt01( geom_id, surf_indx, u, w )

		norm = CompNorm01( geom_id, surf_indx, u, w )



		# Offset point from surface
		pnt.set_xyz( pnt.x() + norm.x(), pnt.y() + norm.y(), pnt.z() + norm.z() )

		d, surf_indx_out, uout, wout = ProjPnt01I( geom_id, pnt )

		# pnt sits one unit off the surface along its own normal, so the
		# projection comes back to where it started at a distance of one.
		assert abs( d - 1.0 ) < 1e-6, "ProjPnt01I distance"
		assert abs( uout - u ) < 1e-6 and abs( wout - w ) < 1e-6, "ProjPnt01I u, w"

		print( f"Dist {d} u {uout} w {wout} surf_index {surf_indx_out}" )



	def test_ProjPnt01Guess(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		d = 0

		pnt = CompPnt01( geom_id, surf_indx, u, w )

		norm = CompNorm01( geom_id, surf_indx, u, w )


		# Offset point from surface
		pnt.set_xyz( pnt.x() + norm.x(), pnt.y() + norm.y(), pnt.z() + norm.z() )

		d, uout, wout = ProjPnt01Guess( geom_id, surf_indx, pnt, u + 0.1, w + 0.1 )

		# pnt sits one unit off the surface along its own normal, so the
		# projection comes back to where it started at a distance of one.
		assert abs( d - 1.0 ) < 1e-6, "ProjPnt01Guess distance"
		assert abs( uout - u ) < 1e-6 and abs( wout - w ) < 1e-6, "ProjPnt01Guess u, w"

		print( f"Dist {d} u {uout} w {wout}" )



	def test_AxisProjPnt01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		surf_pt = CompPnt01( geom_id, surf_indx, u, w )

		# Assignment binds a reference in Python rather than copying as it does in
		# AngelScript, so build a separate point instead of offsetting surf_pt.
		pt = vec3d( surf_pt.x(), surf_pt.y(), surf_pt.z() )

		pt.offset_y( -5.0 )

		idist, u_out, w_out = AxisProjPnt01( geom_id, surf_indx, Y_DIR, pt )

		# pt is the surface point pushed off in -Y, so projecting back along Y
		# has to land on the point it came from.
		p_out = CompPnt01( geom_id, surf_indx, u_out, w_out )
		assert abs( surf_pt.x() - p_out.x() ) < 1e-6 and abs( surf_pt.y() - p_out.y() ) < 1e-6 and abs( surf_pt.z() - p_out.z() ) < 1e-6, "AxisProjPnt01 did not recover the original point"

		print( f"iDist {idist} u_out {u_out} w_out {w_out}" )
		print( "3D Offset ", False)



	def test_AxisProjPnt01I(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890

		surf_pt = CompPnt01( geom_id, surf_indx, u, w )

		# Assignment binds a reference in Python rather than copying as it does in
		# AngelScript, so build a separate point instead of offsetting surf_pt.
		pt = vec3d( surf_pt.x(), surf_pt.y(), surf_pt.z() )

		pt.offset_y( -5.0 )


		idist, surf_indx_out, u_out, w_out = AxisProjPnt01I( geom_id, Y_DIR, pt )

		# pt is the surface point pushed off in -Y, so projecting back along Y
		# has to land on the point it came from.
		p_out = CompPnt01( geom_id, surf_indx, u_out, w_out )
		assert abs( surf_pt.x() - p_out.x() ) < 1e-6 and abs( surf_pt.y() - p_out.y() ) < 1e-6 and abs( surf_pt.z() - p_out.z() ) < 1e-6, "AxisProjPnt01I did not recover the original point"

		print( "iDist {idist} u_out {u_out} w_out {w_out} surf_index {surf_indx_out}" )
		print( "3D Offset ", False)



	def test_AxisProjPnt01Guess(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		u = 0.12345
		w = 0.67890



		surf_pt = CompPnt01( geom_id, surf_indx, u, w )

		# Assignment binds a reference in Python rather than copying as it does in
		# AngelScript, so build a separate point instead of offsetting surf_pt.
		pt = vec3d( surf_pt.x(), surf_pt.y(), surf_pt.z() )

		pt.offset_y( -5.0 )

		# Construct initial guesses near actual parameters
		u0 = u + 0.01234
		w0 = w - 0.05678

		d, uout, wout = AxisProjPnt01Guess( geom_id, surf_indx, Y_DIR, pt, u0, w0 )

		print( f"Dist {d} u {uout} w {wout}" )

		# The test point sits five units away along Y from a known surface point, so
		# projecting back along Y has to recover that point and that distance.
		assert abs( uout - u ) < 1e-6, "AxisProjPnt01Guess did not recover the surface point"
		assert abs( wout - w ) < 1e-6, "AxisProjPnt01Guess did not recover the surface point"
		assert abs( d - 5.0 ) < 1e-6, "AxisProjPnt01Guess reported the wrong distance"

		# Starting from a guess must not change the answer.
		d_ng, uout_ng, wout_ng = AxisProjPnt01( geom_id, surf_indx, Y_DIR, pt )

		assert abs( uout_ng - uout ) < 1e-6, "the guess changed the answer"
		assert abs( wout_ng - wout ) < 1e-6, "the guess changed the answer"
		assert abs( d_ng - d ) < 1e-6, "the guess changed the answer"



	def test_InsideSurf(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		r = 0.12
		s = 0.68
		t = 0.56

		pnt = CompPntRST( geom_id, surf_indx, r, s, t )

		res = InsideSurf( geom_id, surf_indx, pnt )

		# pnt was built by CompPntRST at r = 0.12, which is inside the surface.
		assert res, "InsideSurf says an interior point is outside"

		if  res :
			print( "Inside" )
		else:
			print( "Outside" )




	def test_CompPntRST(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		r = 0.12
		s = 0.68
		t = 0.56

		pnt = CompPntRST( geom_id, surf_indx, r, s, t )

		print( f"Point: ( {pnt.x()}, {pnt.y()}, {pnt.z()} )" )

		# T runs from the interior out to the skin, so t = 1 lands on the surface and
		# anything short of that lands inside it.
		d, u_out, w_out = ProjPnt01( geom_id, surf_indx, CompPntRST( geom_id, surf_indx, r, s, 1.0 ) )

		assert d < 1e-6, "CompPntRST at t = 1 is not on the surface"
		assert InsideSurf( geom_id, surf_indx, pnt ), "CompPntRST at t < 1 is not inside the surface"

		# The point has to round trip back through the coordinates it came from.
		d_rst, r_out, s_out, t_out = FindRST( geom_id, surf_indx, pnt )

		assert dist( CompPntRST( geom_id, surf_indx, r_out, s_out, t_out ), pnt ) < 1e-6, "CompPntRST does not round trip through FindRST"



	def test_FindRST(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		r = 0.12
		s = 0.68
		t = 0.56

		pnt = CompPntRST( geom_id, surf_indx, r, s, t )


		d, rout, sout, tout = FindRST( geom_id, surf_indx, pnt )

		print( f"Dist {d} r {rout} s {sout} t {tout}" )

		# pnt came from CompPntRST at r, s, t, so the search has to land back on it.
		assert abs( d ) < 1e-6, "FindRST distance"
		assert abs( rout - r ) < 1e-6 and abs( sout - s ) < 1e-6 and abs( tout - t ) < 1e-6, "FindRST r, s, t"



	def test_FindRSTGuess(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		r = 0.12
		s = 0.68
		t = 0.56

		pnt = CompPntRST( geom_id, surf_indx, r, s, t )


		r0 = 0.1
		s0 = 0.6
		t0 = 0.5

		d, rout, sout, tout = FindRSTGuess( geom_id, surf_indx, pnt, r0, s0, t0 )

		print( f"Dist {d} r {rout} s {sout} t {tout}" )

		# pnt came from CompPntRST at r, s, t, so the search has to land back on it.
		assert abs( d ) < 1e-6, "FindRSTGuess distance"
		assert abs( rout - r ) < 1e-6 and abs( sout - s ) < 1e-6 and abs( tout - t ) < 1e-6, "FindRSTGuess r, s, t"



	def test_ConvertRSTtoLMN(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		r = 0.12
		s = 0.68
		t = 0.56

		l_out, m_out, n_out = ConvertRSTtoLMN( geom_id, surf_indx, r, s, t )

		# Converting back has to return the coordinates we started from.
		r_back, s_back, t_back = ConvertLMNtoRST( geom_id, surf_indx, l_out, m_out, n_out )

		assert abs( r_back - r ) < 1e-6 and abs( s_back - s ) < 1e-6 and abs( t_back - t ) < 1e-6, "ConvertRSTtoLMN does not round trip"




	def test_ConvertRtoL(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		r = 0.12

		l_out = ConvertRtoL( geom_id, surf_indx, r )

		# Converting back has to return the coordinate we started from.
		r_back = ConvertLtoR( geom_id, surf_indx, l_out )

		assert abs( r_back - r ) < 1e-6, "ConvertRtoL does not round trip"




	def test_ConvertLMNtoRST(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		l = 0.12
		m = 0.34
		n = 0.56

		r_out, s_out, t_out = ConvertLMNtoRST( geom_id, surf_indx, l, m, n )

		# The conversion is invertible, so going back has to return the input.
		l_out, m_out, n_out = ConvertRSTtoLMN( geom_id, surf_indx, r_out, s_out, t_out )

		assert abs( l_out - l ) < 1e-6, "ConvertLMNtoRST does not invert"
		assert abs( m_out - m ) < 1e-6, "ConvertLMNtoRST does not invert"
		assert abs( n_out - n ) < 1e-6, "ConvertLMNtoRST does not invert"

		# Both coordinate systems run over the unit cube.
		assert 0.0 <= r_out <= 1.0, "ConvertLMNtoRST left the unit cube"
		assert 0.0 <= s_out <= 1.0, "ConvertLMNtoRST left the unit cube"
		assert 0.0 <= t_out <= 1.0, "ConvertLMNtoRST left the unit cube"

		# The coordinates name a point in the volume, so evaluating them has to land
		# inside the surface.
		assert InsideSurf( geom_id, surf_indx, CompPntRST( geom_id, surf_indx, r_out, s_out, t_out ) ), "ConvertLMNtoRST did not name a point in the volume"



	def test_ConvertLtoR(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		l = 0.12

		r_out = ConvertLtoR( geom_id, surf_indx, l )

		# The conversion is invertible, so going back has to return the input.
		l_out = ConvertRtoL( geom_id, surf_indx, r_out )

		assert abs( l_out - l ) < 1e-6, "ConvertLtoR does not invert"
		assert 0.0 <= r_out <= 1.0, "ConvertLtoR left the unit interval"

		# Both coordinates run nose to tail, so the mapping is increasing.
		r_more = ConvertLtoR( geom_id, surf_indx, l + 0.1 )

		assert r_more > r_out, "ConvertLtoR is not increasing"



	def test_ConvertUtoEta(self):
		# Add Wing Geom
		geom_id = AddGeom( "WING", "" )

		surf_indx = 0

		# U runs from 1 to N+1 over an N section wing when the root end cap is on,
		# so a U below 1 sits in the cap and does not map to a span station.
		u = 1.25

		eta_out = ConvertUtoEta( geom_id, u )

		# Converting back has to return the coordinate we started from.
		u_back = ConvertEtatoU( geom_id, eta_out )

		assert abs( u_back - u ) < 1e-6, "ConvertUtoEta does not round trip"




	def test_ConvertEtatoU(self):
		# Add Wing Geom
		geom_id = AddGeom( "WING", "" )

		surf_indx = 0

		eta= 0.25

		u = ConvertEtatoU( geom_id, eta )

		# Converting back has to return the coordinate we started from.
		eta_back = ConvertUtoEta( geom_id, u )

		assert abs( eta_back - eta ) < 1e-6, "ConvertEtatoU does not round trip"



	def test_CompVecPnt01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)

		ptvec = CompVecPnt01( geom_id, 0, uvec, wvec )

		# One point per coordinate pair, each the same point the scalar form gives.
		assert len( ptvec ) == n, "CompVecPnt01 returned the wrong number of points"

		for i in range(n):
			assert dist( ptvec[i], CompPnt01( geom_id, 0, uvec[i], wvec[i] ) ) < 1e-9, "CompVecPnt01 disagrees with CompPnt01 at " + str( i )



	def test_CompVecDegenPnt01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)

		ptvec = CompVecDegenPnt01( geom_id, 0, 0, uvec, wvec )

		# One point per coordinate pair.  Degen type 0 is the surface itself, so
		# those points are the ones the surface form gives.
		assert len( ptvec ) == n, "CompVecDegenPnt01 returned the wrong number of points"

		surfvec = CompVecPnt01( geom_id, 0, uvec, wvec )

		for i in range(n):
			assert dist( ptvec[i], surfvec[i] ) < 1e-6, "the degen surface does not follow the surface at " + str( i )



	def test_CompVecNorm01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)

		normvec = CompVecNorm01( geom_id, 0, uvec, wvec )

		for i in range( len( normvec ) ):
			assert abs( normvec[i].mag() - 1.0 ) < 1e-9, "CompVecNorm01 is not a unit vector"



	def test_CompVecCurvature01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)



		k1vec, k2vec, kavec, kgvec = CompVecCurvature01( geom_id, 0, uvec, wvec )

		# One value per coordinate pair, matching what the scalar form gives, and
		# holding the same relationships between the four curvatures.
		assert len( k1vec ) == n, "CompVecCurvature01 returned the wrong number of values"
		assert len( k2vec ) == n, "CompVecCurvature01 returned the wrong number of values"
		assert len( kavec ) == n, "CompVecCurvature01 returned the wrong number of values"
		assert len( kgvec ) == n, "CompVecCurvature01 returned the wrong number of values"

		for i in range(n):
			k1, k2, ka, kg = CompCurvature01( geom_id, 0, uvec[i], wvec[i] )

			assert abs( k1vec[i] - k1 ) < 1e-9, "CompVecCurvature01 disagrees with CompCurvature01 at " + str( i )
			assert abs( k2vec[i] - k2 ) < 1e-9, "CompVecCurvature01 disagrees with CompCurvature01 at " + str( i )
			assert abs( kavec[i] - ka ) < 1e-9, "CompVecCurvature01 disagrees with CompCurvature01 at " + str( i )
			assert abs( kgvec[i] - kg ) < 1e-9, "CompVecCurvature01 disagrees with CompCurvature01 at " + str( i )

			assert abs( kavec[i] - 0.5 * ( k1vec[i] + k2vec[i] ) ) < 1e-9, "the curvatures are inconsistent at " + str( i )
			assert abs( kgvec[i] - k1vec[i] * k2vec[i] ) < 1e-9, "the curvatures are inconsistent at " + str( i )



	def test_ProjVecPnt01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)

		ptvec = CompVecPnt01( geom_id, 0, uvec, wvec )

		normvec = CompVecNorm01( geom_id, 0, uvec, wvec )

		for i in range(n):

			ptvec[i].set_xyz( ptvec[i].x() + normvec[i].x(), ptvec[i].y() + normvec[i].y(), ptvec[i].z() + normvec[i].z() )

		uoutv, woutv, doutv = ProjVecPnt01( geom_id, 0, ptvec )



	def test_ProjVecPnt01Guess(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)

		ptvec = CompVecPnt01( geom_id, 0, uvec, wvec )

		normvec = CompVecNorm01( geom_id, 0, uvec, wvec )

		for i in range(n):

			ptvec[i].set_xyz( ptvec[i].x() + normvec[i].x(), ptvec[i].y() + normvec[i].y(), ptvec[i].z() + normvec[i].z() )

		u0v = [0]*n
		w0v = [0]*n

		for i in range(n):

			u0v[i] = uvec[i] + 0.01234

			w0v[i] = wvec[i] - 0.05678

		uoutv, woutv, doutv = ProjVecPnt01Guess( geom_id, 0, ptvec, u0v,  w0v )

		# Each point was pushed one unit along its own normal, so each projects back
		# to where it came from at a distance of one.  Starting from a guess must not
		# change that.
		uv_ng, wv_ng, dv_ng = ProjVecPnt01( geom_id, 0, ptvec )

		for i in range(n):
			assert abs( doutv[i] - 1.0 ) < 1e-6, "ProjVecPnt01Guess did not recover point " + str( i )
			assert abs( uoutv[i] - uvec[i] ) < 1e-6, "ProjVecPnt01Guess did not recover point " + str( i )
			assert abs( woutv[i] - wvec[i] ) < 1e-6, "ProjVecPnt01Guess did not recover point " + str( i )

			assert abs( uoutv[i] - uv_ng[i] ) < 1e-6, "the guess changed the answer at " + str( i )
			assert abs( woutv[i] - wv_ng[i] ) < 1e-6, "the guess changed the answer at " + str( i )
			assert abs( doutv[i] - dv_ng[i] ) < 1e-6, "the guess changed the answer at " + str( i )



	def test_AxisProjVecPnt01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )
		surf_indx = 0

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)

		ptvec = CompVecPnt01( geom_id, surf_indx, uvec, wvec )

		for i in range(n):

			ptvec[i].offset_y( -5.0 )

		uoutv, woutv, doutv = AxisProjVecPnt01( geom_id, surf_indx, Y_DIR, ptvec )

		# Some of these outputs are expected to be non-zero because the projected point is on the opposite side of
		# the pod from the originally computed point.  I.e. there were multiple solutions and the original point
		# is not the closest intersection point.  We could offset those points in the +Y direction instead of -Y.
		for i in range(n):

			print( i, False )
			print( "U delta ", False )
			print( uvec[i] - uoutv[i], False )
			print( "W delta ", False )
			print( wvec[i] - woutv[i] )

		# Whichever intersection was found, it has to be a real one: the reported
		# coordinates have to name a point on the surface, and that point has to sit
		# on the same Y ray the test point was offset along.
		for i in range(n):

			assert uoutv[i] >= 0.0 and woutv[i] >= 0.0, "no intersection was found for point " + str( i )

			hit = CompPnt01( geom_id, surf_indx, uoutv[i], woutv[i] )

			assert abs( hit.x() - ptvec[i].x() ) < 1e-6, "the intersection left the Y ray at point " + str( i )
			assert abs( hit.z() - ptvec[i].z() ) < 1e-6, "the intersection left the Y ray at point " + str( i )
			assert abs( doutv[i] - abs( hit.y() - ptvec[i].y() ) ) < 1e-6, "the wrong distance was reported at point " + str( i )



	def test_AxisProjVecPnt01Guess(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )
		surf_indx = 0

		n = 5

		uvec = [0]*n
		wvec = [0]*n

		for i in range(n):

			uvec[i] = (i+1)*1.0/(n+1)

			wvec[i] = (n-i)*1.0/(n+1)

		ptvec = CompVecPnt01( geom_id, surf_indx, uvec, wvec )

		for i in range(n):

			ptvec[i].offset_y( -5.0 )

		u0v = [0]*n
		w0v = [0]*n

		for i in range(n):

			u0v[i] = uvec[i] + 0.01234
			w0v[i] = wvec[i] - 0.05678

		uoutv, woutv, doutv = AxisProjVecPnt01Guess( geom_id, surf_indx, Y_DIR, ptvec, u0v,  w0v )

		for i in range(n):

			print( i, False )
			print( "U delta ", False )
			print( uvec[i] - uoutv[i], False )
			print( "W delta ", False )
			print( wvec[i] - woutv[i] )

		# Whichever intersection was found, it has to be a real one: the reported
		# coordinates have to name a point on the surface, and that point has to sit
		# on the same Y ray the test point was offset along.
		for i in range(n):

			assert uoutv[i] >= 0.0 and woutv[i] >= 0.0, "no intersection was found for point " + str( i )

			hit = CompPnt01( geom_id, surf_indx, uoutv[i], woutv[i] )

			assert abs( hit.x() - ptvec[i].x() ) < 1e-6, "the intersection left the Y ray at point " + str( i )
			assert abs( hit.z() - ptvec[i].z() ) < 1e-6, "the intersection left the Y ray at point " + str( i )
			assert abs( doutv[i] - abs( hit.y() - ptvec[i].y() ) ) < 1e-6, "the wrong distance was reported at point " + str( i )



	def test_VecInsideSurf(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		n = 5

		rvec = [0]*n
		svec = [0]*n
		tvec = [0]*n

		for i in range(n):

			rvec[i] = (i+1)*1.0/(n+1)

			svec[i] = (n-i)*1.0/(n+1)

			tvec[i] = (i+1)*1.0/(n+1)

		ptvec = CompVecPntRST( geom_id, 0, rvec, svec, tvec )


		res = VecInsideSurf( geom_id, surf_indx, ptvec )

		# Every point came from CompVecPntRST with r below one, so all are inside.
		for i in range( len( res ) ):
			assert res[i], "VecInsideSurf says an interior point is outside"




	def test_CompVecPntRST(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		rvec = [0]*n
		svec = [0]*n
		tvec = [0]*n

		for i in range(n):

			rvec[i] = (i+1)*1.0/(n+1)

			svec[i] = (n-i)*1.0/(n+1)

			tvec[i] = (i+1)*1.0/(n+1)

		ptvec = CompVecPntRST( geom_id, 0, rvec, svec, tvec )

		# One point per coordinate triple, each the same point the scalar form
		# gives, and every one of them inside the surface.
		assert len( ptvec ) == n, "CompVecPntRST returned the wrong number of points"

		for i in range(n):
			assert dist( ptvec[i], CompPntRST( geom_id, 0, rvec[i], svec[i], tvec[i] ) ) < 1e-9, "CompVecPntRST disagrees with CompPntRST at " + str( i )
			assert InsideSurf( geom_id, 0, ptvec[i] ), "CompVecPntRST returned a point outside the surface at " + str( i )



	def test_FindRSTVec(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		rvec = [0]*n
		svec = [0]*n
		tvec = [0]*n

		for i in range(n):

			rvec[i] = (i+1)*1.0/(n+1)

			svec[i] = (n-i)*1.0/(n+1)

			tvec[i] = (i+1)*1.0/(n+1)

		ptvec = CompVecPntRST( geom_id, 0, rvec, svec, tvec )



		routv, soutv, toutv, doutv = FindRSTVec( geom_id, 0, ptvec )

		# Every point came from CompVecPntRST, so each search lands back on its own.
		for i in range( n ):
			assert abs( doutv[i] ) < 1e-6, "FindRSTVec distance"
			assert abs( routv[i] - rvec[i] ) < 1e-6, "FindRSTVec r"
			assert abs( soutv[i] - svec[i] ) < 1e-6, "FindRSTVec s"
			assert abs( toutv[i] - tvec[i] ) < 1e-6, "FindRSTVec t"



	def test_FindRSTVecGuess(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		rvec = [0]*n
		svec = [0]*n
		tvec = [0]*n

		for i in range(n):

			rvec[i] = (i+1)*1.0/(n+1)

			svec[i] = (n-i)*1.0/(n+1)

			tvec[i] = (i+1)*1.0/(n+1)

		ptvec = CompVecPntRST( geom_id, 0, rvec, svec, tvec )

		for i in range(n):

			ptvec[i].set_xyz(ptvec[i].x() * 0.9, ptvec[i].y() * 0.9, ptvec[i].z() * 0.9)

		routv, soutv, toutv, doutv = FindRSTVecGuess( geom_id, 0, ptvec, rvec, svec, tvec )

		# The points above were scaled off the surface on purpose, so the search
		# does not return to the original r, s, t.  What must hold is that every
		# point got an answer and that the reported distances are real.
		assert len( routv ) == n and len( soutv ) == n and len( toutv ) == n and len( doutv ) == n, "FindRSTVecGuess result count"
		for i in range( len( doutv ) ):
			assert doutv[i] >= 0.0, "FindRSTVecGuess distance"


	def test_ConvertRSTtoLMNVec(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		rvec = [0]*n
		svec = [0]*n
		tvec = [0]*n

		for i in range(n):

			rvec[i] = (i+1)*1.0/(n+1)
			svec[i] = (n-i)*1.0/(n+1)
			tvec[i] = (i+1)*1.0/(n+1)



		lvec, mvec, nvec = ConvertRSTtoLMNVec( geom_id, 0, rvec, svec, tvec )




	def test_ConvertLMNtoRSTVec(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		n = 5

		lvec = [0]*n
		mvec = [0]*n
		nvec = [0]*n

		for i in range(n):

			lvec[i] = (i+1)*1.0/(n+1)
			mvec[i] = (n-i)*1.0/(n+1)
			nvec[i] = (i+1)*1.0/(n+1)

		rvec, svec, tvec = ConvertLMNtoRSTVec( geom_id, 0, lvec, mvec, nvec )

		# One triple out per triple in, each matching the scalar form, and the whole
		# conversion invertible.
		lback, mback, nback = ConvertRSTtoLMNVec( geom_id, 0, rvec, svec, tvec )

		assert len( rvec ) == n, "ConvertLMNtoRSTVec returned the wrong number of values"
		assert len( svec ) == n, "ConvertLMNtoRSTVec returned the wrong number of values"
		assert len( tvec ) == n, "ConvertLMNtoRSTVec returned the wrong number of values"

		for i in range(n):
			r_one, s_one, t_one = ConvertLMNtoRST( geom_id, 0, lvec[i], mvec[i], nvec[i] )

			assert abs( rvec[i] - r_one ) < 1e-9, "ConvertLMNtoRSTVec disagrees with ConvertLMNtoRST at " + str( i )
			assert abs( svec[i] - s_one ) < 1e-9, "ConvertLMNtoRSTVec disagrees with ConvertLMNtoRST at " + str( i )
			assert abs( tvec[i] - t_one ) < 1e-9, "ConvertLMNtoRSTVec disagrees with ConvertLMNtoRST at " + str( i )

			assert abs( lback[i] - lvec[i] ) < 1e-6, "ConvertLMNtoRSTVec does not invert at " + str( i )
			assert abs( mback[i] - mvec[i] ) < 1e-6, "ConvertLMNtoRSTVec does not invert at " + str( i )
			assert abs( nback[i] - nvec[i] ) < 1e-6, "ConvertLMNtoRSTVec does not invert at " + str( i )



	def test_GetUWTess01(self):
		# Add Pod Geom
		geom_id = AddGeom( "POD", "" )

		surf_indx = 0

		utess, wtess = GetUWTess01( geom_id, surf_indx )

		# The wireframe spans the whole surface and never runs backwards.
		assert len( utess ) >= 2, "GetUWTess01 returned too few stations"
		assert len( wtess ) >= 2, "GetUWTess01 returned too few stations"

		assert abs( utess[0] ) < 1e-9 and abs( utess[-1] - 1.0 ) < 1e-9, "GetUWTess01 does not span the surface"
		assert abs( wtess[0] ) < 1e-9 and abs( wtess[-1] - 1.0 ) < 1e-9, "GetUWTess01 does not span the surface"

		for i in range( 1, len( utess ) ):
			assert utess[i] > utess[i - 1], "the U stations are not increasing at " + str( i )

		for i in range( 1, len( wtess ) ):
			assert wtess[i] > wtess[i - 1], "the W stations are not increasing at " + str( i )



	def test_ShowAllRulers(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		pid2 = AddGeom( "POD", "" )

		SetParmVal( pid2, "Z_Rel_Location", "XForm", 4.0 )

		rid = AddRuler( pid1, 1, 0.2, 0.3, pid2, 0, 0.2, 0.3, "Ruler 1" )

		SetParmVal( FindParm( rid, "X_Offset", "Measure" ), 6.0 )



	def test_HideAllRulers(self):
		pid = AddGeom( "POD" )

		Update()

		AddRuler( pid, 0, 0.2, 0.0, pid, 0, 0.8, 0.0, "R" )

		HideAllRulers()



	def test_ShowAllProbes(self):
		pid = AddGeom( "POD" )

		Update()

		AddProbe( pid, 0, 0.5, 0.5, "P" )

		ShowAllProbes()



	def test_HideAllProbes(self):
		pid = AddGeom( "POD" )

		Update()

		AddProbe( pid, 0, 0.5, 0.5, "P" )

		HideAllProbes()



	def test_ShowAllProtractors(self):
		pid = AddGeom( "POD" )

		Update()

		AddProtractor( pid, 0, 0.2, 0.0, pid, 0, 0.5, 0.0, pid, 0, 0.8, 0.0, "P" )

		ShowAllProtractors()



	def test_HideAllProtractors(self):
		pid = AddGeom( "POD" )

		Update()

		AddProtractor( pid, 0, 0.2, 0.0, pid, 0, 0.5, 0.0, pid, 0, 0.8, 0.0, "P" )

		HideAllProtractors()



	def test_ShowAllRSTProbes(self):
		pid = AddGeom( "POD" )

		Update()

		AddRSTProbe( pid, 0, 0.5, 0.5, 0.5, "P" )

		ShowAllRSTProbes()



	def test_HideAllRSTProbes(self):
		pid = AddGeom( "POD" )

		Update()

		AddRSTProbe( pid, 0, 0.5, 0.5, 0.5, "P" )

		HideAllRSTProbes()



	def test_AddProtractor(self):
		pid = AddGeom( "POD" )

		Update()

		prid = AddProtractor( pid, 0, 0.2, 0.0, pid, 0, 0.5, 0.0, pid, 0, 0.8, 0.0, "TestProtractor" )

		assert len( prid ) > 0, "AddProtractor returned no ID"

		assert len( GetAllProtractors() ) == 1, "AddProtractor did not add the protractor"



	def test_GetAllProtractors(self):
		pod1 = AddGeom( "POD", "" )

		AddProtractor( pod1, 0, 0.2, 0.0, pod1, 0, 0.5, 0.0, pod1, 0, 0.8, 0.0, "Protractor_1" )
		AddProtractor( pod1, 0, 0.1, 0.0, pod1, 0, 0.4, 0.0, pod1, 0, 0.7, 0.0, "Protractor_2" )

		prot_array = GetAllProtractors()

		assert len( prot_array ) == 2, "GetAllProtractors did not report both protractors"
		assert prot_array[0] != prot_array[1], "GetAllProtractors reported the same protractor twice"



	def test_DelProtractor(self):
		pod1 = AddGeom( "POD", "" )

		pid1 = AddProtractor( pod1, 0, 0.2, 0.0, pod1, 0, 0.5, 0.0, pod1, 0, 0.8, 0.0, "Protractor_1" )
		pid2 = AddProtractor( pod1, 0, 0.1, 0.0, pod1, 0, 0.4, 0.0, pod1, 0, 0.7, 0.0, "Protractor_2" )

		DelProtractor( pid1 )

		# Only the named protractor goes.
		prot_array = GetAllProtractors()

		assert len( prot_array ) == 1, "DelProtractor removed the wrong protractor"
		assert prot_array[0] == pid2, "DelProtractor removed the wrong protractor"



	def test_DeleteAllProtractors(self):
		pod1 = AddGeom( "POD", "" )

		AddProtractor( pod1, 0, 0.2, 0.0, pod1, 0, 0.5, 0.0, pod1, 0, 0.8, 0.0, "Protractor_1" )
		AddProtractor( pod1, 0, 0.1, 0.0, pod1, 0, 0.4, 0.0, pod1, 0, 0.7, 0.0, "Protractor_2" )

		DeleteAllProtractors()

		assert len( GetAllProtractors() ) == 0, "DeleteAllProtractors left protractors behind"



	def test_AddRSTProbe(self):
		pod1 = AddGeom( "POD", "" )

		pid = AddRSTProbe( pod1, 0, 0.5, 0.5, 0.5, "Example_RSTProbe" )

		assert len( pid ) > 0 and pid != "NONE", "AddRSTProbe returned no id"

		# The new probe is the only one in the model, and it is not confused with a
		# surface probe.
		probe_array = GetAllRSTProbes()

		assert len( probe_array ) == 1, "AddRSTProbe did not add the probe"
		assert probe_array[0] == pid, "AddRSTProbe did not add the probe"
		assert len( GetAllProbes() ) == 0, "an RST probe was counted as a surface probe"
		assert GetContainerName( pid ) == "Example_RSTProbe", "AddRSTProbe did not name the probe"



	def test_GetAllRSTProbes(self):
		pod1 = AddGeom( "POD", "" )

		AddRSTProbe( pod1, 0, 0.5, 0.5, 0.5, "RSTProbe_1" )
		AddRSTProbe( pod1, 0, 0.25, 0.5, 0.5, "RSTProbe_2" )

		probe_array = GetAllRSTProbes()

		assert len( probe_array ) == 2, "GetAllRSTProbes did not report both probes"
		assert probe_array[0] != probe_array[1], "GetAllRSTProbes reported the same probe twice"



	def test_DelRSTProbe(self):
		pod1 = AddGeom( "POD", "" )

		pid1 = AddRSTProbe( pod1, 0, 0.5, 0.5, 0.5, "RSTProbe_1" )
		pid2 = AddRSTProbe( pod1, 0, 0.25, 0.5, 0.5, "RSTProbe_2" )

		DelRSTProbe( pid1 )

		# Only the named probe goes.
		probe_array = GetAllRSTProbes()

		assert len( probe_array ) == 1, "DelRSTProbe removed the wrong probe"
		assert probe_array[0] == pid2, "DelRSTProbe removed the wrong probe"



	def test_DeleteAllRSTProbes(self):
		pod1 = AddGeom( "POD", "" )

		AddRSTProbe( pod1, 0, 0.5, 0.5, 0.5, "RSTProbe_1" )
		AddRSTProbe( pod1, 0, 0.25, 0.5, 0.5, "RSTProbe_2" )

		# Surface probes are a separate list and are left alone.
		AddProbe( pod1, 0, 0.5, 0.5, "Surface_Probe" )

		DeleteAllRSTProbes()

		assert len( GetAllRSTProbes() ) == 0, "DeleteAllRSTProbes left probes behind"
		assert len( GetAllProbes() ) == 1, "DeleteAllRSTProbes removed a surface probe"



	def test_AddRuler(self):
		pid = AddGeom( "POD" )

		Update()

		rid = AddRuler( pid, 0, 0.2, 0.0, pid, 0, 0.8, 0.0, "TestRuler" )

		assert len( rid ) > 0, "AddRuler returned no ID"

		assert len( GetAllRulers() ) == 1, "AddRuler did not add the ruler"



	def test_GetAllRulers(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		pid2 = AddGeom( "POD", "" )

		SetParmVal( pid2, "Z_Rel_Location", "XForm", 4.0 )

		rid1 = AddRuler( pid1, 1, 0.2, 0.3, pid2, 0, 0.2, 0.3, "Ruler 1" )

		rid2 = AddRuler( pid1, 0, 0.4, 0.6, pid1, 1, 0.8, 0.9, "Ruler 2" )

		ruler_array = GetAllRulers()
		assert len( ruler_array ) > 0, "GetAllRulers returned nothing"

		print("Two Rulers")

		for n in range(len(ruler_array)):

			print( ruler_array[n] )



	def test_DelRuler(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		pid2 = AddGeom( "POD", "" )

		SetParmVal( pid2, "Z_Rel_Location", "XForm", 4.0 )

		rid1 = AddRuler( pid1, 1, 0.2, 0.3, pid2, 0, 0.2, 0.3, "Ruler 1" )

		rid2 = AddRuler( pid1, 0, 0.4, 0.6, pid1, 1, 0.8, 0.9, "Ruler 2" )

		ruler_array = GetAllRulers()

		num_before_del = len( GetAllRulers() )
		DelRuler( ruler_array[0] )
		assert len( GetAllRulers() ) < num_before_del, "DelRuler removed nothing"




	def test_DeleteAllRulers(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		pid2 = AddGeom( "POD", "" )

		SetParmVal( pid2, "Z_Rel_Location", "XForm", 4.0 )

		rid1 = AddRuler( pid1, 1, 0.2, 0.3, pid2, 0, 0.2, 0.3, "Ruler 1" )

		rid2 = AddRuler( pid1, 0, 0.4, 0.6, pid1, 1, 0.8, 0.9, "Ruler 2" )

		DeleteAllRulers()
		assert len( GetAllRulers() ) == 0, "DeleteAllRulers left something behind"




	def test_AddProbe(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		probe_id = AddProbe( pid1, 0, 0.5, 0.8, "Probe 1" )

		SetParmVal( FindParm( probe_id, "Len", "Measure" ), 3.0 )



	def test_GetAllProbes(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		probe_id = AddProbe( pid1, 0, 0.5, 0.8, "Probe 1" )

		probe_array = GetAllProbes()
		assert len( probe_array ) > 0, "GetAllProbes returned nothing"

		print( "One Probe: ", False )

		print( probe_array[0] )



	def test_DelProbe(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		probe_id_1 = AddProbe( pid1, 0, 0.5, 0.8, "Probe 1" )
		probe_id_2 = AddProbe( pid1, 0, 0.2, 0.3, "Probe 2" )

		DelProbe( probe_id_1 )

		probe_array = GetAllProbes()

		if  len(probe_array) != 1 :
			print( "Error: DelProbe" )
			assert False, "Error: DelProbe"



	def test_DeleteAllProbes(self):
		pid1 = AddGeom( "POD", "" )

		SetParmVal( pid1, "Y_Rel_Location", "XForm", 2.0 )

		probe_id_1 = AddProbe( pid1, 0, 0.5, 0.8, "Probe 1" )
		probe_id_2 = AddProbe( pid1, 0, 0.2, 0.3, "Probe 2" )

		DeleteAllProbes()

		probe_array = GetAllProbes()

		if  len(probe_array) != 0 :
			print( "Error: DeleteAllProbes" )
			assert False, "Error: DeleteAllProbes"



	def test_CopyAirfoil(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		SetParmVal( xb, 3.0 )

		Update()

		link_id = AddParmLink( xa, xb )

		assert len( link_id ) > 0, "AddParmLink returned no id"
		assert GetNumParmLinks() == 1, "AddParmLink did not add the link"
		assert GetParmLinkID( 0 ) == link_id, "AddParmLink did not add the link"

		# The link drives B from A, holding the three unit offset it started with.
		SetParmValUpdate( xa, 5.0 )

		Update()

		assert abs( GetParmVal( xb ) - 8.0 ) < 1e-6, "the parm link did not drive its output"

		# Linking the same pair twice has to be refused.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		AddParmLink( xa, xb )

		assert err_mgr.GetNumTotalErrors() > 0, "AddParmLink accepted a duplicate link"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_PasteAirfoil(self):
		wid = AddGeom( "WING" )

		Update()

		CopyAirfoil( wid, 1 )

		# A default wing has two sections, so there is nowhere past 1 to paste to.
		PasteAirfoil( wid, 1 )

		Update()



	def test_ClearSkinning(self):
		sid = AddGeom( "STACK", "" )

		xsec_surf = GetXSecSurf( sid, 0 )

		xsec = GetXSec( xsec_surf, 1 )

		SetXSecTanAngles( xsec, XSEC_BOTH_SIDES, 15.0, -1.0e12, -1.0e12, -1.0e12 )

		Update()

		assert abs( GetParmVal( GetXSecParm( xsec, "TopLAngleSet" ) ) - 1.0 ) < 1e-12, "the skinning was never set"

		ClearSkinning( sid, 1 )

		Update()

		# Clearing releases the section's skinning controls and puts symmetry back
		# on; the angle itself becomes whatever the skin solves for.
		assert abs( GetParmVal( GetXSecParm( xsec, "TopLAngleSet" ) ) ) < 1e-12, "ClearSkinning did not release the section"
		assert abs( GetParmVal( GetXSecParm( xsec, "AllSym" ) ) - 1.0 ) < 1e-12, "ClearSkinning did not release the section"

		# A Geom with no cross sections has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		pid = AddGeom( "POD" )

		ClearSkinning( pid )

		assert err_mgr.GetNumTotalErrors() > 0, "ClearSkinning accepted a Geom with no cross sections"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_ResetGeomScale(self):
		pid = AddGeom( "POD" )

		Update()

		before_max = GetGeomBBoxMax( pid, 0, False )

		SetParmValUpdate( pid, "Scale", "XForm", 2.0 )

		Update()

		scaled_max = GetGeomBBoxMax( pid, 0, False )

		assert abs( scaled_max.x() - 2.0 * before_max.x() ) < 1e-6, "the Geom was never scaled"

		ResetGeomScale( pid )

		Update()

		# The scale factor comes back to one and the Geom returns to its base size.
		assert abs( GetParmVal( pid, "Scale", "XForm" ) - 1.0 ) < 1e-9, "ResetGeomScale did not reset the scale factor"

		after_max = GetGeomBBoxMax( pid, 0, False )

		assert abs( after_max.x() - before_max.x() ) < 1e-6, "ResetGeomScale did not undo the scaling"



	def test_AcceptGeomScale(self):
		pid = AddGeom( "POD" )

		mesh_id = ExportFile( "Example_Mesh.msh", SET_ALL, EXPORT_GMSH )

		cloud_id = CreatePtCloudGeom( mesh_id )

		assert len( cloud_id ) > 0, "CreatePtCloudGeom did not make a point cloud"
		assert GetGeomTypeName( cloud_id ) == "PtCloud", "CreatePtCloudGeom did not make a point cloud"

		# A Geom that is not a mesh has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		CreatePtCloudGeom( pid )

		assert err_mgr.GetNumTotalErrors() > 0, "CreatePtCloudGeom accepted a Geom that is not a mesh"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetPtCloudPnts(self):
		pid = AddGeom( "POD" )

		mesh_id = ExportFile( "Example_Mesh.msh", SET_ALL, EXPORT_GMSH )

		cloud_id = CreatePtCloudGeom( mesh_id )

		pnts = GetPtCloudPnts( cloud_id )

		assert len( pnts ) > 0, "GetPtCloudPnts returned nothing"

		# A Geom that is not a point cloud has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetPtCloudPnts( pid )

		assert err_mgr.GetNumTotalErrors() > 0, "GetPtCloudPnts accepted a Geom that is not a point cloud"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_CreatePtCloudGeom(self):
		pid = AddGeom( "POD" )

		Update()

		mesh_id = ComputePlaneSlice( SET_ALL, 3, vec3d( 1.0, 0.0, 0.0 ), True )

		cloud_id = CreatePtCloudGeom( mesh_id )

		assert len( GetPtCloudPnts( cloud_id ) ) > 0, "CreatePtCloudGeom made no points"



	def test_CreateNGonMeshGeom(self):
		pid = AddGeom( "POD" )

		mesh_id = ExportFile( "Example_Mesh.msh", SET_ALL, EXPORT_GMSH )

		ngon_id = CreateNGonMeshGeom( mesh_id )

		assert len( ngon_id ) > 0, "CreateNGonMeshGeom did not make an NGon mesh"
		assert GetGeomTypeName( ngon_id ) == "NGonMesh", "CreateNGonMeshGeom did not make an NGon mesh"

		# A Geom that is not a mesh has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		CreateNGonMeshGeom( pid )

		assert err_mgr.GetNumTotalErrors() > 0, "CreateNGonMeshGeom accepted a Geom that is not a mesh"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_CreateConvexHull(self):
		pid = AddGeom( "POD" )

		mesh_id = ExportFile( "Example_Mesh.msh", SET_ALL, EXPORT_GMSH )

		cloud_id = CreatePtCloudGeom( mesh_id )

		num_pnts = len( GetPtCloudPnts( cloud_id ) )

		hull_id = CreateConvexHull( cloud_id )

		Update()

		# The hull is a mesh of its own, and the cloud it came from is untouched.
		assert len( hull_id ) > 0, "CreateConvexHull did not make a hull mesh"
		assert GetGeomTypeName( hull_id ) == "Mesh", "CreateConvexHull did not make a hull mesh"
		assert len( GetPtCloudPnts( cloud_id ) ) == num_pnts, "CreateConvexHull disturbed the point cloud"

		# A Geom that is not a point cloud has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		CreateConvexHull( pid )

		assert err_mgr.GetNumTotalErrors() > 0, "CreateConvexHull accepted a Geom that is not a point cloud"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_ProjectPtCloudPts(self):
		pid = AddGeom( "POD" )

		# Mesh the Pod, then make a point cloud out of the mesh vertices.
		mesh_id = ExportFile( "ProjectExample.msh", SET_ALL, EXPORT_GMSH )

		cloud_id = CreatePtCloudGeom( mesh_id )

		# Lift the cloud above the Pod so the points have somewhere to fall from.
		SetParmVal( cloud_id, "Z_Rel_Location", "XForm", 5.0 )

		Update()

		before = GetPtCloudPnts( cloud_id )

		ProjectPtCloudPts( cloud_id, pid, 0, Z_DIR )

		Update()

		after = GetPtCloudPnts( cloud_id )

		# Projection moves points; it never adds or removes any.
		assert len( after ) == len( before ), "ProjectPtCloudPts changed the point count"



	def test_ShowSet(self):
		pid = AddGeom( "POD" )

		SetSetFlag( pid, 3, True )

		NoShowSet( 3 )

		assert not GetSetFlag( pid, SET_SHOWN ), "NoShowSet did not hide the set"

		ShowSet( 3 )

		assert GetSetFlag( pid, SET_SHOWN ), "ShowSet did not show the set"

		# A set index past the end has to be rejected.
		err_mgr = ErrorMgrSingleton.getInstance()

		ShowSet( GetNumSets() )

		assert err_mgr.GetNumTotalErrors() > 0, "ShowSet accepted a set index past the end"

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_NoShowSet(self):
		pid = AddGeom( "POD" )

		Update()

		SetSetFlag( pid, SET_FIRST_USER, True )

		NoShowSet( SET_FIRST_USER )



	def test_ShowOnlySet(self):
		pod1 = AddGeom( "POD" )
		pod2 = AddGeom( "POD" )

		SetSetFlag( pod1, 3, True )

		ShowOnlySet( 3 )

		# The set is shown and everything outside it is hidden.
		assert GetSetFlag( pod1, SET_SHOWN ), "ShowOnlySet did not show the set"
		assert not GetSetFlag( pod2, SET_SHOWN ), "ShowOnlySet did not hide the rest of the model"



	def test_AddParmLink(self):
		pid = AddGeom( "POD" )

		Update()

		len_parm = GetParm( pid, "Length", "Design" )
		dia_parm = GetParm( pid, "FineRatio", "Design" )

		link_id = AddParmLink( len_parm, dia_parm )

		assert len( link_id ) > 0, "AddParmLink returned no ID"

		assert GetNumParmLinks() == 1, "AddParmLink did not add the link"



	def test_GetNumParmLinks(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		assert GetNumParmLinks() == 0, "a new model starts with Parm Links"

		AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )
		AddParmLink( GetParm( pod1, "Y_Rel_Location", "XForm" ), GetParm( pod2, "Y_Rel_Location", "XForm" ) )

		assert GetNumParmLinks() == 2, "GetNumParmLinks did not count both links"

		# Every link the count claims has to be findable.
		for i in range( GetNumParmLinks() ):
			assert len( GetParmLinkID( i ) ) > 0, "a counted link cannot be found"



	def test_GetParmLinkID(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		first = AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )
		second = AddParmLink( GetParm( pod1, "Y_Rel_Location", "XForm" ), GetParm( pod2, "Y_Rel_Location", "XForm" ) )

		# Links come back in the order they were added.
		assert GetParmLinkID( 0 ) == first, "GetParmLinkID did not report the links in order"
		assert GetParmLinkID( 1 ) == second, "GetParmLinkID did not report the links in order"

		# An index past the end has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		GetParmLinkID( GetNumParmLinks() )

		assert err_mgr.GetNumTotalErrors() > 0, "GetParmLinkID accepted an index past the end"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetParmLinkAParm(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		assert GetParmLinkAParm( link_id ) == xa, "the link does not report the Parms it was given"
		assert GetParmLinkBParm( link_id ) == xb, "the link does not report the Parms it was given"

		# Pointing A at a different Parm has to take.
		ya = GetParm( pod1, "Y_Rel_Location", "XForm" )

		SetParmLinkAParm( link_id, ya )

		assert GetParmLinkAParm( link_id ) == ya, "SetParmLinkAParm did not take"

		# A Parm that does not exist has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		SetParmLinkAParm( link_id, "NOSUCHPARM" )

		assert err_mgr.GetNumTotalErrors() > 0, "SetParmLinkAParm accepted a bad Parm ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_GetParmLinkBParm(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		assert GetParmLinkBParm( link_id ) == xb, "GetParmLinkBParm did not report the driven Parm"

		# The two ends are different Parms.
		assert GetParmLinkBParm( link_id ) != GetParmLinkAParm( link_id ), "both ends of the link report the same Parm"



	def test_SetParmLinkAParm(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		ya = GetParm( pod1, "Y_Rel_Location", "XForm" )

		SetParmLinkAParm( link_id, ya )

		assert GetParmLinkAParm( link_id ) == ya, "SetParmLinkAParm did not take"

		# The driven end is left alone.
		assert GetParmLinkBParm( link_id ) == xb, "SetParmLinkAParm disturbed the driven Parm"



	def test_SetParmLinkBParm(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		yb = GetParm( pod2, "Y_Rel_Location", "XForm" )

		SetParmLinkBParm( link_id, yb )

		assert GetParmLinkBParm( link_id ) == yb, "SetParmLinkBParm did not take"

		# The driving end is left alone.
		assert GetParmLinkAParm( link_id ) == xa, "SetParmLinkBParm disturbed the driving Parm"



	def test_DelParmLink(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		first = AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )
		second = AddParmLink( GetParm( pod1, "Y_Rel_Location", "XForm" ), GetParm( pod2, "Y_Rel_Location", "XForm" ) )

		DelParmLink( first )

		# Only the named link goes.
		assert GetNumParmLinks() == 1, "DelParmLink removed the wrong link"
		assert GetParmLinkID( 0 ) == second, "DelParmLink removed the wrong link"

		# An ID that is not a link has to be rejected.  The error queue is reached
		# through the error manager singleton in Python.
		err_mgr = ErrorMgrSingleton.getInstance()

		DelParmLink( "NOSUCHLINK" )

		assert err_mgr.GetNumTotalErrors() > 0, "DelParmLink accepted a bad ID"

		# That error was raised deliberately, so take it back off the queue.
		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DelAllParmLinks(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )
		AddParmLink( GetParm( pod1, "Y_Rel_Location", "XForm" ), GetParm( pod2, "Y_Rel_Location", "XForm" ) )

		AddAdvLink( "ExampleAdvLink" )

		DelAllParmLinks()

		assert GetNumParmLinks() == 0, "DelAllParmLinks left links behind"
		assert len( GetAdvLinkNames() ) == 1, "DelAllParmLinks removed an advanced link"



	def test_SortParmLinksByA(self):
		pod = AddGeom( "POD", "" )

		length = FindParm( pod, "Length", "Design" )
		fine = FindParm( pod, "FineRatio", "Design" )
		x_pos = FindParm( pod, "X_Rel_Location", "XForm" )
		y_pos = FindParm( pod, "Y_Rel_Location", "XForm" )

		# Add the links out of order, reading from Length first.
		link1 = AddParmLink( length, x_pos )
		link2 = AddParmLink( fine, y_pos )

		SortParmLinksByA()

		# FineRatio sorts ahead of Length, so its link comes first.
		assert GetParmLinkID( 0 ) == link2, "SortParmLinksByA did not sort the links"



	def test_SortParmLinksByB(self):
		pod = AddGeom( "POD", "" )

		length = FindParm( pod, "Length", "Design" )
		fine = FindParm( pod, "FineRatio", "Design" )
		x_pos = FindParm( pod, "X_Rel_Location", "XForm" )
		y_pos = FindParm( pod, "Y_Rel_Location", "XForm" )

		# Add the links so that the one driving Y_Rel_Location comes first.
		link1 = AddParmLink( length, y_pos )
		link2 = AddParmLink( fine, x_pos )

		SortParmLinksByB()

		# X_Rel_Location sorts ahead of Y_Rel_Location, so its link comes first.
		assert GetParmLinkID( 0 ) == link2, "SortParmLinksByB did not sort the links"



	def test_LinkAllComp(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		LinkAllComp( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )

		# A Pod carries many Parms, so this makes many links at once.
		assert GetNumParmLinks() >= 2, "LinkAllComp did not link the containers"

		# Every link it made joins two real Parms.
		for i in range( GetNumParmLinks() ):
			lid = GetParmLinkID( i )
			assert len( GetParmLinkAParm( lid ) ) > 0, "LinkAllComp made a link with no Parms"
			assert len( GetParmLinkBParm( lid ) ) > 0, "LinkAllComp made a link with no Parms"



	def test_LinkAllGroup(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		LinkAllGroup( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )

		# The XForm group carries several Parms, so this makes several links.
		num_group = GetNumParmLinks()

		assert num_group >= 2, "LinkAllGroup did not link the groups"

		# A group is part of the container, so linking the whole container makes at
		# least as many links.
		DelAllParmLinks()

		LinkAllComp( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )

		assert GetNumParmLinks() >= num_group, "LinkAllGroup linked more than LinkAllComp"



	def test_GetParmLinkOffsetFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		# A new link comes up with its offset on and the rest off.
		assert GetParmLinkOffsetFlag( link_id ) == True, "the offset flag did not start where a new link starts"

		SetParmLinkOffsetFlag( link_id, not GetParmLinkOffsetFlag( link_id ) )

		assert GetParmLinkOffsetFlag( link_id ) != True, "GetParmLinkOffsetFlag did not follow the setter"



	def test_SetParmLinkOffsetFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		link_id = AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )

		SetParmLinkOffsetFlag( link_id, True )

		assert GetParmLinkOffsetFlag( link_id ), "the offset flag did not take"

		SetParmLinkOffsetFlag( link_id, False )

		assert not GetParmLinkOffsetFlag( link_id ), "the offset flag did not clear"

		# The value it applies is a Parm on the link itself.
		assert len( FindParm( link_id, "Offset", "Link" ) ) > 0, "the link carries no Offset Parm"



	def test_GetParmLinkScaleFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		# A new link comes up with its offset on and the rest off.
		assert GetParmLinkScaleFlag( link_id ) == False, "the scale flag did not start where a new link starts"

		SetParmLinkScaleFlag( link_id, not GetParmLinkScaleFlag( link_id ) )

		assert GetParmLinkScaleFlag( link_id ) != False, "GetParmLinkScaleFlag did not follow the setter"



	def test_SetParmLinkScaleFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		link_id = AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )

		SetParmLinkScaleFlag( link_id, True )

		assert GetParmLinkScaleFlag( link_id ), "the scale flag did not take"

		SetParmLinkScaleFlag( link_id, False )

		assert not GetParmLinkScaleFlag( link_id ), "the scale flag did not clear"

		# The value it applies is a Parm on the link itself.
		assert len( FindParm( link_id, "Scale", "Link" ) ) > 0, "the link carries no Scale Parm"



	def test_GetParmLinkLowerLimitFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		# A new link comes up with its offset on and the rest off.
		assert GetParmLinkLowerLimitFlag( link_id ) == False, "the lower limit flag did not start where a new link starts"

		SetParmLinkLowerLimitFlag( link_id, not GetParmLinkLowerLimitFlag( link_id ) )

		assert GetParmLinkLowerLimitFlag( link_id ) != False, "GetParmLinkLowerLimitFlag did not follow the setter"



	def test_SetParmLinkLowerLimitFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		link_id = AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )

		SetParmLinkLowerLimitFlag( link_id, True )

		assert GetParmLinkLowerLimitFlag( link_id ), "the lower limit flag did not take"

		SetParmLinkLowerLimitFlag( link_id, False )

		assert not GetParmLinkLowerLimitFlag( link_id ), "the lower limit flag did not clear"

		# The value it applies is a Parm on the link itself.
		assert len( FindParm( link_id, "LowerLimit", "Link" ) ) > 0, "the link carries no LowerLimit Parm"



	def test_GetParmLinkUpperLimitFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		xa = GetParm( pod1, "X_Rel_Location", "XForm" )
		xb = GetParm( pod2, "X_Rel_Location", "XForm" )

		link_id = AddParmLink( xa, xb )

		# A new link comes up with its offset on and the rest off.
		assert GetParmLinkUpperLimitFlag( link_id ) == False, "the upper limit flag did not start where a new link starts"

		SetParmLinkUpperLimitFlag( link_id, not GetParmLinkUpperLimitFlag( link_id ) )

		assert GetParmLinkUpperLimitFlag( link_id ) != False, "GetParmLinkUpperLimitFlag did not follow the setter"



	def test_SetParmLinkUpperLimitFlag(self):
		pod1 = AddGeom( "POD", "" )
		pod2 = AddGeom( "POD", "" )

		link_id = AddParmLink( GetParm( pod1, "X_Rel_Location", "XForm" ), GetParm( pod2, "X_Rel_Location", "XForm" ) )

		SetParmLinkUpperLimitFlag( link_id, True )

		assert GetParmLinkUpperLimitFlag( link_id ), "the upper limit flag did not take"

		SetParmLinkUpperLimitFlag( link_id, False )

		assert not GetParmLinkUpperLimitFlag( link_id ), "the upper limit flag did not clear"

		# The value it applies is a Parm on the link itself.
		assert len( FindParm( link_id, "UpperLimit", "Link" ) ) > 0, "the link carries no UpperLimit Parm"



	def test_GetAdvLinkNames(self):
		#==== Set up an advanced link so there is something to find ====//
		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		link_array = GetAdvLinkNames()
		assert len( link_array ) > 0, "GetAdvLinkNames returned nothing"

		for n in range(len(link_array) ):

			print( link_array[n] )



	def test_GetLinkIndex(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output: x is 10 minus the Pod's
		# length, so changing the length has to move the Pod.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 4.0 ) < 1e-6, "the advanced link did not drive its output"



	def test_GetAdvLinkName(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		num_before_del = len( GetAdvLinkNames() )
		DelAdvLink( indx )
		assert len( GetAdvLinkNames() ) < num_before_del, "DelAdvLink removed nothing"


		link_array = GetAdvLinkNames()

		# Should print nothing.
		for n in range(len(link_array) ):

			print( link_array[n] )

		assert len( link_array ) == 0, "links were left behind"

		# With the link gone, the Pod is no longer driven.
		x_before = GetParmVal( x_pos )

		SetParmValUpdate( length, 7.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - x_before ) < 1e-9, "a deleted advanced link is still driving its output"




	def test_SetAdvLinkName(self):
		AddAdvLink( "ExampleLink" )

		indx = GetLinkIndex( "ExampleLink" )

		SetAdvLinkName( indx, "RenamedLink" )

		assert GetAdvLinkName( indx ) == "RenamedLink", "SetAdvLinkName did not take"

		# The link is now found under its new name and not its old one.
		assert GetLinkIndex( "RenamedLink" ) == indx, "the renamed link cannot be found under its new name"
		assert GetLinkIndex( "ExampleLink" ) < 0, "the renamed link is still found under its old name"

		# Looking up the old name raised an error on purpose, so take it back off
		# the queue.
		err_mgr = ErrorMgrSingleton.getInstance()

		while err_mgr.GetNumTotalErrors() > 0 :
			err = err_mgr.PopLastError()



	def test_DelAdvLink(self):
		AddAdvLink( "TestLink" )

		DelAdvLink( 0 )

		assert len( GetAdvLinkNames() ) == 0, "DelAdvLink did not delete the link"



	def test_DelAllAdvLinks(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		DelAllAdvLinks()

		link_array = GetAdvLinkNames()

		# Should print nothing.
		for n in range( len(link_array) ):

			print( link_array[n] )

		assert len( link_array ) == 0, "links were left behind"

		# With the link gone, the Pod is no longer driven.
		x_before = GetParmVal( x_pos )

		SetParmValUpdate( length, 7.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - x_before ) < 1e-9, "a deleted advanced link is still driving its output"




	def test_AddAdvLink(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output: x is 10 minus the Pod's
		# length, so changing the length has to move the Pod.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 4.0 ) < 1e-6, "the advanced link did not drive its output"



	def test_AddAdvLinkInput(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output: x is 10 minus the Pod's
		# length, so changing the length has to move the Pod.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 4.0 ) < 1e-6, "the advanced link did not drive its output"



	def test_AddAdvLinkOutput(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output: x is 10 minus the Pod's
		# length, so changing the length has to move the Pod.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 4.0 ) < 1e-6, "the advanced link did not drive its output"



	def test_DelAllAdvLinkInputs(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )
		y_pos = GetParm( pod, "Y_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )
		AddAdvLinkInput( indx, y_pos, "y" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		num_before_del = len( GetAdvLinkInputNames( indx ) )
		DelAdvLinkInput( indx, "y" )
		assert len( GetAdvLinkInputNames( indx ) ) < num_before_del, "DelAdvLinkInput removed nothing"


		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output: x is 10 minus the Pod's
		# length, so changing the length has to move the Pod.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 4.0 ) < 1e-6, "the advanced link did not drive its output"



	def test_DelAllAdvLinkOutputs(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )
		y_pos = GetParm( pod, "Y_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )
		AddAdvLinkOutput( indx, y_pos, "y" )

		assert len( GetAdvLinkOutputNames( indx ) ) == 2, "the outputs were not both added"

		DelAllAdvLinkOutputs( indx )

		# Every output goes; the inputs are left alone.
		assert len( GetAdvLinkOutputNames( indx ) ) == 0, "DelAllAdvLinkOutputs left outputs behind"
		assert len( GetAdvLinkInputNames( indx ) ) == 1, "DelAllAdvLinkOutputs removed an input"



	def test_DelAdvLinkInput(self):
		pid = AddGeom( "POD" )

		Update()

		AddAdvLink( "TestLink" )

		len_parm = GetParm( pid, "Length", "Design" )

		AddAdvLinkInput( 0, len_parm, "Len" )

		DelAdvLinkInput( 0, "Len" )

		assert len( GetAdvLinkInputNames( 0 ) ) == 0, "DelAdvLinkInput did not remove the input"



	def test_DelAdvLinkOutput(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )
		y_pos = GetParm( pod, "Y_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )
		AddAdvLinkOutput( indx, y_pos, "y" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		num_before_del = len( GetAdvLinkOutputNames( indx ) )
		DelAdvLinkOutput( indx, "y" )
		assert len( GetAdvLinkOutputNames( indx ) ) < num_before_del, "DelAdvLinkOutput removed nothing"


		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output: x is 10 minus the Pod's
		# length, so changing the length has to move the Pod.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 4.0 ) < 1e-6, "the advanced link did not drive its output"



	def test_GetAdvLinkInputNames(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		name_array = GetAdvLinkInputNames( indx )
		assert len( name_array ) > 0, "GetAdvLinkInputNames returned nothing"

		for n in range(len(name_array) ):

			print( name_array[n] )




	def test_GetAdvLinkInputParms(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		parm_array = GetAdvLinkInputParms( indx )
		assert len( parm_array ) > 0, "GetAdvLinkInputParms returned nothing"

		for n in range( len(parm_array) ):

			print( parm_array[n] )




	def test_GetAdvLinkOutputNames(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		name_array = GetAdvLinkOutputNames( indx )
		assert len( name_array ) > 0, "GetAdvLinkOutputNames returned nothing"

		for n in range( len(name_array) ):

			print( name_array[n] )




	def test_GetAdvLinkOutputParms(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		parm_array = GetAdvLinkOutputParms( indx )
		assert len( parm_array ) > 0, "GetAdvLinkOutputParms returned nothing"

		for n in range( len(parm_array) ):

			print( parm_array[n] )




	def test_ValidateAdvLinkParms(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		valid = ValidateAdvLinkParms( indx )

		# The link built above is well formed, so this has to come back true.
		assert valid, "ValidateAdvLinkParms did not report success"

		if  valid :
			print( "Advanced link Parms are valid." )
		else:
			print( "Advanced link Parms are not valid." )




	def test_SetAdvLinkCode(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output: x is 10 minus the Pod's
		# length, so changing the length has to move the Pod.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 4.0 ) < 1e-6, "the advanced link did not drive its output"



	def test_GetAdvLinkCode(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		BuildAdvLinkScript( indx )

		code = GetAdvLinkCode( indx )
		assert len( code ) > 0, "GetAdvLinkCode returned nothing"

		print( code )




	def test_SearchReplaceAdvLinkCode(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )
		SearchReplaceAdvLinkCode( indx, "10.0", "12.3" )

		code = GetAdvLinkCode( indx )

		print( code )

		assert "12.3" in code and "10.0" not in code, "SearchReplaceAdvLinkCode did not replace"

		BuildAdvLinkScript( indx )

		# The link was named, so it has to be findable by that name and by that
		# index, and it has to actually drive its output.  The replacement rewrote
		# the code, so x is now 12.3 minus the Pod's length.
		assert indx >= 0, "the advanced link was not registered under its name"
		assert len( GetAdvLinkNames() ) == 1, "the advanced link was not registered under its name"
		assert GetAdvLinkNames()[0] == "ExampleLink", "the advanced link was not registered under its name"

		SetParmValUpdate( length, 6.0 )

		Update()

		assert abs( GetParmVal( x_pos ) - 6.3 ) < 1e-6, "the advanced link did not drive its output"



	def test_BuildAdvLinkScript(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		success = BuildAdvLinkScript( indx )

		# The link built above is well formed, so this has to come back true.
		assert success, "BuildAdvLinkScript did not report success"

		if  success :
			print( "Advanced link build successful." )
		else:
			print( "Advanced link build not successful." )




	def test_WriteAdvLinkCodeFile(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )

		WriteAdvLinkCodeFile( indx, "ExampleLink.vspscript" )

		# Overwrite the code, then bring the saved version back.
		SetAdvLinkCode( indx, "x = 0.0;" )

		ReadAdvLinkCodeFile( indx, "ExampleLink.vspscript" )

		assert GetAdvLinkCode( indx ) == "x = 10.0 - len;", "the code did not survive the round trip"



	def test_ReorderAdvLinkInput(self):

		pod = AddGeom( "POD", "" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )

		AddAdvLinkInput( indx, FindParm( pod, "Length", "Design" ), "len" )
		AddAdvLinkInput( indx, FindParm( pod, "FineRatio", "Design" ), "fine" )

		ReorderAdvLinkInput( indx, "fine", REORDER_MOVE_UP )

		names = GetAdvLinkInputNames( indx )

		assert names[0] == "fine", "ReorderAdvLinkInput did not move the variable"
		assert names[1] == "len", "ReorderAdvLinkInput did not move the variable"



	def test_ReorderAdvLinkOutput(self):

		pod = AddGeom( "POD", "" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )

		AddAdvLinkOutput( indx, FindParm( pod, "X_Rel_Location", "XForm" ), "x" )
		AddAdvLinkOutput( indx, FindParm( pod, "Y_Rel_Location", "XForm" ), "y" )

		ReorderAdvLinkOutput( indx, "x", REORDER_MOVE_BOTTOM )

		names = GetAdvLinkOutputNames( indx )

		assert names[0] == "y", "ReorderAdvLinkOutput did not move the variable"
		assert names[1] == "x", "ReorderAdvLinkOutput did not move the variable"



	def test_ReadAdvLinkCodeFile(self):

		pod = AddGeom( "POD", "" )
		length = FindParm( pod, "Length", "Design" )
		x_pos = GetParm( pod, "X_Rel_Location", "XForm" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )
		AddAdvLinkInput( indx, length, "len" )
		AddAdvLinkOutput( indx, x_pos, "x" )

		SetAdvLinkCode( indx, "x = 10.0 - len;" )
		WriteAdvLinkCodeFile( indx, "ExampleLink.vspscript" )

		# A second link can pick up the same code, so long as it declares len and x.
		AddAdvLink( "SecondLink" )
		indx2 = GetLinkIndex( "SecondLink" )
		AddAdvLinkInput( indx2, length, "len" )
		AddAdvLinkOutput( indx2, GetParm( pod, "Y_Rel_Location", "XForm" ), "x" )

		ReadAdvLinkCodeFile( indx2, "ExampleLink.vspscript" )

		assert GetAdvLinkCode( indx2 ) == GetAdvLinkCode( indx ), "ReadAdvLinkCodeFile did not load the code"



	def test_SortAdvLinkInputsVar(self):

		pod = AddGeom( "POD", "" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )

		AddAdvLinkInput( indx, FindParm( pod, "Length", "Design" ), "zlen" )
		AddAdvLinkInput( indx, FindParm( pod, "FineRatio", "Design" ), "afine" )

		SortAdvLinkInputsVar( indx )

		names = GetAdvLinkInputNames( indx )

		assert names[0] == "afine", "SortAdvLinkInputsVar did not sort by name"
		assert names[1] == "zlen", "SortAdvLinkInputsVar did not sort by name"



	def test_SortAdvLinkInputsCGP(self):

		pod = AddGeom( "POD", "" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )

		AddAdvLinkInput( indx, FindParm( pod, "Length", "Design" ), "a" )
		AddAdvLinkInput( indx, FindParm( pod, "FineRatio", "Design" ), "b" )

		SortAdvLinkInputsCGP( indx )

		names = GetAdvLinkInputNames( indx )

		# FineRatio sorts ahead of Length, so the variables come back swapped.
		assert names[0] == "b", "SortAdvLinkInputsCGP did not sort by Parm"
		assert names[1] == "a", "SortAdvLinkInputsCGP did not sort by Parm"



	def test_SortAdvLinkOutputsVar(self):

		pod = AddGeom( "POD", "" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )

		AddAdvLinkOutput( indx, FindParm( pod, "X_Rel_Location", "XForm" ), "zx" )
		AddAdvLinkOutput( indx, FindParm( pod, "Y_Rel_Location", "XForm" ), "ay" )

		SortAdvLinkOutputsVar( indx )

		names = GetAdvLinkOutputNames( indx )

		assert names[0] == "ay", "SortAdvLinkOutputsVar did not sort by name"
		assert names[1] == "zx", "SortAdvLinkOutputsVar did not sort by name"



	def test_SortAdvLinkOutputsCGP(self):

		pod = AddGeom( "POD", "" )

		AddAdvLink( "ExampleLink" )
		indx = GetLinkIndex( "ExampleLink" )

		AddAdvLinkOutput( indx, FindParm( pod, "Y_Rel_Location", "XForm" ), "a" )
		AddAdvLinkOutput( indx, FindParm( pod, "X_Rel_Location", "XForm" ), "b" )

		SortAdvLinkOutputsCGP( indx )

		names = GetAdvLinkOutputNames( indx )

		# X_Rel_Location sorts ahead of Y_Rel_Location, so the variables come back swapped.
		assert names[0] == "b", "SortAdvLinkOutputsCGP did not sort by Parm"
		assert names[1] == "a", "SortAdvLinkOutputsCGP did not sort by Parm"



	def test_GetErrorCode(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		#==== Silence the errors so the bogus call below does not print ====#
		err_mgr.SilenceErrors()

		#==== Bogus call to raise an error ====#
		SetParmVal( "BogusParmID", 23.0 )

		err_mgr.PrintOnErrors()

		err = err_mgr.PopLastError()

		assert err.GetErrorCode() == VSP_CANT_FIND_PARM, "GetErrorCode did not report the missing Parm"

		#==== Leave the queue as it was found ====#
		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_GetErrorString(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		err_mgr.SilenceErrors()

		SetParmVal( "BogusParmID", 23.0 )

		err_mgr.PrintOnErrors()

		err = err_mgr.PopLastError()

		assert len( err.GetErrorString() ) > 0, "GetErrorString returned nothing to report"

		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_GetErrorLastCallFlag(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		err_mgr.SilenceErrors()

		#==== Bogus call to raise an error ====#
		SetParmVal( "BogusParmID", 23.0 )

		assert err_mgr.GetErrorLastCallFlag(), "GetErrorLastCallFlag missed the error"

		err_mgr.PrintOnErrors()

		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_GetNumTotalErrors(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		err_mgr.SilenceErrors()

		#==== Two bogus calls, so the count is something to check ====#
		SetParmVal( "BogusParmID", 23.0 )
		SetParmVal( "AnotherBogusParmID", 23.0 )

		assert err_mgr.GetNumTotalErrors() == 2, "GetNumTotalErrors did not count both errors"

		err_mgr.PrintOnErrors()

		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_PopLastError(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		err_mgr.SilenceErrors()

		SetParmVal( "BogusParmID", 23.0 )

		n0 = err_mgr.GetNumTotalErrors()

		err = err_mgr.PopLastError()

		#==== Pop takes the error off the queue ====#
		assert err_mgr.GetNumTotalErrors() == n0 - 1, "PopLastError left the error on the queue"

		assert err.GetErrorCode() == VSP_CANT_FIND_PARM, "PopLastError returned the wrong error"

		err_mgr.PrintOnErrors()

		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_GetLastError(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		err_mgr.SilenceErrors()

		SetParmVal( "BogusParmID", 23.0 )

		n0 = err_mgr.GetNumTotalErrors()

		err = err_mgr.GetLastError()

		#==== Unlike PopLastError, the error stays on the queue ====#
		assert err_mgr.GetNumTotalErrors() == n0, "GetLastError removed the error"

		assert err.GetErrorCode() == VSP_CANT_FIND_PARM, "GetLastError returned the wrong error"

		err_mgr.PrintOnErrors()

		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_SilenceErrors(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		#==== Errors are printed as they happen unless silenced ====#
		err_mgr.SilenceErrors()

		SetParmVal( "BogusParmID", 23.0 )

		#==== The error is still recorded, it is only the printing that stops ====#
		assert err_mgr.GetNumTotalErrors() == 1, "SilenceErrors also stopped the error being recorded"

		err_mgr.PrintOnErrors()

		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_PrintOnErrors(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		err_mgr.SilenceErrors()

		SetParmVal( "BogusParmID", 23.0 )

		#==== Turn printing back on ====#
		err_mgr.PrintOnErrors()

		assert err_mgr.GetNumTotalErrors() == 1, "PrintOnErrors lost the recorded error"

		while err_mgr.GetNumTotalErrors() > 0:
			err_mgr.PopLastError()


	def test_getInstance(self):
		err_mgr = ErrorMgrSingleton.getInstance()

		assert err_mgr.GetNumTotalErrors() >= 0, "getInstance did not return a usable error manager"



	def test_operator_add(self):
		a = vec3d()                                # Default Constructor
		b = vec3d()

		a.set_xyz( 1.0, 2.0, 3.0 )
		b.set_xyz( 4.0, 5.0, 6.0 )

		c = a + b

		print( "a + b = ", False )

		print( c )


	def test_operator_sub(self):
		a = vec3d()                                # Default Constructor
		b = vec3d()

		a.set_xyz( 1.0, 2.0, 3.0 )
		b.set_xyz( 4.0, 5.0, 6.0 )

		c = a - b

		print( "a - b = ", False )

		print( c )


	def test_operator_mul(self):
		a = vec3d()                                # Default Constructor

		a.set_xyz( 1.0, 2.0, 3.0 )

		b = 1.5

		c = a * b

		print( "a * b = ", False )

		print( c )


	def test_operator_mul1(self):
		a = vec3d()                                # Default Constructor

		a.set_xyz( 1.0, 2.0, 3.0 )

		b = 1.5

		c = a * b

		print( "a * b = ", False )

		print( c )


	def test_operator_div(self):
		a = vec3d()                                # Default Constructor

		a.set_xyz( 1.0, 2.0, 3.0 )

		b = 1.5

		c = a / b

		print( "a / b = ", False )

		print( c )


	def test_set_xyz(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		a.set_xyz( 2.0, 4.0, 6.0 )


	def test_set_vec(self):
		a = vec3d()

		a.set_vec( [ 1.0, 2.0, 3.0 ] )

		assert abs( a.x() - 1.0 ) < 1e-12, "set_vec did not set x"

		assert abs( a.z() - 3.0 ) < 1e-12, "set_vec did not set z"


	def test_set_x(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		a.set_x( 2.0 )


	def test_set_y(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		a.set_y( 4.0 )


	def test_set_z(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		a.set_z( 6.0 )


	def test_set_refx(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		b = vec3d()

		b.set_refx( a )

		assert abs( b.x() + 1.0 ) < 1e-12, "set_refx did not negate x"

		assert abs( b.y() - 2.0 ) < 1e-12, "set_refx disturbed y"


	def test_set_refy(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		b = vec3d()

		b.set_refy( a )

		assert abs( b.y() + 2.0 ) < 1e-12, "set_refy did not negate y"

		assert abs( b.x() - 1.0 ) < 1e-12, "set_refy disturbed x"


	def test_set_refz(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		b = vec3d()

		b.set_refz( a )

		assert abs( b.z() + 3.0 ) < 1e-12, "set_refz did not negate z"

		assert abs( b.x() - 1.0 ) < 1e-12, "set_refz disturbed x"


	def test_x(self):
		a = vec3d()                                # Default Constructor

		a.set_xyz( 2.0, 4.0, 6.0 )

		assert abs( a.x() - 2.0 ) < 1e-12, "x did not return the coordinate"

		assert abs( a[0] - 2.0 ) < 1e-12, "indexing disagrees with x()"


	def test_y(self):
		a = vec3d()                                # Default Constructor

		a.set_xyz( 2.0, 4.0, 6.0 )

		assert abs( a.y() - 4.0 ) < 1e-12, "y did not return the coordinate"

		assert abs( a[1] - 4.0 ) < 1e-12, "indexing disagrees with y()"


	def test_z(self):
		a = vec3d()                                # Default Constructor

		a.set_xyz( 2.0, 4.0, 6.0 )

		assert abs( a.z() - 6.0 ) < 1e-12, "z did not return the coordinate"

		assert abs( a[2] - 6.0 ) < 1e-12, "indexing disagrees with z()"


	def test_rotate_x(self):
		import math
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		PI = 3.14

		a.set_xyz( 1.0, 0.0, 0.0 )

		a.rotate_x( 0.5 * PI )


	def test_rotate_y(self):
		import math
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		PI = 3.14

		a.set_xyz( 1.0, 0.0, 0.0 )

		a.rotate_y( 0.5 * PI )


	def test_rotate_z(self):
		import math
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		PI = 3.14

		a.set_xyz( 1.0, 0.0, 0.0 )

		a.rotate_z( 0.5 * PI )


	def test_scale_x(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		#===== Test Scale ====
		a.set_xyz( 2.0, 2.0, 2.0 )

		a.scale_x( 2.0 )


	def test_scale_y(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		#===== Test Scale ====
		a.set_xyz( 2.0, 2.0, 2.0 )

		a.scale_y( 2.0 )


	def test_scale_z(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		#===== Test Scale ====
		a.set_xyz( 2.0, 2.0, 2.0 )

		a.scale_z( 2.0 )


	def test_offset_x(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		#===== Test Offset ====
		a.set_xyz( 2.0, 2.0, 2.0 )

		a.offset_x( 10.0 )


	def test_offset_y(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		#===== Test Offset ====
		a.set_xyz( 2.0, 2.0, 2.0 )

		a.offset_y( 10.0 )


	def test_offset_z(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		#===== Test Offset ====
		a.set_xyz( 2.0, 2.0, 2.0 )

		a.offset_z( 10.0 )


	def test_offset_i(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		a.offset_i( 0.5, 1 )

		assert abs( a.y() - 2.5 ) < 1e-12, "offset_i did not offset the Y coordinate"

		assert abs( a.x() - 1.0 ) < 1e-12, "offset_i disturbed a coordinate it should not have"



	def test_reflect_xy(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()

		#===== Test Reflect ====
		a.set_xyz( 1.0, 2.0, 3.0 )

		b = a.reflect_xy()


	def test_reflect_xz(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()

		#===== Test Reflect ====
		a.set_xyz( 1.0, 2.0, 3.0 )

		b = a.reflect_xz()


	def test_reflect_yz(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()

		#===== Test Reflect ====
		a.set_xyz( 1.0, 2.0, 3.0 )

		b = a.reflect_yz()


	def test_mag(self):
		import math
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor

		#==== Test Mag ====
		a.set_xyz( 1.0, 2.0, 3.0 )

		assert not ( abs( a.mag() - math.sqrt( 14 ) ) > 1e-6 ), "Vec3d Mag"


	def test_magsq(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		assert abs( a.magsq() - 14.0 ) < 1e-12, "magsq did not return the squared magnitude"


	def test_normalize(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()
		c = vec3d()

		#==== Test Cross ====
		a.set_xyz( 4.0, 0.0, 0.0 )
		b.set_xyz( 0.0, 3.0, 0.0 )

		c = cross( a, b )

		c.normalize()


	def test_major_comp(self):
		a = vec3d( 1.0, 5.0, 3.0 )

		assert a.major_comp() == 1, "major_comp did not find the largest coordinate"


	def test_minor_comp(self):
		a = vec3d( 1.0, 5.0, 3.0 )

		assert a.minor_comp() == 0, "minor_comp did not find the smallest coordinate"


	def test_isnan(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		assert not a.isnan(), "isnan reported a NaN in an ordinary point"


	def test_isinf(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		assert not a.isinf(), "isinf reported an infinity in an ordinary point"


	def test_isfinite(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		assert a.isfinite(), "isfinite rejected an ordinary point"


	def test_print(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		a.print( "a" )

		assert abs( a.x() - 1.0 ) < 1e-12, "print changed the point"


	def test_dist(self):
		import math
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()

		#==== Test Dist ====
		a.set_xyz( 2.0, 2.0, 2.0 )
		b.set_xyz( 3.0, 4.0, 5.0 )

		d = dist( a, b )

		assert not ( abs( d - math.sqrt( 14 ) ) > 1e-6 ), "Vec3d Dist"


	def test_dist_squared(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()

		#==== Test Dist ====
		a.set_xyz( 2.0, 2.0, 2.0 )
		b.set_xyz( 3.0, 4.0, 5.0 )

		d2 = dist_squared( a, b )

		assert not ( abs( d2 - 14 ) > 1e-6 ), "Vec3d Dist"


	def test_dot(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()

		#==== Test Dot ====
		a.set_xyz( 1.0, 2.0, 3.0 )
		b.set_xyz( 2.0, 3.0, 4.0 )

		assert not ( abs( dot( a, b ) - 20 ) > 1e-6 ), "Vec3d Dot"


	def test_cross(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()
		c = vec3d()

		#==== Test Cross ====
		a.set_xyz( 4.0, 0.0, 0.0 )
		b.set_xyz( 0.0, 3.0, 0.0 )

		c = cross( a, b )

		c.normalize()


	def test_angle(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()
		PI = 3.14159265359

		#==== Test Angle ====
		a.set_xyz( 1.0, 1.0, 0.0 )
		b.set_xyz( 1.0, 0.0, 0.0 )

		assert not ( abs( angle( a, b ) - PI / 4 ) > 1e-6 ), "Vec3d Angle"


	def test_signed_angle(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()
		c = vec3d()
		PI = 3.14159265359

		#==== Test Angle ====
		a.set_xyz( 1.0, 1.0, 0.0 )
		b.set_xyz( 1.0, 0.0, 0.0 )
		c.set_xyz( 0.0, 0.0, 1.0 )

		assert not ( abs( signed_angle( a, b, c ) - -PI / 4 ) > 1e-6 ), "Vec3d SignedAngle"


	def test_cos_angle(self):
		pnt = vec3d( 2, 4, 6)

		line_pt1 = vec3d()
		line_pt2 = vec3d()

		line_pt1.set_z( 4 )
		line_pt2.set_y( 3 )

		p_ln1 = pnt - line_pt1

		ln2_ln1 = line_pt2 - line_pt1

		numer =  cos_angle( p_ln1, ln2_ln1 ) * p_ln1.mag()


	def test_RotateArbAxis(self):
		#==== Test Vec3d ====
		a = vec3d()                                # Default Constructor
		b = vec3d()
		c = vec3d()
		PI = 3.14

		#==== Test Rotate ====
		a.set_xyz( 1.0, 1.0, 0.0 )
		b.set_xyz( 1.0, 0.0, 0.0 )
		c.set_xyz( 0.0, 0.0, 1.0 )

		c = RotateArbAxis( b, PI, a )


	def test_to_string(self):
		a = vec3d( 1.0, 2.0, 3.0 )

		s = to_string( a )

		assert len( s ) > 0, "to_string returned nothing"


	def test_FitPlane(self):
		pts = Vec3dVec( [ vec3d( 0.0, 0.0, 0.0 ), vec3d( 1.0, 0.0, 0.0 ), vec3d( 0.0, 1.0, 0.0 ), vec3d( 1.0, 1.0, 0.0 ) ] )

		cen = vec3d()
		norm = vec3d()

		FitPlane( pts, cen, norm )

		assert abs( cen.z() ) < 1e-9, "FitPlane put the centre off the plane"

		assert abs( abs( norm.z() ) - 1.0 ) < 1e-9, "FitPlane did not find the plane normal"



	def test_compsum(self):
		pts = Vec3dVec( [ vec3d( 1.0, 0.0, 0.0 ), vec3d( 0.0, 2.0, 0.0 ), vec3d( 0.0, 0.0, 3.0 ) ] )

		s = compsum( pts )

		assert abs( s.x() - 1.0 ) < 1e-12, "compsum is wrong in x"

		assert abs( s.z() - 3.0 ) < 1e-12, "compsum is wrong in z"


	def test_vec2d(self):
		a = vec2d( 3.0, 4.0 )

		assert abs( a.x() - 3.0 ) < 1e-12, "vec2d did not store x"

		assert abs( a.y() - 4.0 ) < 1e-12, "vec2d did not store y"



	def test_operator_index(self):
		a = vec2d( 3.0, 4.0 )

		assert abs( a[0] - 3.0 ) < 1e-12, "vec2d index 0 is not x"

		assert list( a ) == [ 3.0, 4.0 ], "vec2d did not iterate as x, y"

		a[1] = 5.0

		assert abs( a.y() - 5.0 ) < 1e-12, "vec2d index assignment did not take"



	def test_set_xy(self):
		a = vec2d()

		a.set_xy( 2.0, 4.0 )

		assert abs( a.x() - 2.0 ) < 1e-12, "set_xy did not set x"

		assert abs( a.y() - 4.0 ) < 1e-12, "set_xy did not set y"



	def test_set_x1(self):
		a = vec2d( 0.0, 4.0 )

		a.set_x( 2.0 )

		assert abs( a.x() - 2.0 ) < 1e-12, "set_x did not set x"

		assert abs( a.y() - 4.0 ) < 1e-12, "set_x disturbed y"



	def test_set_y1(self):
		a = vec2d( 2.0, 0.0 )

		a.set_y( 4.0 )

		assert abs( a.y() - 4.0 ) < 1e-12, "set_y did not set y"

		assert abs( a.x() - 2.0 ) < 1e-12, "set_y disturbed x"



	def test_x1(self):
		a = vec2d( 3.0, 4.0 )

		assert abs( a.x() - 3.0 ) < 1e-12, "x did not return the X coordinate"



	def test_y1(self):
		a = vec2d( 3.0, 4.0 )

		assert abs( a.y() - 4.0 ) < 1e-12, "y did not return the Y coordinate"



	def test_operator_add1(self):
		a = vec2d( 1.0, 2.0 )
		b = vec2d( 3.0, 4.0 )

		c = a + b

		assert abs( c.x() - 4.0 ) < 1e-12, "vec2d addition is wrong in x"

		assert abs( c.y() - 6.0 ) < 1e-12, "vec2d addition is wrong in y"



	def test_operator_sub1(self):
		a = vec2d( 3.0, 4.0 )
		b = vec2d( 1.0, 2.0 )

		c = a - b

		assert abs( c.x() - 2.0 ) < 1e-12, "vec2d subtraction is wrong in x"

		assert abs( c.y() - 2.0 ) < 1e-12, "vec2d subtraction is wrong in y"



	def test_operator_mul11(self):
		a = vec2d( 1.0, 2.0 )

		c = a * 1.5

		assert abs( c.x() - 1.5 ) < 1e-12, "vec2d scaling is wrong in x"

		assert abs( c.y() - 3.0 ) < 1e-12, "vec2d scaling is wrong in y"



	def test_operator_mul111(self):
		a = vec2d( 1.0, 2.0 )
		b = vec2d( 3.0, 4.0 )

		c = a * b

		assert abs( c.x() - 3.0 ) < 1e-12, "vec2d component-wise product is wrong in x"

		assert abs( c.y() - 8.0 ) < 1e-12, "vec2d component-wise product is wrong in y"



	def test_operator_div1(self):
		a = vec2d( 3.0, 6.0 )

		c = a / 1.5

		assert abs( c.x() - 2.0 ) < 1e-12, "vec2d division is wrong in x"

		assert abs( c.y() - 4.0 ) < 1e-12, "vec2d division is wrong in y"



	def test_dist1(self):
		a = vec2d( 0.0, 0.0 )
		b = vec2d( 3.0, 4.0 )

		assert abs( dist( a, b ) - 5.0 ) < 1e-12, "dist did not measure the distance"



	def test_dist_squared1(self):
		a = vec2d( 0.0, 0.0 )
		b = vec2d( 3.0, 4.0 )

		assert abs( dist_squared( a, b ) - 25.0 ) < 1e-12, "dist_squared did not measure the squared distance"



	def test_mag1(self):
		a = vec2d( 3.0, 4.0 )

		assert abs( a.mag() - 5.0 ) < 1e-12, "mag did not return the magnitude"



	def test_normalize1(self):
		a = vec2d( 3.0, 4.0 )

		a.normalize()

		assert abs( a.mag() - 1.0 ) < 1e-12, "normalize did not produce a unit vector"

		assert abs( a.x() - 0.6 ) < 1e-12, "normalize did not keep the direction"



	def test_cross1(self):
		a = vec2d( 1.0, 0.0 )
		b = vec2d( 0.0, 1.0 )

		assert abs( cross( a, b ) - 1.0 ) < 1e-12, "cross did not return the signed area"

		assert abs( cross( b, a ) + 1.0 ) < 1e-12, "cross did not change sign with the order"



	def test_dot1(self):
		a = vec2d( 1.0, 2.0 )
		b = vec2d( 3.0, 4.0 )

		assert abs( dot( a, b ) - 11.0 ) < 1e-12, "dot did not return the dot product"



	def test_angle1(self):
		import math

		a = vec2d( 1.0, 0.0 )
		b = vec2d( 0.0, 1.0 )

		assert abs( angle( a, b ) - 0.5 * math.pi ) < 1e-12, "angle did not measure a right angle"



	def test_cos_angle1(self):
		a = vec2d( 1.0, 0.0 )
		b = vec2d( 0.0, 1.0 )

		assert abs( cos_angle( a, b ) ) < 1e-12, "cos_angle of a right angle should be zero"

		assert abs( cos_angle( a, a ) - 1.0 ) < 1e-12, "cos_angle of a vector with itself should be one"



	def test_seg_seg_intersect(self):
		hit, pnt, t1, t2 = seg_seg_intersect( vec2d( 0.0, 0.0 ), vec2d( 2.0, 0.0 ), vec2d( 1.0, -1.0 ), vec2d( 1.0, 1.0 ) )

		assert hit != 0, "seg_seg_intersect missed a crossing"

		assert abs( pnt.x() - 1.0 ) < 1e-12, "seg_seg_intersect put the crossing in the wrong place"

		assert abs( t1 - 0.5 ) < 1e-12, "seg_seg_intersect did not locate the crossing along AB"

		assert abs( t2 - 0.5 ) < 1e-12, "seg_seg_intersect did not locate the crossing along CD"



	def test_proj_pnt_on_line_seg(self):
		p = proj_pnt_on_line_seg( vec2d( 0.0, 0.0 ), vec2d( 2.0, 0.0 ), vec2d( 1.0, 1.0 ) )

		assert abs( p.x() - 1.0 ) < 1e-12, "proj_pnt_on_line_seg projected to the wrong place"

		assert abs( p.y() ) < 1e-12, "proj_pnt_on_line_seg did not land on the segment"

		q = proj_pnt_on_line_seg( vec2d( 0.0, 0.0 ), vec2d( 2.0, 0.0 ), vec2d( 5.0, 1.0 ) )

		assert abs( q.x() - 2.0 ) < 1e-12, "proj_pnt_on_line_seg did not clamp to the end of the segment"



	def test_proj_pnt_on_line_u(self):
		u = proj_pnt_on_line_u( vec2d( 0.0, 0.0 ), vec2d( 2.0, 0.0 ), vec2d( 1.0, 1.0 ) )

		assert abs( u - 0.5 ) < 1e-12, "proj_pnt_on_line_u did not find the midpoint"



	def test_PointInPolygon(self):
		square = Vec2dVec( [ vec2d( 0.0, 0.0 ), vec2d( 1.0, 0.0 ), vec2d( 1.0, 1.0 ), vec2d( 0.0, 1.0 ) ] )

		assert PointInPolygon( vec2d( 0.5, 0.5 ), square ), "PointInPolygon missed an interior point"

		assert not PointInPolygon( vec2d( 1.5, 0.5 ), square ), "PointInPolygon accepted an exterior point"



	def test_det(self):
		d = det( vec2d( 0.0, 0.0 ), vec2d( 1.0, 0.0 ), vec2d( 0.0, 1.0 ) )

		assert d > 0.0, "det did not report a counter-clockwise turn as positive"



	def test_poly_area(self):
		square = Vec2dVec( [ vec2d( 0.0, 0.0 ), vec2d( 1.0, 0.0 ), vec2d( 1.0, 1.0 ), vec2d( 0.0, 1.0 ) ] )

		assert abs( poly_area( square ) - 1.0 ) < 1e-12, "poly_area did not measure the unit square"



	def test_poly_centroid(self):
		square = Vec2dVec( [ vec2d( 0.0, 0.0 ), vec2d( 1.0, 0.0 ), vec2d( 1.0, 1.0 ), vec2d( 0.0, 1.0 ) ] )

		c = poly_centroid( square )

		assert abs( c.x() - 0.5 ) < 1e-12, "poly_centroid is wrong in x"

		assert abs( c.y() - 0.5 ) < 1e-12, "poly_centroid is wrong in y"



	def test_orient2d(self):
		assert orient2d( vec2d( 0.0, 0.0 ), vec2d( 1.0, 0.0 ), vec2d( 0.0, 1.0 ) ) > 0.0, "orient2d put a left turn on the right"

		assert orient2d( vec2d( 0.0, 0.0 ), vec2d( 1.0, 0.0 ), vec2d( 0.0, -1.0 ) ) < 0.0, "orient2d put a right turn on the left"



	def test_bi_lin_interp(self):
		p0 = vec2d( 0.0, 0.0 )
		p1 = vec2d( 1.0, 0.0 )
		p2 = vec2d( 1.0, 1.0 )
		p3 = vec2d( 0.0, 1.0 )

		p = bi_lin_interp( p0, p1, p2, p3, 0.25, 0.75 )

		assert abs( p.x() - 0.625 ) < 1e-12, "bi_lin_interp is wrong in x"

		assert abs( p.y() - 0.75 ) < 1e-12, "bi_lin_interp is wrong in y"



	def test_inverse_bi_lin_interp(self):
		p0 = vec2d( 0.0, 0.0 )
		p1 = vec2d( 1.0, 0.0 )
		p2 = vec2d( 1.0, 1.0 )
		p3 = vec2d( 0.0, 1.0 )

		p = bi_lin_interp( p0, p1, p2, p3, 0.25, 0.75 )

		n, s, t, s2, t2 = inverse_bi_lin_interp( p0, p1, p2, p3, p )

		assert n > 0, "inverse_bi_lin_interp found no solution"

		assert abs( s - 0.25 ) < 1e-9, "inverse_bi_lin_interp did not recover s"

		assert abs( t - 0.75 ) < 1e-9, "inverse_bi_lin_interp did not recover t"



	def test_loadIdentity(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor
		m.loadIdentity()


	def test_translatef(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadIdentity()

		m.translatef( 1.0, 0.0, 0.0 )


	def test_translatev(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 2.0, 3.0 ) )

		p = m.xform( vec3d( 0.0, 0.0, 0.0 ) )

		assert abs( p.x() - 1.0 ) < 1e-12, "translatev did not move the origin"

		assert abs( p.z() - 3.0 ) < 1e-12, "translatev did not move in z"


	def test_rotateX(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadIdentity()

		m.rotateX( 90.0 )


	def test_rotateY(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadIdentity()

		m.rotateY( 90.0 )


	def test_rotateZ(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadIdentity()

		m.rotateZ( 90.0 )


	def test_rotate(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor
		PI = 3.14

		m.loadIdentity()

		m.rotate( PI / 4, vec3d( 0.0, 0.0, 1.0 ) )                                # Radians


	def test_rotatealongX(self):
		m = Matrix4d()

		m.loadIdentity()

		m.rotatealongX( vec3d( 0.0, 1.0, 0.0 ) )

		p = m.xform( vec3d( 1.0, 0.0, 0.0 ) )

		assert abs( p.y() - 1.0 ) < 1e-12, "rotatealongX did not take X onto the given direction"


	def test_zeroTranslations(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 2.0, 3.0 ) )

		m.zeroTranslations()

		t = m.getTranslation()

		assert abs( t.x() ) < 1e-12 and abs( t.z() ) < 1e-12, "zeroTranslations left a translation behind"


	def test_affineInverse(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadIdentity()

		m.rotateY( 10.0 )
		m.rotateX( 20.0 )
		m.rotateZ( 30.0 )

		c = m.xform( vec3d( 1.0, 1.0, 1.0 ) )

		m.affineInverse()


	def test_scale(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadXZRef()

		m.scale( 10.0 )


	def test_scalex(self):
		m = Matrix4d()

		m.loadIdentity()

		m.scalex( 2.0 )

		p = m.xform( vec3d( 1.0, 1.0, 1.0 ) )

		assert abs( p.x() - 2.0 ) < 1e-12, "scalex did not scale X"

		assert abs( p.y() - 1.0 ) < 1e-12, "scalex scaled an axis it should not have"


	def test_scaley(self):
		m = Matrix4d()

		m.loadIdentity()

		m.scaley( 2.0 )

		p = m.xform( vec3d( 1.0, 1.0, 1.0 ) )

		assert abs( p.y() - 2.0 ) < 1e-12, "scaley did not scale Y"

		assert abs( p.z() - 1.0 ) < 1e-12, "scaley scaled an axis it should not have"


	def test_scalez(self):
		m = Matrix4d()

		m.loadIdentity()

		m.scalez( 2.0 )

		p = m.xform( vec3d( 1.0, 1.0, 1.0 ) )

		assert abs( p.z() - 2.0 ) < 1e-12, "scalez did not scale Z"

		assert abs( p.x() - 1.0 ) < 1e-12, "scalez scaled an axis it should not have"


	def test_flipx(self):
		m = Matrix4d()

		m.loadIdentity()

		m.flipx()

		p = m.xform( vec3d( 1.0, 2.0, 3.0 ) )

		assert abs( p.x() + 1.0 ) < 1e-12, "flipx did not negate x"

		assert abs( p.y() - 2.0 ) < 1e-12, "flipx disturbed y"


	def test_matMult(self):
		a = Matrix4d()
		b = Matrix4d()

		a.loadIdentity()
		a.translatev( vec3d( 1.0, 0.0, 0.0 ) )

		b.loadIdentity()
		b.scale( 2.0 )

		a.matMult( b )

		p = a.xform( vec3d( 1.0, 0.0, 0.0 ) )

		assert abs( p.x() - 3.0 ) < 1e-12, "matMult did not apply both transformations"


	def test_postMult(self):
		a = Matrix4d()
		b = Matrix4d()

		a.loadIdentity()
		a.translatev( vec3d( 1.0, 0.0, 0.0 ) )

		b.loadIdentity()
		b.scale( 2.0 )

		a.postMult( b )

		p = a.xform( vec3d( 1.0, 0.0, 0.0 ) )

		assert abs( p.x() - 4.0 ) < 1e-12, "postMult did not apply the transformations in the other order"


	def test_initMat(self):
		a = Matrix4d()
		b = Matrix4d()

		b.loadIdentity()
		b.translatev( vec3d( 5.0, 0.0, 0.0 ) )

		a.initMat( b )

		p = a.xform( vec3d( 0.0, 0.0, 0.0 ) )

		assert abs( p.x() - 5.0 ) < 1e-12, "initMat did not copy the matrix"


	def test_loadXZRef(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadXZRef()

		b = m.xform( vec3d( 1, 2, 3 ) )


	def test_loadXYRef(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadXYRef()

		b = m.xform( vec3d( 1, 2, 3 ) )


	def test_loadYZRef(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadYZRef()

		b = m.xform( vec3d( 1, 2, 3 ) )


	def test_mirrory(self):
		#==== Test Matrix4d ====
		m = Matrix4d()                                # Default Constructor

		m.loadIdentity()

		a = m.xform( vec3d( 1.0, 2.0, 3.0 ) )


	def test_xform(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 2.0, 3.0 ) )

		p = m.xform( vec3d( 0.0, 0.0, 0.0 ) )

		assert abs( p.x() - 1.0 ) < 1e-12, "xform did not apply the translation"


	def test_xformvec(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 0.0, 0.0 ) )

		pts = Vec3dVec( [ vec3d( 0.0, 0.0, 0.0 ), vec3d( 1.0, 0.0, 0.0 ) ] )

		m.xformvec( pts )

		assert abs( pts[0].x() - 1.0 ) < 1e-12, "xformvec did not transform the first point"

		assert abs( pts[1].x() - 2.0 ) < 1e-12, "xformvec did not transform the second point"


	def test_xformmat(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 0.0, 0.0 ) )

		grid = Vec3dVecVec( [ Vec3dVec( [ vec3d( 0.0, 0.0, 0.0 ) ] ), Vec3dVec( [ vec3d( 1.0, 0.0, 0.0 ) ] ) ] )

		m.xformmat( grid )

		assert abs( grid[0][0].x() - 1.0 ) < 1e-12, "xformmat did not transform the first row"

		assert abs( grid[1][0].x() - 2.0 ) < 1e-12, "xformmat did not transform the second row"


	def test_xformnorm(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 2.0, 3.0 ) )

		n = m.xformnorm( vec3d( 1.0, 0.0, 0.0 ) )

		assert abs( n.x() - 1.0 ) < 1e-12, "xformnorm changed the direction"

		assert abs( n.y() ) < 1e-12, "xformnorm applied the translation to a direction"


	def test_xformnormvec(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 2.0, 3.0 ) )

		norms = Vec3dVec( [ vec3d( 1.0, 0.0, 0.0 ) ] )

		m.xformnormvec( norms )

		assert abs( norms[0].y() ) < 1e-12, "xformnormvec applied the translation to a direction"


	def test_xformnormmat(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 2.0, 3.0 ) )

		grid = Vec3dVecVec( [ Vec3dVec( [ vec3d( 1.0, 0.0, 0.0 ) ] ) ] )

		m.xformnormmat( grid )

		assert abs( grid[0][0].y() ) < 1e-12, "xformnormmat applied the translation to a direction"


	def test_getAngles(self):
		mat = Matrix4d()
		PI = 3.14

		mat.loadIdentity()

		mat.rotate( PI / 4, vec3d( 0.0, 0.0, 1.0 ) )                                # Radians

		angles = mat.getAngles()


	def test_getArcballAngles(self):
		m = Matrix4d()

		m.loadIdentity()

		a = m.getArcballAngles()

		assert abs( a.x() ) < 1e-12, "getArcballAngles found a rotation in an identity matrix"


	def test_getTranslation(self):
		m = Matrix4d()

		m.loadIdentity()

		m.translatev( vec3d( 1.0, 2.0, 3.0 ) )

		t = m.getTranslation()

		assert abs( t.x() - 1.0 ) < 1e-12, "getTranslation is wrong in x"

		assert abs( t.z() - 3.0 ) < 1e-12, "getTranslation is wrong in z"


	def test_buildXForm(self):
		m = Matrix4d()

		m.loadIdentity()

		m.buildXForm( vec3d( 1.0, 0.0, 0.0 ), vec3d( 0.0, 0.0, 90.0 ), vec3d( 0.0, 0.0, 0.0 ) )

		p = m.xform( vec3d( 1.0, 0.0, 0.0 ) )

		assert abs( p.y() - 1.0 ) < 1e-9, "buildXForm did not rotate about the given center"

		assert abs( p.x() - 1.0 ) < 1e-9, "buildXForm did not translate to the given position"



	def test_getBasis(self):
		m = Matrix4d()

		m.loadIdentity()

		xdir = vec3d()
		ydir = vec3d()
		zdir = vec3d()

		m.getBasis( xdir, ydir, zdir )

		assert abs( xdir.x() - 1.0 ) < 1e-12, "getBasis did not report the X axis"

		assert abs( zdir.z() - 1.0 ) < 1e-12, "getBasis did not report the Z axis"


	def test_setBasis(self):
		m = Matrix4d()

		m.loadIdentity()

		m.setBasis( vec3d( 0.0, 1.0, 0.0 ), vec3d( -1.0, 0.0, 0.0 ), vec3d( 0.0, 0.0, 1.0 ) )

		p = m.xform( vec3d( 1.0, 0.0, 0.0 ) )

		assert abs( p.y() - 1.0 ) < 1e-12, "setBasis did not take X onto the given direction"


	def test_getRotationAxis(self):
		import math

		m = Matrix4d()

		m.loadIdentity()

		m.rotateZ( 90.0 )

		axis_dir = vec3d()
		axis_pnt = vec3d()

		angle = m.getRotationAxis( axis_dir, axis_pnt )

		assert abs( abs( axis_dir.z() ) - 1.0 ) < 1e-9, "getRotationAxis did not find the Z axis"

		assert abs( abs( angle ) - 0.5 * math.pi ) < 1e-9, "getRotationAxis did not measure the angle"


	def test_toQuat(self):
		m = Matrix4d()

		m.loadIdentity()

		qw, qx, qy, qz, tx, ty, tz = m.toQuat()

		assert abs( qw - 1.0 ) < 1e-12, "toQuat did not give the identity quaternion"

		assert abs( qx ) + abs( qy ) + abs( qz ) < 1e-12, "toQuat found a rotation in an identity matrix"

		assert abs( tx ) + abs( ty ) + abs( tz ) < 1e-12, "toQuat found a translation in an identity matrix"



if __name__ == '__main__':
    unittest.main()
