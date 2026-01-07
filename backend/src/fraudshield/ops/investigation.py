from __future__  import annotations
import os
import json
from typing import Any, Dict

from ..core.settings import settings
from ..tools import enrichment as E
from ..util.jsonx import extract_json

def run_investigation(trans_id: str, base_packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a multi-agent CrewAI pipeline.
    IMPORTANT: this module requires `fraudshield[ops]`.
    """
    # Imports only inside ops module
    from crewai import Agent, Task, Crew, Process, LLM

    s = settings()
    if not s.openai_api_key:
        return {**base_packet, "error": "missing_openai_api_key", "message": "Set OPENAI_API_KEY to run agents."}

    llm = LLM(model=f"openai/{s.openai_model}", api_key=s.openai_api_key)

    context = json.dumps(
        {
            "transaction_id": trans_id,
            "decision_packet": base_packet,
            "pii_note": "PII redacted unless INCLUDE_PII=true",
        },
        indent=2,
    )

    data_sentry = Agent(
        role="Data Sentry",
        goal="Produce evidence JSON using only retrieved tool data.",
        backstory="Risk investigator focused on verifiable internal facts.",
        llm=llm,
        verbose=True,
    )

    threat_intel = Agent(
        role="Threat Intel",
        goal="Produce intel JSON from IP intel and flags.",
        backstory="Threat intel analyst for proxy/datacenter risk.",
        llm=llm,
        verbose=True,
    )

    compliance_guard = Agent(
        role="Compliance Guard",
        goal="Use KYC and disputes evidence to produce compliance JSON. No decisioning.",
        backstory="AML/KYC specialist ensuring audit-ready compliance review.",
        llm=llm,
        verbose=True,
    )

    rca_writer = Agent(
        role="RCA Writer",
        goal="Write a markdown case narrative summarizing evidence and deterministic decision rationale.",
        backstory="Senior fraud operations writer.",
        llm=llm,
        verbose=True,
    )

    # Tool outputs injected in prompts (keep tool-calling out of LLM for demo stability)
    txn = E.lookup_transaction(trans_id)
    if not txn.get("found"):
        return {**base_packet, "error": "transaction_not_found"}

    t = txn["transaction"]
    user_id = t["user_id"]
    user_hist = E.lookup_user_history(user_id)
    ip_intel = E.lookup_ip_intel(t.get("device_ip", ""))
    kyc = E.lookup_kyc(user_id)
    disputes = E.lookup_disputes(user_id)
    similar = E.find_similar_cases_stub(trans_id)

    evidence_blob = json.dumps({"transaction": txn, "user_history": user_hist, "similar_cases": similar}, indent=2, default=str)
    intel_blob = json.dumps({"ip_intel": ip_intel}, indent=2, default=str)
    compliance_blob = json.dumps({"kyc": kyc, "disputes": disputes}, indent=2, default=str)

    t1 = Task(
        description=(
            "Return ONLY valid JSON:\n"
            "{ \"transaction\": {...}, \"user_history\": {...}, \"similar_cases\": {...}, "
            "\"observations\": [ {\"key\":\"...\",\"value\":\"...\",\"evidence\":\"...\"} ] }\n"
            "No markdown.\n\n"
            f"Context:\n{context}\n\nEvidence Inputs:\n{evidence_blob}"
        ),
        expected_output="JSON only",
        agent=data_sentry,
    )

    t2 = Task(
        description=(
            "Return ONLY valid JSON:\n"
            "{ \"ip_intel\": {...}, \"flags\": [\"proxy\", ...], \"notes\": \"...\" }\n"
            "No markdown.\n\n"
            f"Context:\n{context}\n\nIntel Inputs:\n{intel_blob}"
        ),
        expected_output="JSON only",
        agent=threat_intel,
    )

    t3 = Task(
        description=(
            "Return ONLY valid JSON:\n"
            "{ \"evidence_sources\": {\"kyc\": {...}, \"disputes\": {...}}, "
            "\"policy_concerns\": [ {\"policy_area\":\"KYC|AML|DISPUTES|OTHER\",\"summary\":\"...\",\"severity\":\"low|medium|high\"} ], "
            "\"required_actions\": [\"...\"], "
            "\"constraints\": \"Only mention concerns supported by evidence_sources or context.\" }\n"
            "No markdown.\n\n"
            f"Context:\n{context}\n\nCompliance Inputs:\n{compliance_blob}"
        ),
        expected_output="JSON only",
        agent=compliance_guard,
    )

    t4 = Task(
        description=(
            "Write MARKDOWN ONLY with these sections:\n"
            "### Summary\n### Evidence (bullets)\n### Model & Rules\n### Recommended Next Steps\n### Escalation Notes\n\n"
            "Explicitly state: ML+Rules made the decision; this narrative is explanatory only.\n\n"
            f"Context:\n{context}"
        ),
        expected_output="Markdown only",
        agent=rca_writer,
    )

    crew = Crew(agents=[data_sentry, threat_intel, compliance_guard, rca_writer], tasks=[t1, t2, t3, t4], process=Process.sequential, verbose=True)
    aggregate = crew.kickoff()

    # Robustly extract outputs
    def _task_out(task) -> str:
        try:
            out = getattr(task, "output", None)
            if out is not None:
                raw = getattr(out, "raw", None)
                if raw:
                    return str(raw)
                return str(out)
        except Exception:
            pass
        try:
            res = getattr(task, "result", None)
            if res:
                return str(res)
        except Exception:
            pass
        return str(aggregate or "")

    evidence = extract_json(_task_out(t1))
    intel = extract_json(_task_out(t2))
    compliance = extract_json(_task_out(t3))
    rca_md = _task_out(t4).strip() or str(aggregate)

    artifacts_dir = os.path.join(settings().reports_path, "cases", trans_id)
    os.makedirs(artifacts_dir, exist_ok=True)

    with open(os.path.join(artifacts_dir, "evidence.json"), "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)
    with open(os.path.join(artifacts_dir, "intel.json"), "w", encoding="utf-8") as f:
        json.dump(intel, f, indent=2, ensure_ascii=False)
    with open(os.path.join(artifacts_dir, "compliance.json"), "w", encoding="utf-8") as f:
        json.dump(compliance, f, indent=2, ensure_ascii=False)
    with open(os.path.join(artifacts_dir, "case_summary.md"), "w", encoding="utf-8") as f:
        f.write(rca_md + "\n")

    return {
        **base_packet,
        "artifacts_dir": artifacts_dir,
        "agent_outputs": {
            "data_sentry": evidence,
            "threat_intel": intel,
            "compliance_guard": compliance,
            "rca_writer_md": rca_md,
        },
    }
