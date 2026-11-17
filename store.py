import sqlite3, json, os, uuid
from pathlib import Path
from datetime import datetime, timezone

ORG='org_demo_trama'
SCHEMA='''CREATE TABLE IF NOT EXISTS records (
 id TEXT PRIMARY KEY, org TEXT NOT NULL, kind TEXT NOT NULL,
 operation TEXT NOT NULL, occupation TEXT, payload TEXT NOT NULL,
 fingerprint TEXT, created TEXT NOT NULL,
 UNIQUE(org,kind,fingerprint));
 CREATE INDEX IF NOT EXISTS scope ON records(org,kind,operation,occupation);
 PRAGMA user_version=1;'''
class Store:
    def __init__(self, path=None):
        self.path=path or os.getenv('TRAMA_DB_PATH','data/trama.sqlite')
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db: db.executescript(SCHEMA)
    def connect(self):
        return sqlite3.connect(self.path)
    def all(self,kind,operation=None,occupation=None):
        sql='SELECT id,payload FROM records WHERE org=? AND kind=?'; args=[ORG,kind]
        if operation: sql+=' AND operation=?'; args.append(operation)
        if occupation: sql+=' AND occupation=?'; args.append(occupation)
        with self.connect() as db: rows=db.execute(sql,args).fetchall()
        return [dict(json.loads(p),id=i) for i,p in rows]
    def add(self,kind,data,actor='Demonstração',fingerprint=None,audit=True):
        data=dict(data); ident=data.pop('id',None) or str(uuid.uuid4())
        if data.get('org',ORG)!=ORG: raise PermissionError('Organização inválida.')
        now=datetime.now(timezone.utc).isoformat()
        try:
            with self.connect() as db:
                db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?)',(ident,ORG,kind,data.get('operation_id','global'),data.get('occupation'),json.dumps(data,ensure_ascii=False),fingerprint,now))
                if audit:
                    a={'operation_id':data.get('operation_id','global'),'action':'create','kind':kind,'record':ident,'actor':actor,'date':now}
                    db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),ORG,'audit',a['operation_id'],None,json.dumps(a),None,now))
            return ident
        except sqlite3.IntegrityError:
            if fingerprint:
                with self.connect() as db: found=db.execute('SELECT id FROM records WHERE org=? AND kind=? AND fingerprint=?',(ORG,kind,fingerprint)).fetchone()
                if found:return found[0]
            raise
    def update(self,kind,ident,data,actor='Demonstração'):
        data=dict(data); data.pop('id',None)
        with self.connect() as db:
            existing=db.execute('SELECT operation,occupation FROM records WHERE org=? AND kind=? AND id=?',(ORG,kind,ident)).fetchone()
            if not existing: raise PermissionError('Registro indisponível.')
            if data.get('operation_id')!=existing[0] or data.get('occupation')!=existing[1]: raise PermissionError('Mudança de escopo bloqueada.')
            db.execute('UPDATE records SET payload=? WHERE org=? AND kind=? AND id=?',(json.dumps(data,ensure_ascii=False),ORG,kind,ident))
            now=datetime.now(timezone.utc).isoformat()
            event={'operation_id':existing[0],'action':'update','kind':kind,'record':ident,'actor':actor,'date':now}
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),ORG,'audit',existing[0],None,json.dumps(event),None,now))
