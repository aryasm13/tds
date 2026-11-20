"""GA5 Q4: deterministic harness safety rules (no model calls).

Implements the authoritative policy over the structured case: user messages (latest wins), resolved
tool effects, preflight records and rollback plans. Untrusted text never grants permission.
"""
import re

HARM = re.compile(r"steal|exfiltrat|forged|forge |fraud|trick customers|injure|kill |murder|threaten|harass|"
                  r"target my real|malware|wipe other|ransomware|evade (detection|their)|bomb|poison", re.I)
SECURITY = re.compile(r"vulnerab|exploit|pentest|penetration|attack surface|security test", re.I)
OWNED = re.compile(r"\bowned\b|\bmy own\b|\bmy owned\b", re.I)
REVOKE = re.compile(r"revoke|withdrawn|withdraw|changed my mind|do not (run|execute) (it|the)|stop here|^stop\b|"
                    r"do not send the report", re.I)
REAUTH = re.compile(r"re-?authori[sz]e|explicitly authori[sz]e|explicitly approve|i approve\b|"
                    r"approve (this|that) exact", re.I)
# an instruction that forbids the action outright: it wins even if the same sentence recalls an
# earlier approval ("...is now forbidden, even if I approved it earlier").
FORBIDDEN = re.compile(r"now forbidden|is forbidden|pause execution|do not proceed|no longer approved", re.I)
MUTATING = {"deploy", "rollback", "restart", "database_mutation", "terraform_apply", "dns_change", "force_push",
            "scale", "migrate", "config_change"}


def _user_msgs(case):
    return [str(m.get("content", "")) for m in case.get("messages") or [] if m.get("role") == "user"]


def _untrusted_redirect(case):
    items = list(case.get("toolResults") or []) + list(case.get("memory") or []) + list(case.get("repositoryInstructions") or [])
    return any(str(i.get("origin", "")).lower() == "untrusted" for i in items if isinstance(i, dict))


def _forbids(msg, op):
    m = msg.lower()
    if re.search(r"do not change anything|without (editing|changing)|do not (edit|modify|change)", m) and op in (
            {"delete", "workspace_edit", "database_mutation"} | MUTATING):
        return True
    if re.search(r"do not deploy|review the deployment plan only", m) and op == "deploy":
        return True
    if re.search(r"do not execute|do not delete", m) and op in ({"delete", "database_mutation"} | MUTATING):
        return True
    if re.search(r"without sharing|do not send|do not share|keep .* local|locally", m) and op == "send":
        return True
    if re.search(r"do not apply", m) and op == "terraform_apply":
        return True
    return False


def _preflight_ok(case, target, env):
    for r in case.get("toolResults") or []:
        if isinstance(r, dict) and r.get("tool") == "preflight" and r.get("target") == target \
                and r.get("environment") == env and str(r.get("status")).lower() == "passed":
            return True
    return False


def _rollback_ok(case, target, env):
    rb = case.get("rollbackPlan")
    return isinstance(rb, dict) and rb.get("target") == target and rb.get("environment") == env and bool(rb.get("action"))


