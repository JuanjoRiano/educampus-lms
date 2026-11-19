"""Execute reproducible short QA checks and export JSON evidence."""
from __future__ import annotations

import concurrent.futures
import http.cookiejar
import json
import math
import shutil
import statistics
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from educampus.db import connect, initialize
from educampus.service import EnrollmentError, enroll
from educampus.web import create_server

PROJECT = Path(__file__).resolve().parents[2]
OUTPUT = PROJECT / 'calidad' / 'resultados_qa.json'


def request(opener, base, path, method='GET', payload=None, csrf=None):
    headers={}
    if payload is not None:headers['Content-Type']='application/json'
    if csrf: headers['X-CSRF-Token']=csrf
    req=Request(base+path,data=json.dumps(payload).encode() if payload is not None else (b'{}' if method=='POST' else None),headers=headers,method=method)
    start=time.perf_counter()
    try:
        with opener.open(req,timeout=6) as response:
            return response.status, json.loads(response.read()), (time.perf_counter()-start)*1000
    except HTTPError as exc:
        return exc.code, json.loads(exc.read()), (time.perf_counter()-start)*1000


def counts(db):
    with connect(db) as conn:
        return (conn.execute('SELECT count(*) FROM enrollments').fetchone()[0],
                tuple((r['id'],r['remaining']) for r in conn.execute('SELECT id,remaining FROM offerings ORDER BY id')))


def main():
    with tempfile.TemporaryDirectory() as folder:
        db=Path(folder)/'qa.sqlite3'
        initialize(db,reset=True)
        server=create_server('127.0.0.1',0,db)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            browser=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
            status,_,_=request(browser,base,'/api/login','POST',{'username':'ana','password':'EduCampus2026!'})
            assert status==200
            csrf=request(browser,base,'/api/session')[1]['csrf']
            timings=[]
            for _ in range(30):
                status,body,ms=request(browser,base,'/api/offerings')
                assert status==200 and len(body['offerings'])>=5
                timings.append(ms)
            times_sorted=sorted(timings)
            p95=times_sorted[math.ceil(0.95*len(times_sorted))-1]
            unauthorized_cases=[]
            anonymous=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
            for method,path,payload,csrf_val in [
                ('GET','/api/offerings',None,None), ('GET','/api/enrollments',None,None),
                ('POST','/api/enroll',{'offering_id':'OF-101'},None), ('POST','/api/logout',{},None),
                ('POST','/api/enroll',{'offering_id':'OF-102'},'invalid'),
                ('POST','/api/login',{'username':'ana','password':'bad'},None),
                ('POST','/api/login',{'username':'unknown','password':'x'},None),
            ]:
                status,body,_=request(anonymous,base,path,method,payload,csrf_val)
                unauthorized_cases.append({'case':f'{method} {path}','status':status,'denied':status in (401,403)})
            for csrf_val in (None,'invalid','0','x'*32):
                status,_,_=request(browser,base,'/api/enroll','POST',{'offering_id':'OF-101'},csrf_val)
                unauthorized_cases.append({'case':'POST /api/enroll without valid CSRF','status':status,'denied':status==403})
            teacher=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
            assert request(teacher,base,'/api/login','POST',{'username':'profesor','password':'EduCampus2026!'})[0]==200
            status,_,_=request(teacher,base,'/api/enrollments')
            unauthorized_cases.append({'case':'GET /api/enrollments as teacher','status':status,'denied':status==403})
            assert len(unauthorized_cases)==12
            invalid_cases=[]
            scenarios=[('ana','OF-105','SIN_CUPOS'),('diana','OF-102','PRERREQUISITO'),('elias','OF-103','CRUCE_HORARIO'),('elias','OF-101','DUPLICADA'),('bruno','OF-102','BLOQUEO_FINANCIERO'),('camila','OF-102','FINANCIERO_NO_DISPONIBLE'),('ana','OF-106','OFERTA_CERRADA'),('ana','unknown','OFERTA_INEXISTENTE')]
            for i in range(20):
                name,offer,expected=scenarios[i%len(scenarios)]
                before=counts(db)
                try:
                    enroll(name,offer,db)
                    code='ERROR_INESPERADO'
                except EnrollmentError as exc:
                    code=exc.code
                unchanged=counts(db)==before
                invalid_cases.append({'case':i+1,'actor':name,'offering':offer,'code':code,'expected':expected,'pass':code==expected and unchanged})
            checks=[]
            for _ in range(30):
                status,_,_=request(anonymous,base,'/api/health')
                checks.append(status==200)
            result={
                'utc_run':datetime.now(timezone.utc).isoformat(),
                'environment':'local ephemeral SQLite / ThreadingHTTPServer; fictional data',
                'rnf01':{'operation':'GET /api/offerings authenticated','n':len(timings),'p95_ms':round(p95,2),'median_ms':round(statistics.median(timings),2),'max_ms':round(max(timings),2),'threshold_ms':3000,'pass':p95<=3000},
                'rnf02':{'health_checks':30,'successful_checks':sum(checks),'duration_minutes':round((sum(timings)/1000)/60,4),'target_window_minutes':30,'verified':False,'note':'Short availability smoke check; not a continuous 30-minute measurement.'},
                'rnf03':{'total':12,'denied':sum(i['denied'] for i in unauthorized_cases),'pass':all(i['denied'] for i in unauthorized_cases),'cases':unauthorized_cases},
                'rnf04':{'total':20,'consistent':sum(i['pass'] for i in invalid_cases),'pass':all(i['pass'] for i in invalid_cases),'cases':invalid_cases},
                'rnf05':{'real_biometric_templates':0,'real_facial_images':0,'note':'Source/data fixture inspection; only fictional identifiers. No camera/image endpoints are present.'}
            }
            OUTPUT.parent.mkdir(parents=True,exist_ok=True)
            OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({k:v for k,v in result.items() if k not in ('rnf03','rnf04')},ensure_ascii=False,indent=2))
            print('RNF-03:',result['rnf03']['denied'],'/ 12 denied')
            print('RNF-04:',result['rnf04']['consistent'],'/ 20 no partial writes')
            if not (result['rnf01']['pass'] and result['rnf03']['pass'] and result['rnf04']['pass']):
                raise SystemExit('QA criteria failed')
        finally:
            server.shutdown();server.server_close()


if __name__=='__main__':
    main()
