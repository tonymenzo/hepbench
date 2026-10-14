"""Publication figures from retained campaign evidence; run with the hepbench env.
Only the rcParams style is borrowed from rare_W/publication_figures.ipynb.
No simulation or grading is rerun. JSON sidecars retain plotted aggregates.
"""
from pathlib import Path
import os, json, math, hashlib, tarfile, importlib.util
from collections import Counter
ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'tmp/publication/mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator, NullLocator
from scipy.stats import beta
OUT = ROOT/'campaigns/publication/figures'; OUT.mkdir(parents=True, exist_ok=True)
LLP = ROOT/'campaigns/llp_forward'
SYM = ROOT/'campaigns/symbolic'
BLUE, RED, GREEN = '#0072B2', '#B94040', '#228B22'
COL = {'core':RED, 'tools':BLUE, 'gpt':GREEN}
LABEL = {'core':'Core', 'tools':'Domain tools', 'gpt':'GPT-5.5 core'}
plt.rcParams.update({'text.usetex':False,'mathtext.fontset':'cm','font.family':'serif',
 'font.serif':['cmr10','Computer Modern Serif','DejaVu Serif'], 'axes.unicode_minus':False,
 'axes.formatter.use_mathtext':True,'font.size':13,'axes.labelsize':16,'axes.titlesize':13,
 'xtick.labelsize':13,'ytick.labelsize':13,'legend.fontsize':12,'legend.frameon':False,
 'figure.constrained_layout.w_pad':0.07,'figure.constrained_layout.h_pad':0.07,
 'figure.constrained_layout.wspace':0.08,'figure.constrained_layout.hspace':0.08,
 'axes.labelpad':7,'xtick.major.pad':6,'ytick.major.pad':6,'figure.dpi':110,'savefig.dpi':300,'savefig.bbox':'tight','axes.linewidth':0.8,
 'lines.linewidth':1.8,'xtick.major.width':0.8,'ytick.major.width':0.8,
 'xtick.direction':'in','ytick.direction':'in','xtick.top':True,'ytick.right':True,
 'xtick.minor.visible':True,'ytick.minor.visible':True,'pdf.fonttype':42,'ps.fonttype':42})
