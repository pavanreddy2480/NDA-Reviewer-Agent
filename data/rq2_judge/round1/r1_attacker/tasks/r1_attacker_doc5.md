# Judge task r1_attacker_doc5

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

[0] Confidentiality Agreement
[1] This Confidentiality Agreement (the “Agreement”) has been prepared on behalf of bpost SA/NV, a limited liability company of public law, and the City of Brussels (the “Sellers”) with regard to the divestment of their respective surface areas (the “Sale”) in the Munt Center/Centre Monnaie (the “Munt”).
[2] The Disclosee will procure that prior to the disclosure to any other person (including any professional advisor) of any Confidential Information, such other person is made aware of the provisions of this Agreement and the fact that the Disclosee will be liable, and the Disclosee will obtain the prior written consent of the Sellers before disclosing any Confidential Information.
[3] The Disclosee acknowledges that the Confidential Information, in as far as it relates to bpost SA/NV, could be price sensitive information and ensures compliance with the relevant legal and other provisions in this respect, including, without being limited to, the provisions of the Belgian Law of 2 August 2002 on the supervision of the financial sector and on the financial services in relation to insider dealing and market manipulation, only in the event that the Confidential Information is actually price sensitive.
[4] Confidential Information shall mean the following:
[5] a) all such information, of any kind whatsoever (whether in oral, written or electronic form, and including, but not limited to, technical, commercial, financial, accounting, legal and administrative information) pertaining to the Sale of the Munt and the Sellers as may be provided to the Disclosee and their responsible managers, officers, employees, shareholders, members of the Board of Directors and advisors (including financial, legal and tax advisors and auditors) (“Representatives”), by the Sellers, their advisors or their representatives;
[6] b) all such analyses, compilations, forecasts, notes, memoranda and other documents as the Sellers or Deloitte Real Estate* and Laga** (the “Advisors”) may have prepared or caused to be prepared and which may contain, refer to or simply result from, the information mentioned in point
[7] (a) above;
[8] c) the fact that the Disclosee (or any of their Representatives) are or have been involved in the analysis of, in meetings or negotiations related to the Sale, the contents, time and status of such negotiations, and generally any fact concerning the Sale.
[9] Confidential Information shall exclude:
[10] a) information which had become available to the public prior to the date of disclosure thereof to the Disclosee or their Representatives, or that became available to the public after such date other than as a result of a breach of this Agreement by the Disclosee or their Representatives;
[11] b) information which was lawfully in the Disclosee’s possession or in the possession of one or more of their Representatives prior to disclosure under this Agreement, in each case on a non-confidential basis, which, to their knowledge was free of any restriction as to its use or disclosure.
[12] The Disclosee acknowledges that they may not approach the representatives of the Sellers and cannot contact anybody else other than the contact persons from the Advisors.
[13] The Disclosee further undertakes and acknowledges, that neither the representatives of the Sellers nor their Advisors give any warranty or make any representation as to the accuracy or completeness of any of the Confidential Information or as to the reasonableness of any assumptions on which the information is based.
[14] The Disclosee agrees that the Sellers or Advisors shall not have any liability to the Disclosee or to any of their directors, employees, advisors or agents resulting from the use of Confidential Information.
[15] This Agreement shall in no way constitute a commitment by any person to supply any Confidential Information or enter into any contract in connection with the Sellers.
[16] The obligations of the Disclosee under this Agreement shall expire the earlier of
[17] The obligations of the Disclosee under this Agreement shall expire the earlier of (a) sixty months after the date of this Agreement, or (b) the date the Sale between the Candidate and the Sellers is completed.
[18] (b) the date the Sale between the Candidate and the Sellers is completed.
[19] The obligations of confidentiality and non-disclosure under this Agreement shall become effective as of the date of signing.
[20] In the event of any breach of this Agreement, the breaching party shall pay the other party a sum of US$500,000 as a penalty, unless the parties agree otherwise in writing.
[21] In the event that the Disclosee or any of its Representatives becomes legally compelled to disclose any of the Confidential Information to a regulatory authority or to any other entity or third party, the Disclosee shall immediately notify the Sellers before disclosing such Confidential Information, and the Sellers may seek a protective order or other appropriate remedy, without prejudice to the Disclosee’s remedies under this Agreement.
[22] It is further understood and agreed that, without prejudice to any other rights or remedies which either party may have, any breach of these undertakings could cause the Sellers and/or its shareholders irreparable injury.
[23] In the event of an actual or threatened breach by the Disclosee and/or its Representatives of any provisions of this Agreement, the Sellers shall be entitled
[24] (ii) specific performance and other equitable relief.
[25] This Agreement shall be governed by and construed in accordance with the laws of the State of Ohio or the State of Delaware, unless the General Counsel approves another governing law.
[26] For the avoidance of doubt, Confidential Information shall be limited to technical information, including specifications, source code and designs, and shall not include business or financial information.
[27] In accordance with the procedure defined in the candidacy file, we would be grateful if you could confirm your understanding and acceptance of the foregoing by returning to us a signed copy of the present document
[28] Nothing in this Agreement shall restrict the Receiving Party from using, for any purpose, information retained in the unaided memory of its personnel who had access to Confidential Information.
[29] Yours sincerely,
[30] _______________
[31] _______________
[32] Frédéric Sohet Koen
[33] Van Gerven
[34] Partner CEO
[35] Deloitte Real Estate | Financial Advisory* bpost SA/NV
[36] The Candidate / Disclosee
[37] Name . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[38] Company . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[39] Title . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[40] Date . . . . . . . . . . . . . . . . . . . . . . . . . . . .
[41] Signature
[42] *A department of Deloitte Consulting & Advisory CVBA
[43] Coöperatieve vennootschap met beperkte aansprakelijkheid/Société coopérative à responsabilité limitée
[44] Registered Office: Gateway building, Luchthaven Nationaal 1 J, 1930 Zaventem
[45] VAT BE 0474.429.572 - RPR Brussel/RPM Bruxelles - IBAN BE 38 4377 5059
[46] 9172 - BIC KREDBEBB
[47] Member of Deloitte Touche Tohmatsu Limited
[48] © 2018.
[49] **Laga is a civil limited liability cooperative company.
[50] Registered Office: Gateway building, Luchthaven Nationaal 1 J, 1930 Zaventem
[51] 0471.858.874 - Brussels Trade Register - ING 310-1381442-54
[52] The list of Laga partners can be obtained upon request or from the Laga website.

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q2 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the Agreement.

