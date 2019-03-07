#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: Sergey.Vinogradov@noaa.gov
"""
import os,sys
import argparse
import csdlpy
import datetime
from datetime import timedelta as dt
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
def PDYtoDate (PDY):
    return datetime.datetime.strptime(PDY, "%Y%m%d")

#==============================================================================
def Date2PDY (date):
    YYYY = str(date.year).zfill(4)
    MM   = str(date.month).zfill(2)
    DD   = str(date.day).zfill(2)
    return YYYY+MM+DD

#==============================================================================
def read_cmd_argv (argv):

    parser = argparse.ArgumentParser()
    
    parser.add_argument('-i','--ofsDir',         required=True)
    parser.add_argument('-z','--PDY',            required=True)    
    parser.add_argument('-m','--maxLeadHours',   required=True)
    parser.add_argument('-d','--dbDir',          required=True)
    parser.add_argument('-n','--modelName',      required=True)
    
    args = parser.parse_args() 
    if 'latest' in args.PDY:
        args.PDY = Date2PDY(datetime.datetime.utcnow()-dt(days=1))
    print '[info]: retrospect.py is configured with :', args
    return args
    
#==============================================================================
def run_post(argv):

    #Receive command line arguments
    args = read_cmd_argv(argv)
    timestamp()

    # Decode PDY and maxLeadHours, collect valid forecast PDYs
    date     = PDYtoDate(args.PDY)
    numdays  = int(args.maxLeadHours)/24
    datelist = [ date - datetime.timedelta(days=x) for x in range(0, numdays)]
    pdys = []
    for d in sorted(datelist):
        #pdy = os.path.join(args.ofsDir, Date2PDY (d))
        pdy = args.ofsDir + '.' + Date2PDY (d) + '/'
        if os.path.exists (pdy):
            pdys.append(pdy)
        else:
            print '[warn]: PDY ', pdy, ' does not exist, skipping'
    
    # Collect model output files 
    cwlFiles = []
    swlFiles = []
    for p in pdys:
        for cwl in glob.glob( p+'/*.points.cwl.nc'):  # Combined water level
            cwlFiles.append(cwl)
        for swl in glob.glob( p+'/*.points.swl.nc'):  # Surge only
            swlFiles.append(cwl)
    print '[info]: collected ', str(len(cwlFiles)),' cwl files'
    print '[info]: collected ', str(len(swlFiles)),' swl files'
 
    #Find date range in forecasts    
    fx1  = []
    fx2  = []
    cwls = []
    swls = []
    for swl in swlFiles:
        s = csdlpy.estofs.getPointsWaterlevel ( swl, verbose=0 )
        swls.append(s)

    for cwl in cwlFiles:
        c = csdlpy.estofs.getPointsWaterlevel ( cwl, verbose=0 )
        cwls.append(c)
        span = min(c['time']), max(c['time'])
        fx1.append(span[0]) 
        fx2.append(span[1])
        
    forecastStartDate = min(fx1)
    forecastEndDate   = max(fx2)
    print '[info]: Forecasts cover: ', forecastStartDate, forecastEndDate

    # Extract NOS IDs
    masterListRemote = 'ftp://ocsftp.ncd.noaa.gov/estofs/data/ETSS_ESTOFS_Stations.csv'
    masterListLocal  = 'master.csv'
    csdlpy.transfer.download(masterListRemote, masterListLocal)

    nosids = []
    cwl = csdlpy.estofs.getPointsWaterlevel(cwlFiles[0])
    for ids in cwl['stations']:
        datums, floodlevels, nosid, stationTitle = \
            csdlpy.obs.parse.setDatumsFloodLevels (ids, masterListLocal)
        nosids.append(nosid)
    print '[info]: stations available: ', str(len(nosids))
    
     # Define skill assessment period ( a full UTC day)
    skillStartDate = date.replace(hour=0, minute=0)
    skillEndDate   = skillStartDate+datetime.timedelta(hours=1*24)
    print '[info]: Skill Assessment Period: ', skillStartDate, skillEndDate   
        
    # Check db path, PDY
    dbFolder = os.path.join(args.dbDir, args.PDY)
    if not os.path.exists(dbFolder):
        print '[warn]: db Folder ='+ dbFolder+' does not exist. Trying to mkdir.'
        try:
            os.makedirs( dbFolder )
        except:
            print '[warn]: cannot make dbFolder=' + dbFolder
            dbFolder = os.path.dirname(os.path.realpath(__file__))
            print '[warn]: look for your output in a current dir=' + dbFolder
    else:
        print '[warn]: dbFolder ' + dbFolder + ' already exists.'


    # Do the thing...
    for nosid in nosids:
        print '[info]: working on ', nosid

        # Get OBS
        obs_cwl  = csdlpy.obs.coops.getData(nosid, [skillStartDate, skillEndDate], \
                                                product='waterlevelrawsixmin')
        obs_htp = csdlpy.obs.coops.getData(nosid, [skillStartDate, skillEndDate], \
                                                product='predictions')
        obs_swl = []
        for n in range(len(obs_cwl['values'])):
            obs_swl.append( obs_cwl['values'][n] - obs_htp['values'][n] )

        if len(obs_cwl['values']) > 0:
              
            # Compute CWL stats
            leadtime = []
            metrics  = []
        
            for n in range(len(cwls)):
                c = cwls[n]
                ctime = c['time']
                if ctime[0]  <= skillStartDate + datetime.timedelta(hours=1) and \
                   ctime[-1] >= skillEndDate - datetime.timedelta(hours=1):
                   
                    idx1 = np.where( np.datetime64(skillStartDate) <= ctime)[0]
                    idx2 = np.where( np.datetime64(skillEndDate)   >= ctime)[0]
                    idx  = list(set(idx1).intersection(idx2))
                    
                    refDates, obsValsProjCWL, modValsProjCWL = \
                            csdlpy.interp.projectTimeSeries (obs_cwl['dates'], obs_cwl['values'], \
                                                             c['time'][idx], \
                                                             c['zeta'][idx,nosids.index(nosid)], \
                                                             refStepMinutes=6)

                    M = csdlpy.valstat.metrics (obsValsProjCWL, modValsProjCWL, refDates)
                    metrics.append(M)

                    leadHours = -1.*round(1/3600.*(ctime[0] - skillStartDate).total_seconds())
                    leadtime.append(leadHours)              
                else:
                    print '[warn]: skipping nowcasts, ctime=', ctime[0], ' to ', ctime[-1]

            # Write to the file
            outFile = dbFolder + '/' + args.modelName + '.' + nosid + '.cwl.csv'
            with open(outFile,'w') as f:
                f.write('LeadTime (HRS), obsMax (m MSL), Peak (m), PLag (min), Bias(m), RMSD (m), RVal, Skil, VExp (%), nPts,\n')
                #count = 0
                idx = np.argsort(leadtime)
                #for lt in leadtime:
                for count in idx:
#                    line = str(lt) + ',' + str(np.nanmax(obsValsProjCWL)) + ',' \
                    line = str(leadtime[count]) + ',' + str(np.nanmax(obsValsProjCWL)) + ',' \
                          + str(metrics[count]['peak']) + ',' \
                          + str(metrics[count]['plag']) + ',' \
                          + str(metrics[count]['bias']) + ',' \
                          + str(metrics[count]['rmsd']) + ',' \
                          + str(metrics[count]['rval']) + ',' \
                          + str(metrics[count]['skil']) + ',' \
                          + str(metrics[count]['vexp']) + ',' \
                          + str(metrics[count]['npts']) + ',\n'
                    f.write(line)                              
                    #count = count + 1
            f.close()    
        
            # Plot
            xlim = (skillStartDate, skillEndDate)
            ylim = (-2, 3)
            # Stage the plot with datums and floodlevels   
            datums, floodlevels, nosid, stationTitle = \
                    csdlpy.obs.parse.setDatumsFloodLevels (nosid, masterListLocal)
    
            fig, ax, ax2 = csdlpy.plotter.stageStationPlot ( xlim, ylim,
                                            date, datums, floodlevels)
            titleString = cwls[0]['stations'][nosids.index(nosid)] + ' CWL: [' + \
                              xlim[0].strftime('%m/%d %H:%MZ') + '--' + \
                              xlim[1].strftime('%m/%d %H:%MZ') + ']'
            plt.title( titleString, fontsize=9 )
        
            ncol = len(cwls)
            col  = 0 
            for n in range(len(cwls)):
                c = cwls[n]
                ctime = c['time']
                if ctime[0] <= skillStartDate + datetime.timedelta(hours=1) and ctime[-1] >= skillEndDate - datetime.timedelta(hours=1):
                    idx1 = np.where( np.datetime64(skillStartDate) <= ctime)[0]
                    idx2 = np.where( np.datetime64(skillEndDate)   >= ctime)[0]
                    idx  = list(set(idx1).intersection(idx2))

                    refDates, obsValsProjCWL, modValsProjCWL = \
                        csdlpy.interp.projectTimeSeries (obs_cwl['dates'], obs_cwl['values'], \
                                                 c['time'][idx], \
                                                 c['zeta'][idx,nosids.index(nosid)], \
                                                 refStepMinutes=6)

                    leadHours = -1.*round(1/3600.*(ctime[0] - skillStartDate).total_seconds())
                    col = float(n)/float(ncol)
                    if leadHours > 0:
                        ax.plot(refDates, modValsProjCWL, '.',color=(col,col,col),linewidth=1)
                    else:    
                        ax.plot(refDates, modValsProjCWL, '.',color='blue',linewidth=5)
            
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
            plt.savefig(dbFolder + '/' + args.modelName + '.' + nosid + '.cwl.png')
        else:
            print '[warn]: no data for observations available. Skipping...'
    

#==============================================================================    
if __name__ == "__main__":

    timestamp()
    run_post (sys.argv[1:])
    timestamp()
    


