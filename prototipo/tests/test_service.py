"""Automated acceptance, integrity, concurrency and permission tests."""
from __future__ import annotations

import concurrent.futures
import shutil
import tempfile
import unittest
from pathlib import Path

from educampus.db import PERIOD, connect, initialize
from educampus.service import EnrollmentError, enroll, offerings, student_enrollments


class EnrollmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_dir = tempfile.TemporaryDirectory()
        cls.template_path = Path(cls.template_dir.name) / 'template.sqlite3'
        initialize(cls.template_path, reset=True)

    @classmethod
    def tearDownClass(cls):
        cls.template_dir.cleanup()

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.db = Path(self.workspace.name) / 'test.sqlite3'
        shutil.copyfile(self.template_path, self.db)

    def tearDown(self):
        self.workspace.cleanup()

    def snapshot(self):
        with connect(self.db) as conn:
            return (conn.execute('SELECT count(*) FROM enrollments').fetchone()[0],
                    tuple((x['id'],x['remaining']) for x in conn.execute('SELECT id,remaining FROM offerings ORDER BY id')))

    def rejection(self, user, offer, code):
        before = self.snapshot()
        with self.assertRaises(EnrollmentError) as ctx:
            enroll(user, offer, self.db)
        self.assertEqual(ctx.exception.code, code)
        self.assertEqual(self.snapshot(), before)

    def test_success_is_atomic_and_traceable(self):
        before = self.snapshot()
        result = enroll('ana', 'OF-101', self.db)
        self.assertEqual(result['status'],'CONFIRMADA')
        self.assertEqual(result['period'],PERIOD)
        self.assertEqual(self.snapshot()[0],before[0]+1)
        self.assertEqual(next(o for o in offerings(self.db) if o['id']=='OF-101')['remaining'],before[1][0][1]-1)
        self.assertEqual(student_enrollments(self.db,'ana')[0]['offering_id'],'OF-101')

    def test_duplicate_a4(self):
        enroll('ana','OF-101',self.db)
        self.rejection('ana','OF-101','DUPLICADA')

    def test_no_slots_a1(self):
        self.rejection('ana','OF-105','SIN_CUPOS')

    def test_prerequisite_a2(self):
        self.rejection('diana','OF-102','PRERREQUISITO')

    def test_schedule_conflict_a3(self):
        self.rejection('elias','OF-103','CRUCE_HORARIO')

    def test_financial_block_a5(self):
        self.rejection('bruno','OF-102','BLOQUEO_FINANCIERO')

    def test_financial_unavailable_a6(self):
        self.rejection('camila','OF-102','FINANCIERO_NO_DISPONIBLE')

    def test_offer_closed(self):
        self.rejection('ana','OF-106','OFERTA_CERRADA')

    def test_period_closed(self):
        with connect(self.db) as conn:
            conn.execute("UPDATE academic_periods SET status='CERRADO'")
            conn.commit()
        self.rejection('ana','OF-102','OFERTA_CERRADA')

    def test_unknown_offer(self):
        self.rejection('ana','invalid','OFERTA_INEXISTENTE')

    def test_invalid_identifier(self):
        self.rejection('ana','', 'OFERTA_INVALIDA')

    def test_teacher_cannot_enroll(self):
        self.rejection('profesor','OF-102','NO_AUTORIZADO')

    def test_rollback_storage_failure_e1(self):
        before=self.snapshot()
        with self.assertRaises(EnrollmentError) as ctx:
            enroll('ana','OF-102',self.db, fail_after_insert=True)
        self.assertEqual(ctx.exception.code,'ERROR_PERSISTENCIA')
        self.assertEqual(self.snapshot(),before)

    def test_student_cannot_see_another_student_enrollments(self):
        self.assertEqual(student_enrollments(self.db,'ana'),[])
        self.assertEqual(len(student_enrollments(self.db,'elias')),1)

    def test_simultaneous_last_seat_only_one_confirmed(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda user: _attempt(user,self.db), ['ana','diana','elias','ana','diana','elias']))
        self.assertEqual(sum(result=='OK' for result in results),1)
        with connect(self.db) as conn:
            self.assertEqual(conn.execute("SELECT remaining FROM offerings WHERE id='OF-104'").fetchone()[0],0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM enrollments WHERE offering_id='OF-104'").fetchone()[0],1)

    def test_sequential_conflict_after_enrollment(self):
        enroll('ana','OF-101',self.db)
        self.rejection('ana','OF-103','CRUCE_HORARIO')

    def test_different_sections_and_different_period_rules(self):
        with connect(self.db) as conn:
            conn.execute("INSERT INTO academic_periods VALUES ('2027-1','Semestre 2027-1','ABIERTO')")
            conn.execute("INSERT INTO offerings VALUES ('OF-201','SIS101','2027-1','A',1,'08:00','10:00',5,5,'ABIERTA')")
            conn.commit()
        # This tests that schedule conflicts are restricted to a single period.
        result=enroll('elias','OF-201',self.db)
        self.assertEqual(result['period'],'2027-1')


def _attempt(user,path):
    try:
        enroll(user,'OF-104',path)
        return 'OK'
    except EnrollmentError as exc:
        return exc.code


if __name__=='__main__':
    unittest.main()