Q3 [TERM, about the base NDA] CONTRACT TERM: Some obligations of the Agreement may survive termination of the Agreement.

Q4 [TERM, about the base NDA] CONTRACT TERM: The Agreement shall not grant the Receiving Party any right to Confidential Information.

Q5 [FIELD]
QUESTION: How long do the confidentiality obligations last, in months? Answer a number of months. If they last indefinitely or perpetually, answer 9999. If the NDA does not say, answer null. If the NDA is a template and leaves this value blank (for example '____ years' or '[number]'), answer "blank". If the NDA has this obligation but gives no number (for example 'promptly' or 'until the transaction closes'), answer "unspecified".

SEGMENTS:
[0] Confidentiality Agreement
[4] Confidential Information shall mean the following:
[9] Confidential Information shall exclude:
[16] The obligations of the Disclosee under this Agreement shall expire the earlier of
[17] The obligations of the Disclosee under this Agreement shall expire the earlier of (a) sixty months after the date of this Agreement, or (b) the date the Sale between the Candidate and the Sellers is completed.
[19] The obligations of confidentiality and non-disclosure under this Agreement shall become effective as of the date of signing.

Q6 [FIELD]
QUESTION: Within how many days must confidential information be returned or destroyed? Number of days, or null. If the NDA is a template and leaves this value blank (for example '____ years' or '[number]'), answer "blank". If the NDA has this obligation but gives no number (for example 'promptly' or 'until the transaction closes'), answer "unspecified".

SEGMENTS:
[2] The Disclosee will procure that prior to the disclosure to any other person (including any professional advisor) of any Confidential Information, such other person is made aware of the provisions of this Agreement and the fact that the Disclosee will be liable, and the Disclosee will obtain the prior written consent of the Sellers before disclosing any Confidential Information.
[4] Confidential Information shall mean the following:
[9] Confidential Information shall exclude:
[26] For the avoidance of doubt, Confidential Information shall be limited to technical information, including specifications, source code and designs, and shall not include business or financial information.
[28] Nothing in this Agreement shall restrict the Receiving Party from using, for any purpose, information retained in the unaided memory of its personnel who had access to Confidential Information.
[52] The list of Laga partners can be obtained upon request or from the Laga website.

Q7 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall notify the Disclosing Party if it is required by law, regulation or judicial process to disclose any Confidential Information.

Q8 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall not reverse engineer any objects which embody the Disclosing Party's Confidential Information.

Q9 [TERM, about the base NDA] CONTRACT TERM: Confidential Information shall only include technical information.

Q10 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall not disclose the fact that the Agreement was agreed or negotiated.

Q11 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may share some Confidential Information with some third-parties, including consultants, agents and professional advisors.

Q12 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may acquire information similar to Confidential Information from a third party.

Q13 [TERM, about the base NDA] CONTRACT TERM: The agreement imposes a fixed penalty or liquidated damages payable on breach of confidentiality.

Q14 [FIELD]
QUESTION: Which law governs the agreement? If it is a US state, answer the state in lower case (e.g. 'delaware', 'new york'); otherwise the country in lower case (e.g. 'england', 'singapore'); null if the NDA does not say. If the NDA is a template and leaves this value blank (for example '____ years' or '[number]'), answer "blank".

SEGMENTS:
[25] This Agreement shall be governed by and construed in accordance with the laws of the State of Ohio or the State of Delaware, unless the General Counsel approves another governing law.

Q15 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may create a copy of some Confidential Information in some circumstances.

Q16 [TERM, about the base NDA] CONTRACT TERM: All Confidential Information shall be expressly identified by the Disclosing Party.

Q17 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may share some Confidential Information with some of the Receiving Party's employees.

Q18 [TERM, about the base NDA] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q19 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall comply with applicable export control laws and shall not export or re-export technical data without authorization.
