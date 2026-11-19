"""Measure RNF-02 over a real 30-minute cloud observation window."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def main():
    parser=argparse.ArgumentParser(description='30-minute, 30-check availability evidence')
    parser.add_argument('base_url',help='Deployed https://*.onrender.com URL')
    parser.add_argument('--output',default='observacion_cloud_30min.json')
    args=parser.parse_args()
    if not args.base_url.startswith('https://'):
        parser.error('Use an HTTPS URL from the deployed service.')
    target=args.base_url.rstrip('/')+'/api/health'
    start=time.monotonic()
    samples=[]
    for i in range(30):
        target_time=start + i*60
        delay=target_time-time.monotonic()
        if delay>0:time.sleep(delay)
        now=datetime.now(timezone.utc).isoformat()
        try:
            with urlopen(target,timeout=18) as resp:
                data=json.loads(resp.read(1024))
                success=resp.status==200 and data.get('ok') is True
                code=resp.status
        except (URLError,TimeoutError,ValueError) as exc:
            success=False;code=str(type(exc).__name__)
        samples.append({'utc':now,'success':success,'http_status_or_error':code})
        print(f'{i+1:02}/30 {"OK" if success else "FAIL"}: {code}',flush=True)
    final_delay=start+1800-time.monotonic()
    if final_delay>0:time.sleep(final_delay)
    report={'url':target,'utc_end':datetime.now(timezone.utc).isoformat(),'window_seconds':round(time.monotonic()-start,2),
            'successful_checks':sum(x['success'] for x in samples),'total_checks':30,
            'rnf02_threshold':29,'pass':sum(x['success'] for x in samples)>=29,'samples':samples}
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))

if __name__=='__main__':main()
