import os
import shutil
import subprocess
import threading
from pathlib import Path

class GridRescueProlog:
    def __init__(self):
        self.lock = threading.Lock()
        
        self.base_dir = Path(__file__).resolve().parent
        self.kb_path = self.base_dir / "prolog" / "knowledge_base.pl"
        self.temp_facts_path = self.base_dir / "prolog" / "temp_facts.pl"
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
            with open(self.temp_facts_path, "w") as f:
                if location:
                    clean_loc = str(location).strip().lower().replace(" ", "_")
                    f.write(f"incident_location({incident_id}, {clean_loc}).\n")
                for r in reports:
                    source = r['source_type']
                    evidence = r['evidence_category']
                    f.write(f"report({incident_id}, {source}, {evidence}).\n")
            
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
                "-l", str(self.temp_facts_path),
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
            
            try:
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
                result_data["fault"] = f"PROLOG ERROR: {e.stderr.strip()}"
                return result_data
            except FileNotFoundError:
                result_data["fault"] = "SWI-PROLOG NOT CONFIGURED"
                return result_data

prolog_engine = GridRescueProlog()