# Judge task loop_doc6_round2

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

[0] The Receiving Party acknowledges that the Confidential Information may be subject to the Freedom of Information and Protection of Privacy Act, Province of Nova Scotia, and such other laws of the Province of Nova Scotia and Canada which may apply from time to time.
[1] MUTUAL NON-DISCLOSURE/CONFIDENTIALITY AGREEMENT
[2] THIS AGREEMENT effective the day of , 2013.
[3] BETWEEN:
[4] HER MAJESTY THE QUEEN in right of the Province of Nova Scotia, as represented by the Minister of Finance
[5] OF THE FIRST PART
[6] -and-
[7] HALIFAX REGIONAL MUNICIPALITY, as represented by the Chief
[8] Administrative Officer
[9] OF THE SECOND PART
[10] WHEREAS the Province of Nova Scotia (the “Province”) and Halifax Regional Municipality (the “HRM”) hereinafter referred to as the “Receiving or Disclosing Party” or “Parties”, may be facilitating the potential transaction of business related to the provision of SAP Services by the Province to the HRM where each Party may disclose certain confidential information to each other.
[11] AND WHEREAS each Party wishes to ensure that the other treats this information in the strictest confidence.
[12] NOW THEREFORE in consideration of the promises and mutual covenants contained herein, and other good and valuable consideration, the receipt of which is hereby acknowledged, the Parties agree as follows:
[13] 1. The confidential, proprietary and trade secret information of the Disclosing Party (hereinafter "Confidential Information") provided hereunder is any and all information, in whatever form (including electronic data) that will be disclosed to facilitate the potential transaction of business (related to the provision of SAP Services to HRM) between the Parties, including, but not limited to, portions or parts of the November 1, 2012 Agreement (including any schedules or appendices) between the Province of Nova Scotia and IBM, each Party's disclosure of intellectual property, techniques, sketches, drawings, models, inventions, know-how, processes, apparatus, equipment, algorithms, software programs, software source documents, and formulae related to the current, future and proposed products, documents and services, research, experimental work, development, design details and specifications, engineering, financial information, procurement requirements, purchasing, manufacturing, licensing, sales or service customer lists, business forecasts, sales and merchandizing, and marketing plans and information.
[14] For purposes of this Agreement confidential, proprietary and trade secret information of the Province’s SAP Service Provider or any other Province’s Service Provider, any parent company, subsidiary or affiliate of the Disclosing party shall be considered Confidential Information of the Disclosing Party for purposes of this Agreement.
[15] (a) in the public domain other than by a breach of this Agreement by the Receiving Party; or
[16] (b) rightfully received from a third party with no duty of confidentiality; or
[17] (c) rightfully known to the Receiving Party without any limitation on use or disclosure prior to its receipt from the Disclosing Party; or
[18] (e) generally made available to third parties by the Disclosing Party without restriction on disclosure.
[19] 3. The Receiving Party agrees that Confidential Information shall be used only for the purposes of facilitating the business relationship between the Parties.
[20] Additionally, subject to section 4 below, the Receiving Party shall not disclose Confidential Information to any third party without the prior written approval of the Disclosing Party.
[21] The Receiving Party shall not make any copies of Confidential Information except as necessary to perform hereunder.
[22] Each Party shall be responsible for any breach of this Agreement by such Party, its employees, agents, officials, representatives or consultants acting within the scope of their engagement or employment.
[23] 4. The HRM acknowledges and agrees that the Province may disclose the Confidential Information received from the HRM to its external or internal auditors, as well as the Province’s SAP Service Provider or Province’s other service providers for the purpose of provision or extension of the SAP Services to HRM.
[24] 5. The Receiving Party will adhere to all Canadian export laws, rules and regulations, and will not export or re-export any technical data or products received from the Disclosing Party, nor will the receiving party export or re-export the associated products of such technical data, to any restricted country and/or to any company, individual or government entity listed in the Table of Denial Orders published from time to time by the Canadian Government (called denied persons).
[25] 6. This Agreement will be effective as of the date of this Agreement, but will apply to any Confidential Information disclosed to the Receiving Party from the Disclosing Party prior to such date and will continue in perpetuity.
[26] 7. Each Party agrees that the harm resulting from improper disclosure of Confidential Information may be irreparable; therefore, the Disclosing Party shall be entitled to seek injunctive and other equitable relief to prevent or restrain breaches of any of the provisions of this Agreement by the Receiving Party or any of its employees, agents, officials, representatives or consultants, or to enforce the terms and provisions hereof, by an action instituted in a court of competent jurisdiction, which remedy or remedies are in addition to and not in substitution for any other remedy to which the Disclosing Party may be entitled at law or in equity.
[27] The Receiving Party may develop, acquire or market products or services similar to those of the Disclosing Party, and nothing herein shall prevent it from doing so, whether or not such development uses ideas learned from the Disclosing Party.
[28] The information provided hereunder, including Confidential Information, is provided strictly "as is" and without representation and warranty of any kind as to its accuracy, completeness, freedom from error, value, merchantability, fitness for a particular purpose or non-infringement.
[29] In the event of any breach of this Agreement, the breaching party shall pay the other party a sum of US$500,000 as a penalty, irrespective of the actual loss suffered.
[30] 9. This Agreement will terminate on the date and time the Agreement between the Parties over the provision of SAP Services is terminated.
[31] The obligations of the Receiving Party under this Agreement shall survive the termination of this Agreement or the return of the Confidential Information to the Disclosing Party.
[32] 10. The Parties acknowledge and understand that all documentation and information, including Confidential Information, provided to the Province of Nova Scotia or HRM, as the case may be, pursuant to this Agreement shall be kept confidential, subject to the provisions of the Freedom of Information and Protection of Privacy Act, Province of Nova Scotia, and such other laws of the Province of Nova Scotia and Canada which may apply from time to time.
[33] During the term of this Agreement and for twelve (12) months thereafter, neither party shall, directly or indirectly, solicit for employment or hire any employee of the other party with whom it had contact in connection with the Purpose.
[34] 11. This Agreement shall not be construed as creating a joint venture, partnership or other form of business association between the Parties, nor an obligation to buy or sell products using or incorporating the Confidential Information, nor to create an implied or express license from either Party to the other.
[35] 12. The failure of either Party to enforce any right resulting from breach of any provision of this Agreement by the other Party shall not be deemed a waiver of any right relating to a subsequent breach of such provision or of any other right hereunder.
[36] This Agreement shall be governed by, and construed in accordance with the laws of the Province of Nova Scotia and the laws of Canada applicable therein.
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

