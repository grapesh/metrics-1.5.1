#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 13:12:59 2018

@author: Sergey.Vinogradov@noaa.gov
"""
import os,sys
import argparse
import glob
import csdlpy
import datetime

#==============================================================================
def timestamp():
    print '------'
    print '[Time]: ' + str(datetime.datetime.utcnow()) + ' UTC'
    print '------'
    
#==============================================================================
def read_cmd_argv (argv):

    parser = argparse.ArgumentParser()
    
    parser.add_argument('-i','--hsofsDir',       required=True)
    parser.add_argument('-s','--stormID',        required=True)
    parser.add_argument('-z','--stormCycle',     required=True)    
    parser.add_argument('-o','--outputDir',      required=True)
    parser.add_argument('-t','--tmpDir',         required=True)
    parser.add_argument('-p','--pltCfgFile',     required=True)
    parser.add_argument('-u','--ftpLogin',       required=True)
    parser.add_argument('-f','--ftpPath',        required=True)
    
    args = parser.parse_args()    
    print '[info]: hsofs_post.py is configured with :', args
    return args
    
#==============================================================================
def run_post(argv):

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))    
    from hsofs import plot
    
    doMaxele   = True
    doStations = True
    
    #Receive command line arguments
    args = read_cmd_argv(argv)

    #Locate hsofs path
    hsofsPath = args.hsofsDir +'hsofs.'+ args.stormCycle[:-2] +'/'
    if not os.path.exists(hsofsPath):
        print '[error]: hsofs path ' +hsofsPath+ ' does not exist. Exiting'
        return
    
    ens   = [] #Compile the list of available ensemble members

    fls   = glob.glob(hsofsPath + 'hsofs.' + args.stormID + '.' + \
                    args.stormCycle + '*.surfaceforcing')    
    for f in fls:
        s = os.path.basename(f).split('.')
        ens.append(s[3] +'.'+ s[4] +'.'+ s[5] +'.'+ s[6])
        if s[5] == 'ofcl':
            advisoryTrackFile = f
    print '[info]: ', str(len(ens)),' hsofs ensembles detected: ', ens
           
    # Try to create tmp directory
    if not os.path.exists(args.tmpDir):
        print '[warn]: tmpDir='+args.tmpDir+' does not exist. Trying to mkdir.'
        try:
            os.makedirs(args.tmpDir)
        except:
            print '[warn]: cannot make tmpDir=' +args.tmpDir
            args.tmpDir = os.path.dirname(os.path.realpath(__file__))
            print '[warn]: look for your output in a current dir='+args.tmpDir

    # Read plotting parameters                   
    pp = csdlpy.plotter.read_config_ini (args.pltCfgFile)
    
    # Define local files
    gridFile      = os.path.join(args.tmpDir,'fort.14')
    coastlineFile = os.path.join(args.tmpDir,'coastline.dat')
    citiesFile    = os.path.join(args.tmpDir,'cities.csv')
    
    timestamp()
    # Download files if they do not exist
    csdlpy.transfer.download (      pp['Grid']['url'],      gridFile)
    csdlpy.transfer.download ( pp['Coastline']['url'], coastlineFile)
    csdlpy.transfer.download (    pp['Cities']['url'],    citiesFile)
    
    timestamp()
    grid   = csdlpy.adcirc.readGrid(gridFile)
    coast  = csdlpy.plotter.readCoastline(coastlineFile)
    advTrk = csdlpy.atcf.readTrack(advisoryTrackFile)
    
    # Max elevations
    if doMaxele:
        tracks = []
        for e in ens:
            timestamp()
            
            maxeleFile = \
                    hsofsPath + 'hsofs.' + args.stormID + '.' + \
                    args.stormCycle + '.' + e + '.fields.maxele.nc'
            trackFile = \
                    hsofsPath + 'hsofs.' + args.stormID + '.' + \
                    args.stormCycle + '.' + e + '.surfaceforcing'

            maxele = csdlpy.estofs.getFieldsWaterlevel (maxeleFile, 'zeta_max')    
            track = csdlpy.atcf.readTrack(trackFile)       
            tracks.append( track )
            
            titleStr = 'HSOFS experimental ' + args.stormID + \
                    '.' + args.stormCycle + '.' + e + ' MAX ELEV ' + \
                    pp['General']['units'] + ', ' + pp['General']['datum']

            plotFile = args.outputDir + args.stormID +'.'+ \
                        args.stormCycle +'.'+ e +'.maxele.png'
            plot.maxele (maxele, track, advTrk, grid, coast, pp, titleStr, plotFile)
            csdlpy.transfer.upload(plotFile, args.ftpLogin, args.ftpPath)
    
    # Plot ens statistics: maxPS and rangePS
    try:
        timestamp()
        psFile = hsofsPath + 'hsofs.' + args.stormID + '.' + \
                    args.stormCycle + '.fields.maxPS.nc'
        maxPS = csdlpy.estofs.getFieldsWaterlevel (psFile, 'zeta_max')
        titleStr = 'HSOFS experimental ' + args.stormID + \
                    '.' + args.stormCycle + '.maxPS MAX ELEV ' + \
                    pp['General']['units'] + ', ' + pp['General']['datum']
        plotFile = args.outputDir + args.stormID +'.'+ args.stormCycle +'.maxPS.png'
        plot.maxele (maxPS, tracks, advTrk, grid, coast, pp, titleStr, plotFile)
        csdlpy.transfer.upload(plotFile, args.ftpLogin, args.ftpPath)

        timestamp()
        psFile = hsofsPath + 'hsofs.' + args.stormID + '.' + \
                    args.stormCycle + '.fields.rangePS.nc'

        maxPS = csdlpy.estofs.getFieldsWaterlevel (psFile, 'zeta_max')
        titleStr = 'HSOFS experimental ' + args.stormID + \
                    '.' + args.stormCycle + '.rangePS MAX ELEV ' + \
                    pp['General']['units']
        plotFile = args.outputDir + args.stormID +'.'+ args.stormCycle +'.rangePS.png'
        pp['Limits']['cmax'] = 2.0
        plot.maxele (maxPS, tracks, advTrk, grid, coast, pp, titleStr, plotFile)
        csdlpy.transfer.upload(plotFile, args.ftpLogin, args.ftpPath)
    except:
        print '[error]: ensemble max and range were NOT plotted.'

    # Plot time series for all ensembles
    if doStations:
        timestamp()
        ensFiles = []
        titleStr = 'HSOFS experimental ' + args.stormID + \
                    '.' + args.stormCycle + ' CWL ' + \
                    pp['General']['units']
        plotPath = args.outputDir + args.stormID +'.'+ args.stormCycle +'.ts.'
        
        for e in ens:
            ensFiles.append(hsofsPath + 'hsofs.' + args.stormID + '.' + \
                            args.stormCycle + '.' + e + '.points.waterlevel.nc')
            
        plot.stations (ensFiles, ens, pp, titleStr, plotPath, args)
    # TODO plot time series    

    #7. Clean up temporary folder

#==============================================================================    
if __name__ == "__main__":

    timestamp()
    run_post (sys.argv[1:])
    timestamp()
    
    
