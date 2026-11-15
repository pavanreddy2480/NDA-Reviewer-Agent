# Judge task r1_doc4_round1

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

[0] Non-Disclosure
[1] Agreement
[2] Date:
[3] Parties: [NAME OF INDIVIDUAL RECEIVING INFORMATION] of [address of individual] and FRODSHAM TOWN COUNCIL whose registered office is at CASTLE PARK HOUSE, CASTLE PARK, FRODSHAM, WA6 6SB (the Discloser)
[4] 1. The Discloser intends to disclose information (the Confidential Information) to the Recipient for the purpose of recommendation of future land use of the decommissioned play area on Ship Street (the Purpose).
[5] 2. The Recipient undertakes not to use the Confidential Information for any purpose except the Purpose, without first obtaining the written agreement of the Discloser.
[6] 3. The Recipient undertakes to keep the Confidential Information secure and not to disclose it to any third party.
[7] 4. The undertakings in clauses 2 and 3 above apply to all of the information disclosed by the Discloser to the Recipient, regardless of the way or form in which it is disclosed or recorded but they do not apply to:
[8] a) any information which is or in future comes into the public domain (unless as a result of the breach of this Agreement); or
[9] b) any information which is already known to the Recipient and which was not subject to any obligation of confidence before it was disclosed to the Recipient by the Discloser.
[10] 5. Nothing in this Agreement will prevent the Recipient from making any disclosure of the Confidential Information required by law or by any competent authority.
[11] 6. The Recipient will, on request from the Discloser, return all copies and records of the Confidential Information to the Discloser and will not retain any copies or records of the Confidential Information.
[12] 7. Neither this Agreement nor the supply of any information grants the Recipient any licence, interest or right in respect of any intellectual property rights of the Discloser except the right to copy the Confidential Information solely for the Purpose.
[13] 8. The undertakings in clauses 2 and 3 will continue in force indefinitely.
[14] 9. This Agreement is governed by, and is to be construed in accordance with, English law.
[15] The Receiving Party may develop, acquire or market products or services similar to those of the Disclosing Party, and nothing herein shall prevent it from doing so, whether or not such development uses ideas learned from the Disclosing Party.
[16] The English Courts will have non-exclusive jurisdiction to deal with any dispute which has arisen or may arise out of, or in connection with, this Agreement.
[17] Signed and Delivered as a Deed by:
[18] [name of Recipient] in the presence of:
[19] _____________________________
[20] Signature
[21] _____________________________
[22] Signature of witness
[23] _____________________________
[24] Name of witness

## NDA V1: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [13] insert:
    The duty of confidence must last at least 24 months; a shorter period needs Deputy General Counsel approval.

## NDA V2: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [13] insert:
    When personal data is involved, the duty of confidence must last at least 36 months.

## NDA V3: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [13] insert:
    Receiving Party may acquire information similar to Confidential Information from a third party.

## NDA V4: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [-1] insert:
    In the event of a breach of this Agreement, the Recipient shall not be entitled to any injunctive or equitable relief, but shall be limited to damages.

## Questions

Q1 [TERM, about NDA V1] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q2 [TERM, about NDA V2] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q3 [TERM, about NDA V3] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q4 [TERM, about NDA V4] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.
