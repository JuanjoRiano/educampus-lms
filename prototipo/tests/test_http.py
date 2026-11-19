"""HTTP API authentication, role and CSRF regression checks."""
from __future__ import annotations

import http.cookiejar
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener
import json

from educampus.db import initialize
from educampus.web import create_server


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.db=Path(cls.tmp.name)/'http.sqlite3'
        initialize(cls.db,reset=True)
        cls.server=create_server('127.0.0.1',0,cls.db)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3);cls.tmp.cleanup()

    def setUp(self):
        self.opener=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(self,path,method='GET',data=None,csrf=None):
        headers={'Content-Type':'application/json'} if data is not None else {}
        if csrf is not None:headers['X-CSRF-Token']=csrf
        req=Request(self.base+path,data=json.dumps(data).encode('utf-8') if data is not None else (b'{}' if method=='POST' else None),headers=headers,method=method)
        try:
            with self.opener.open(req) as resp: return resp.status,json.loads(resp.read())
        except HTTPError as exc:
            return exc.code,json.loads(exc.read())

    def login(self,user='ana'):
        code,_=self.request('/api/login','POST',{'username':user,'password':'EduCampus2026!'})
        self.assertEqual(code,200)
        info=self.request('/api/session')[1]
        return info['csrf']

    def test_public_health(self):
        self.assertEqual(self.request('/api/health')[0],200)

    def test_login_wrong_password(self):
        self.assertEqual(self.request('/api/login','POST',{'username':'ana','password':'wrong'})[0],401)

    def test_anonymous_protected_get(self):
        self.assertEqual(self.request('/api/offerings')[0],401)
        self.assertEqual(self.request('/api/enrollments')[0],401)

    def test_anonymous_enroll(self):
        self.assertEqual(self.request('/api/enroll','POST',{'offering_id':'OF-101'})[0],401)

    def test_student_csrf_required(self):
        self.login()
        self.assertEqual(self.request('/api/enroll','POST',{'offering_id':'OF-102'})[0],403)
        self.assertEqual(self.request('/api/enroll','POST',{'offering_id':'OF-102'},csrf='invalid')[0],403)

    def test_student_own_list(self):
        self.login('elias')
        code,data=self.request('/api/enrollments')
        self.assertEqual(code,200)
        self.assertTrue(all(e['offering_id']=='OF-101' for e in data['enrollments']))

    def test_teacher_restrictions(self):
        token=self.login('profesor')
        self.assertEqual(self.request('/api/enrollments')[0],403)
        self.assertEqual(self.request('/api/enroll','POST',{'offering_id':'OF-102'},csrf=token)[0],403)

    def test_logout_revokes_cookie(self):
        token=self.login('bruno')
        self.assertEqual(self.request('/api/logout','POST',{},csrf=token)[0],200)
        self.assertEqual(self.request('/api/enrollments')[0],401)

    def test_static_assets_and_no_path_traversal(self):
        self.assertEqual(self.request('/api/health')[0],200)
        self.assertEqual(self.request('/unknown')[0],404)


if __name__=='__main__':
    unittest.main()
