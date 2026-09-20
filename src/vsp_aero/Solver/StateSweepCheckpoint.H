// This file is released under the NASA Open Source Agreement (NOSA), version
// 1.3, as detailed in the LICENSE file accompanying this software.
// Checkpoint I/O only; shared by the solver and Windows contention regression.
#pragma once
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <errno.h>
#ifdef WIN32
#include <windows.h>
#endif

static void StateSweepWriteCheckpoint(const char *Path, uint64_t Hash, uint64_t Next, uint64_t Total)
{
    char Temporary[4096];
    snprintf(Temporary,sizeof(Temporary),"%s.tmp",Path);
    FILE *File = fopen(Temporary,"w");
    if ( File == NULL ) { printf("Could not write State Sweep checkpoint: %s\n",Temporary); exit(1); }
    fprintf(File,"%016llx %llu %llu\n",(unsigned long long)Hash,
            (unsigned long long)Next,(unsigned long long)Total);
    fflush(File);
    fclose(File);
#ifdef WIN32
    // ReplaceFile permits an existing target to remain open by readers using
    // FILE_SHARE_DELETE. MoveFileEx does not provide that replacement behavior.
    // Keep retries for unrelated transient locks; never truncate the old record.
    int Published = 0;
    DWORD PublishError = ERROR_SUCCESS;
    for ( int Attempt = 0 ; Attempt < 40 && !Published ; Attempt++ ) {
       Published = ReplaceFileA(Path,Temporary,NULL,0,NULL,NULL) != 0;
       if ( !Published ) {
          PublishError = GetLastError();
          if ( PublishError == ERROR_FILE_NOT_FOUND ) {
             // First publication only. A racing creator must not be overwritten
             // with MoveFileEx; retry ReplaceFile on the next attempt instead.
             Published = MoveFileExA(Temporary,Path,MOVEFILE_WRITE_THROUGH) != 0;
             if ( !Published ) PublishError = GetLastError();
          }
       }
       if ( !Published ) Sleep(50);
    }
    if ( !Published ) {
       printf("Could not publish State Sweep checkpoint: %s (Windows error %lu; 40 attempts; temporary file %s retained)\n",Path,(unsigned long)PublishError,Temporary);
       exit(1);
    }
#else
    if ( rename(Temporary,Path) != 0 ) {
       printf("Could not publish State Sweep checkpoint: %s (errno %d)\n",Path,errno); exit(1);
    }
#endif
}
