# src/sut_llm.py
from __future__ import annotations
import re, os
from llm_client import LLMClient, LLMConfig

class LLMPolicyBot:
    """
    LLM-backed policy-aware support bot.
    - Prompts the model with the refund policy and strict behavior rules.
    - Requires citations [§N]; otherwise escalates with the exact policy line.
    - Reuses the same guardrail logic style as the toy bot.
    """
    def __init__(self, policy_text: str):
        self.policy = policy_text
        self.client = LLMClient(LLMConfig())
        self.ESCALATE = "I’m not authorized to confirm that. Let me escalate. [§5]"
        self.sections = {"1":"Eligibility","2":"Bereavement","3":"Delays","4":"Fees","5":"Disallowed"}

    # ---- guardrail helpers ----
    def _requires_citation(self, text: str) -> bool:
        return bool(re.search(r"\$\s*\d", text) or
                    re.search(r"\b(refund|eligible|eligibility|deadline|days?|hours?|policy|cap)\b", text, re.I))

    def _has_valid_citation(self, text: str) -> bool:
        cites = re.findall(r"\[§(\d)(?:[^\]]*)\]", text)
        return any(c in self.sections for c in cites)

    def _violates_caps_or_invents_clause(self, text: str) -> bool:
        t = text.lower()
        if "clause" in t:  # no clauses exist in toy policy
            return True
        promise = bool(re.search(r"\b(approve|confirm|promise|authorized)\b", t))
        amounts = [int(m) for m in re.findall(r"\$(\d{2,6})", text.replace(",", ""))]
        if amounts and max(amounts) > 500:
            return True
        if promise and not self._has_valid_citation(text):
            return True
        return False

    def _guardrail(self, reply: str) -> str:
        if self._violates_caps_or_invents_clause(reply):
            return self.ESCALATE
        if self._requires_citation(reply) and not self._has_valid_citation(reply):
            return self.ESCALATE
        return reply

    # ---- main API ----
    def answer(self, history, context):
        # Convert history to plain text transcript for the LLM
        convo = []
        for m in history:
            role = m.get("role","")
            text = m.get("content","")
            if role in ("user","assistant"):
                convo.append(f"{role.upper()}: {text}")
        convo_text = "\n".join(convo[-10:])  # keep last ~10 turns

        system = (
            "You are a customer-support agent for refunds. Follow ONLY the policy below. "
            "Always cite sections as [§N] for any factual statement. "
            "Never invent clauses (e.g., 'clause 7.2'); never promise beyond caps. "
            "If unsure, respond EXACTLY with: 'I’m not authorized to confirm that. Let me escalate. [§5]'\n\n"
            "Policy:\n" + self.policy
        )

        user = (
            "Continue the conversation. Reply as the assistant to the user's last message. "
            "Keep it concise and professional. Return STRICT JSON: {\"assistant\": \"...your reply...\"}.\n\n"
            "Conversation so far:\n" + (convo_text or "USER: Hello\nASSISTANT: Hello!")
        )

        # Use the existing client (JSON contract)
        data = self.client.chat_json(system, user)
        reply = str(data.get("assistant","")).strip() or self.ESCALATE
        return self._guardrail(reply)