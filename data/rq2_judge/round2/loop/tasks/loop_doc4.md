# Judge task loop_doc4

You are the independent judge for a contract-repair experiment. Answer every question below on your
own reading of the NDA text in this file. Do not use tools other than reading this file and writing the answer file.

Two kinds of question:

TERM questions. You are auditing a revised contract for a senior lawyer. Read the whole NDA and decide whether it
contains the CONTRACT TERM. Answer "Entailment" if the NDA contains the term (in any wording), "Contradiction" if it
says something incompatible with it, and "NotMentioned" if it does not deal with it. Exceptions and carve-outs count.
Cite segment numbers as evidence. Give your probability of being right as confidence, and a one-sentence rationale.
Answer: {"rationale": "...", "label": "Entailment|Contradiction|NotMentioned", "evidence": [ints], "confidence": 0-1}

FIELD questions. You extract facts from NDAs. Use only the numbered segments given with that question.
Answer: {"value": <as the question asks: a number, null, "blank" or "unspecified">, "evidence": [ints]}

Write ONE JSON object to the answer file: {"Q1": {...}, "Q2": {...}, ...} with every question id. Valid JSON only.

## NDA (base text)

[0] The Agreement does not grant the Receiving Party any right or licence to Confidential Information.
[1] Non-Disclosure
[2] Agreement
[3] Date:
[4] Parties: [NAME OF INDIVIDUAL RECEIVING INFORMATION] of [address of individual] and FRODSHAM TOWN COUNCIL whose registered office is at CASTLE PARK HOUSE, CASTLE PARK, FRODSHAM, WA6 6SB (the Discloser)
[5] The duty of confidence must last at least 24 months; a shorter period needs Deputy General Counsel approval.
[6] The duty of confidence must last at least 36 months when personal data is involved.
[7] 1. The Discloser intends to disclose information (the Confidential Information) to the Recipient for the purpose of recommendation of future land use of the decommissioned play area on Ship Street (the Purpose).
[8] The agreement gives notice that an individual is immune from liability for disclosing a trade secret in confidence to a government official or an attorney solely to report a suspected violation of law, or in a sealed court filing.
[9] Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the Agreement.
[10] 3. The Recipient undertakes to keep the Confidential Information secure and not to disclose it to any third party.
[11] Confidential Information may include verbally conveyed information.
[12] When personal data is involved, the duty of confidence must last at least 36 months.
[13] Receiving Party shall not disclose the fact that the Agreement was agreed or negotiated.
[14] 4. The undertakings in clauses 2 and 3 above apply to all of the information disclosed by the Discloser to the Recipient, regardless of the way or form in which it is disclosed or recorded but they do not apply to:
[15] All Confidential Information shall be expressly identified by the Disclosing Party.
[16] Receiving Party may share some Confidential Information with some of Receiving Party's employees.
[17] Receiving Party may share some Confidential Information with some third-parties, including consultants, agents and professional advisors.
[18] Receiving Party may acquire information similar to Confidential Information from a third party.
[19] a) any information which is or in future comes into the public domain (unless as a result of the breach of this Agreement); or
[20] b) any information which is already known to the Recipient and which was not subject to any obligation of confidence before it was disclosed to the Recipient by the Discloser.
[21] 5. Nothing in this Agreement will prevent the Recipient from making any disclosure of the Confidential Information required by law or by any competent authority.
[22] In the event of a breach of confidence, the Discloser may seek injunctive or equitable relief.
[23] Obligations that survive the end of the agreement must survive for at least 36 months.
[24] Agreements must be governed by Delaware or New York law unless the General Counsel approves otherwise.
[25] This Agreement may be governed by Delaware or New York law unless the General Counsel approves otherwise.
[26] The Agreement includes the notice of immunity under the Defend Trade Secrets Act for disclosures of trade secrets to government officials or attorneys.
[27] The Receiving Party may develop, acquire or market products or services similar to those of the Disclosing Party, and nothing herein shall prevent it from doing so, whether or not such development uses ideas learned from the Disclosing Party.
[28] Receiving Party may create a copy of some Confidential Information in some circumstances, including for backup, disaster recovery and legally required records.
[29] Signed and Delivered as a Deed by:
[30] [name of Recipient] in the presence of:
[31] _____________________________
[32] Signature
[33] _____________________________
[34] Signature of witness
[35] _____________________________
[36] Name of witness

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that the Agreement was agreed or negotiated.

Q2 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some of Receiving Party's employees.

Q3 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some third-parties, including consultants, agents and professional advisors.

Q4 [TERM, about the base NDA] CONTRACT TERM: The agreement gives notice that an individual is immune from liability for disclosing a trade secret in confidence to a government official or an attorney solely to report a suspected violation of law, or in a sealed court filing.
