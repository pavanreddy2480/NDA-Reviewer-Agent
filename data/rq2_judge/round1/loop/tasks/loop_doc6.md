# Judge task loop_doc6

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

[0] The agreement shall not grant the Receiving Party any right to Confidential Information.
[1] Some obligations of the agreement may survive termination of the agreement.
[2] The Receiving Party acknowledges that the Confidential Information may be subject to the Freedom of Information and Protection of Privacy Act, Province of Nova Scotia, and such other laws of the Province of Nova Scotia and Canada which may apply from time to time.
[3] MUTUAL NON-DISCLOSURE/CONFIDENTIALITY AGREEMENT
[4] THIS AGREEMENT effective the day of , 2013.
[5] BETWEEN:
[6] HER MAJESTY THE QUEEN in right of the Province of Nova Scotia, as represented by the Minister of Finance
[7] OF THE FIRST PART
[8] -and-
[9] HALIFAX REGIONAL MUNICIPALITY, as represented by the Chief
[10] Administrative Officer
[11] OF THE SECOND PART
[12] AND WHEREAS each Party wishes to ensure that the other treats this information in the strictest confidence.
[13] NOW THEREFORE in consideration of the promises and mutual covenants contained herein, and other good and valuable consideration, the receipt of which is hereby acknowledged, the Parties agree as follows:
[14] For purposes of this Agreement confidential, proprietary and trade secret information of the Province’s SAP Service Provider or any other Province’s Service Provider, any parent company, subsidiary or affiliate of the Disclosing party shall be considered Confidential Information of the Disclosing Party for purposes of this Agreement.
[15] (a) in the public domain other than by a breach of this Agreement by the Receiving Party; or
[16] (b) rightfully received from a third party with no duty of confidentiality; or
[17] (e) generally made available to third parties by the Disclosing Party without restriction on disclosure.
[18] The Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the agreement.
[19] The Receiving Party may share some Confidential Information with some of its employees.
[20] The Receiving Party may share some Confidential Information with some of its employees.
[21] The Receiving Party shall protect Confidential Information with reasonable administrative, physical and technical safeguards.
[22] 4. The HRM acknowledges and agrees that the Province may disclose the Confidential Information received from the HRM to its external or internal auditors, as well as the Province’s SAP Service Provider or Province’s other service providers for the purpose of provision or extension of the SAP Services to HRM.
[23] 5. The Receiving Party will adhere to all Canadian export laws, rules and regulations, and will not export or re-export any technical data or products received from the Disclosing Party, nor will the receiving party export or re-export the associated products of such technical data, to any restricted country and/or to any company, individual or government entity listed in the Table of Denial Orders published from time to time by the Canadian Government (called denied persons).
[24] 6. This Agreement will be effective as of the date of this Agreement, but will apply to any Confidential Information disclosed to the Receiving Party from the Disclosing Party prior to such date and will continue in perpetuity.
[25] 7. Each Party agrees that the harm resulting from improper disclosure of Confidential Information may be irreparable; therefore, the Disclosing Party shall be entitled to seek injunctive and other equitable relief to prevent or restrain breaches of any of the provisions of this Agreement by the Receiving Party or any of its employees, agents, officials, representatives or consultants, or to enforce the terms and provisions hereof, by an action instituted in a court of competent jurisdiction, which remedy or remedies are in addition to and not in substitution for any other remedy to which the Disclosing Party may be entitled at law or in equity.
[26] The Receiving Party may develop, acquire or market products or services similar to those of the Disclosing Party, and nothing herein shall prevent it from doing so, whether or not such development uses ideas learned from the Disclosing Party.
[27] The information provided hereunder, including Confidential Information, is provided strictly "as is" and without representation and warranty of any kind as to its accuracy, completeness, freedom from error, value, merchantability, fitness for a particular purpose or non-infringement.
[28] 9. This Agreement will terminate on the date and time the Agreement between the Parties over the provision of SAP Services is terminated.
[29] The Receiving Party shall not disclose the fact that the agreement was agreed or negotiated.
[30] The Receiving Party shall destroy or return some Confidential Information upon the termination of the agreement.
[31] 10. The Parties acknowledge and understand that all documentation and information, including Confidential Information, provided to the Province of Nova Scotia or HRM, as the case may be, pursuant to this Agreement shall be kept confidential, subject to the provisions of the Freedom of Information and Protection of Privacy Act, Province of Nova Scotia, and such other laws of the Province of Nova Scotia and Canada which may apply from time to time.
[32] During the term of this Agreement and for twelve (12) months thereafter
[33] 11. This Agreement shall not be construed as creating a joint venture, partnership or other form of business association between the Parties, nor an obligation to buy or sell products using or incorporating the Confidential Information, nor to create an implied or express license from either Party to the other.
[34] 12. The failure of either Party to enforce any right resulting from breach of any provision of this Agreement by the other Party shall not be deemed a waiver of any right relating to a subsequent breach of such provision or of any other right hereunder.
[35] This Agreement shall be governed by, and construed in accordance with the laws of the Province of Nova Scotia and the laws of Canada applicable therein.
[36] The NDA must be governed by California or Delaware law unless the General Counsel approves otherwise.
[37] 14. This Agreement constitutes the entire agreement, written or verbal, between the parties with respect to the terms set forth herein.
[38] This Agreement may not be amended except in writing signed by a duly authorized representative of the respective parties.
[39] 15. Time shall be of the essence in this Agreement.
[40] IN WITNESS WHEREOF the parties hereto have caused this Agreement to be executed by its duly authorized officers as of the day and year first above written.
[41] SIGNED, SEALED AND DELIVERED in the presence of:
[42] ________________________________
[43] Witness
[44] ________________________________
[45] Witness
[46] HER MAJESTY THE QUEEN in right of the Province of Nova Scotia as represented by the Minister of Finance
[47] Per:
[48] ____________________________________
[49] HALIFAX REGIONAL MUNICIPALITY as represented by the Chief Administrative Officer
[50] Per:
[51] ____________________________________

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q2 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall notify the Disclosing Party if it is required by law, regulation or judicial process to disclose any Confidential Information.

