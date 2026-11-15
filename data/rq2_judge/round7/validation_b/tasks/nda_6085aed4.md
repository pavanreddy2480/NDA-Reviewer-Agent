# Judge task nda_6085aed4

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

[0] Mutual Non-Disclosure
[1] Agreement
[2] 
[3] THIS MUTUAL NON DISCLOSURE AGREEMENT
[4] is made and entered into this ____day of _________, 20______ between Product Development Experts, Inc. with address at; 2440 SE Federal Hwy., Suite 101-P Stuart FL 34994 and
[5] _______________________________________________________________________
[6] (Inventor), with address at; __________________________________________________________________________________
[7] Purpose.
[8] The parties wish to explore a business opportunity of mutual interest and in connection with this opportunity, each party may disclose to the other party certain confidential technical and business information which the disclosing party desires the receiving party to treat as confidential.
[9] "Confidential Information" means any information disclosed by either party to the other party, either directly or indirectly, in writing, orally or by inspection of tangible objects, including without limitation documents, prototypes, samples, plant and equipment, research, product plans, products, services, customer lists, software, developments, inventions, processes, designs, drawings, engineering, hardware configuration, marketing materials or finances, which is designated as "Confidential," "Proprietary" or some similar designation.
[10] Information communicated orally shall be considered Confidential Information if such information is confirmed in writing as being Confidential Information within a reasonable time after the initial disclosure.
[11] Confidential Information may also include information disclosed to a disclosing party by third parties.
[12] Confidential Information shall not, however, include any information which
[13] (i) was publicly known and made generally available in the public domain prior to the time of disclosure by the disclosing party;
[14] (ii) becomes publicly known and made generally available after disclosure by the disclosing party to the receiving party through no action or inaction of the receiving party;
[15] (iii) is already in the possession of the receiving party at the time of disclosure by the disclosing party as shown by the receiving party's files and records immediately prior to the time of disclosure;
[16] (iv) is obtained by the receiving party from a third party without a breach of such third party's obligations of confidentiality;
[17] (v) is independently developed by the receiving party without use of or reference to the disclosing party's Confidential Information, as shown by documents and other competent evidence in the receiving party's possession; or
[18] (vi) is required by law to be disclosed by the receiving party, provided that the receiving party gives the disclosing party prompt written notice of such requirement prior to such disclosure and assistance in obtaining an order protecting the information from public disclosure.
[19] Non-use and Non-disclosure.
[20] Each party shall not use the Confidential Information of the other party for any purpose except to evaluate and engage in discussions concerning a potential business relationship between the parties.
[21] Neither party shall disclose any Confidential Information of the other party to third parties.
[22] If any party makes copies of the Confidential Information of the other party, such copies shall also constitute Confidential Information and any and all confidential markings on such documents shall be maintained.
[23] Neither party shall reverse engineer, disassemble or decompile any prototypes, software or other tangible objects which embody the other party's Confidential Information and which are provided to the party hereunder.
[24] Maintenance of Confidentiality.
[25] Each party shall take reasonable measures to protect the secrecy of and avoid disclosure and unauthorized use of the Confidential Information of the other party.
[26] Without limiting the foregoing, each party shall take at least those measures that it takes to protect its own most highly confidential information, and shall promptly notify the disclosing party of any misuse or misappropriation of Confidential Information of which it becomes aware.
[27] Each party shall disclose Confidential Information only to those officers, directors, employees and contractors who are required to have the information in order to evaluate or engage in discussions concerning the contemplated business relationship, and such party shall remain responsible for compliance with the terms of this Agreement by its officers, directors, employees and contractors.
[28] No Obligation.
[29] Nothing herein shall obligate either party to proceed with any transaction between them, and each party reserves the right, in its sole discretion, to terminate the discussions contemplated by this Agreement concerning the business opportunity.
[30] No Warranty.
[31] ALL CONFIDENTIAL INFORMATION IS PROVIDED "AS IS."
[32] NEITHER PARTY MAKES ANY WARRANTIES, EXPRESS, IMPLIED OR OTHERWISE, REGARDING ITS ACCURACY, COMPLETENESS OR PERFORMANCE.
[33] Paid For Work.
[34] All paid for information, work, designs, ideas will become the property of the payor (the person or company paying).
[35] Return of Materials.
[36] All documents and other tangible objects containing or representing Confidential Information which have been disclosed by either party to the other party, and all copies thereof which are in the possession of the other party, shall be and remain the property of the disclosing party and shall be promptly returned to the disclosing party upon the disclosing party's written request.
[37] No License.
[38] Nothing in this Agreement is intended to grant any rights to either party under any patent, mask work right or copyright of the other party, nor shall this Agreement grant any party any rights in or to the Confidential Information of the other party except as expressly set forth herein.
[39] Term.
[40] The obligations of each receiving party hereunder shall survive for a period of five years after the disclosure of the Confidential Information or until such time as all Confidential Information of the other party disclosed hereunder becomes publicly known and made generally available through no action or inaction of the receiving party, whichever is earlier.
[41] Parties agree to honor all patent protections.
[42] Remedies.
[43] Each party agrees that any violation or threatened violation of this Agreement may cause irreparable injury to the other party, entitling the other party to seek injunctive relief in addition to all legal remedies.
[44] Choice of Laws and Forum.
[45] The interpretation and enforcement of this Agreement shall be governed by the laws of the State of Florida, U.S.A., as it applies to a contract executed, delivered, and performed solely in such state.
[46] Both PARTIES agree that all disputes concerning the interpretation and enforcement of this Agreement shall be heard by a court of competent jurisdiction in the State of Florida, U.S.A.
[47] Furthermore, both PARTIES hereby consents to personal jurisdiction in the State of Florida, U.S.A., for any dispute arising out of a violation of this Agreement, or any attempt to recover losses incurred on such dispute.
[48] Miscellaneous.
[49] Neither party may assign its rights or obligations under this Agreement without the prior written consent of the other party.
[50] Any attempted assignment in violation of this Section 11 will be null and void.
[51] This Agreement shall be governed by the laws of the State of Florida, without reference to conflict of laws principles.
[52] This document contains the entire agreement between the parties with respect to the subject matter hereof, and neither party shall have any obligation, express or implied by law, with respect to trade secret or proprietary information of the other party except as set forth herein.
[53] The invalidity or unenforceability of any provision of this Agreement, or any of its terms or provisions, will not affect the validity of this Agreement as a whole, which will at all times remain in full force and effect.
[54] A failure to enforce any provision of this Agreement will not constitute a waiver thereof or of any other provision.
[55] This Agreement may not be amended, nor any obligation waived, except by a writing signed by both parties hereto.
[56] Any notices required to be given under this agreement shall be deemed given upon the earlier of receipt of five (5) days after mailing by certified mail, return receipt requested, or hand delivery by messenger or express service, to the addresses stated on the first page, or to such other address as the either party may specify to the other in writing form time to time.
[57] Product Development Experts, Inc.
[58] ____________________________________,
[59] Inventor
[60] By:
[61] ________________________,
[62] President Signe
[63] d:________________________________
[64] Signed:
[65] ______________________________
[66] Print
[67] Name:____________________________
[68] Date;
[69] ________________________________
[70] Title:__________________________________

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