REPORT={'sources':{},'llp':{},'symbolic':{}}
def read(p):
 REPORT['sources'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
def save(fig,name):
 for ext in ['pdf','png']: fig.savefig(OUT/f'{name}.{ext}',bbox_inches='tight',pad_inches=.06)
 plt.close(fig)
def arm_handles(): return [Line2D([],[],color=COL[a],ls='--' if a=='core' else '-',label=LABEL[a]) for a in ['core','tools']]
def soften(ax,axis='y'):
 ax.set_axisbelow(True); ax.grid(axis=axis,which='major',color='.9',lw=.6)
def summarize(v): return {'median':float(np.median(v)),'min':float(np.min(v)),'max':float(np.max(v)),'n':len(v)}

# LLP: exact retained bare-variant cell selection, no discovery in legacy runs.
index=read(LLP/'dataset/index.json')
cells=[read(p) for p in sorted((LLP/'dataset/cells').glob('*.json'))]
assert len(cells)==8 and all(c['n']==5 and c['variant']=='bare' for c in cells)
assert all(c['rubric_fingerprint']==index['rubric_fingerprint'] for c in cells)
systems=['Opus 4.8','Sonnet 5','Codex GPT-5.5','Codex GPT-5.6']
short=lambda s:s.replace('Codex ','')
CJ={(c['system'],c['arm']):c for c in cells}
scores=lambda s,a:np.array([t['score'] for t in CJ[s,a]['trials']])
for c in cells:
 vals=scores(c['system'],c['arm']); assert np.allclose(sorted(vals),sorted(c['scores'].values()))
 REPORT['llp'][c['id']]={'mean':float(vals.mean()),'sd':float(vals.std(ddof=1)),'passes':int(sum(vals>=.9))}
# No panel titles: identify panels by position in the manuscript captions.
fig,axs=plt.subplots(1,2,figsize=(11.5,4.7))
fig.subplots_adjust(left=.075,right=.985,bottom=.17,top=.97,wspace=.32)
order=sorted(systems,key=lambda s:scores(s,'core').mean())
reach_colors={'core':'#B94040','tools':'#0072B2'}
system_colors={'Sonnet 5':'#0072B2','Codex GPT-5.5':'#D55E00','Opus 4.8':'#009E73','Codex GPT-5.6':'#CC79A7'}
for a,off in [('core',-.17),('tools',.17)]:
 for i,s in enumerate(order):
  v=scores(s,a); x=i+off
  axs[0].scatter(x+np.linspace(-.055,.055,5),v,s=65,c=reach_colors[a],alpha=.75,edgecolors='white',linewidths=.4,zorder=3)
  axs[0].errorbar(x,v.mean(),yerr=v.std(ddof=1),fmt='D',color=reach_colors[a],ecolor='black',mec='black',mew=.6,ms=10,capsize=4,zorder=4)
axs[0].set(xticks=range(4),xticklabels=[short(s) for s in order],ylabel=r'Reach $R_r$',ylim=(-.03,1.04))
axs[0].tick_params(axis='x',labelsize=17,top=False,pad=9)
axs[0].tick_params(axis='y',labelsize=16)
axs[0].set_xlim(-.48,3.48)
axs[0].xaxis.set_minor_locator(NullLocator())
axs[0].axhline(.9,color='.4',ls=':',lw=1)
axs[0].legend(handles=[Line2D([],[],marker='o',ms=9,color=reach_colors[a],ls='',label=LABEL[a]) for a in ['core','tools']],loc='lower right',fontsize=15)
for s in order:
 pts=[(scores(s,a).mean(),scores(s,a).std(ddof=1)) for a in ['core','tools']]
 color=system_colors[s]
 axs[1].annotate('',xy=pts[1],xytext=pts[0],arrowprops={'arrowstyle':'-|>','color':color,'lw':1.8,'shrinkA':7,'shrinkB':7,'mutation_scale':13})
 axs[1].plot(*pts[0],'o',ms=9,mfc='white',mec=color,mew=1.8)
 axs[1].plot(*pts[1],'s',ms=9,color=color,mec='white',mew=.5)
axs[1].set(xlabel='Mean reach',ylabel='Sample standard deviation',yscale='log',xlim=(.40,1.01),ylim=(.0015,.65))
axs[1].tick_params(axis='both',labelsize=16)
axs[1].set_xlabel('Mean reach',fontsize=18)
system_handles=[Line2D([],[],color=system_colors[s],lw=2,label=short(s)) for s in order]
loadout_handles=[Line2D([],[],marker='o',mfc='white',mec='black',ls='',label='Core'),Line2D([],[],marker='s',color='black',ls='',label='Domain tools')]
axs[1].legend(handles=[system_handles[0],system_handles[2],loadout_handles[0],system_handles[1],system_handles[3],loadout_handles[1]],loc='lower left',bbox_to_anchor=(.02,.015),fontsize=14,ncol=2,columnspacing=1.2,handlelength=1.5,handletextpad=.6,labelspacing=.6,borderaxespad=.3)
save(fig,'llp_bare_allsystems')

# Exact empirical step curves; no gridded approximation to break points.
fig,axs=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
for a in ['core','tools']:
 ts=[t for c in cells if c['arm']==a for t in c['trials']]
 d=[max(t['stage_distance'][k] for k in ['yield_distance','contour_lower','contour_upper']) if all(t['stage_distance'].get(k) is not None for k in ['yield_distance','contour_lower','contour_upper']) else math.inf for t in ts]
 for j,vals in enumerate([np.power(10.,d),[t['score'] for t in ts]]):
  x=np.unique(np.r_[([1,40] if j==0 else [0.4,1]),[v for v in vals if np.isfinite(v)]])
  y=[np.mean(np.array(vals)<=v) if j==0 else np.mean(np.array(vals)>=v) for v in x]
  axs[j].step(x,y,where='post' if j==0 else 'pre',color=COL[a],ls='--' if a=='core' else '-',label=LABEL[a])
axs[0].set(xscale='log',xlim=(1,40),xlabel=r'Allowed discrepancy $F$',ylabel='Fraction of trials');axs[0].axvline(1.5,color='.5',ls=':',lw=1)
axs[1].set(xlim=(.4,1),xlabel=r'Reach threshold $R_\star$',ylabel='Fraction of trials');axs[1].axvline(.9,color='.5',ls=':',lw=1)
for ax in axs:ax.set_ylim(-.02,1.03)
axs[0].legend(loc='lower right',fontsize=13,handlelength=2.2);fig.align_xlabels();save(fig,'llp_bare_threshold_sensitivity')

# Read each submitted scan with the exact retained campaign parser.
spec=importlib.util.spec_from_file_location('llp_checks',LLP/'config/checks.py'); C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
read(LLP/'dataset/index.json')
REPORT['sources'][str((LLP/'config/checks.py').relative_to(ROOT))]=hashlib.sha256((LLP/'config/checks.py').read_bytes()).hexdigest()
truth=read(ROOT/'benchmarks/llp_forward/soln/truth.json'); peaks=C._truth_peaks(truth); bands=C._truth_bands(truth)
archive=LLP/'graded_record.tar.gz';REPORT['sources'][str(archive.relative_to(ROOT))]=hashlib.sha256(archive.read_bytes()).hexdigest()
TMP=ROOT/'tmp/publication/scans';TMP.mkdir(parents=True,exist_ok=True)
PK={};BD={}
with tarfile.open(archive) as tar:
 names=tar.getnames()
 for (s,a),cell in CJ.items():
  pa={};ba={}
  for row in cell['trials']:
   suffix=f"{cell['run_id']}/bundle/trials/{row['trial_id']}/artifacts/results/scan.csv"
   hits=[n for n in names if n.endswith(suffix)]
   if not hits:
    REPORT.setdefault('missing_scans',[]).append(suffix);continue
   assert len(hits)==1,(suffix,hits)
   p=TMP/cell['id']/row['trial_id']/'results/scan.csv';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tar.extractfile(hits[0]).read())
   scan,err=C._load_scan(p.parent.parent,{});assert not err,err
   for key,pts in scan.items():
    pk=max(n for g,n in pts)
    if pk>0:pa.setdefault(key,[]).append(pk)
    lo,hi=C._crossings(pts,3.)
    if lo and hi:ba.setdefault(key,[]).append((lo,hi))
  PK[s,a]={k:summarize(v) for k,v in pa.items()}
  BD[s,a]={k:{'lo':summarize([v[0] for v in vs]),'hi':summarize([v[1] for v in vs])} for k,vs in ba.items()}
