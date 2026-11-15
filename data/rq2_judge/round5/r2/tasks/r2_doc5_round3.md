# Judge task r2_doc5_round3

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

[0] This Agreement shall be governed by and construed in accordance with the laws of the State of Ohio or the State of Delaware, unless the General Counsel approves another governing law, in which case the parties shall agree on the governing law in writing.
[1] Confidentiality Agreement
[2] This Confidentiality Agreement (the “Agreement”) has been prepared on behalf of bpost SA/NV, a limited liability company of public law, and the City of Brussels (the “Sellers”) with regard to the divestment of their respective surface areas (the “Sale”) in the Munt Center/Centre Monnaie (the “Munt”).
[3] In consideration of the Sellers agreeing to disclose confidential information (the “Confidential Information”) to the Candidate (“Disclosee”), the latter hereby undertakes to the Sellers that as Disclosee, they will keep confidential all and any Confidential Information received at any time.
[4] The Disclosee will procure that prior to the disclosure to any other person (including any professional advisor) of any Confidential Information, such other person is made aware of the provisions of this Agreement and the fact that the Disclosee will be liable.
[5] The Disclosee acknowledges that the Confidential Information, in as far as it relates to bpost SA/NV, could be price sensitive information and ensures compliance with the relevant legal and other provisions in this respect (including, without being limited to, the provisions of the Belgian Law of 2 August 2002 on the supervision of the financial sector and on the financial services in relation to insider dealing and market manipulation).
[6] Confidential Information shall mean the following:
[7] a) all such information, of any kind whatsoever (whether in oral, written or electronic form, and including, but not limited to, technical, commercial, financial, accounting, legal and administrative information) pertaining to the Sale of the Munt and the Sellers as may be provided to the Disclosee and their responsible managers, officers, employees, shareholders, members of the Board of Directors and advisors (including financial, legal and tax advisors and auditors) (“Representatives”), by the Sellers, their advisors or their representatives;
[8] b) all such analyses, compilations, forecasts, notes, memoranda and other documents as the Sellers or Deloitte Real Estate* and Laga** (the “Advisors”) may have prepared or caused to be prepared and which may contain, refer to or simply result from, the information mentioned in point
[9] (a) above;
[10] c) the fact that the Disclosee (or any of their Representatives) are or have been involved in the analysis of, in meetings or negotiations related to the Sale, the contents, time and status of such negotiations, and generally any fact concerning the Sale.
[11] Confidential Information shall exclude:
[12] a) information which had become available to the public prior to the date of disclosure thereof to the Disclosee or their Representatives, or that became available to the public after such date other than as a result of a breach of this Agreement by the Disclosee or their Representatives;
[13] b) information which was lawfully in the Disclosee’s possession or in the possession of one or more of their Representatives prior to disclosure under this Agreement, in each case on a non-confidential basis, which, to their knowledge was free of any restriction as to its use or disclosure.
[14] The Disclosee acknowledges that they may not approach the representatives of the Sellers and cannot contact anybody else other than the contact persons from the Advisors.
[15] The Disclosee further undertakes and acknowledges, that neither the representatives of the Sellers nor their Advisors give any warranty or make any representation as to the accuracy or completeness of any of the Confidential Information or as to the reasonableness of any assumptions on which the information is based.
[16] The Disclosee agrees that the Sellers or Advisors shall not have any liability to the Disclosee or to any of their directors, employees, advisors or agents resulting from the use of Confidential Information.
[17] This Agreement shall in no way constitute a commitment by any person to supply any Confidential Information or enter into any contract in connection with the Sellers.
[18] The obligations of the Disclosee under this Agreement shall expire the earlier of
[19] three years after the date of this Agreement, or the date the Sale between the Candidate and the Sellers is completed, or sixty months after the date of this Agreement
[20] (b) the date the Sale between the Candidate and the Sellers is completed.
[21] The obligations of confidentiality and non-disclosure under this Agreement shall become effective as of the date of signing.
[22] In the event of any breach of this Agreement, the breaching party shall pay the other party a sum of US$500,000 as a penalty, irrespective of the actual loss suffered.
[23] In the event that the Disclosee or any of its Representatives becomes legally compelled to disclose any of the Confidential Information to a regulatory authority or to any other entity or third party, the Disclosee shall immediately notify the Sellers before disclosing such Confidential Information, so that the Sellers may seek a protective order or other appropriate remedy, without prejudice to the Disclosee’s remedies under this Agreement.
[24] It is further understood and agreed that, without prejudice to any other rights or remedies which either party may have, any breach of these undertakings could cause the Sellers and/or its shareholders irreparable injury.
[25] In the event of an actual or threatened breach by the Disclosee and/or its Representatives of any provisions of this Agreement, the Sellers shall be entitled
[26] (i) to seek injunctive relief in any court of competent jurisdiction restraining the Disclosee and/or its Representatives from breaching the terms hereof or from disclosing any Confidential Information to any person and
[27] (ii) specific performance and other equitable relief.
[28] This Agreement shall be governed by and construed in accordance with the laws of the State of Ohio or the State of Delaware, unless the General Counsel approves another governing law, in which case the parties shall agree on the governing law in writing.
[29] For the avoidance of doubt, Confidential Information shall be limited to technical information, including specifications, source code and designs, and shall not include business or financial information.
[30] In accordance with the procedure defined in the candidacy file, we would be grateful if you could confirm your understanding and acceptance of the foregoing by returning to us a signed copy of the present document
[31] Nothing in this Agreement shall restrict the Receiving Party from using, for any purpose, information retained in the unaided memory of its personnel who had access to Confidential Information.
[32] Yours sincerely,
[33] _______________
[34] _______________
[35] Frédéric Sohet Koen
[36] Van Gerven
[37] Partner CEO
[38] Deloitte Real Estate | Financial Advisory* bpost SA/NV
[39] The Candidate / Disclosee
[40] Name . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[41] Company . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[42] Title . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[43] Date . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[44] Signature
[45] *A department of Deloitte Consulting & Advisory CVBA
[46] Coöperatieve vennootschap met beperkte aansprakelijkheid/Société coopérative à responsabilité limitée
[47] Registered Office: Gateway building, Luchthaven Nationaal 1 J, 1930 Zaventem
[48] VAT BE 0474.429.572 - RPR Brussel/RPM Bruxelles - IBAN BE 38 4377 5059
[49] 9172 - BIC KREDBEBB
[50] Member of Deloitte Touche Tohmatsu Limited
[51] © 2018.
[52] **Laga is a civil limited liability cooperative company.
[53] Registered Office: Gateway building, Luchthaven Nationaal 1 J, 1930 Zaventem
[54] 0471.858.874 - Brussels Trade Register - ING 310-1381442-54
[55] The list of Laga partners can be obtained upon request or from the Laga website.

## NDA V1: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- base segments [18]..[18] are replaced by:
    three years after the date of this Agreement, or the date the Sale between the Candidate and the Sellers is completed, or sixty months after the date of this Agreement

## NDA V2: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- base segments [20]..[20] are replaced by:
    the date the Sale between the Candidate and the Sellers is completed

## NDA V3: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- base segments [27]..[27] are replaced by:
    the State of Ohio or the State of Delaware, unless the General Counsel approves another governing law, in which case the parties shall agree on the governing law in writing

## NDA V4: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [-1] insert:
    Unless the General Counsel approves another governing law, the governing law shall be Ohio or Delaware.

## Questions

Q1 [TERM, about NDA V1] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q2 [TERM, about NDA V2] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q3 [TERM, about NDA V3] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q4 [TERM, about NDA V4] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.
