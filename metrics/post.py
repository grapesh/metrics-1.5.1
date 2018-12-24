#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: Sergey.Vinogradov@noaa.gov
"""
import os,sys
import argparse
import csdlpy
import datetime
import glob
import numpy as np
# Move to plot.py
import matplotlib
matplotlib.use('Agg',warn=False)
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.dates as mdates

#==============================================================================
def timestamp():
    print '------'
    print '[Time]: ' + str(datetime.datetime.utcnow()) + ' UTC'
    print '------'
    
#==============================================================================
def findLatestCycle (dirMask):
    
    dirs = glob.glob(dirMask+'*')
    latestDir = max(dirs, key=os.path.getctime)    
    D = os.path.basename(latestDir).split('.')[-1]

    files = glob.glob(latestDir + '/*.points.cwl.nc')
    latestFile = max(files)

    F = os.path.basename(latestFile)
    latestCycle =  D + F[F.find('.t')+2:F.find('z.')]

    return latestCycle
    
#==============================================================================
def read_cmd_argv (argv):

    parser = argparse.ArgumentParser()
    
    parser.add_argument('-i','--ofsDir',         required=True)
    parser.add_argument('-s','--domain',         required=True)
    parser.add_argument('-z','--stormCycle',     required=True)    
    parser.add_argument('-o','--outputDir',      required=True)
    parser.add_argument('-t','--tmpDir',         required=True)
    parser.add_argument('-p','--pltCfgFile',     required=True)
    parser.add_argument('-u','--ftpLogin',       required=True)
    parser.add_argument('-f','--ftpPath',        required=True)
    
    args = parser.parse_args()    
           
    if 'latest' in args.stormCycle:
        args.stormCycle = findLatestCycle(args.ofsDir+'estofs_'+args.domain+'.')
        
    print '[info]: estofs_post.py is configured with :', args
    return args
    
#==============================================================================
def run_post(argv):

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))    
    from metrics import plot
    
    #Receive command line arguments
    args = read_cmd_argv(argv)

    # Read plotting parameters                   
    pp = csdlpy.plotter.read_config_ini (args.pltCfgFile)
    timestamp()

    # Try to create tmp directory
    if not os.path.exists(args.tmpDir):
        print '[warn]: tmpDir='+args.tmpDir+' does not exist. Trying to mkdir.'
        try:
            os.makedirs(args.tmpDir)
        except:
            print '[warn]: cannot make tmpDir=' +args.tmpDir
            args.tmpDir = os.path.dirname(os.path.realpath(__file__))
            print '[warn]: look for your output in a current dir='+args.tmpDir

    #Locate available estofs paths
    #ofsPattern = args.ofsDir +'estofs_'+ args.domain + '.*'
    ofsPattern = args.ofsDir +'*'  
    ofsPaths   = sorted( glob.glob(ofsPattern) )#, \
                        #key=os.path.getmtime )
    print '[info]: looking for pattern ', ofsPattern

    if len(ofsPaths) == 0:
        print '[error]: ofs path ' + ofsPaths+ ' does not exist. Exiting'
        return
    
    cwls = []
    htps = []
    for p in ofsPaths:
        files =     sorted( glob.glob(os.path.join(p,'*z.points.cwl.nc')), \
                        key=os.path.getmtime )    
        files_htp = sorted( glob.glob(os.path.join(p,'*z.points.htp.nc')), \
                        key=os.path.getmtime )
 
        for f in files:
            cwls.append( csdlpy.estofs.getPointsWaterlevel ( f ) )
        for f in files_htp:
            htps.append( csdlpy.estofs.getPointsWaterlevel ( f ) )    
    print '[info]: number of forecasts found: ', str(len(cwls))   

    # Compute surge fcst
    swl = []
    for n in range(len(cwls)):
        swl.append( cwls[n]['zeta'] - htps[n]['zeta'])       

    # Download master list
    masterListRemote = pp['Stations']['url']
    masterListLocal  = 'masterlist.csv'
    csdlpy.transfer.download(masterListRemote, masterListLocal)

    # Extract NOS IDs     
    nosids = []
    for ids in cwls[0]['stations']:
        datums, floodlevels, nosid, stationTitle = \
            csdlpy.obs.parse.setDatumsFloodLevels (ids, masterListLocal)
        nosids.append(nosid)

    #Find date range in forecasts    
    fx1 = []
    fx2 = []
    for c in cwls:
        span = min(c['time']), max(c['time'])
        fx1.append(span[0]) 
        fx2.append(span[1])
    forecastStartDate = min(fx1)
    forecastEndDate   = max(fx2)
    print '[info]: Forecasts cover: ', forecastStartDate, forecastEndDate

    # Define skill assessment period ( a full UTC day prior to now)
    now = datetime.datetime.utcnow()
    now = datetime.datetime.strptime('2018111623','%Y%m%d%H')

    print '[info]: Date now: ', now
    skillStartDate = now-datetime.timedelta(days=1)
    skillStartDate = skillStartDate.replace(hour=0, minute=0)
    skillEndDate   = skillStartDate+datetime.timedelta(hours=1*24)
    print '[info]: Skill Assessment Period: ', skillStartDate, skillEndDate
    
    nosid = '8449130' # Nantucket
    nosid = '8727520' # Cedar Key FL    
    nosid = '8720218' # Mayport
    nosid = '8516945' # Kings Point
    nosid = '8443970' # Boston
    nosid = '8518750' # The Battery
    nosid = '8410140' # Eastport ME
    nosid = '8423898' # Portsmouth NH
    nosid = '8467150' # Bridgeport CT
    nosid = '8639348' # Money Point VA
    nosid = '8665530' # Charleston NC
    nosid = '8721604' # Trident Pier FL
    nosid = '8725110' # Key West
    nosid = '8735180' # Dauphin I AL
    nosid = '8747437' # Waveland MS
    nosid = '8770475' # Port Arthur TX
    nosid = '8771341' # Galveston Bay entrance TX
    nosid = '9755371' # San Juan PR 
    nosid = '9761115' # Barbuda
    nosid = '8418150' # Portland ME
    nosid = '8443970' # Boston
    nosid = '8510560' # Montauk NY
    nosid = '8531680' # Sandy Hook NJ
    nosid = '8573927' # Chesapeake City MD
    nosid = '8652587' # Oregon Inlet MC
    nosid = '8447386' # Fall river MA
    nosid = '8534720' # Atlantic City NJ 
    nosid = '8518750' # The Battery
    nosid = '8531680' # Sandy Hook NJ
    nosid = '8461490' # New London CT
    nosid = '8534720' # Atlantic City NJ 
    
    observed  = csdlpy.obs.coops.getData(nosid, [skillStartDate, skillEndDate], \
                                                product='waterlevelrawsixmin')
    predicted = csdlpy.obs.coops.getData(nosid, [skillStartDate, skillEndDate], \
                                                product='predictions')
    surge = []
    for n in range(len(observed['values'])):
        surge.append( observed['values'][n] - predicted['values'][n] )

    # Plot
    #xlim = (forecastStartDate, forecastEndDate)
    xlim = (skillStartDate, skillEndDate)
    ylim = (-2, 3)
    # Stage the plot with datums and floodlevels   
    datums, floodlevels, nosid, stationTitle = \
            csdlpy.obs.parse.setDatumsFloodLevels (nosid, masterListLocal)
    

    fig, ax, ax2 = csdlpy.plotter.stageStationPlot ( xlim, ylim,
                                        now, datums, floodlevels)
    titleString = cwls[0]['stations'][nosids.index(nosid)] + ' CWL: [' + \
                  xlim[0].strftime('%m/%d %H:%MZ') + '--' + \
                  xlim[1].strftime('%m/%d %H:%MZ') + ']'
    plt.title( titleString, fontsize=9 )
    # PLot Time Series 
    m_metrics_CWL = []
    m_leadtime    = []
    
    for n in range(len(cwls)):
        c = cwls[n]
        ctime = c['time']
        if ctime[0] <= skillStartDate + datetime.timedelta(hours=1) and ctime[-1] >= skillEndDate - datetime.timedelta(hours=1):
            idx1 = np.where( np.datetime64(skillStartDate) <= ctime)[0]
            idx2 = np.where( np.datetime64(skillEndDate)   >= ctime)[0]
            idx  = list(set(idx1).intersection(idx2))

            print 'ctime=', ctime[0], ' to ', ctime[-1] 
            print 'len idx=', len(idx)
                    
            refDates, obsValsProjCWL, modValsProjCWL = \
                csdlpy.interp.projectTimeSeries (observed['dates'], observed['values'], \
                                             c['time'][idx], \
                                             c['zeta'][idx,nosids.index(nosid)], \
                                             refStepMinutes=6)

            M = csdlpy.valstat.metrics (obsValsProjCWL, modValsProjCWL, refDates)
            m_metrics_CWL.append(M)

            leadHours = -1.*round(1/3600.*(ctime[0] - skillStartDate).total_seconds())
            print 'leadHours=',  leadHours
            m_leadtime.append(leadHours)              
            ax.plot(refDates, modValsProjCWL, '.', linewidth=1)
            
            peak_mod_val = np.nanmax(modValsProjCWL)
            peak_mod_dat = refDates[np.nanargmax(modValsProjCWL)]
            ax.plot(peak_mod_dat,peak_mod_val,'ok')
        else:
            print '[warn]: skipping nowcasts, ctime=', ctime[0], ' to ', ctime[-1]
    
    ax.plot(refDates, obsValsProjCWL,'.', color='lime',linewidth=5.0)
    peak_obs_val = np.nanmax(obsValsProjCWL)
    peak_obs_dat = refDates[np.nanargmax(obsValsProjCWL)]
    ax.plot(peak_obs_dat, peak_obs_val,'o',markerfacecolor='limegreen',markeredgecolor='k')

    ax.set_ylabel ('WATER LEVELS, meters MSL')
    ax2.set_ylabel('WATER LEVELS, feet MSL')
    ax.set_xlabel('DATE/TIME UTC')
    ax.grid(True,which='both')   

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %m/%d\n%H:00'))
    ax.xaxis.set_minor_locator(MultipleLocator(0.5))

    ax.set_xlim (        xlim)
    ax.set_ylim (        ylim)
    ax2.set_ylim(3.28084*ylim[0], 3.28084*ylim[1])
    ax2.plot([],[])

    plt.tight_layout()
    plt.savefig('metrics-CWL-series.png')

    #Plot SWL
    fig, ax, ax2 = csdlpy.plotter.stageStationPlot ( xlim, ylim,
                                        now, datums, floodlevels)
    titleString = cwls[0]['stations'][nosids.index(nosid)] + ' CWL: [' + \
                  xlim[0].strftime('%m/%d %H:%MZ') + '--' + \
                  xlim[1].strftime('%m/%d %H:%MZ') + ']'
    plt.title( titleString, fontsize=9 )

    m_metrics_SWL = []

    for n in range(len(cwls)):
        c = cwls[n]
        h = htps[n]
        ctime = c['time']
        if ctime[0] <= skillStartDate + datetime.timedelta(hours=1) and ctime[-1] >= skillEndDate - datetime.timedelta(hours=1):
            idx1 = np.where( np.datetime64(skillStartDate) <= ctime)[0]
            idx2 = np.where( np.datetime64(skillEndDate)   >= ctime)[0]
            idx  = list(set(idx1).intersection(idx2))

            refDates, obsValsProjSWL, modValsProjSWL = \
                csdlpy.interp.projectTimeSeries (observed['dates'], surge, \
                                             c['time'][idx], \
                                             c['zeta'][idx,nosids.index(nosid)]-h['zeta'][idx,nosids.index(nosid)], \
                                             refStepMinutes=6)

            M = csdlpy.valstat.metrics (obsValsProjSWL, modValsProjSWL, refDates)
            m_metrics_SWL.append(M)

            leadHours = -1.*round(1/3600.*(ctime[0] - skillStartDate).total_seconds())
            ax.plot(refDates, modValsProjSWL, '.', linewidth=1)

            peak_mod_val = np.nanmax(modValsProjSWL)
            peak_mod_dat = refDates[np.nanargmax(modValsProjSWL)]
            ax.plot(peak_mod_dat,peak_mod_val,'ok')
        else:
            print '[warn]: skipping nowcasts, ctime=', ctime[0], ' to ', ctime[-1]

    ax.plot(refDates, obsValsProjSWL,'.', color='lime',linewidth=5.0)
    peak_obs_val = np.nanmax(obsValsProjSWL)
    peak_obs_dat = refDates[np.nanargmax(obsValsProjSWL)]

    ax.plot(peak_obs_dat, peak_obs_val,'o',markerfacecolor='limegreen',markeredgecolor='k')

    ax.set_ylabel ('WATER LEVELS, meters MSL')
    ax2.set_ylabel('WATER LEVELS, feet MSL')
    ax.set_xlabel('DATE/TIME UTC')
    ax.grid(True,which='both')

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %m/%d\n%H:00'))
    ax.xaxis.set_minor_locator(MultipleLocator(0.5))

    ax.set_xlim (        xlim)
    ax.set_ylim (        ylim)
    ax2.set_ylim(3.28084*ylim[0], 3.28084*ylim[1])
    ax2.plot([],[])

    plt.tight_layout()
    plt.savefig('metrics-SWL-series.png')

    # Plot Metrics CWL
    xx = []
    yy_bias = []
    yy_peak = []
    yy_rval = []
    yy_rmsd = []
    yy_vexp = []
    yy_skil = []
    yy_plag = []

    for n in range(len(m_leadtime)):
        xx.append( m_leadtime[n] )
        yy_bias.append( m_metrics_CWL[n]['bias'] )
        yy_peak.append( m_metrics_CWL[n]['peak'] )
        yy_rval.append( m_metrics_CWL[n]['rval'] )
        yy_rmsd.append( m_metrics_CWL[n]['rmsd'] )
        yy_vexp.append( m_metrics_CWL[n]['vexp'] )
        yy_skil.append( m_metrics_CWL[n]['skil'] )
        yy_plag.append( m_metrics_CWL[n]['plag']/60. )
        
    #hticks = np.arange(-168,6,6)   
    hticks = np.arange(0,168,6)
 
    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_rmsd,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    plt.plot([xx[0], xx[-1]],[0.5,0.5],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('RMSD, METERS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.01,0.7)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-CWL-rmsd.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_bias,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('BIAS, METERS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.51,0.51)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-CWL-bias.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_peak,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('PEAK, METERS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.51,0.51)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-CWL-peak.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_rval,'ko-')
    plt.plot([xx[0], xx[-1]],[1,1],'g')
    plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('RVAL')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.1, 1.1)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-CWL-rval.png')
    
    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_skil,'ko-')
    plt.plot([xx[0], xx[-1]],[1,1],'g')
    plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('SKIL')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.1, 1.1)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-CWL-skil.png')
  
    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_vexp,'ko-')
    plt.plot([xx[0], xx[-1]],[100,100],'g')
    plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('VAR EXP, %')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-1, 101)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-CWL-vexp.png')    

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_plag,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    #plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD_TIME, HRS')
    plt.ylabel('PLAG, HOURS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-6., 6.)
    ax = f.gca()
    ax.set_xticks( hticks )
    ax.set_yticks (np.arange(-6,12,2))
    plt.grid()
    plt.savefig('metrics-CWL-plag.png')


    # Plot Metrics SWL
    xx = []
    yy_bias = []
    yy_peak = []
    yy_rval = []
    yy_rmsd = []
    yy_vexp = []
    yy_skil = []
    yy_plag = []

    for n in range(len(m_leadtime)):
        xx.append( m_leadtime[n] )
        yy_bias.append( m_metrics_SWL[n]['bias'] )
        yy_peak.append( m_metrics_SWL[n]['peak'] )
        yy_rval.append( m_metrics_SWL[n]['rval'] )
        yy_rmsd.append( m_metrics_SWL[n]['rmsd'] )
        yy_vexp.append( m_metrics_SWL[n]['vexp'] )
        yy_skil.append( m_metrics_SWL[n]['skil'] )
        yy_plag.append( m_metrics_SWL[n]['plag']/60. )

    #hticks = np.arange(-168,6,6)
    hticks = np.arange(0,168,6)

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_rmsd,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    plt.plot([xx[0], xx[-1]],[0.5,0.5],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('SWL RMSD, METERS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.01,0.7)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-SWL-rmsd.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_bias,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('SWL BIAS, METERS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.51,0.51)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-SWL-bias.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_peak,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('SWL PEAK, METERS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.51,0.51)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-SWL-peak.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_rval,'ko-')
    plt.plot([xx[0], xx[-1]],[1,1],'g')
    plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('SWL RVAL')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.1, 1.1)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-SWL-rval.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_skil,'ko-')
    plt.plot([xx[0], xx[-1]],[1,1],'g')
    plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('SWL SKIL')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-0.1, 1.1)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-SWL-skil.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_vexp,'ko-')
    plt.plot([xx[0], xx[-1]],[100,100],'g')
    plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD TIME, HRS')
    plt.ylabel('SWL VAR EXP, %')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-1, 101)
    ax = f.gca()
    ax.set_xticks( hticks )
    plt.grid()
    plt.savefig('metrics-SWL-vexp.png')

    f = plt.figure(figsize=(10,4))
    plt.plot(xx, yy_plag,'ko-')
    plt.plot([xx[0], xx[-1]],[0,0],'g')
    #plt.plot([xx[0], xx[-1]],[0,0],'r')
    plt.xlabel('LEAD_TIME, HRS')
    plt.ylabel('SWL PLAG, HOURS')
    plt.title('NOSID: ' + str(nosid) + ' SPAN: ' + skillStartDate.strftime('%Y/%m/%d %H:%M') + '-'+skillEndDate.strftime('%Y/%m/%d %H:%M'))
    plt.ylim(-6., 6.)
    ax = f.gca()
    ax.set_xticks( hticks )
    ax.set_yticks (np.arange(-6,12,2))
    plt.grid()
    plt.savefig('metrics-SWL-plag.png')



    #Transfer
    csdlpy.transfer.upload('*.png', args.ftpLogin, args.ftpPath) 
    #Clean up temporary folder
    csdlpy.transfer.cleanup(args.tmpDir)

#==============================================================================    
if __name__ == "__main__":

    timestamp()
    run_post (sys.argv[1:])
    timestamp()
    