REPORT['llp_observables']={f'{s}/{a}':{'peaks':{str(k):v for k,v in PK[s,a].items()},'bands':{str(k):v for k,v in BD[s,a].items()}} for s,a in CJ}
# Separate systems into panels; keep search channels separate rather than joining them.
fig,axs=plt.subplots(2,2,figsize=(9,6.4),sharex=True,sharey=True,layout='constrained',gridspec_kw={'wspace':.10,'hspace':.10})
for ax,s,letter in zip(axs.flat,systems,'abcd'):
 ax.axhspan(1/3,3,color='.93');ax.axhline(1,color='.35',lw=1)
 ax.axvline(2*0.1056583745,color='.4',ls='--',lw=1,zorder=2)
 for a in ['core','tools']:
  for ch,mk in [('gg','o'),('mumu','s')]:
   ks=sorted([k for k in peaks if k[0]==ch and peaks[k]>0 and k in PK[s,a]],key=lambda k:k[1])
   x=[k[1] for k in ks];vs=PK[s,a]
   ax.fill_between(x,[vs[k]['min']/peaks[k] for k in ks],[vs[k]['max']/peaks[k] for k in ks],color=COL[a],alpha=.12,lw=0)
   ax.plot(x,[vs[k]['median']/peaks[k] for k in ks],color=COL[a],ls='--' if a=='core' else '-',marker=mk,ms=5)
   for k in ks:
    if vs[k]['n']==1:ax.plot(k[1],vs[k]['median']/peaks[k],'x',color='.2',ms=8)
 ax.set(xscale='log',yscale='log');ax.set_xticks([.06,.1,.2],labels=['0.06','0.1','0.2']);ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
