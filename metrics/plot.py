import csdlpy
import numpy as np
import matplotlib
matplotlib.use('Agg',warn=False)
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from datetime import datetime
from datetime import timedelta as dt
import matplotlib.dates as mdates

#==============================================================================
def stations (cwlFile, htpFile, pp, titleStr, plotPath, args):

    clim = -0.5,3.5
    try:
        clim = float(pp['Stations']['cmin']),  float(pp['Stations']['cmax'])
    except:
        pass
    
    # Download master list
    masterListRemote = pp['Stations']['url']
    masterListLocal  = 'masterlist.csv'
    csdlpy.transfer.download(masterListRemote, masterListLocal)
    
#    Read model output
    cwl = csdlpy.estofs.getPointsWaterlevel (cwlFile)
    htp = csdlpy.estofs.getPointsWaterlevel (htpFile)
    nStations = len(cwl['stations'])
    print '[info]: Plotting ' + str(nStations) + ' point stations.'
    
    now   = datetime.utcnow()
    dates = (now-dt(days=2), now)
 
    # Plot limits
    xlim =    min(dates[0],  cwl['time'][0] ),    \
              max(dates[-1], cwl['time'][-1])
    ylim = clim[0], clim[1]
    
    for n in range(nStations):
        
        fullStationName = cwl['stations'][n]
        # Get datums        
        datums, floodlevels, nosid, stationTitle = \
            csdlpy.obs.parse.setDatumsFloodLevels (fullStationName, masterListLocal)            

        # Stage the plot with datums and floodlevels   
        fig, ax, ax2 = csdlpy.plotter.stageStationPlot (xlim, ylim, now, datums, floodlevels)
        plt.title(titleStr + ' @ ' + stationTitle, fontsize=9)

       # Get OBS
        obs   = csdlpy.obs.coops.getData(nosid, 
                                         dates, product='waterlevelrawsixmin') 
        # Plot
        now_obs = np.nan
        try:
            ax.plot(obs['dates'], obs['values'],
                    color='lime',label='OBSERVED',  linewidth=2.0)

            peak_obs_val = np.nanmax(obs['values'])
            peak_obs_dat = obs['dates'][np.argmax(obs['values'])]
            
            if ylim[0] <= peak_obs_val and peak_obs_val <= ylim[1]:
                    
                ax.plot(peak_obs_dat, peak_obs_val, 'o',
                        markerfacecolor='limegreen', markeredgecolor='k')
                ax.plot([peak_obs_dat, peak_obs_dat],[ylim[0],peak_obs_val], 
                        '--',c='limegreen')
                ax.text(peak_obs_dat, 1.06*peak_obs_val, 
                        str(np.round(peak_obs_val,1)) + "m (" + 
                           str(np.round(3.28084*peak_obs_val,1)) +"ft)",
                           color='forestgreen', fontsize=7, weight='bold')
                        
            # Find offset
            now_obs = obs['values'][obs['dates'].index(min(obs['dates'], \
                          key=lambda x: abs(x - now)))]
        except:
            pass     

        ax.plot(htp['time'], htp['zeta'][:,n],      
                color='c',label='ASTRON TIDE',linewidth=.5)
        ax.plot(cwl['time'], cwl['zeta'][:,n],      
                color='navy',label='STORM TIDE',linewidth=2.0)
        ax.plot(cwl['time'], cwl['zeta'][:,n]-htp['zeta'][:,n],
                color='m',label='STORM SURGE',linewidth=.5)
        
        # Find model value closest to Now
        mint = min(cwl['time'], key=lambda x: abs(x - now))        
        now_mod_ind = np.where(cwl['time'] == mint)[0][0]
        now_mod = cwl['zeta'][now_mod_ind,n]
        offset  = now_obs  -  now_mod 
        print '[debug]: offset=', str(offset)
        
        peak_val = np.nanmax(cwl['zeta'][:,n])
        peak_dat = cwl['time'][np.argmax(cwl['zeta'][:,n])]
        
        # Plot peak forecast value
        ax.text(peak_dat, 1.05*peak_val, 
                str(np.round(peak_val,1)) + "m (" + 
                str(np.round(3.28084*peak_val,1)) +"ft)", color='navy',fontsize=7)
        ax.plot([peak_dat, peak_dat], [ylim[0], peak_val], '--',color='navy')
        peak_str = str(peak_dat.hour).zfill(2) + ':' + str(peak_dat.minute).zfill(2) + 'z'
        ax.text(peak_dat+dt(hours=0.5), ylim[0], peak_str ,color='navy', fontsize=7)            
        ax.plot(peak_dat, peak_val, 'o',markeredgecolor='navy',markerfacecolor='b')

        # Plot offset forecast
        ax.plot(cwl['time'][now_mod_ind:], offset + cwl['zeta'][now_mod_ind:,n],      
                color='gray', linestyle=':', linewidth=.5)
        
        # offset value
        if ylim[0] <= 0.5*(now_mod+now_obs) and 0.5*(now_mod+now_obs) <= ylim[1]:
            ax.text(cwl['time'][now_mod_ind]+dt(hours=1), 0.5*(now_mod+now_obs), 
                    r'$\Delta$='+str(np.round(offset,2)) + 'm', color='gray',
                    fontsize=7, fontstyle='italic', fontweight='bold')

        # add offseted peak forecast value
        if ylim[0] <= peak_val+offset and peak_val+offset <= ylim[1]:
            ax.plot(peak_dat, peak_val+offset, marker='+',
                    markeredgecolor='gray', markerfacecolor='gray', markersize=5)
            ax.text(peak_dat, 1.05*(peak_val+offset), 
                str(np.round(peak_val+offset,1)) + "m (" + 
                str(np.round(3.28084*(peak_val+offset),1)) +"ft)", color='gray',
                   fontstyle='italic', fontsize=6)

        ax.legend(bbox_to_anchor=(0.8, 1.001, 0.17, 0.07), loc=3, 
                  ncol=2, mode="expand", borderaxespad=0., fontsize=7)

        ax.text(xlim[0],ylim[1]+0.05,'NOAA / OCEAN SERVICE')
        ax.set_ylabel ('WATER LEVELS, meters MSL')
        ax2.set_ylabel('WATER LEVELS, feet MSL')
        ax.set_xlabel('DATE/TIME UTC')
        ax.grid(True,which='both')   
        
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %m/%d\n00:00'))
        ax.xaxis.set_minor_locator(MultipleLocator(0.5))
        
        #ax.set_xlim (        xlim)
        ax.set_ylim (        ylim)
        ax2.set_ylim(3.28084*ylim[0], 3.28084*ylim[1])
        ax2.plot([],[])

        plt.tight_layout()
        figFile = plotPath + str(n+1).zfill(3) + '.png'
        plt.savefig(figFile)
        plt.close()
        csdlpy.transfer.upload(figFile, args.ftpLogin, args.ftpPath)
        
    csdlpy.transfer.cleanup()
        


