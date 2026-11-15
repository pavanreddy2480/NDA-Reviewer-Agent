# Judge task nda_bf0b4eca

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

[0] NON DISCLOSURE AGREEMENT (page 1 of 3)
[1] THIS AGREEMENT is made between the parties named at the end of this document.
[2] WHEREAS, both parties may provide certain confidential and proprietary information to each other in connection with the business purposes described in Exhibit A attached hereto ("the Business Purpose") and each desires that any such information provided shall be kept confidential by the other party; and
[3] WHEREAS, in consideration of the disclosure of such information each party is willing to keep the other party's information confidential in accordance with the terms and conditions set forth in this Agreement.
[4] NOW IT IS HEREBY AGREED AS FOLLOWS:
[5] 1. Confidentiality
[6] Each party may use the information received from the other party hereunder and may provide such information to its parent corporation or any other subsidiaries thereof and their respective employees as applicable for their use only in connection with the Business Purpose.
[7] Each party agrees that, for a period of 5 years from receipt of information from the other party hereunder, such party shall use the same means it uses to protect its own confidential and proprietary information to prevent the disclosure and to protect the confidentiality of both:
[8] i) written information received from the other party which is marked or identified as "confidential"; and
[9] ii) oral or visual information identified as confidential at the time of disclosure which is reduced to written form and provided to the other in such written form promptly after such oral or visual disclosure,
[10] hereinafter collectively referred to as "the Information".
[11] The foregoing shall not prevent either party from disclosing Information which is:
[12] i) already known by the recipient party prior to the disclosure thereof with no obligation of confidentiality; or
[13] ii) publicly known or becomes publicly known not due to any unauthorised act of the recipient party; or
[14] iii) rightfully received from a third party; or
[15] iv) independently developed by the recipient party without use of the other party's Information; or
[16] v) disclosed without similar restrictions by the party owning the Information to any third party; or
[17] vi) approved by the other party for disclosure; or
[18] vii) required to be disclosed pursuant to a governmental or legal requirement provided that the disclosing party gives to the other party written notice of such requirement prior to any such disclosure.
[19] viii) publicly known or becomes publicly known not due to any unauthorised act of the recipient party; or
[20] ix) rightfully received from a third party; or
[21] x) independently developed by the recipient party without use of the other party's Information; or
[22] xi) disclosed without similar restrictions by the party owning the Information to any third party; or
[23] xii) approved by the other party for disclosure; or
[24] xiii) required to be disclosed pursuant to a governmental or legal requirement provided that the disclosing party gives to the other party written notice of such requirement prior to any such disclosure.
[25] 2. Return of Information
[26] Upon completion of the Business Purpose and/or upon written request of the party providing the Information, the other party shall within 14 days return all copies of the Information to the providing party or certify in writing that all copies of the Information have been destroyed.
[27] Nothing in this clause shall affect the right of either party voluntarily to return the Information, or any part thereof, to the other party at any time.
[28] 3. No Warranty/Liability
[29] Neither party makes any warranty, express or implied, with respect to the Information.
[30] Neither party shall be liable to the other or to any other person hereunder for amounts representing loss of profits or loss of business or indirect, consequential or punitive damages of the other or of such other person in connection with the provision or use of the Information hereunder.
[31] 4. No Further Rights
[32] Nothing contained in this Agreement shall be construed as granting or conferring any rights by licence or otherwise in the Information except as provided herein.
[33] 5. Business Purpose
[34] The parties expressly agree that the provision of Information hereunder and any discussions held in connection with the Business Purpose shall not prevent either party from pursuing similar discussions with third parties provided that no breach of this Agreement is so occasioned or oblige that party to take, continue or forego any action relating to the Business Purpose.
[35] Any forecasts or similar material provided by either party to the other shall not constitute any commitments.
[36] 6. Injunctive Rights
[37] Each party acknowledges and agrees that the Information is the confidential and/or proprietary and/or trade secret information of the other and the unauthorised use or disclosure of the Information could cause irreparable harm and significant injury to the other party for which that other party would have no adequate remedy at law.
[38] Therefore, each party shall have the right, in addition to any other rights it may have at law or in equity, to seek and obtain immediate injunctive relief in respect of any breach or potential breach of this Agreement by the other.
[39] 7. Media Releases
[40] No media releases, public announcements or public disclosure by either party relating to this Agreement, its subject matter or the Information, including but not limited to promotional or marketing, shall be made without the prior written consent of the other party.
[41] 8. General
[42] 8.1 Notices
[43] Any notices required under this Agreement shall be in writing and posted by registered mail return receipt requested to the applicable address indicated in Exhibit A.
[44] 8.2 Entire Agreement
[45] This Agreement and any attachments hereto:
[46] i) are the complete and exclusive statement between the parties with respect to the protection of the confidentiality of the Information; and
[47] ii) supersede all related discussions and other communications between the parties; and
[48] iii) may only be modified in writing by authorised representatives of the parties.
[49] 8.3 Governing Law
[50] This Agreement shall be governed by and interpreted in accordance with the law of England and shall be subject to the exclusive jurisdiction of the courts of England.
[51] AS WITNESS WHEREOF the parties named below have caused this Agreement to be signed and delivered by its duly authorised representative on this date: …………………………………………………..
[52] For and on behalf of For and on behalf of
[53] iTagg Limited …………………………………………………………
[54] (herein known as “Party 1”) (herein known as “Party 2”)
[55] Address Address
[56] 3rd Floor
[57] 12 Gough Square
[58] London
[59] EC4A 3DW
[60] England
[61] Company number 4344060
[62] Company number..............................
[63] Signed Signed................................................
[64] Name Steve Procter Name..................................................
[65] Title Director Title....................................................
[66] EXHIBIT
[67] A
[68] 1. Business Purpose:
[69] All business related support services, as well as affiliate, reseller and introducer deals and all commercial and business opportunities.
[70] For the purpose of clarity, all information and discussions related to service and product prices, costs, commissions, fees and other monetary matters are also covered under this agreement and to be kept confidential.
[71] This includes any prices, costs, commissions, fees or other monetary information offered by one party to the other even if not accepted, as well as any prices, costs, commissions, fees or other monetary information that are accepted by both parties and drawn into a subsequent contract between the parties.
[72] 2. Addresses for Notices:
[73] a) Party 1: As above
[74] b) Party 2: As above (insert alternative address and contact name below if necessary)

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement.

Q2 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information.

Q3 [TERM, about the base NDA] CONTRACT TERM: Agreement shall not grant Receiving Party any right to Confidential Information.

Q4 [TERM, about the base NDA] CONTRACT TERM: All Confidential Information shall be expressly identified by the Disclosing Party.

Q5 [TERM, about the base NDA] CONTRACT TERM: Confidential Information shall only include technical information.

Q6 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may retain some Confidential Information even after the return or destruction of Confidential Information.

Q7 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that Agreement was agreed or negotiated.

Q8 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may independently develop information similar to Confidential Information.

Q9 [TERM, about the base NDA] CONTRACT TERM: Some obligations of Agreement may survive termination of Agreement.

Q10 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q11 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not solicit some of Disclosing Party's representatives.

Q12 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some third-parties (including consultants, agents and professional advisors).

Q13 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may create a copy of some Confidential Information in some circumstances.

Q14 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall notify Disclosing Party in case Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.

Q15 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may acquire information similar to Confidential Information from a third party.

Q16 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some of Receiving Party's employees.

Q17 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in Agreement.
