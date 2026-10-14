"""Update numbers in the original author-approved colored table design."""
from pathlib import Path
import json,ast,math,re
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'campaigns/publication'
d=json.loads((BASE/'data.json').read_text())
systems=['Opus 4.8','Sonnet 5','Codex GPT-5.5','Codex GPT-5.6']
peaks={ast.literal_eval(k):v for k,v in d['llp_reference']['peaks'].items()}
bands={ast.literal_eval(k):v for k,v in d['llp_reference']['bands'].items()}
def sig(v,n=3):
 return f'{v:.{max(0,n-1-math.floor(math.log10(abs(v))))}f}' if v else '0'
def sci(v):
 if .1<=v<1000:return sig(v)
 e=math.floor(math.log10(v));return rf'{v/10**e:.2f}\times10^{{{e}}}'
def shade(v,ref):
 z=abs(math.log10(v/ref));return 'llp'+('A' if z<.02 else 'B' if z<.05 else 'C' if z<.15 else 'D')
def cell(v,ref,scale=1,yield_ratio=False):
 if not v:return '--',''
 color=rf"\cellcolor{{{shade(v['median'],ref)}}}"
 fmt=(lambda x:f'{x:.2f}') if yield_ratio else sig
 den=ref if yield_ratio else scale
 sup=rf"^{{({v['n']})}}" if v['n']<5 else ''
 med=color+'$'+fmt(v['median']/den)+sup+'$'
 if v['n']==1:return med,color
 f=(lambda x:f'{x:.2f}' if .1<=x<10 else sig(x,2)) if yield_ratio else sig
 rng=rf"{{\scriptsize$[{f(v['min']/den)},\,{f(v['max']/den)}]$}}"
 if v['max']/v['min']>2:rng=r'{\color{llpSpread}'+rng+'}'
 return med,color+rng
row=lambda xs:' & '.join(xs)+r' \\'+'\n'
text=(BASE/'table-template.tex').read_text()
text=text[text.index('% Requires'):]
text='% Generated from retained scan records; original table styling preserved.\n'+text
# Preserve all original dimensions, colors, headers, ordering and units.
# Caption correction only: positive-peak coverage is not five in every cell.
text=text.replace('Each entry gives the median over five trials, with the minimum and maximum below it.',r'Each entry gives the median over trials with a positive peak, with the minimum and maximum below it. A superscript gives the contributing count when fewer than five trials qualify.')
start=text.index('0.06 &');end=text.index(r'\bottomrule',start)
rows=''
for i,(k,ref) in enumerate(sorted(peaks.items())):
 vals=[cell(d['llp_observables'][s+'/'+a]['peaks'].get(str(k)),ref,yield_ratio=True) for s in systems for a in ['tools','core']]
 rows+=row([f'{k[1]:g}','$'+sci(ref)+'$']+[v[0] for v in vals])
 rows+=row(['','']+[v[1] for v in vals]).rstrip('\n')+('[2pt]' if i<len(peaks)-1 else '')+'\n'
text=text[:start]+rows+text[end:]
start=text.index(r'\multicolumn{7}{l}{\textit{Lower edge');end=text.index(r'\bottomrule',start)
rows='';keys=sorted(k for k,v in bands.items() if v and all(v))
for edge,idx,scale,label in [('lo',0,1e-6,'Lower'),('hi',1,1e-3,'Upper')]:
 if idx:rows+='\\midrule\n'
 rows+=rf'\multicolumn{{7}}{{l}}{{\textit{{{label} edge, $g/10^{{{-6 if idx==0 else -3}}}$}}}} \\'+'\n\\midrule\n'
 rows+=row([r'\multicolumn{2}{l}{Reference}']+['$'+sig(bands[k][idx]/scale)+'$' for k in keys]).rstrip('\n')+'[2pt]\n'
 for si,s in enumerate(systems):
  for a in ['tools','core']:
   vals=[cell(d['llp_observables'][s+'/'+a]['bands'].get(str(k),{}).get(edge),bands[k][idx],scale) for k in keys]
   label=s.replace('Codex ','').replace('Opus ','Opus~').replace('Sonnet ','Sonnet~') if a=='tools' else ''
   rows+=row([label,'domain' if a=='tools' else 'core']+[v[0] for v in vals])
   rows+=row(['','']+[v[1] for v in vals]).rstrip('\n')+('[2pt]' if not(si==3 and a=='core') else '')+'\n'
text=text[:start]+rows+text[end:]
text=text.replace(r'\begin{table}[H]', '\\clearpage\n\\begin{table}[H]')
(BASE/'llp-tables.tex').write_text(text)
print('Restored original colored tables with regenerated values, ranges and coverage.')
