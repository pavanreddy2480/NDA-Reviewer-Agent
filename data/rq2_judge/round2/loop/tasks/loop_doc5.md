# Judge task loop_doc5

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

[0] The confidentiality obligations under this Agreement shall survive termination of the Agreement for a minimum of 36 months.
[1] Some obligations of the Agreement may survive termination of the Agreement.
[2] The Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the Agreement.
[3] The confidentiality obligations under this Agreement shall last for a minimum of 60 months.
[4] Confidentiality Agreement
[5] This Confidentiality Agreement (the “Agreement”) has been prepared on behalf of bpost SA/NV, a limited liability company of public law, and the City of Brussels (the “Sellers”) with regard to the divestment of their respective surface areas (the “Sale”) in the Munt Center/Centre Monnaie (the “Munt”).
[6] The Agreement shall not grant the Receiving Party any right to Confidential Information.
[7] keep confidential all and any Confidential Information received at any time.
[8] prior to the disclosure to any other person (including any professional advisor) of any Confidential Information, such other person is made aware of the provisions of this Agreement and the fact that the Disclosee will be liable.
[9] ensures compliance with the relevant legal and other provisions in this respect (including, without being limited to, the provisions of the Belgian Law of 2 August 2002 on the supervision of the financial sector and on the financial services in relation to insider dealing and market manipulation).
[10] Confidential Information shall mean the following:
[11] The Receiving Party shall not reverse engineer any objects which embody the Disclosing Party's Confidential Information.
[12] The Receiving Party shall notify the Disclosing Party if it is required by law, regulation or judicial process to disclose any Confidential Information.
[13] a) all such information, of any kind whatsoever (whether in oral, written or electronic form, and including, but not limited to, technical, commercial, financial, accounting, legal and administrative information) pertaining to the Sale of the Munt and the Sellers as may be provided to the Disclosee and their responsible managers, officers, employees, shareholders, members of the Board of Directors and advisors (including financial, legal and tax advisors and auditors) (“Representatives”), by the Sellers, their advisors or their representatives;
[14] b) all such analyses, compilations, forecasts, notes, memoranda and other documents as the Sellers or Deloitte Real Estate* and Laga** (the “Advisors”) may have prepared or caused to be prepared and which may contain, refer to or simply result from, the information mentioned in point
[15] (a) above;
[16] c) the fact that the Disclosee (or any of their Representatives) are or have been involved in the analysis of, in meetings or negotiations related to the Sale, the contents, time and status of such negotiations, and generally any fact concerning the Sale.
[17] Confidential Information shall exclude:
[18] a) information which had become available to the public prior to the date of disclosure thereof to the Disclosee or their Representatives, or that became available to the public after such date other than as a result of a breach of this Agreement by the Disclosee or their Representatives;
[19] b) information which was lawfully in the Disclosee’s possession or in the possession of one or more of their Representatives prior to disclosure under this Agreement, in each case on a non-confidential basis, which, to their knowledge was free of any restriction as to its use or disclosure.
[20] The Disclosee acknowledges that they may not approach the representatives of the Sellers and cannot contact anybody else other than the contact persons from the Advisors.
[21] The Disclosee further undertakes and acknowledges, that neither the representatives of the Sellers nor their Advisors give any warranty or make any representation as to the accuracy or completeness of any of the Confidential Information or as to the reasonableness of any assumptions on which the information is based.
[22] The Receiving Party may acquire information similar to Confidential Information from a third party.
[23] The Receiving Party may acquire information similar to Confidential Information from a third party.
[24] The Receiving Party may share some Confidential Information with some third-parties, including consultants, agents and professional advisors.
[25] The Disclosee agrees that the Sellers or Advisors shall not have any liability to the Disclosee or to any of their directors, employees, advisors or agents resulting from the use of Confidential Information.
[26] This Agreement shall in no way constitute a commitment by any person to supply any Confidential Information or enter into any contract in connection with the Sellers.
[27] The obligations of the Disclosee under this Agreement shall expire the earlier of
[28] three years after the date of this Agreement, or
[29] (b) the date the Sale between the Candidate and the Sellers is completed.
[30] The obligations of confidentiality and non-disclosure under this Agreement shall become effective as of the date of signing.
[31] The Receiving Party shall not disclose the fact that the Agreement was agreed or negotiated.
[32] The Receiving Party shall not disclose the fact that the Agreement was agreed or negotiated.
[33] the Disclosee shall immediately notify the Sellers before disclosing such Confidential Information, so that the Sellers may seek a protective order or other appropriate remedy, without prejudice to the Disclosee’s remedies under this Agreement.
[34] It is further understood and agreed that, without prejudice to any other rights or remedies which either party may have, any breach of these undertakings could cause the Sellers and/or its shareholders irreparable injury.
[35] In the event of an actual or threatened breach by the Disclosee and/or its Representatives of any provisions of this Agreement, the Sellers shall be entitled
[36] seek injunctive relief in any court of competent jurisdiction restraining the Disclosee and/or its Representatives from breaching the terms hereof or from disclosing any Confidential Information to any person and
[37] The Receiving Party shall comply with applicable export control laws and shall not export or re-export technical data without authorization.
[38] (ii) specific performance and other equitable relief.
[39] This Agreement shall be governed by and construed in accordance with Belgian law and the Parties irrevocably agree to submit themselves to the exclusive jurisdiction of the Courts of Brussels.
[40] Belgian law
[41] Confidential Information shall only include technical information, including specifications, source code and designs, and shall not include business or financial information.
[42] In accordance with the procedure defined in the candidacy file, we would be grateful if you could confirm your understanding and acceptance of the foregoing by returning to us a signed copy of the present document
[43] Nothing in this Agreement shall restrict the Receiving Party from using, for any purpose, information retained in the unaided memory of its personnel who had access to Confidential Information.
[44] Yours sincerely,
[45] _______________
[46] _______________
[47] Frédéric Sohet Koen
[48] Van Gerven
[49] Partner CEO
[50] Deloitte Real Estate | Financial Advisory* bpost SA/NV
[51] The Candidate / Disclosee
[52] Name . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[53] Company . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[54] Title . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[55] Date . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[56] Signature
[57] *A department of Deloitte Consulting & Advisory CVBA
[58] Coöperatieve vennootschap met beperkte aansprakelijkheid/Société coopérative à responsabilité limitée
[59] Registered Office: Gateway building, Luchthaven Nationaal 1 J, 1930 Zaventem
[60] VAT BE 0474.429.572 - RPR Brussel/RPM Bruxelles - IBAN BE 38 4377 5059
[61] 9172 - BIC KREDBEBB
[62] Member of Deloitte Touche Tohmatsu Limited
[63] © 2018.
[64] **Laga is a civil limited liability cooperative company.
[65] Registered Office: Gateway building, Luchthaven Nationaal 1 J, 1930 Zaventem
[66] 0471.858.874 - Brussels Trade Register - ING 310-1381442-54
[67] The list of Laga partners can be obtained upon request or from the Laga website.

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the Agreement.

Q2 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall not reverse engineer any objects which embody the Disclosing Party's Confidential Information.

Q3 [TERM, about the base NDA] CONTRACT TERM: The Agreement shall not grant the Receiving Party any right to Confidential Information.

Q4 [TERM, about the base NDA] CONTRACT TERM: Some obligations of the Agreement may survive termination of the Agreement.

Q5 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may acquire information similar to Confidential Information from a third party.

Q6 [TERM, about the base NDA] CONTRACT TERM: The agreement imposes a fixed penalty or liquidated damages payable on breach of confidentiality.

Q7 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall comply with applicable export control laws and shall not export or re-export technical data without authorization.

Q8 [TERM, about the base NDA] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.
