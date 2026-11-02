import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

def to_prolog_atom(val: str) -> str:
    if not val:
        return "unknown"
    s = re.sub(r'[^a-zA-Z0-9_]+', '_', str(val).strip().lower()).strip('_')
    if not s:
        return "unknown"
    if not s[0].isalpha() or s[0].isupper():
        s = "item_" + s
    return s

class GridRescueProlog:
    def __init__(self):
        self.lock = threading.Lock()
        
        self.base_dir = Path(__file__).resolve().parent
        self.kb_path = self.base_dir / "prolog" / "knowledge_base.pl"
        self.swipl_bin = self._find_swipl()
        
        print(f"Prolog Engine Initialized. Binary: {self.swipl_bin}")
        print(f"Knowledge Base: {self.kb_path}")

    def _find_swipl(self):
        candidates = [
            r"D:\prolog\swipl\bin\swipl.exe",
            r"C:\Program Files\swipl\bin\swipl.exe",
            r"C:\Program Files (x86)\swipl\bin\swipl.exe",
            shutil.which("swipl")
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return "swipl"

    def analyze_incident(self, incident_id, reports, location=None):
        with self.lock:
            # Create an isolated temporary facts file for this specific analysis run
            temp_file = tempfile.NamedTemporaryFile(
                mode="w", 
                suffix=".pl", 
                prefix=f"facts_{incident_id}_",
                dir=str(self.base_dir / "prolog"),
                delete=False
            )
            temp_path = Path(temp_file.name)
            
            try:
                if location:
                    clean_loc = to_prolog_atom(location)
                    temp_file.write(f"incident_location({incident_id}, {clean_loc}).\n")
                for r in reports:
                    source = to_prolog_atom(r['source_type'])
                    evidence = to_prolog_atom(r['evidence_category'])
                    temp_file.write(f"report({incident_id}, {source}, {evidence}).\n")
                temp_file.flush()
                temp_file.close()

                query = (
                    f"diagnose_fault({incident_id}, Fault), "
                    f"suspect_component({incident_id}, Suspect), "
                    f"incident_severity({incident_id}, Severity), "
                    f"recommend_action({incident_id}, Action), "
                    f"(incident_location({incident_id}, Loc), upstream_chain(Loc, Chain) -> true ; Chain = []), "
                    f"format('FAULT:~w~nSUSPECT:~w~nSEVERITY:~w~nACTION:~w~nCHAIN:~w~n', [Fault, Suspect, Severity, Action, Chain]), "
                    f"halt."
                )
                
                cmd = [
                    self.swipl_bin,
                    "-q",
                    "-f", str(self.kb_path),
                    "-l", str(temp_path),
                    "-g", query,
                    "-t", "halt"
                ]
                
                result_data = {
                    "fault": "UNKNOWN FAULT",
                    "suspect_component": "unknown",
                    "severity": "STANDARD",
                    "upstream_path": "",
                    "action_plan": "Deploy field survey team to verify reports"
                }
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                output = result.stdout.strip()
                
                for line in output.splitlines():
                    if line.startswith("FAULT:"):
                        result_data["fault"] = line.replace("FAULT:", "").strip()
                    elif line.startswith("SUSPECT:"):
                        result_data["suspect_component"] = line.replace("SUSPECT:", "").strip()
                    elif line.startswith("SEVERITY:"):
                        result_data["severity"] = line.replace("SEVERITY:", "").strip()
                    elif line.startswith("ACTION:"):
                        result_data["action_plan"] = line.replace("ACTION:", "").strip()
                    elif line.startswith("CHAIN:"):
                        chain_raw = line.replace("CHAIN:", "").strip().strip("[]")
                        if chain_raw:
                            nodes = [n.strip() for n in chain_raw.split(",") if n.strip()]
                            nodes.reverse()
                            result_data["upstream_path"] = " -> ".join(nodes)
                
                return result_data
                
            except subprocess.CalledProcessError as e:
                print(f"PROLOG ERROR STDOUT: {e.stdout}")
                print(f"PROLOG ERROR STDERR: {e.stderr}")
                return {
                    "fault": f"PROLOG ERROR: {e.stderr.strip()}",
                    "suspect_component": "unknown",
                    "severity": "STANDARD",
                    "upstream_path": "",
                    "action_plan": "Review incident logs and retry analysis"
                }
            except FileNotFoundError:
                return {
                    "fault": "SWI-PROLOG NOT CONFIGURED",
                    "suspect_component": "unknown",
                    "severity": "STANDARD",
                    "upstream_path": "",
                    "action_plan": "Ensure SWI-Prolog is installed and in system PATH"
                }
            finally:
                # Clean up temporary facts file
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception:
                    pass

prolog_engine = GridRescueProlog()