## NDA V1: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [31] insert:
    The Receiving Party shall destroy or return some Confidential Information upon the termination of the agreement.

## NDA V2: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- segments [31]..[31] of the base are deleted

## NDA V3: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- base segments [19]..[19] are replaced by:
    The Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the agreement.

## NDA V4: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [20] insert:
    The Receiving Party may share some Confidential Information with some of its employees.

## NDA V5: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [22] insert:
    The Receiving Party shall protect Confidential Information with reasonable administrative, physical and technical safeguards.

## NDA V6: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- base segments [20]..[20] are replaced by:
    The Receiving Party may share some Confidential Information with some of its employees.

## NDA V7: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- after base segment [30] insert:
    The Receiving Party shall not disclose the fact that the agreement was agreed or negotiated.

## NDA V8: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- segments [10]..[10] of the base are deleted

## NDA V9: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- segments [29]..[29] of the base are deleted

## NDA V10: the base NDA with these changes (renumber nothing: cite base numbers, or describe inserted text as 'new')

- segments [22]..[22] of the base are deleted

## Questions

Q1 [TERM, about NDA V1] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q2 [TERM, about NDA V2] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q3 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q4 [TERM, about NDA V3] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q5 [TERM, about NDA V4] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q6 [TERM, about NDA V5] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q7 [TERM, about NDA V6] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q8 [TERM, about NDA V7] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q9 [TERM, about NDA V8] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q10 [TERM, about NDA V9] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q11 [TERM, about NDA V10] CONTRACT TERM: Confidential Information may include verbally conveyed information.
