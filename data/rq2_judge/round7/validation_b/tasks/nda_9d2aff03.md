# Judge task nda_9d2aff03

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

[0] Exhibit
[1] (d)(2)
[2] MUTUAL NON-DISCLOSURE AGREEMENT
[3] This Agreement is entered into on September 28, 2006 (the “Effective Date”) between SafeNet, Inc. (“SafeNet”), a Delaware corporation with its principal place of business at 4690 Millennium Drive, Belcamp, MD) 21017 and Vector Capital Corporation (“Vector”), a Delaware corporation with its principal place of business at 456 Montgomery Street, 19th Floor, San Francisco, CA 94104 (collectively the “Parties”),
[4] The Parties both expect to disclose information (in such capacity, a “Disclosing Party”) and receive information (in such capacity, a “Receiving Party”),
[5] 
[6] WHEREAS, the Parties desire to engage in discussions concerning a potential corporate transaction (the “Transaction”); and
[7] 
[8] WHEREAS, the Parties may disclose certain information to each other on a confidential basis to further their discussions concerning such Transaction;
[9] 
[10] NOW THEREFORE, in consideration of the disclosure of such confidential information by either Party, the Parties agree as follows:
[11] 1. For purposes of this Agreement, “Information” is defined as confidential or proprietary communications or data of a Party hereto, including business information, financial information, marketing plans.
[12] technical or financial information, customer lists or proposals, sketches, models, samples, computer programs and documentation, drawings, specifications, whether conveyed in oral, written, graphic, or electromagnetic form or otherwise, and all notes, analyses, compilations, forecasts, studies, interpretations or other documents prepared by either Party to the extent that they contain any such information.
[13] In addition, the existence of this Agreement and information and discussions regarding the Transaction shall be considered Information hereunder.
[14] The definition of Information shall not include information that:
[15] 
[16] (a) is in or enters the public domain, through no fault of the Receiving Party; or
[17] 
[18] (b) is or has been disclosed by the Disclosing Party to the Receiving Party or to a third Party without restriction; or
[19] 
[20] (c) is already in the possession of the Receiving Party, without restriction and prior to disclosure of the information hereunder; or
[21] 
[22] (d) is or has been lawfully disclosed by a third Party to the Receiving Party without an obligation of confidentiality; or
[23] 
[24] (e) is developed by the Receiving Party independently of Information disclosed by the Disclosing Party and without breach of this Agreement.
[25] 2. The Receiving Party agrees that;
[26] 
[27] (a) it will use Information disclosed by the Disclosing Party solely for the purpose of discussing and evaluating the Transaction, and for no other purpose;
[28] 
[29] (b) it will not distribute, disclose or disseminate Information to any third Party without the prior consent of the Disclosing Party, and will only distribute, disclose or disseminate Information to its directors, officers, employees consultants, advisors, potential sources of financing or other representatives with a need to know such information for purposes of discussing and evaluating the Transaction and who are informed by such Receiving Party of the confidential nature of the Information;
[30] 
[31] (c) it will protect the Information of the Disclosing Part), against unauthorized disclosure and warrants that will use the same means to protect Information that it uses to protect its own confidential information, in any event no less than reasonable means.
[32] 3. Information of the Disclosing Party shall remain the property of the Disclosing Party.
[33] No license or right is granted by the Disclosing Party to the Receiving Party under any patent, patent application, trademark, copyright, software or trade secret.
[34] 4. Vector agrees that, for a period of three (3) months from the termination or expiration of this Agreement, unless such shall have been specifically invited in writing by SafeNet, neither Vector nor any of the investment funds it manages will in any manner, directly or indirectly:
[35] 
[36] (a) effect to seek, offer or propose (whether publicly or otherwise) to effect, or cause or participate in or in any way assist any other person to effect or seek, offer or propose (whether publicly or otherwise) to effect or participate in,
[37] (i) any acquisition of any securities (or beneficial ownership thereof) or assets of SafeNet;
[38] (ii) any tender or exchange offer, merger or other business combination involving SafeNet;
[39] (iii) any recapitalization, restructuring, liquidation, dissolution or other extraordinary transaction with respect to SafeNet; or
[40] (iv) any “solicitation” or “proxies” (as such terms are used in the proxy rules of the Securities and Exchange Commission) or consents to vote any voting securities of SafeNet;
[41] 
[42] (b) form, join or in any way participate in a “group” (as defined under the Securities Exchange Act) relating to SafeNet or its securities;
[43] 
[44] (c) otherwise act, alone or in concert.
[45] with others, to seek to control or influence the management, Board of Directors or policies of SafeNet;
[46] 
[47] (d) take any action which might force SafeNet to make a public announcement regarding any of the types of matters set forth in
[48] (a) above; or
[49] 
[50] (e) enter into any discussions or arrangements with any third party with respect to any of the foregoing.
[51] You also agree during such period not to request SafeNet (or its directors, officers, employees or agents), directly or indirectly, to amend or waive any provision of this Section (including this sentence).
[52] Notwithstanding the foregoing, nothing herein shall limit Vector’s ability to acquire up to l% of the SafeNet’s equity securities, subject only to full compliance with all applicable securities laws and regulations.
[53] 5. The Disclosing Party warrants that it has the right to possession and disclosure of the Information according to the terms of this Agreement.
[54] Each Party understands and acknowledges that neither Party has made any representation or warranty, express or implied, as to the accuracy or completeness of the Information and that neither Party shall have any liability to the other or any other person resulting from reliance on the Information.
[55] Only those representations or warranties that are made in a definitive agreement, and subject to such limitations and restrictions as may be specified therein, will have any legal effect.
[56] 6. Vector understands that SafeNet is a publicly-held company and that all or part of SafeNet’s information may constitute material non-public information under the United States securities laws, and each Party acknowledges that it is aware that the United States securities laws prohibit any person who is in the possession of material non-public information about a company from purchasing or selling that company’s securities in reliance upon such information or from communicating such information to any other person or entity under circumstances in which it is reasonably foreseeable that such person or entity is likely to purchase or sell such securities in reliance upon such information.
[57] Each Party represents that, as of the date of this agreement, neither Party nor its controlled affiliates, nor anyone acting on its or their behalf in connection with the Transaction, has acquired record or beneficial ownership of any voting securities of the other Party or of any securities convertible or exchangeable into or exercisable for voting securities of the other Party, and each Party agrees that neither it, nor any of its directors, officers or employees who have been provided with the Information will perform any purchase, sale or other transfer of any of the securities of the other Party in violation of United States securities laws.
[58] 7. In the event that a Receiving Party is requested pursuant to, or required by, applicable law, regulation or legal process to disclose any of the Disclosing Party’s Information, the Receiving Party will notify the Disclosing Party promptly before such Information is disclosed so that the Disclosing Party may seek a protective order or other appropriate remedy or, in the sole reasonable discretion of the Disclosing Party, waive compliance with the terms of this Agreement.
[59] In the event that no such protective order or other remedy is obtained, or that such Disclosing Party waives compliance with the terms of this Agreement, the Receiving Party will furnish only that portion of such Information which it is advised in writing by outside counsel is legally required and will exercise its best efforts to obtain reliable assurance that confidential treatment will be accorded such Information.
[60] Disclosure of information in accordance with this Section shall not be considered a breach of this Agreement.
[61] 8. The Receiving Party shall have, or shall enter into, agreements with its parent, divisions and subsidiary companies as necessary to safeguard the Information disclosed hereunder consistent with the terms of this Agreement.
[62] With respect to its directors, officers and employees, the Receiving Party warrants that it has executed confidentiality agreements with all such directors, officers and employees who will have access to Information, and shall ensure that such directors, officers and employees protect Information according to the terms of this Agreement.
[63] 9. Each Party acknowledges that remedies at law may be inadequate to protect it against any actual or threatened breach of this Agreement by the other Party, and, without prejudice to any other rights and remedies otherwise available to each Party, each Party agrees to any grant of injunctive relief in favor of the other Party without proof of actual damages.
[64] In the event of litigation relating to this Agreement, if a court of competent jurisdiction determines that this Agreement has been breached by a Party, then the breaching Party will reimburse the non-breaching Party for its costs and expenses (including, without limitation, legal fees and expenses) incurred in connection with all such litigation.
[65] 10. Either Party may terminate this Agreement at will by written notice to the other Party and, if not terminated earlier, shall terminate automatically one (1) year from the Effective Date, except the obligations of use and confidentiality pursuant to Sections 2 shall continue for a period of two (2) years from the Effective Date,
[66] 11. Neither this Agreement nor the disclosure or receipt of Information shall constitute or imply a commitment by either Party with respect to the Transaction, present or future business agreements, or any other subject matter not expressly set forth herein,
[67] 12. At the Disclosing Party’s request, all Information of the Disclosing Party in tangible form, or any copies thereof, that is in the possession of the Receiving Party shall be returned to the Disclosing Party or destroyed,
[68] 13. Nothing in this Agreement shall grant to either Party the right to make commitments of any kind for or on behalf of the other Party.
[69] Each Party to this Agreement is an independent organization and no agency relationship, joint venture or partnership shall be created hereby.
[70] 14. Any amendment to this Agreement must be in writing and signed by authorized officials of each Party.
[71] No failure or delay in exercising any right under this Agreement shall operate as a waiver thereof.
[72] 15. This Agreement shall be governed by the laws of the State of Maryland.
[73] Each Party agrees that any proceeding relating to this Agreement shall be brought in a state court of Maryland or a court of the United States of America located in the State of Maryland.
[74] Each Party hereby consents to personal jurisdiction in any such action, consent to service of process by mail and waive any objection to venue in any such court or to any claim that such court is an inconvenient forum.
[75] 16. This Agreement contains the entire agreement between the parties concerning the confidentiality of the Information and shall be binding upon its respective affiliates, successors and assigns.
[76] No modification of this Agreement or waiver of the terms and conditions hereof will be binding upon the parties, unless approved in writing by each Party.
[77] Agreed by:
[78] SAFENET, INC.
[79] VECTOR CAPITAL CORPORATION
[80] By: /s/ Kevin Hicks
[81] By: /s/ David Fishman
[82] 
[83] Name: Kevin Hicks Name: David Fishman
[84] 
[85] Title: General Counsel and Vice President Title: Principal and Authorized Signatory

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information.

Q2 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement.

Q3 [TERM, about the base NDA] CONTRACT TERM: Agreement shall not grant Receiving Party any right to Confidential Information.

Q4 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that Agreement was agreed or negotiated.

Q5 [TERM, about the base NDA] CONTRACT TERM: Confidential Information shall only include technical information.

Q6 [TERM, about the base NDA] CONTRACT TERM: All Confidential Information shall be expressly identified by the Disclosing Party.

Q7 [TERM, about the base NDA] CONTRACT TERM: Some obligations of Agreement may survive termination of Agreement.

Q8 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q9 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may retain some Confidential Information even after the return or destruction of Confidential Information.

Q10 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may independently develop information similar to Confidential Information.

Q11 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not solicit some of Disclosing Party's representatives.

Q12 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some third-parties (including consultants, agents and professional advisors).

Q13 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may create a copy of some Confidential Information in some circumstances.

Q14 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall notify Disclosing Party in case Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.

Q15 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may acquire information similar to Confidential Information from a third party.

Q16 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some of Receiving Party's employees.

Q17 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in Agreement.
