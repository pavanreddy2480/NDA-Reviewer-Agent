# Judge task nda_9facd28a

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

[0] LAST MAN STANDS INTERNATIONAL NON-DISCLOSURE AGREEMENT
[1] THIS AGREEMENT is made on
[2] ____________________________________
[3] (Date)
[4] BETWEEN
[5] 1. Last Man Stands, (the "Disclosing Party"); and
[6] 2. _____________, (the "Receiving Party"),
[7] Collectively referred to as the "Parties".
[8] RECITALS
[9] A. The Receiving Party understands that the Disclosing Party has disclosed or may disclose information relating to Last Man Stands which to the extent previously, presently, or subsequently disclosed to the Receiving Party is hereinafter referred to as "Proprietary Information" of the Disclosing Party.
[10] OPERATIVE PROVISIONS
[11] 1. In consideration of the disclosure of Proprietary Information by the Disclosing Party, the Receiving Party hereby agrees:
[12] (i) to hold the Proprietary Information in strict confidence and to take all reasonable precautions to protect such Proprietary Information (including, without limitation, all precautions the Receiving Party employs with respect to its own confidential materials),
[13] (ii) not to disclose any such Proprietary Information or any information derived there from to any third person,
[14] (iii) not to make any use whatsoever at any time of such Proprietary Information except to evaluate internally its relationship with the Disclosing Party, and
[15] (iv) not to copy or reverse engineer any such Proprietary Information.
[16] The Receiving Party shall procure that its employees, agents and sub-contractors to whom Proprietary Information is disclosed or who have access to Proprietary Information sign a nondisclosure or similar agreement in content substantially similar to this Agreement.
[17] For a period of eighteen months following the execution of this agreement to the Receiving Party shall not, directly or indirectly hire, solicit, or encourage to leave the Disclosing Party employment, any employee, contractor or player of the Disclosing Party or hire any such employee or contractor who has left the Disclosing Parties employment, contractual engagement or player within one year of such employment or engagement, the Receiving Party.
[18] For a period of three years following the execution of this agreement, the contractor shall not start up his/her own cricket related business using the customer lists, trade secrets, inventions, innovations, processes, information, records and specifications of the Disclosing Party and/or used by the Disclosing party in connection with the operation of its business including, without limitation, the Disclosing parties business and product processes, methods, accounts and procedures.
[19] 2. Without granting any right or license, the Disclosing Party agrees that the foregoing shall not apply with respect to any information after five years following the disclosure thereof or any information that the Receiving Party can document
[20] (i) is or becomes (through no improper action or inaction by the Receiving Party or any affiliate, agent, consultant or employee) generally available to the public, or
[21] (ii) was in its possession or known by it prior to receipt from the Disclosing Party as evidenced in writing, except to the extent that such information was unlawfully appropriated, or
[22] (iii) was rightfully disclosed to it by a third party, or
[23] (iv) was independently developed without use of any Proprietary Information of the Disclosing Party.
[24] The Receiving Party may make disclosures required by law or court order provided the Receiving Party uses diligent reasonable efforts to limit disclosure and has allowed the Disclosing Party to seek a protective order.
[25] 3. Immediately upon the written request by the Disclosing Party at any time, the Receiving Party will return to the Disclosing Party all Proprietary Information and all documents or media containing any such Proprietary Information and any and all copies or extracts thereof, save that where such Proprietary Information is a form incapable of return or has been copied or transcribed into another document, it shall be destroyed or erased, as appropriate.
[26] 4. The Receiving Party understands that nothing herein
[27] (i) requires the disclosure of any Proprietary Information or
[28] (ii) requires the Disclosing Party to proceed with any transaction or relationship.
[29] 5. The Receiving Party further acknowledges and agrees that no representation or warranty, express or implied, is or will be made, and no responsibility or liability is or will be accepted by the Disclosing Party, or by any of its respective directors, officers, employees, agents or advisers, as to, or in relation to, the accuracy of completeness of any Proprietary Information made available to the Receiving Party or its advisers; it is responsible for making its own evaluation of such Proprietary Information.
[30] 6. The failure of either party to enforce its rights under this Agreement at any time for any period shall not be construed as a waiver of such rights.
[31] If any part, term or provision of this Agreement is held to be illegal or unenforceable neither the validity, nor enforceability of the remainder of this Agreement shall be affected.
[32] Neither Party shall assign or transfer all or any part of its rights under this Agreement without the consent of the other Party.
[33] This Agreement may not be amended for any other reason without the prior written agreement of both Parties.
[34] This Agreement constitutes the entire understanding between the Parties relating to the subject matter hereof unless any representation or warranty made about this Agreement was made fraudulently and, save as may be expressly referred to or referenced herein, supersedes all prior representations, writings, negotiations or understandings with respect hereto.
[35] 7. This Agreement shall be governed by the laws of the jurisdiction in which the Disclosing Party is located (or if the Disclosing Party is based in more than one country, the country in which its headquarters are located) (the "Territory") and the parties agree to submit disputes arising out of or in connection with this Agreement to the non-exclusive of the courts in the Territory.
[36] [Receiving Party]
[37] Signature
[38] ___________________________
[39] Name and Tile:_______________________
[40] Address:
[41] ____________________________

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information.

Q2 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement.

Q3 [TERM, about the base NDA] CONTRACT TERM: Agreement shall not grant Receiving Party any right to Confidential Information.

Q4 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that Agreement was agreed or negotiated.

Q5 [TERM, about the base NDA] CONTRACT TERM: Confidential Information shall only include technical information.

Q6 [TERM, about the base NDA] CONTRACT TERM: All Confidential Information shall be expressly identified by the Disclosing Party.

Q7 [TERM, about the base NDA] CONTRACT TERM: Some obligations of Agreement may survive termination of Agreement.

Q8 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may independently develop information similar to Confidential Information.

Q9 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may retain some Confidential Information even after the return or destruction of Confidential Information.

Q10 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q11 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not solicit some of Disclosing Party's representatives.

Q12 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some third-parties (including consultants, agents and professional advisors).

Q13 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may create a copy of some Confidential Information in some circumstances.

Q14 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall notify Disclosing Party in case Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.

Q15 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may acquire information similar to Confidential Information from a third party.

Q16 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some of Receiving Party's employees.

Q17 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in Agreement.