Q3 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the agreement.

Q4 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall destroy or return some Confidential Information upon the termination of the agreement.

Q5 [FIELD]
QUESTION: How long do the confidentiality obligations last, in months? Answer a number of months. If they last indefinitely or perpetually, answer 9999. If the NDA does not say, answer null. If the NDA is a template and leaves this value blank (for example '____ years' or '[number]'), answer "blank". If the NDA has this obligation but gives no number (for example 'promptly' or 'until the transaction closes'), answer "unspecified".

SEGMENTS:
[1] Some obligations of the agreement may survive termination of the agreement.
[3] MUTUAL NON-DISCLOSURE/CONFIDENTIALITY AGREEMENT
[32] During the term of this Agreement and for twelve (12) months thereafter
[33] 11. This Agreement shall not be construed as creating a joint venture, partnership or other form of business association between the Parties, nor an obligation to buy or sell products using or incorporating the Confidential Information, nor to create an implied or express license from either Party to the other.
[37] 14. This Agreement constitutes the entire agreement, written or verbal, between the parties with respect to the terms set forth herein.
[40] IN WITNESS WHEREOF the parties hereto have caused this Agreement to be executed by its duly authorized officers as of the day and year first above written.

Q6 [FIELD]
QUESTION: Within how many days must confidential information be returned or destroyed? Number of days, or null. If the NDA is a template and leaves this value blank (for example '____ years' or '[number]'), answer "blank". If the NDA has this obligation but gives no number (for example 'promptly' or 'until the transaction closes'), answer "unspecified".

SEGMENTS:
[0] The agreement shall not grant the Receiving Party any right to Confidential Information.
[1] Some obligations of the agreement may survive termination of the agreement.
[19] The Receiving Party may share some Confidential Information with some of its employees.
[20] The Receiving Party may share some Confidential Information with some of its employees.
[21] The Receiving Party shall protect Confidential Information with reasonable administrative, physical and technical safeguards.
[30] The Receiving Party shall destroy or return some Confidential Information upon the termination of the agreement.

Q7 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall protect Confidential Information with reasonable administrative, physical and technical safeguards.

Q8 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall promptly notify the Disclosing Party of any unauthorized use or disclosure of Confidential Information.

Q9 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may share some Confidential Information with some of its employees.

Q10 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may share some Confidential Information with some third parties, including consultants, agents and professional advisors.

Q11 [TERM, about the base NDA] CONTRACT TERM: Some obligations of the agreement may survive termination of the agreement.

Q12 [FIELD]
QUESTION: For how many months do obligations survive termination? Number of months, or null. If the NDA is a template and leaves this value blank (for example '____ years' or '[number]'), answer "blank". If the NDA has this obligation but gives no number (for example 'promptly' or 'until the transaction closes'), answer "unspecified".

SEGMENTS:
[1] Some obligations of the agreement may survive termination of the agreement.
[30] The Receiving Party shall destroy or return some Confidential Information upon the termination of the agreement.
[40] IN WITNESS WHEREOF the parties hereto have caused this Agreement to be executed by its duly authorized officers as of the day and year first above written.

Q13 [FIELD]
QUESTION: Which law governs the agreement? If it is a US state, answer the state in lower case (e.g. 'delaware', 'new york'); otherwise the country in lower case (e.g. 'england', 'singapore'); null if the NDA does not say. If the NDA is a template and leaves this value blank (for example '____ years' or '[number]'), answer "blank".

SEGMENTS:
[2] The Receiving Party acknowledges that the Confidential Information may be subject to the Freedom of Information and Protection of Privacy Act, Province of Nova Scotia, and such other laws of the Province of Nova Scotia and Canada which may apply from time to time.
[23] 5. The Receiving Party will adhere to all Canadian export laws, rules and regulations, and will not export or re-export any technical data or products received from the Disclosing Party, nor will the receiving party export or re-export the associated products of such technical data, to any restricted country and/or to any company, individual or government entity listed in the Table of Denial Orders published from time to time by the Canadian Government (called denied persons).
[31] 10. The Parties acknowledge and understand that all documentation and information, including Confidential Information, provided to the Province of Nova Scotia or HRM, as the case may be, pursuant to this Agreement shall be kept confidential, subject to the provisions of the Freedom of Information and Protection of Privacy Act, Province of Nova Scotia, and such other laws of the Province of Nova Scotia and Canada which may apply from time to time.
[33] 11. This Agreement shall not be construed as creating a joint venture, partnership or other form of business association between the Parties, nor an obligation to buy or sell products using or incorporating the Confidential Information, nor to create an implied or express license from either Party to the other.
[35] This Agreement shall be governed by, and construed in accordance with the laws of the Province of Nova Scotia and the laws of Canada applicable therein.
[36] The NDA must be governed by California or Delaware law unless the General Counsel approves otherwise.

Q14 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall pay liquidated damages or a contractual penalty for breach of the agreement.

Q15 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may independently develop information similar to Confidential Information.

Q16 [TERM, about the base NDA] CONTRACT TERM: The agreement shall not grant the Receiving Party any right to Confidential Information.

Q17 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party shall not disclose the fact that the agreement was agreed or negotiated.

Q18 [TERM, about the base NDA] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.
