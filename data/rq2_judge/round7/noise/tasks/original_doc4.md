# Judge task original_doc4

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

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: The confidentiality obligations would stop a party from disclosing sexual harassment or sexual assault, with no exception for such disclosures.

Q2 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may acquire information similar to Confidential Information from a third party.

Q3 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall notify Disclosing Party if Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.

Q4 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q5 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may create a copy of some Confidential Information in some circumstances.

Q6 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some of Receiving Party's employees.

Q7 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the Agreement.

Q8 [TERM, about the base NDA] CONTRACT TERM: The Agreement does not grant the Receiving Party any right or licence to Confidential Information.

Q9 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that the Agreement was agreed or negotiated.

Q10 [TERM, about the base NDA] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q11 [TERM, about the base NDA] CONTRACT TERM: The agreement gives notice that an individual is immune from liability for disclosing a trade secret in confidence to a government official or an attorney solely to report a suspected violation of law, or in a sealed court filing.

Q12 [TERM, about the base NDA] CONTRACT TERM: Some obligations of the Agreement survive termination or expiry of the Agreement.

Q13 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may freely use residual knowledge, ideas or know-how retained in unaided memory from Confidential Information.

Q14 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some third-parties, including consultants, agents and professional advisors.

Q15 [TERM, about the base NDA] CONTRACT TERM: The Agreement assigns or transfers ownership of the Disclosing Party's Confidential Information or derivative works to the Receiving Party.
