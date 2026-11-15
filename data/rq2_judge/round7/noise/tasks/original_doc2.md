# Judge task original_doc2

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

[0] MUTUAL NON-DISCLOSURE AGREEMENT
[1] Between
[2] AND
[3] Subject Matter:
[4] Effective Date of Agreement: Period , 2017
[5] for Exchange of Information: , 2017 to
[6] Period of Confidentiality:
[7] THIS AGREEMENT is made as of the Effective Date of Agreement noted above, by and between the above parties.
[8] BACKGROUND:
[9] I. The parties desire to have discussions of or relating to the Subject Matter for the purposes of evaluating a possible business relationship between them (“Purpose”).
[10] The parties may extend the Subject Matter or add additional parties by executing one or more addenda to this Agreement.
[11] II. Such discussions may involve disclosure by one party to the other party of confidential, proprietary or trade secret information of its own or its licensors (“Confidential Information” as defined below), during the Period for Exchange of Information.
[12] III. Both parties recognize the value of the Confidential Information and that it is in their mutual best interests to maintain the confidential, proprietary and secret nature of the Confidential Information.
[13] THEREFORE, in consideration of the Subject Matter, and the mutual promises herein, the parties agree as follows:
[14] 1. CONFIDENTIAL INFORMATION.
[15] (i) marked confidential or proprietary, or
[16] (ii) given the nature of the information or the circumstances surrounding its disclosure, reasonably should be deemed confidential.
[17] Confidential Information includes, but is not limited to documents, drawings, models, apparatus, sketches, designs, schedules, product plans, marketing plans, technical procedures, manufacturing processes, software, prototypes, samples, methodologies, formulations, trade secrets, patent applications, know-how, experimental results, specifications and other business information.
[18] 2. PERIOD OF CONFIDENTIALITY AND NON-USE.
[19] The Recipient will use Confidential Information only in connection with the Purpose as set forth in this Agreement.
[20] Recipient shall use the same degree of care to avoid disclosure or use of the Confidential Information as it uses for its own confidential, proprietary and trade secret information, but in no case use less than a reasonable degree of care.
[21] Recipient will not disclose or permit access to Confidential Information to contract workers, consultants or contractors of Recipient or its Affiliates unless authorized by Disclosing Party in writing and on condition that such persons are bound by obligations of confidentiality inuring to the benefit of Disclosing Party and its Affiliates at least as restrictive as these terms and conditions.
[22] Recipient shall not without Disclosing Party’s prior written consent reverse engineer, disassemble or decompile any prototypes, software or other objects which embody the Disclosing Party’s Confidential Information to obtain access to Disclosing Party’s trade secrets and to the extent such consent is granted Recipient shall receive and hold such Confidential Information subject to the terms of this Agreement.
[23] 3. TERM.
[24] The term of this Agreement shall be for the Period of Exchange set forth above.
[25] Either party may terminate this Agreement upon 30 days prior written notice.
[26] 4. NOTICE OF UNAUTHORIZED USE.
[27] Recipient shall provide written notice to Disclosing Party without undue delay of any misuse or misappropriation of Confidential Information which may come to the attention of Recipient.
[28] The Recipient shall cooperate with and aid the Disclosing Party in mitigating and preventing the unauthorized use and disclosure and any furtherance thereof.
[29] 5. EXCLUSIONS AND EXEMPTIONS.
[30] Recipient shall have no obligation of confidentiality with respect to any information which:
[31] 5.1. is already known or in the possession of Recipient or its Affiliate at the time of disclosure as shown by the Recipient’s and/or its Affiliates´ files and records prior to the time of disclosure, otherwise than as a result of any improper act or omission of Recipient or its Affiliate; or
[32] 5.2. is or becomes public knowledge through no wrongful act of Recipient; or
[33] 5.3. is rightfully acquired from others who did not obtain it under obligation of confidentiality; or
[34] 5.4. is independently developed by an employee, agent or consultant of Recipient without reference to the Confidential Information; or
[35] 5.5. is approved for release by written authorization from Disclosing Party.
[36] 5.6. The Recipient is hereby notified that, as set forth in 18 U.S.C. §1833(b), he/she does not have criminal or civil liability under U.S. trade secret law for the following disclosures of a trade secret:
[37] 5.6.1. disclosure in confidence to a federal, state or local government official, either directly or indirectly, or to an attorney, provided the disclosure is for the sole purpose of reporting or investigating a suspected violation of law; and/or
[38] 5.6.2. disclosure in a complaint or other document filed in a lawsuit or other proceeding if such filing is made under seal; and/or
[39] 5.6.3. under those circumstances where Recipient files a lawsuit for retaliation against the Disclosing Party for reporting a suspected violation of law, Recipient may disclose the Disclosing Party’s trade secret information to its attorney and may use the trade secret information in the court proceeding if Recipient files any document containing the trade secret under seal and does not disclose the trade secret, except pursuant to court order.
[40] 6. REPRODUCTION AND RETURN OF CONFIDENTIAL INFORMATION.
[41] The Confidential Information provided by the Disclosing Party shall not be copied or reproduced without the Disclosing Party’s prior written permission, except for such copies as may reasonably be required for the purpose as set forth in Section I of this Agreement.
[42] All such retained copies shall remain subject to the use and disclosure restrictions in this Agreement.
[43] 7. DISCLOSURES REQUIRED BY LAW.
[44] If Recipient is requested, ordered or required by a regulatory agency or any other government authority or a court to disclose any Confidential Information, Recipient shall promptly notify Disclosing Party of such request, order or requirement so that Disclosing Party may have the opportunity to contest the disclosure, including seeking a protective order, or waive Recipient’s compliance with this Agreement.
[45] If Recipient is (in the opinion of its counsel) compelled to disclose any Confidential Information, or else be liable for contempt or other penalty or be subject to claims from a third party, Recipient may disclose such Confidential Information without liability under this Agreement.
[46] 8. EXPORT LAWS.
[47] Neither party shall export, directly or indirectly, any of the Confidential Information to any country, person or entity which the US Government, at the time of export, requires an export license or other governmental approval without first obtaining such license or approval.
[48] The Recipient shall first obtain the written consent of Disclosing Party prior to submitting any request for authority to export such Confidential Information.
[49] For the purposes of this Agreement, export occurs when Confidential Information is transferred from one country to another by any means, including but not limited to physical shipments, FTP file transfers, e-mails, faxes, oral transfers or remote server access and an export may also occur when Confidential Information is transferred to or accessed by a person who is neither a citizen nor permanent resident of the country in which such transfer or access is taking place.
[50] 9. OWNERSHIP OF CONFIDENTIAL INFORMATION.
[51] Disclosing Party or its licensors, as the case may be, retain all rights in Confidential Information disclosed and all documents, prototypes, software development kits (SDKs) and other similar tangible property embodying, containing or reflecting the same shall remain the property of Disclosing Party.
[52] 10. NO LICENSE.
[53] Neither the execution of this Agreement nor the disclosure of any Confidential Information is construed as granting either expressly or by implication, estoppel or otherwise, any license or right to the Confidential Information or any intellectual property rights embodied therein.
[54] 11. NO WARRANTY.
[55] All Confidential Information provided under this Agreement is provided “AS IS” and specifically excludes any warranty, whether express or implied, including without limitation, any implied warranty of merchantability, fitness for a particular purpose, or accuracy.
[56] The Disclosing Party is not liable under this Agreement for any damages in connection with, related to, or arising out of the use of its Confidential Information.
[57] 12. NO OBLIGATION.
[58] This Agreement shall not be construed in any manner to be an obligation to enter into a further substantive contract or to disclose any particular Confidential Information.
[59] 13. INDEPENDENT DEVELOPMENTS.
[60] Disclosing Party understands that Recipient may develop or have developed information internally, or receive or have received information from other parties that is similar to the Confidential Information.
[61] Accordingly, nothing in this Agreement shall be construed as a representation that Recipient has not or will not independently develop products that compete with the products or systems contemplated by the Confidential Information provided that it does so without breaching the terms of this Agreement.
[62] 14. RELATIONSHIP.
[63] Each party hereto shall be considered as an independent contractor responsible for its own expenses and financial obligations incurred in the performance of this Agreement.
[64] 15. NO WAIVER.
[65] For a period of twenty-four (24) months after the termination of this Agreement, the Receiving Party shall not engage in, or assist any person in, any business that competes with the business of the Disclosing Party.
[66] Neither party waives any rights in invention or development lawfully possessed by it at the time of signing this Agreement.
[67] In addition, this Agreement does not imply any waiver of any rights or action under the patent, trademark, copyright, trade secret, unfair competition, fair trade or related laws.
[68] Failure to exercise any rights under this Agreement shall not be construed as a waiver of such rights.
[69] 16. INUREMENT.
[70] This Agreement shall inure to the benefit of the parties hereto and their respective “Affiliates” (as defined below), successors, assigns and legal representatives.
[71] The parties agree that each party and its Affiliates may receive Confidential Information from and/or disclose Confidential Information to the other party and the other party's Affiliates, and that all such Confidential Information shall be governed by this Agreement.
[72] Recipient shall be fully responsible to the Disclosing Party for any breach of this Agreement by the Recipient’s Affiliates.
[73] “Affiliate”, as used herein, means an entity that directly or indirectly controls, is controlled by or is under common control with a party to this Agreement; and as used in this Section ”control”, “controls” or ”controlled” means:
[74] (i) fifty-one percent (51%) or more ownership or beneficial interest of income or capital of such entity;
[75] (ii) ownership of at least fifty-one percent (51%) of the voting power or voting equity; or
[76] (iii) the ability to otherwise direct or share management policies of such entity.
[77] 17. INJUNCTIVE RELIEF.
[78] The parties agree that any use of Confidential Information in violation of this Agreement may cause the other party irreparable harm, and may leave it with no adequate remedy at law and shall, thereby, entitle it to seek injunctive relief in any court with competent jurisdiction over the party or party’s Affiliate in violation.
[79] 18. CHOICE OF LAW.
[80] This Agreement is governed and construed in accordance with the laws of the State of Michigan, without regard to principles of conflict or choice of laws.
[81] The Parties hereby unconditionally and irrevocably agree to submit to the exclusive jurisdiction of the state and federal courts of the State of Michigan.
[82] 19. SURVIVAL.
[83] 20. SEVERABILITY.
[84] If a court finds any provision of this Agreement or any right or obligation invalid or unenforceable, this Agreement shall be immediately deemed amended to:
[85] (i) include a provision that reflects the intent of the parties, or, if
[86] (i) is not possible,
[87] (ii) to exclude such provision and the parties shall negotiate in good faith a substitute provision that reflect the parties’ intent at the time of entering into the Agreement.
[88] 21. ENTIRE AGREEMENT.
[89] This Agreement contains the entire understanding between the parties regarding the Confidential Information and supersedes all other communications, reports or understandings between the parties in respect thereto.
[90] No change or addition to any provision shall be binding unless it is in writing and signed by an authorized representative of both parties.
[91] All notices shall be in writing and delivered by electronic mail, registered or certified mail (return receipt requested) to the appropriate address set forth in the signature block below.
[92] 22. HEADINGS.
[93] Headings in this Agreement are for reference only and shall not affect the meaning of the provisions.
[94] 23. COUNTERPARTS.
[95] This Agreement may be signed in two or more counterparts including signing facsimile copies.
[96] Each counterpart is deemed an original and all counterparts together shall constitute one and the same instrument.
[97] IN WITNESS WHEREOF, the parties hereto have caused their authorized representatives to execute this Agreement as of the date first written above.
[98] Signature: Signature:
[99] Print Name: Print Name:
[100] Title: Title:
[101] Date: Date:
[102] Signature:
[103] Print Name:
[104] Title:
[105] Date

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: The NDA stops a party from reporting possible violations of law to, or communicating with, government agencies or regulators, with no exception for such reports.

