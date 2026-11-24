"""Validate the actual draft migration against SQLite. No Cloudflare access."""
import sqlite3
import unittest
from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / 'infrastructure/cloudflare/migrations/0001_initial.sql'

class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript(MIGRATION.read_text())
        self.db.executemany('INSERT INTO workspaces VALUES (?,?,?)', [('a','A','t'),('b','B','t')])
        self.db.executemany('INSERT INTO workspace_members VALUES (?,?,?)', [('a','alice','owner'),('b','bob','producer')])
        self.db.execute('INSERT INTO assets VALUES (?,?,?,?,?,?,?)', ('b','img','b/img','a'*64,'image/png','approved','t'))

    def tearDown(self):
        self.db.close()

    def job(self, workspace='a', id='j', subject='alice', state='queued', key='k', artifact=None):
        self.db.execute('INSERT INTO render_jobs VALUES (?,?,?,?,?,?,?,?,?)', (workspace,id,subject,'metallic-smoke-v1',state,key,'t',None,artifact))

    def test_valid_and_idempotency(self):
        self.job()
        with self.assertRaises(sqlite3.IntegrityError): self.job(id='j2')
        self.job(workspace='b',subject='bob')
        self.assertEqual(self.db.execute('SELECT count(*) FROM render_jobs').fetchone()[0],2)

    def test_member_scope(self):
        with self.assertRaises(sqlite3.IntegrityError): self.job(subject='bob')

    def test_asset_scope(self):
        with self.assertRaises(sqlite3.IntegrityError): self.job(artifact='img')
        self.job(workspace='b',subject='bob',artifact='img')

    def test_invalid_state_and_role(self):
        with self.assertRaises(sqlite3.IntegrityError): self.job(state='invented')
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute('INSERT INTO workspace_members VALUES (?,?,?)',('a','x','admin'))

    def test_migration_idempotent(self):
        self.db.executescript(MIGRATION.read_text())
        self.assertEqual(self.db.execute('PRAGMA foreign_keys').fetchone()[0],1)
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(),[])

if __name__ == '__main__': unittest.main()