fig.supylabel(r'Peak yield / reference',fontsize=16)
fig.supxlabel(r'$m_\phi$ [GeV]',fontsize=17)
fig.legend(handles=arm_handles()+[Line2D([],[],marker=m,color='.3',ls='',label=l) for m,l in [('o',r'$\gamma\gamma$'),('s',r'$\mu^+\mu^-$')]],loc='outside upper center',ncol=4,fontsize=14,columnspacing=1.6,handletextpad=.6)
for ax in axs[-1]:
 ax.set_xticks([.1,1],labels=['0.1','1']);ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
save(fig,'llp_bare_yields_vs_truth')
fig,axs=plt.subplots(2,2,figsize=(9,6.4),sharex=True,sharey=True,layout='constrained',gridspec_kw={'wspace':.10,'hspace':.10})
for ax,s,letter in zip(axs.flat,systems,'abcd'):
 for ch in ['gg','mumu']:
  ks=sorted([k for k,b in bands.items() if k[0]==ch and b and b[0] and b[1]],key=lambda k:k[1])
  x=[k[1] for k in ks];ax.fill_between(x,[bands[k][0] for k in ks],[bands[k][1] for k in ks],color='.85',lw=0)
  for edge in [0,1]:ax.plot(x,[bands[k][edge] for k in ks],color='.45',lw=1)
  if len(ks)==1:ax.plot([ks[0][1]]*2,bands[ks[0]],color='.65',lw=4,zorder=0)
  for a in ['core','tools']:
   # NaNs break lines at missing boundaries; do not interpolate over absent results.
   for ed in ['lo','hi']:
    vals=[BD[s,a].get(k,{}).get(ed,{}) for k in ks]
    ax.fill_between(x,[v.get('min',np.nan) for v in vals],[v.get('max',np.nan) for v in vals],color=COL[a],alpha=.12,lw=0)
    ax.plot(x,[v.get('median',np.nan) for v in vals],color=COL[a],ls='--' if a=='core' else '-',marker='o' if ch=='gg' else 's',ms=5)
    for k,v in zip(ks,vals):
     if v.get('n')==1:ax.plot(k[1],v['median'],'x',color='.2',ms=8)
 ax.set(xscale='log',yscale='log');ax.set_xticks([.06,.1,.2],labels=['0.06','0.1','0.2']);ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
fig.supylabel(r'Coupling $g$',fontsize=16)
fig.supxlabel(r'$m_\phi$ [GeV]',fontsize=16)
fig.legend(handles=arm_handles()+[Patch(color='.85',label='Reference')]+[Line2D([],[],marker=m,color='.3',ls='',label=l) for m,l in [('o',r'$\gamma\gamma$'),('s',r'$\mu^+\mu^-$')]],loc='outside upper center',ncol=5,fontsize=12,columnspacing=1.4,handletextpad=.6)
save(fig,'llp_bare_contour_vs_truth')
fig,ax=plt.subplots(figsize=(7.2,3.5),layout='constrained')
for a,off in [('core',-.16),('tools',.16)]:
 v=[CJ[s,a]['code_written_per_trial_mean']['total_lines'] for s in systems]
 ax.barh(np.arange(4)+off,v,height=.29,color=COL[a],label=LABEL[a])
 for y,n in zip(np.arange(4)+off,v):ax.text(n+12,y,f'{n:.0f}',va='center',fontsize=11)