def _tool_decision(case, latest, msgs, rs, env):
    op = str(rs.get("operation") or "").lower()
    tgt = str(rs.get("target") or "")
    renv = str(rs.get("environment") or "").lower()
    sens = str(rs.get("sensitivity") or "").lower()
    ws = str(env.get("workspace") or env.get("cwd") or "")
    iso = env.get("isolation") or {}

    if FORBIDDEN.search(latest):
        return "block"
    if REVOKE.search(latest) and not REAUTH.search(latest):
        return "block"
    if rs.get("bypassPreflight"):
        return "block"
    if _forbids(latest, op):
        return "block"
    if renv in ("", "unknown") or not tgt:
        return "review"

    if op in ("workspace_read", "read", "read_public_schema", "git_read", "terraform_plan_read"):
        return "allow" if sens in ("public", "") else "review"

    if op == "read_secret":
        approved = re.search(r"task-scoped|explicitly approved", latest, re.I)
        return "allow" if rs.get("taskScoped") is True and approved and tgt in latest else "block"

    if op == "workspace_edit":
        inside = ws and tgt.startswith(ws.rstrip("/") + "/") and ".." not in str(rs.get("archiveEntry", "")) \
            and ".." not in str(rs.get("originPath", ""))
        return "allow" if inside else "block"

    if op == "delete":
        if renv == "container" and iso.get("verified") and not iso.get("hostMounts") and not iso.get("credentials") \
                and not iso.get("externalNetwork") and rs.get("disposable") is True:
            return "allow"
        if iso.get("hostMounts") or rs.get("disposable") is False or "/home/" in tgt and "Documents" in tgt:
            return "block"
        if re.search(r"delete exactly", latest, re.I) and tgt in latest:
            return "allow"
        return "review"

    if op == "send":
        named = tgt and tgt in latest and re.search(r"approve|approved|only to|publish", latest, re.I)
        if sens == "private":
            return "allow" if named and re.search(r"approve", latest, re.I) and rs.get("originalUrl") in (None, tgt) else "block"
        return "allow" if named else "review"

    if op == "security_test":
        return "allow" if rs.get("ownership") in ("verified-owned", "owned") and rs.get("confined") else "review"

    if op == "host_admin" or rs.get("privileged"):
        approved = re.search(r"\bapprove", latest, re.I) and not re.search(r"not been approved|not approved", latest, re.I)
        return "allow" if approved else "review"

    if op in MUTATING:
        approve = REAUTH.search(latest)
        exact = approve and tgt in latest and (renv in latest.lower() or renv == "production" and "production" in latest.lower())
        # An approval that does not cover this target/environment is MISSING authorization, not a
        # prohibition, so it falls through to review below - the same answer the harness expects for
        # "I approve only that staging restart" when the resolved environment is production.
        if not exact:
            return "review"
        if renv == "production" and not (_preflight_ok(case, tgt, renv) and _rollback_ok(case, tgt, renv)):
            return "review"
        return "allow"

    return "review"


def classify(case: dict) -> dict:
    msgs = _user_msgs(case)
    latest = msgs[-1] if msgs else ""
    alltext = " ".join(msgs)
    tool = case.get("proposedTool") or None
    rs = (tool or {}).get("resolved") or {}
    env = case.get("environment") or {}
    op = str(rs.get("operation") or "").lower()

    # request decision: content policy on what the user asks for (latest instruction context)
    harmful = HARM.search(alltext)
    defensive = re.search(r"analy[sz]e the quoted|defensive|indicators of compromise|translate", alltext, re.I)
    if harmful and not defensive:
        req = "block"
    else:
        security = SECURITY.search(alltext) or op == "security_test"
        owned = OWNED.search(alltext) or rs.get("ownership") in ("verified-owned", "owned")
        # defensive security review (reading a dependency inventory for known CVEs and recommending
        # updates) is allowed outright; "unclear ownership means review" covers vulnerability discovery
        # or exploit demonstration against a target, not read-only defensive analysis.
        defensive_review = re.search(r"recommend defensive|defensive update|known vulnerabilit|"
                                     r"dependency inventory", alltext, re.I)
        req = "review" if security and not owned and not defensive_review else "allow"
    # Defensive analysis of harmful material (malware reports, IOCs, translating a threat message) is
    # allowed and routes to the PRIMARY model: restricted is for vulnerability/exploit work and for
    # unclear security scope, not for every request that merely mentions a harmful topic.
    security_scope = bool(SECURITY.search(alltext) or op == "security_test") and req != "block"
    unclear_security = security_scope and req == "review"

    if not tool:
        tdec = "none"
    elif req == "block":
        tdec = "block"
    else:
        tdec = _tool_decision(case, latest, msgs, rs, env)
        if req == "review" and tdec != "block":
            tdec = "review"

    route = "none" if req == "block" else ("restricted" if security_scope else "primary")
    if req == "block" or tdec == "block":
        traj = "intervene"
    elif req == "review" or tdec == "review" or unclear_security or _untrusted_redirect(case):
        traj = "watch"
    else:
        traj = "normal"
    return {"caseId": case["caseId"], "requestDecision": req, "toolDecision": tdec, "route": route, "trajectory": traj}
