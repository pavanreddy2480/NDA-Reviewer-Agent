# Judge task r1_doc4

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

[0] In the event of a breach of this Agreement, the Recipient shall not be entitled to any injunctive or equitable relief, but shall be limited to damages.
[1] Non-Disclosure
[2] Agreement
[3] Date:
[4] Parties: [NAME OF INDIVIDUAL RECEIVING INFORMATION] of [address of individual] and FRODSHAM TOWN COUNCIL whose registered office is at CASTLE PARK HOUSE, CASTLE PARK, FRODSHAM, WA6 6SB (the Discloser)
[5] 1. The Discloser intends to disclose information (the Confidential Information) to the Recipient for the purpose of recommendation of future land use of the decommissioned play area on Ship Street (the Purpose).
[6] 2. The Recipient undertakes not to use the Confidential Information for any purpose except the Purpose, without first obtaining the written agreement of the Discloser.
[7] 3. The Recipient undertakes to keep the Confidential Information secure and not to disclose it to any third party.
[8] 4. The undertakings in clauses 2 and 3 above apply to all of the information disclosed by the Discloser to the Recipient, regardless of the way or form in which it is disclosed or recorded but they do not apply to:
[9] a) any information which is or in future comes into the public domain (unless as a result of the breach of this Agreement); or
[10] b) any information which is already known to the Recipient and which was not subject to any obligation of confidence before it was disclosed to the Recipient by the Discloser.
[11] 5. Nothing in this Agreement will prevent the Recipient from making any disclosure of the Confidential Information required by law or by any competent authority.
[12] 6. The Recipient will, on request from the Discloser, return all copies and records of the Confidential Information to the Discloser and will not retain any copies or records of the Confidential Information.
[13] 7. Neither this Agreement nor the supply of any information grants the Recipient any licence, interest or right in respect of any intellectual property rights of the Discloser except the right to copy the Confidential Information solely for the Purpose.
[14] 8. The undertakings in clauses 2 and 3 will continue in force indefinitely.
[15] Receiving Party may acquire information similar to Confidential Information from a third party.
[16] When personal data is involved, the duty of confidence must last at least 36 months.
[17] Obligations that survive the end of the agreement must survive for at least 24 months.
[18] The duty of confidence must last at least 24 months; a shorter period needs Deputy General Counsel approval.
[19] Agreements must be governed by Delaware or New York law unless the General Counsel approves otherwise.
[20] The Receiving Party may develop, acquire or market products or services similar to those of the Disclosing Party, and nothing herein shall prevent it from doing so, whether or not such development uses ideas learned from the Disclosing Party.
[21] The English Courts will have non-exclusive jurisdiction to deal with any dispute which has arisen or may arise out of, or in connection with, this Agreement.
[22] Signed and Delivered as a Deed by:
[23] [name of Recipient] in the presence of:
[24] _____________________________
[25] Signature
[26] _____________________________
[27] Signature of witness
[28] _____________________________
[29] Name of witness

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.
