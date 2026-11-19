"""Render the CU-02 sequence diagram as portable SVG and PDF."""
from __future__ import annotations
from html import escape
from pathlib import Path
import cairosvg

BASE=Path(__file__).resolve().parent
W,H=1980,1550
xs=[125,375,625,900,1170,1430,1720]
labels=["Estudiante","Interfaz Web\n«boundary»","HTTP Handler\n«boundary»","EnrollmentService\n«control»","AcademicValidator\n«control»","SistemaContable\n«external»","Repository + SQLite\n«entity»"]
items=[]
def add(x):items.append(x)
def txt(x,y,string,size=18,color='#1D455C',anchor='middle',weight='normal'):
    add(f'<text x="{x}" y="{y}" fill="{color}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" font-family="DejaVu Sans, sans-serif">{escape(str(string))}</text>')
def line(x1,y1,x2,y2,color='#47798F',dash='',width=2):
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" {"stroke-dasharray="+repr(dash) if dash else ""}/>')
def box(x,y,w,h,stroke='#B4C8D4',fill='white',radius=8,width=1.7):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" stroke="{stroke}" fill="{fill}" stroke-width="{width}"/>')
def msg(a,b,y,label,dashed=False):
    x1,x2=xs[a],xs[b]
    line(x1,y,x2,y,'#52849A','7 5' if dashed else '',2)
    arrow='M '+str(x2-11 if x2>x1 else x2+11)+' '+str(y-6)+' L '+str(x2)+' '+str(y)+' L '+str(x2-11 if x2>x1 else x2+11)+' '+str(y+6)
    add(f'<path d="{arrow}" fill="none" stroke="#35657C" stroke-width="2"/>')
    txt((x1+x2)/2,y-9,label,14,color='#234E62')

def fragment(x,y,w,h,name,desc):
    box(x,y,w,h,stroke='#91ACBA',fill='none',radius=0)
    box(x,y,112,30,stroke='#91ACBA',fill='#E8F3F6',radius=0)
    txt(x+12,y+21,name,15,anchor='start',weight='bold')
    if desc:txt(x+130,y+21,desc,13,anchor='start',color='#617B8B')

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
box(0,0,W,H,stroke='white',fill='#FFFFFF',radius=0)
add('<rect x="0" y="0" width="1980" height="14" fill="#0E7D88"/>')
txt(70,68,'EDUCAMPUS LMS  /  SECUENCIA CU-02',30,anchor='start',weight='bold',color='#113650')
txt(70,104,'UML 2.5 · par, loop, alt · Caso de uso Inscribir asignatura',17,anchor='start',color='#58768A')
for x,label in zip(xs,labels):
    box(x-97,142,194,63,stroke='#80A6B7',fill='#EDF6FA')
    for n,part in enumerate(label.split('\n')):txt(x,168+23*n,part,14,weight='bold' if n==0 else 'normal')
    line(x,205,x,1455,'#B5C9D3','6 7',1.7)
msg(0,1,238,'seleccionar oferta')
msg(1,2,287,'POST /api/enroll')
msg(2,3,336,'execute(estudiante, oferta)')
fragment(756,366,794,385,'par','Validaciones independientes; join espera ambas respuestas')
msg(3,4,418,'check(academia)')
fragment(1045,445,815,152,'loop','')
txt(1163,469,'por cada prerrequisito',13,anchor='start')
msg(4,6,541,'consultar oferta y matrícula')
msg(4,3,610,'OK / error académico',True)
line(756,644,1550,644,'#B7CCD5','',1.2)
txt(774,670,'[rama financiera]',14,anchor='start',weight='bold')
msg(3,5,702,'check(paz y salvo)')
msg(5,3,742,'PAZ_Y_SALVO / BLOQUEADO / NO_DISPONIBLE',True)
fragment(500,781,1380,609,'alt','Evaluación conjunta tras join')
txt(522,821,'[ambas favorables]',14,anchor='start',weight='bold')
msg(3,6,857,'confirm(estudiante, oferta)')
msg(6,6,903,'BEGIN IMMEDIATE / revalidar reglas')
msg(6,6,954,'UPDATE cupos + INSERT matrícula')
msg(6,3,1004,'COMMIT: confirmada',True)
msg(3,2,1051,'201 inscripción confirmada',True)
msg(2,1,1095,'confirmación',True)
line(500,1122,1880,1122,'#B7CCD5','6 5',1.5)
txt(522,1150,'[una falla académica, financiera o de persistencia]',14,anchor='start',weight='bold')
msg(3,2,1190,'rechazar / ROLLBACK si aplica',True)
msg(2,1,1244,'respuesta 201 / 409 / 503 / 500',True)
msg(1,0,1301,'mostrar resultado',True)
txt(65,1360,'El diagrama incluye el flujo ejecutado y sus rutas de excepción; en el simulador financiero no hay API externa real.',14,anchor='start',color='#667B88')
add('</svg>')
s='\n'.join(items)
(BASE/'01_Secuencia_CU02.svg').write_text(s,encoding='utf-8')
cairosvg.svg2pdf(bytestring=s.encode(),write_to=str(BASE/'01_Secuencia_CU02.pdf'))
cairosvg.svg2png(bytestring=s.encode(),write_to=str(BASE/'01_Secuencia_CU02.png'),output_width=1386,output_height=1085)
print(BASE/'01_Secuencia_CU02.pdf')