ax.set(yticks=range(4),yticklabels=[short(s) for s in systems],xlabel='Mean lines of analysis code per trial',xlim=(0,1700),xticks=[0,400,800,1200,1600]);ax.invert_yaxis();ax.legend(loc='lower right');ax.yaxis.set_minor_locator(NullLocator());save(fig,'llp_bare_code_capture')

# Symbolic: regraded per-trial records only, exactly eight common tasks.
BENCHES=[('decay_F_to_FpV',r'$F\to f^\prime V$'),('decay_F_to_FprimeS',r'$F\to f^\prime S$'),('decay_S_to_FFbar',r'$S\to f\bar f$'),('decay_S_to_SS',r'$S\to\chi\chi$'),('decay_S_to_VV',r'$S\to VV$'),('decay_V_to_FFbar',r'$V\to f\bar f$'),('decay_V_to_SVp',r'$V\to SV^\prime$'),('decay_V_to_VVp',r'$V\to VV^\prime$')]
CAMPS={'core':'core_haiku','tools':'tools_haiku','gpt':'core_gpt55'}
ROWS={};SC={};PASS={}
for a,camp in CAMPS.items():
 for b,l in BENCHES:
  hits=list((SYM/'trials'/camp).glob(f'*_symbolic-{b}_*_run/trials.jsonl'));assert len(hits)==1
  p=hits[0];REPORT['sources'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
  rows=[json.loads(l) for l in p.read_text().splitlines() if l.strip()];assert len(rows)==10
  assert {r['seed'] for r in rows}==set(range(1001,1011))
  assert not any(r.get('failure_mode')=='SESSION_LIMIT' for r in rows)
  ROWS[a,b]=rows;SC[a,b]=np.array([r['score'] for r in rows]);PASS[a,b]=sum(all(r['stages'].values()) for r in rows)
  assert PASS[a,b]==sum(SC[a,b]>=1-1e-12)
REPORT['symbolic']['cells']={f'{a}/{b}':{'mean':float(SC[a,b].mean()),'sd':float(SC[a,b].std(ddof=1)),'passes':int(PASS[a,b])} for a in CAMPS for b,l in BENCHES}
REPORT['symbolic']['means']={a:float(np.mean([SC[a,b].mean() for b,l in BENCHES])) for a in CAMPS}
assert np.isclose(REPORT['symbolic']['means']['core'],.269,atol=.001)
assert np.isclose(REPORT['symbolic']['means']['tools'],.906,atol=.001)
fig,ax=plt.subplots(figsize=(8.2,5.3))
fig.subplots_adjust(left=.14,right=.77,bottom=.13,top=.85)
order=sorted(BENCHES,key=lambda bl:SC['core',bl[0]].mean())
for i,(b,lab) in enumerate(order):
 ax.axhline(i,color='.92',lw=.6,zorder=0)
 for a,off,mk in [('core',-.17,'o'),('tools',.17,'s')]:
  v=SC[a,b];ax.scatter(v,i+off+np.linspace(-.045,.045,10),s=17,color=COL[a],alpha=.3)
  mean,sd=v.mean(),v.std(ddof=1)
  lo,hi=max(0.,mean-sd),min(1.,mean+sd)
  ax.errorbar(mean,i+off,xerr=[[mean-lo],[hi-mean]],fmt=mk,ms=7,color=COL[a],elinewidth=1.6,capsize=3,capthick=1.2,zorder=4)
 ax.text(1.09,i,f'{PASS["core",b]}/10',color=RED,ha='center',va='center',fontsize=11,transform=ax.get_yaxis_transform())
 ax.text(1.29,i,f'{PASS["tools",b]}/10',color=BLUE,ha='center',va='center',fontsize=11,transform=ax.get_yaxis_transform())
ax.text(1.09,7.65,'Core',ha='center',fontsize=11,transform=ax.get_yaxis_transform());ax.text(1.29,7.65,'Tools',ha='center',fontsize=11,transform=ax.get_yaxis_transform())
ax.text(1.19,8.15,'Complete trials',ha='center',fontsize=11,transform=ax.get_yaxis_transform())
ax.set(yticks=range(8),yticklabels=[l for b,l in order],xlabel=r'Reach $R_r$',xlim=(-.035,1.04),ylim=(-.65,7.5),xticks=[0,.25,.5,.75,1]);ax.yaxis.set_minor_locator(NullLocator())
ax.spines[['top','right']].set_visible(False);ax.tick_params(which='both',top=False,right=False)
ax.set_xlabel(r'Reach $R_r$',fontsize=14)
ax.legend(handles=[Line2D([],[],marker=mk,markersize=8,color=COL[a],ls='',label=LABEL[a]) for a,mk in [('core','o'),('tools','s')]],loc='lower center',bbox_to_anchor=(.5,1.065),ncol=2,fontsize=13.5,columnspacing=1.6,handletextpad=.5,borderaxespad=0)
save(fig,'symbolic_overview')
# Accuracy is conditional on delivered, gradeable answers; report denominators.
rungs=['order_of_magnitude','within_10pct','within_1pct','formula']
ACC={};OUTCOMES={};DIS={}
for a in CAMPS:
 out=Counter();dis=Counter();num=np.zeros(4,int);den=np.zeros(4,int)
 for b,l in BENCHES:
  for r in ROWS[a,b]:
   st=r['stages'];present=bool(st.get('answer_present',False))
   out['complete' if all(st.values()) else 'partial' if present else 'no delivery']+=1
   if not present:continue
   for j,suffix in enumerate(rungs):
    v=[ok for k,ok in st.items() if k.endswith('_'+suffix)];num[j]+=sum(v);den[j]+=len(v)
   for k,ok in st.items():
    if not k.endswith('_within_1pct'):continue
    prefix=k.removesuffix('_within_1pct');formula=st.get(prefix+'_formula')
    if formula is None:
     dis['number (no formula requested)' if not ok else 'pass']+=1;continue
    dis['both' if not ok and not formula else 'number' if not ok else 'formula' if not formula else 'pass']+=1
 ACC[a]=num/den;OUTCOMES[a]=dict(out);DIS[a]=dict(dis)
 REPORT['symbolic'][a]={'outcomes':dict(out),'accuracy_num':num.tolist(),'accuracy_den':den.tolist(),'discrepancies':dict(dis)}
fig,axs=plt.subplots(1,2,figsize=(10,3.7),layout='constrained',gridspec_kw={'width_ratios':[1,1.1]})
for a,mk,ls in [('core','o','--'),('tools','s','-'),('gpt','^',':')]:
 axs[0].plot(range(4),ACC[a],marker=mk,ls=ls,color=COL[a],label=LABEL[a])
axs[0].set(xticks=range(4),xticklabels=['Order of\nmagnitude','10%','1%','Formula'],ylim=(-.03,1.07),ylabel='Fraction of delivered quantities');axs[0].tick_params(axis='x',labelsize=12,top=False);axs[0].xaxis.set_minor_locator(NullLocator());soften(axs[0])
cat=['complete','partial','no delivery']
for a,off in [('core',-.22),('tools',0),('gpt',.22)]:
 v=[OUTCOMES[a].get(c,0) for c in cat];axs[1].barh(np.arange(3)+off,v,height=.2,color=COL[a])
 for y,n in zip(np.arange(3)+off,v):axs[1].text(n+1,y,str(n),va='center',fontsize=10)
axs[1].set(yticks=range(3),yticklabels=['Complete','Partial','No delivery'],xlabel='Trials (80 per configuration)',xlim=(0,91));axs[1].invert_yaxis();axs[1].yaxis.set_minor_locator(NullLocator());soften(axs[1],'x');fig.legend(handles=axs[0].get_legend_handles_labels()[0],labels=axs[0].get_legend_handles_labels()[1],loc='outside lower center',ncol=3,fontsize=12);save(fig,'symbolic_ladder')
# Appendix reliability: separate metrics so bands are readable; no mean-reach line
# on a pass-probability axis. Exact finite-sample subset estimators.
ks=np.arange(1,11)
fig=plt.figure(figsize=(10,9.2),layout='constrained')
gs=fig.add_gridspec(5,4,height_ratios=[1,1,.12,1,1],wspace=.12,hspace=.10)
axs=np.array([[fig.add_subplot(gs[r,c]) for c in range(4)] for r in [0,1,3,4]])
for r in range(4):
 for c in range(4):
  axs[r,c].tick_params(labelbottom=r==3,labelleft=c==0)
for i,(b,lab) in enumerate(BENCHES):
 for metric in [0,1]:
  ax=axs[(i//4)*2+metric,i%4]
  for a in ['core','tools']:
   c=PASS[a,b];n=10
   vals=[1-(math.comb(n-c,k)/math.comb(n,k) if n-c>=k else 0) if metric==0 else (math.comb(c,k)/math.comb(n,k) if c>=k else 0) for k in ks]
   lo=0 if c==0 else beta.ppf(.025,c,n-c+1);hi=1 if c==n else beta.ppf(.975,c+1,n-c)
   f=lambda p:1-(1-p)**ks if metric==0 else p**ks
   ax.fill_between(ks,f(lo),f(hi),color=COL[a],alpha=.10,lw=0)
   ax.plot(ks,vals,color=COL[a],ls='--' if a=='core' else '-',lw=1.6)
  ax.set(ylim=(-.035,1.035),xticks=[1,4,7,10],yticks=[0,.5,1]);ax.tick_params(labelsize=13);soften(ax)
  if i%4==0:ax.set_ylabel(r'pass@$k$' if metric==0 else r'pass$^k$',fontsize=14)
for ax in axs[-1]:ax.set_xlabel('$k$')
fig.legend(handles=arm_handles(),loc='outside lower center',ncol=2,fontsize=13,handlelength=2.4,columnspacing=2);save(fig,'symbolic_passk')
fig,ax=plt.subplots(figsize=(7.5,3.5),layout='constrained')
keys=['both','number','formula','number (no formula requested)'];labels=['Number and formula fail','Only number fails','Only formula fails','Number fails;\nno formula requested']
for a,off in [('core',-.17),('tools',.17)]:
 v=[DIS[a].get(k,0) for k in keys];ax.barh(np.arange(4)+off,v,height=.3,color=COL[a],label=LABEL[a])
 for y,n in zip(np.arange(4)+off,v):ax.text(n+1,y,str(n),va='center',fontsize=11)
ax.set(yticks=range(4),yticklabels=labels,xlabel='Delivered quantities',xlim=(0,max(DIS['core'].values())*1.16));ax.invert_yaxis();ax.yaxis.set_minor_locator(NullLocator());ax.legend(loc='lower right',fontsize=12);ax.tick_params(axis='y',length=0,pad=8);soften(ax,'x');save(fig,'symbolic_errors')
REPORT['llp_reference']={'peaks':{str(k):v for k,v in peaks.items()},'bands':{str(k):v for k,v in bands.items()}}
REPORT['software']={'matplotlib':matplotlib.__version__,'numpy':np.__version__}
(OUT.parent/'data.json').write_text(json.dumps(REPORT,indent=2)+'\n')
print(json.dumps(REPORT['symbolic'],indent=2))
print('Saved publication figures:',OUT)
