"""
Persistencia real con Postgres (psycopg2). Requiere: pip install -r requirements.txt
y un Postgres corriendo (ver docker-compose.yml en la raíz del repo).
Misma interfaz que db.py (SQLite) y store.py/memory.py (memoria) — drop-in replacement.
"""
import json, hashlib, time, os
import psycopg2
import psycopg2.extras

DSN = os.environ.get("POSTGRES_DSN", "postgres://hypercore:hypercore@localhost:5432/hypercore")


class PostgresDB:
    def __init__(self, dsn: str = DSN):
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = False
        self._init_schema()

    def _init_schema(self):
        with self.conn.cursor() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY, name TEXT, capabilities JSONB, state TEXT,
                token_budget_per_hour INTEGER, memory_namespace TEXT,
                version TEXT, created_at TEXT, updated_at TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS event_queue (
                id SERIAL PRIMARY KEY, agent_id TEXT, payload JSONB,
                created_at DOUBLE PRECISION, consumed BOOLEAN DEFAULT FALSE)""")
            c.execute("""CREATE TABLE IF NOT EXISTS episodic_log (
                id SERIAL PRIMARY KEY, namespace TEXT, event JSONB,
                ts DOUBLE PRECISION, hash TEXT, prev_hash TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS working_memory (
                namespace TEXT PRIMARY KEY, data JSONB)""")
            # pgvector para Semantic Memory real (Sec.10) — requiere: CREATE EXTENSION vector;
            c.execute("CREATE EXTENSION IF NOT EXISTS vector")
            c.execute("""CREATE TABLE IF NOT EXISTS semantic_memory (
                id SERIAL PRIMARY KEY, namespace TEXT, content TEXT, embedding vector(1536))""")
        self.conn.commit()


class AgentStorePG:
    def __init__(self, db: PostgresDB): self.db = db

    def save(self, agent):
        with self.db.conn.cursor() as c:
            c.execute("""INSERT INTO agents VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET state=EXCLUDED.state, updated_at=EXCLUDED.updated_at""",
                (agent.id, agent.name, json.dumps(agent.capabilities), agent.state.value,
                 agent.token_budget_per_hour, agent.memory_namespace, agent.version,
                 agent.created_at, agent.updated_at))
        self.db.conn.commit()

    def get(self, agent_id):
        from agent import AgentDNA, AgentState
        with self.db.conn.cursor() as c:
            c.execute("SELECT * FROM agents WHERE id=%s", (agent_id,))
            row = c.fetchone()
        if not row: return None
        a = AgentDNA(name=row[1], capabilities=row[2], token_budget_per_hour=row[4])
        a.id, a.state = row[0], AgentState(row[3])
        a.memory_namespace, a.version, a.created_at, a.updated_at = row[5], row[6], row[7], row[8]
        return a

    def list_all(self):
        with self.db.conn.cursor() as c:
            c.execute("SELECT id FROM agents")
            ids = [r[0] for r in c.fetchall()]
        return [self.get(i) for i in ids]


class MemoryPlanePG:
    """Working+Episodic en Postgres, Semantic con pgvector real (Sec.10)."""
    def __init__(self, db: PostgresDB): self.db = db

    def working_get(self, ns):
        with self.db.conn.cursor() as c:
            c.execute("SELECT data FROM working_memory WHERE namespace=%s", (ns,))
            row = c.fetchone()
        return row[0] if row else {}

    def working_set(self, ns, data):
        with self.db.conn.cursor() as c:
            c.execute("""INSERT INTO working_memory VALUES (%s,%s)
                ON CONFLICT (namespace) DO UPDATE SET data=EXCLUDED.data""", (ns, json.dumps(data)))
        self.db.conn.commit()

    def episodic_append(self, ns, event):
        with self.db.conn.cursor() as c:
            c.execute("SELECT hash FROM episodic_log WHERE namespace=%s ORDER BY id DESC LIMIT 1", (ns,))
            row = c.fetchone()
            prev_hash = row[0] if row else "0" * 64
            h = hashlib.sha256((json.dumps(event, sort_keys=True) + prev_hash).encode()).hexdigest()
            c.execute("INSERT INTO episodic_log (namespace,event,ts,hash,prev_hash) VALUES (%s,%s,%s,%s,%s)",
                       (ns, json.dumps(event), time.time(), h, prev_hash))
        self.db.conn.commit()

    def episodic_log(self, ns):
        with self.db.conn.cursor() as c:
            c.execute("SELECT event, ts, hash, prev_hash FROM episodic_log WHERE namespace=%s ORDER BY id", (ns,))
            rows = c.fetchall()
        return [{"event": r[0], "ts": r[1], "hash": r[2], "prev_hash": r[3]} for r in rows]

    def verify_chain(self, ns):
        prev = "0" * 64
        for r in self.episodic_log(ns):
            expected = hashlib.sha256((json.dumps(r["event"], sort_keys=True) + prev).encode()).hexdigest()
            if expected != r["hash"]: return False
            prev = r["hash"]
        return True

    def semantic_upsert(self, ns, content: str, embedding: list[float]):
        with self.db.conn.cursor() as c:
            c.execute("INSERT INTO semantic_memory (namespace, content, embedding) VALUES (%s,%s,%s)",
                       (ns, content, embedding))
        self.db.conn.commit()

    def semantic_search(self, ns, query_embedding: list[float], k: int = 5):
        with self.db.conn.cursor() as c:
            c.execute("""SELECT content, embedding <-> %s::vector AS distance FROM semantic_memory
                WHERE namespace=%s ORDER BY distance LIMIT %s""", (query_embedding, ns, k))
            return [{"content": r[0], "distance": r[1]} for r in c.fetchall()]
