// This is our program to read slha files and compute cross sections

#include "Pythia8/Pythia.h"
#include <sstream>
#include <cstdlib>
using namespace Pythia8;
using namespace std;

int run( int nevents, float sqrts /* in TeV */, const string & slhafile,
         const string & cfgfile )
{
  cout << "[pythia8.exe] we run with " << nevents << ", sqrts=" << sqrts << " TeV"
       << ", slhafile=" << slhafile << endl;
  // exit( 0 );
  // Generator. Process selection. LHC initialization. Histogram.
  Pythia pythia;
  pythia.readFile( cfgfile );
  ostringstream o1, o2, o3;
  o1 << "Main:numberOfEvents=" << nevents;
  pythia.readString( o1.str() );
  o2 << "Beams:eCM=" << sqrts * 1000;
  pythia.readString( o2.str() );
  o3 << "SLHA:file=" << slhafile;
  pythia.readString ( o3.str() );
  pythia.init();

  // Begin event loop. Generate event. Skip if error.
  for (int iEvent = 0; iEvent < nevents; ++iEvent ) {
    if (!pythia.next()) continue;
  }
  pythia.stat();
  return 0;
}

void help( const char * name )
{
  cout << "syntax: " << name << " [-h] [-n <nevents>] [-s <sqrts>] [-f <slhafile>] " 
       << "[-c <cfgfile>]" << endl;
  cout << "        -n <nevents>:  number of events to simulate [10000]." << endl;
  cout << "        -s <sqrts>:    center-of mass energy, in TeV [13]." << endl;
  cout << "        -f <slhafile>: slhafile [test.slha]." << endl;
  cout << "        -c <cfgfile>: the pythia8 config file [./pythia8.cfg]." << endl;
  exit( 0 );
};

int main( int argc, const char * argv[] ) {
  int nevents = 10000;
  float sqrts = 13;
  string slhafile = "test.slha";
  string cfgfile = "./pythia8.cfg";
  for ( int i=1; i!=argc ; ++i )
  {
    string s = argv[i];
    if ( s== "-h" )
    {
      help ( argv[0] );
    }

    if ( s== "-n" )
    {
      if ( argc < i+2 ) help ( argv[0] );
      nevents = atoi ( argv[i+1] );
      i++;
      continue;
    }

    if ( s== "-f" )
    {
      if ( argc < i+2 ) help ( argv[0] );
      slhafile = argv[i+1];
      i++;
      continue;
    }

    if ( s== "-c" )
    {
      if ( argc < i+2 ) help ( argv[0] );
      cfgfile = argv[i+1];
      i++;
      continue;
    }

    if ( (s== "-s") )
    {
      if ( argc < i+2 ) help ( argv[0] );
      sqrts = atof ( argv[i+1] );
      if ( sqrts > 360. )
      {
        cout << "Warning. You supplied an extremely high number for sqrts: "
             << sqrts << " TeV. Could it be that you gave the value in GeV?" << endl;
      }
      i++;
      continue;
    }

    cout << "Error. Argument " << argv[i] << " unknown." << endl;
    help ( argv[0] );
  };

  return run ( nevents, sqrts, slhafile, cfgfile );
}