Q2 [TERM, about the base NDA] CONTRACT TERM: The Receiving Party may freely use residual knowledge, ideas or know-how retained in unaided memory from Confidential Information.

Q3 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may create a copy of some Confidential Information in some circumstances.

Q4 [TERM, about the base NDA] CONTRACT TERM: A fixed sum or penalty is payable on breach regardless of the actual loss suffered.

Q5 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in the Agreement.

Q6 [TERM, about the base NDA] CONTRACT TERM: Some obligations of the Agreement survive termination or expiry of the Agreement.

Q7 [TERM, about the base NDA] CONTRACT TERM: The Agreement assigns or transfers ownership of the Disclosing Party's Confidential Information or derivative works to the Receiving Party.

Q8 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall notify Disclosing Party if Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.

Q9 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q10 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some third-parties, including consultants, agents and professional advisors.

Q11 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not solicit some of Disclosing Party's representatives or employees.

Q12 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that the Agreement was agreed or negotiated.

Q13 [TERM, about the base NDA] CONTRACT TERM: The Agreement does not grant the Receiving Party any right or licence to Confidential Information.

Q14 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some of Receiving Party's employees.

Q15 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may acquire information similar to Confidential Information from a third party.

Q16 [TERM, about the base NDA] CONTRACT TERM: Confidential Information shall only include technical information.
