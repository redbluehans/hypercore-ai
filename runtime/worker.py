"""Proceso aislado del agente. En Fase 5 esto llama a un LLM real; aquí es lógica placeholder."""
import sys, json

def main():
    data = json.loads(sys.stdin.read())
    msgs = data["messages"]
    responses = [{"reply": f"[{data['agent_id']}] procesado: {m.get('text','')}"} for m in msgs]
    new_working_memory = {**data["working_memory"], "last_processed": len(msgs)}
    print(json.dumps({"status": "TERMINATED", "responses": responses, "working_memory": new_working_memory}))

if __name__ == "__main__":
    main()
