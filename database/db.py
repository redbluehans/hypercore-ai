"""
Persistencia real (SQLite, stdlib, sin instalación). Mismo modelo relacional que
Postgres — migrar después es cambiar el driver, no el diseño. Reemplaza:
  store.py (AgentStore)      -> AgentStoreDB
  event_bus.py (EventBus)     -> EventBusDB   (cola durable, sobrevive reinicio)
  memory.py (MemoryPlane)     -> MemoryPlaneDB (hash-chain persistido)
"""
import sqlite3, json, hashlib, threading, time
from contextlib import contextmanager


class Database:
    def __init__(self, path="hypercore.db"):
        self.path = path
        self._local = threading.local()
        self._init_schema()

    def _conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.path, check_same_thread=False)
            self._local.conn.execute("PRAGMA journal_mode=WAL")  # durabilidad + concurrencia real
        return self._local.conn

    @contextmanager
    def cursor(self):
        conn = self._conn()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_schema(self):
        with self.cursor() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY, name TEXT, capabilities TEXT, state TEXT,
                token_budget_per_hour INTEGER, memory_namespace TEXT,
                version TEXT, created_at TEXT, updated_at TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS event_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT,
                payload TEXT, created_at REAL, consumed INTEGER DEFAULT 0)""")
            c.execute("""CREATE TABLE IF NOT EXISTS episodic_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, namespace TEXT,
                event TEXT, ts REAL, hash TEXT, prev_hash TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS working_memory (
                namespace TEXT PRIMARY KEY, data TEXT)""")


class AgentStoreDB:
    """Reemplazo persistente de store.py::AgentStore. Misma interfaz."""
    def __init__(self, db: Database):
        self.db = db

    def save(self, agent):
        with self.db.cursor() as c:
            c.execute("""INSERT INTO agents VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET state=excluded.state, updated_at=excluded.updated_at""",
                (agent.id, agent.name, json.dumps(agent.capabilities), agent.state.value,
                 agent.token_budget_per_hour, agent.memory_namespace, agent.version,
                 agent.created_at, agent.updated_at))

    def get(self, agent_id):
        from agent import AgentDNA, AgentState
        with self.db.cursor() as c:
            c.execute("SELECT * FROM agents WHERE id=?", (agent_id,))
            row = c.fetchone()
        if not row:
            return None
        a = AgentDNA(name=row[1], capabilities=json.loads(row[2]), token_budget_per_hour=row[4])
        a.id, a.state = row[0], AgentState(row[3])
        a.memory_namespace, a.version, a.created_at, a.updated_at = row[5], row[6], row[7], row[8]
        return a

    def list_all(self):
        with self.db.cursor() as c:
            c.execute("SELECT id FROM agents")
            ids = [r[0] for r in c.fetchall()]
        return [self.get(i) for i in ids]


class EventBusDB:
    """Reemplazo persistente de event_bus.py::EventBus. Cola sobrevive reinicio (simula JetStream)."""
    def __init__(self, db: Database):
        self.db = db

    def publish(self, agent_id, message):
        with self.db.cursor() as c:
            c.execute("INSERT INTO event_queue (agent_id, payload, created_at) VALUES (?,?,?)",
                       (agent_id, json.dumps(message), time.time()))

    def pending(self, agent_id):
        with self.db.cursor() as c:
            c.execute("SELECT 1 FROM event_queue WHERE agent_id=? AND consumed=0 LIMIT 1", (agent_id,))
            return c.fetchone() is not None

    def consume_all(self, agent_id):
        with self.db.cursor() as c:
            c.execute("SELECT id, payload FROM event_queue WHERE agent_id=? AND consumed=0", (agent_id,))
            rows = c.fetchall()
            ids = [r[0] for r in rows]
            if ids:
                c.executemany("UPDATE event_queue SET consumed=1 WHERE id=?", [(i,) for i in ids])
        return [json.loads(r[1]) for r in rows]


class MemoryPlaneDB:
    """Reemplazo persistente de memory.py::MemoryPlane. Hash-chain persistido en disco."""
    def __init__(self, db: Database):
        self.db = db

    def working_get(self, ns):
        with self.db.cursor() as c:
            c.execute("SELECT data FROM working_memory WHERE namespace=?", (ns,))
            row = c.fetchone()
        return json.loads(row[0]) if row else {}

    def working_set(self, ns, data):
        with self.db.cursor() as c:
            c.execute("INSERT INTO working_memory VALUES (?,?) ON CONFLICT(namespace) DO UPDATE SET data=excluded.data",
                       (ns, json.dumps(data)))

    def episodic_append(self, ns, event):
        with self.db.cursor() as c:
            c.execute("SELECT hash FROM episodic_log WHERE namespace=? ORDER BY id DESC LIMIT 1", (ns,))
            row = c.fetchone()
            prev_hash = row[0] if row else "0" * 64
            h = hashlib.sha256((json.dumps(event, sort_keys=True) + prev_hash).encode()).hexdigest()
            c.execute("INSERT INTO episodic_log (namespace, event, ts, hash, prev_hash) VALUES (?,?,?,?,?)",
                       (ns, json.dumps(event), time.time(), h, prev_hash))

    def episodic_log(self, ns):
        with self.db.cursor() as c:
            c.execute("SELECT event, ts, hash, prev_hash FROM episodic_log WHERE namespace=? ORDER BY id", (ns,))
            rows = c.fetchall()
        return [{"event": json.loads(r[0]), "ts": r[1], "hash": r[2], "prev_hash": r[3]} for r in rows]

    def verify_chain(self, ns):
        prev = "0" * 64
        for r in self.episodic_log(ns):
            expected = hashlib.sha256((json.dumps(r["event"], sort_keys=True) + prev).encode()).hexdigest()
            if expected != r["hash"]:
                return False
            prev = r["hash"]
        return True
