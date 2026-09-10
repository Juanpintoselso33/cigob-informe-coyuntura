import sys,json,csv
from pathlib import Path
sys.path.insert(0,'scripts')
import validacion_externa as v,itcp
p=Path('docs/auditorias/2026-09-08')
valores=v._valores_itcp_por_mes();resultados={m:itcp.calcular_itcp(x) for m,x in valores.items()}
published=json.loads(Path('output/validacion_externa.json').read_text())['serie_itcp']
rows=[];resumen=[]
for n in range(1,9):
 m=f'2026-{n:02d}';anterior='2025-12' if n==1 else f'2026-{n-1:02d}'
 a,b=resultados[anterior],resultados[m]
 assert b['valor']==published[m]
 da,db=a['dimensiones'],b['dimensiones'];sa=sum(d['peso'] for d in da.values());sb=sum(d['peso'] for d in db.values())
 for k in sorted(set(da)|set(db)):
  x,y=da.get(k),db.get(k)
  ca=x['puntaje']*x['peso']/sa if x else 0;cb=y['puntaje']*y['peso']/sb if y else 0
  rows.append({'mes':m,'dimension':k,'aporte_previo':round(ca,4),'aporte_actual':round(cb,4),'cambio_aporte':round(cb-ca,4),'entran':';'.join(sorted(set((y or {}).get('indicadores',{}))-set((x or {}).get('indicadores',{})))),'salen':';'.join(sorted(set((x or {}).get('indicadores',{}))-set((y or {}).get('indicadores',{}))))})
 activos_a={k for d in da.values() for k in d['indicadores']};activos_b={k for d in db.values() for k in d['indicadores']};comunes=activos_a & activos_b
 ac=itcp.calcular_itcp({k:valores[anterior].get(k) for k in comunes});bc=itcp.calcular_itcp({k:valores[m].get(k) for k in comunes})
 top=sorted([r for r in rows if r['mes']==m],key=lambda r:abs(r['cambio_aporte']),reverse=True)[:3]
 assert round(sum(r['aporte_actual'] for r in rows if r['mes']==m),1)==b['valor']
 assert round(sum(r['aporte_previo'] for r in rows if r['mes']==m),1)==a['valor']
 z={'mes':m,'anterior':a['valor'],'actual':b['valor'],'delta':round(b['valor']-a['valor'],1),'delta_componentes_comunes':round(bc['valor']-ac['valor'],1),'entran':sorted(activos_b-activos_a),'salen':sorted(activos_a-activos_b),'dominantes':top}
 resumen.append(z);print(json.dumps(z,ensure_ascii=False))
with (p/'descomposicion-itcp.csv').open('w',encoding='utf-8-sig',newline='') as h:w=csv.DictWriter(h,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
(p/'descomposicion-itcp.json').write_text(json.dumps({'metodo':'Contribución exacta de dimensión: puntaje redondeado que utiliza el motor por peso nominal dividido por pesos de dimensiones presentes. La suma reproduce el índice antes de su redondeo final. El delta común recalcula ambos meses sólo con componentes presentes en los dos; es una comprobación de cobertura, no descomposición causal.','meses':resumen},ensure_ascii=False,indent=2)+'\n')
