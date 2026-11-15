# Judge task nda_664ff5c8

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
[2] MUTUAL NONDISCLOSURE AGREEMENT
[3] This Mutual Nondisclosure Agreement (this “Agreement”) by and between Jamba, Inc., a Delaware corporation, including on behalf of its affiliates (the “Company”), and FOCUS Brands Inc., a Delaware corporation, including on behalf of its subsidiaries (the “Participant” and together with the Company, each a “Party” and collectively, the “Parties”), is dated as of the latest date set forth on the signature page hereto (the “Effective Date”).
[4] 1. General.
[5] In connection with the consideration of a possible negotiated transaction (a “Possible Transaction”) between the Parties, each Party (in its capacity as a provider of information hereunder, a “Provider”) is prepared to make available to the other Party (in its capacity as a recipient of information hereunder, a “Recipient”) certain Evaluation Material (as defined in Section 2 below) in accordance with the provisions of this Agreement, and hereby agrees to take or abstain from taking certain other actions as hereinafter set forth.
[6] 2. Definitions.
[7] (a) The term “affiliates” shall mean, with respect to any Person, any other Person directly or indirectly controlling, controlled by, or under common control with such Person.
[8] (b) The term “Beneficial Ownership” when used with reference to a security shall have the meaning ascribed to it under the Securities Exchange Act of 1934, as amended (the “1934 Act”), except that for purposes of this definition, the term security shall include any option, warrant, or convertible security regardless of exercise or conversion date, and also include any stock appreciation right, or similar right with an exercise or conversion privilege or a settlement payment or mechanism at a price related to the security or with a value derived in whole or in part from the value of the security, whether or not such instrument or right shall be subject to settlement in securities or otherwise and any other direct or indirect opportunity to profit or share in any profit derived from any increase or decrease in the value of the security.
[9] (c) The term “Evaluation Material” means information (whether oral, written, electronic or otherwise) concerning Provider which has been or is furnished to Recipient or its Representatives (as defined below) by or on behalf of Provider in connection with Recipient’s evaluation of a Possible Transaction, including Provider’s business, financial condition, operations, assets, liabilities, personnel and contracts, and includes all notes, analyses, compilations, studies, interpretations or other documents prepared by Recipient or its Representatives which contain or are based upon, in whole or in part, the information furnished by the Provider hereunder.
[10] The term Evaluation Material does not include information which
[11] (i) is or becomes generally available to the public other than as a result of a disclosure by Recipient or any of its Representatives in breach of this Agreement,
[12] (ii) was within a Recipient’s or its Representatives’ (on behalf of Recipient) possession, prior to its being furnished to Recipient or its Representatives by or on behalf of Provider or
[13] (iii) is or becomes available to Recipient or its Representatives (on behalf of Recipient) from a source other than the Provider or its Representatives, provided that the source of such information was not bound by a confidentiality agreement with, or other contractual, legal or fiduciary obligation of confidentiality to, Provider with respect to such information or
[14] (iv) Recipient can reasonably show was independently developed by Recipient or Recipient’s Representatives without the use of or reference to any Evaluation Material provided by or on behalf of Provider or its Representatives.
[15] (d) The term “Representatives” shall include the directors, officers, employees, potential financing sources, partners, agents and advisors (including, without limitation, attorneys, accountants, consultants, bankers and financial advisors) of a Party who have a need to know the Evaluation Material for purposes of evaluating a Possible Transaction, but only those of the foregoing who actually receive Evaluation Material directly from or at the direction of such Party.
[16] For the avoidance of doubt, Roark Capital Acquisition LLC shall be a Representative of FOCUS Brands Inc. under this Agreement.
[17] (e) The term “Person” includes the media and any corporation, partnership, group, individual or other entity.
[18] 3. Use of Evaluation Material.
[19] Each Recipient shall, and shall cause its Representatives to,
[20] (i) use the Evaluation Material solely for the purpose of evaluating a Possible Transaction and
[21] (ii) keep the Evaluation Material confidential, and, subject to Section 5, will not, and will cause its Representatives not to, disclose any of the Evaluation Material in any manner whatsoever; provided, however, that any of such information may be disclosed to Recipient’s Representatives who need to know such information for the sole purpose of helping Recipient evaluate a Possible Transaction.
[22] Each Recipient agrees to be responsible for any breach of this Agreement by any of such Recipient’s Representatives.
[23] This Agreement does not grant Recipient or any of its Representatives any license to use Provider’s Evaluation Material except as provided herein.
[24] In addition, all proprietary and intellectual property rights in and to the Evaluation Material shall remain the sole property of Provider, and nothing in this Agreement shall be construed in any way to grant to Recipient or its Representatives or any other Person any express or implied option, license or other right, title or interest in or to any Evaluation Material, or to any intellectual property rights embodied in such Evaluation Material.
[25] 4. Non-Disclosure of Discussions.
[26] Subject to Section 5, each Party agrees that, without the prior written consent of the other Party, such Party will not, and will cause its Representative not to, disclose to any other Person
[27] (i) that Evaluation Material has been exchanged between the Parties,
[28] (ii) that discussions or negotiations are taking place between the Parties concerning a Possible Transaction or any other transaction between the Parties or
[29] (iii) any of the terms, conditions or other facts with respect thereto (including the status thereof) ; provided, however, that nothing contained herein shall be deemed to inhibit, impair or restrict the ability of Recipient or its Representatives from having discussions or negotiations with other persons relating to potential financing in connection with the Possible Transaction so long as each of such Persons agrees in writing to be bound by the terms of this Agreement applicable to Representatives.
[30] 5. Legally Required Disclosure.
[31] If a Recipient or its Representatives are requested or required (by oral questions, interrogatories, other requests for information or documents in legal proceedings, subpoena, civil investigative demand or other similar process) to disclose any of the Evaluation Material or any of the facts disclosure of which is prohibited under Section 4 above, such Recipient shall provide Provider with prompt written notice of any such request or requirement together with copies of the material proposed to be disclosed so that Provider may seek a protective order or other appropriate remedy and/or waive compliance with the provisions of this Agreement.
[32] If, in the absence of a protective order or other remedy or the receipt of a waiver by Provider, a Recipient or any of its Representatives is nonetheless legally compelled or required to disclose Evaluation Material or any of the facts disclosure of which is prohibited under Section 4 or would be liable for contempt or suffer other censure or penalty, such Recipient or its respective Representatives may, without liability hereunder, disclose to such requiring Person only that portion of such Evaluation Material or any such facts which Recipient or its Representatives is legally compelled or required to disclose, provided that Recipient and/or its Representatives cooperate with Provider to obtain an appropriate protective order or other reliable assurance that confidential treatment will be accorded such Evaluation Material or such facts by the Person receiving the material.
[33] Notwithstanding anything in this Agreement to the contrary, neither Recipient nor Recipient’s Representatives shall be required to provide notice or seek consent to disclose any information in connection with a routine audit by, or blanket request from, a regulatory or governmental entity with jurisdiction over Recipient or Recipient’s Representatives, and not directed at the Company or the Possible Transaction; provided that the Recipient or its Representatives, as applicable, inform any such authority of the confidential nature of the information disclosed to them and to keep such information confidential in accordance with such authority’s policies or procedures.
[34] 6. “Click Through” Agreements.
[35] The terms of this Agreement shall control over any additional purported confidentiality requirements imposed by an offering memorandum or electronic database, dataroom, or similar repository of Evaluation Material to which Recipient or its Representatives are granted access in connection with this Agreement or a Possible Transaction, notwithstanding acceptance of such an offering memorandum or submission of an electronic signature, “clicking” on an “I Agree” icon or other indication of assent to such additional confidentiality conditions, it being understood and agreed that Recipient’s and its Representatives’ confidentiality obligations with respect to the Evaluation Material are exclusively governed by this Agreement and may not be reduced or enlarged except by an agreement executed by the Parties hereto in traditional written format.
[36] 7. Return or Destruction of Evaluation Material.
[37] At any time upon the request of a Provider for any reason, a Recipient will, and will direct its Representatives to, promptly, but not later than 10 business days, after receipt of such notice or request, destroy or return (at Recipient’s option) all Evaluation Material and all documents that incorporate Evaluation Material, and no copy or extract thereof (including electronic copies) shall be retained, except that Recipient and its Representatives may retain one copy to be kept confidential and used solely for archival, legal, and compliance purposes.
[38] Recipient shall provide to the Provider written confirmation of destruction signed by an authorized representative of Recipient.
[39] Notwithstanding the return or destruction of the Evaluation Material, Recipient and its Representatives will continue to be bound by such Recipient’s obligations hereunder with respect to such Evaluation Material.
[40] 8. No Solicitation.
[41] Recipient will not, within eighteen months from the date of this Agreement, directly or indirectly solicit the employment or consulting services of or employ or engage as a consultant any of the senior or key employees of the Provider or any of its subsidiaries nor any other employee of the Provider or any if its subsidiaries with whom Recipient has had direct contact in connection with its evaluation of a Possible Transaction or of whom it has become aware as a result of its receipt of any Evaluation Material, so long as they are employed by the Provider or any of its subsidiaries and for two months thereafter.
[42] For the purposes of clarification, the mere receipt of Provider’s employee list by Recipient shall not be considered a solicitation of or a direct contact with such employees pursuant to this section.
[43] A Recipient is not prohibited from:
[44] (i) soliciting by means of a general advertisement not directed at any particular individual or the employees of the Provider or its subsidiaries generally or
[45] (ii) engaging any recruiting firm or similar organization to identify or solicit individuals for employment on behalf of such Recipient (and soliciting any person identified by any such recruiting firm or organization) so long as such Recipient does not identify either Provider or any of the individuals employed by Provider to be solicited by such recruiting firm or organization.
[46] The provisions of this Section 8 shall terminate and be of no further effect upon the acquisition of such Provider by a third party.
[47] 9. Standstill.
[48] Participant does not own any of the capital stock of the Company as of the Effective Date.
[49] Participant agrees that, for a period of one year after the date of this Agreement (the “Standstill Period”), unless specifically invited in writing by the Company, neither it nor
[50] (1) any of its majority-owned subsidiaries,
[51] (2) its Representatives (acting on its behalf), or
[52] (3) Roark Capital Acquisition LLC or its affiliates who receive Evaluation Material directly from Roark Capital Acquisition LLC or Participant or at their direction, will in any manner, directly or indirectly:
[53] (a) effect, seek, offer or propose (whether publicly or otherwise) to effect, or cause or participate in, or in any way assist any other Person to effect, seek, offer or propose (whether publicly or otherwise) to effect or participate in:
[54] (i) any acquisition of any securities (or any acquisition of Beneficial Ownership thereof) or assets of the Company or any of its subsidiaries,
[55] (ii) any tender or exchange offer, merger or other business combination involving the Company or any of its subsidiaries,
[56] (iii) any recapitalization, restructuring, liquidation, dissolution or other extraordinary transaction with respect to the Company or any of its subsidiaries, or
[57] (iv) any “solicitation” of “proxies” (as such terms are used in the proxy rules of the Securities and Exchange Commission) or consents to vote any voting securities of the Company;
[58] (b) form, join or in any way participate in a “group” (as defined under the Act) with respect to the securities of the Company;
[59] (c) make any public announcement with respect to, or submit an unsolicited proposal for or offer of (with or without condition), any extraordinary transaction involving the Company or its securities or assets;
[60] (d) otherwise act, alone or in concert with others, to seek to control or influence the management, Board of Directors or policies of the Company;
[61] (e) take any action which may reasonably be expected to force the Company to make a public announcement regarding any of the types of matters set forth in
[62] (a) above; or
[63] (f) enter into any discussions or arrangements with any third party with respect to any of the foregoing.
[64] Participant also agrees, and will cause its Representatives to agree, during the Standstill Period, not to request the Company (or its directors, officers, employees or agents), directly or indirectly, to amend or waive any provision of this Section 9 (including this sentence).
[65] Notwithstanding anything in this Section 9 to the contrary, if, at any time during the Standstill Period, a public announcement is made by the Company or any other Person (other than Participant or its Representatives) that a third party (other than Participant or its Representatives) intends to acquire at least twenty percent (20%) of the outstanding capital stock of the Company, voting control or a material part of the Company’s assets (by way of a tender offer, exchange offer, proxy contest, acquisition or other similar transaction), or if a definitive agreement is executed by the Company with a third party relating to such an acquisition of capital stock or assets, the restrictions set forth in this Section 9 shall immediately terminate and cease to be of any further effect on Participant.
[66] Participant further agrees, and will cause its Representatives to agree, that unless otherwise directed by the Company in writing
[67] (i) all communications with the Company regarding a Possible Transaction,
[68] (ii) requests for additional information, facility tours, or management meetings, and
[69] (iii) discussions or questions regarding procedures with respect to a Possible Transaction, will be submitted or directed by Participant or its Representatives only to David Pace, the Company’s Chief Executive Officer, or a person or persons designated in writing by David Pace.
[70] Further, except upon the Company’s prior written consent, neither Participant nor its Representatives acting on behalf of Participant involved with a Possible Transaction or who have received Evaluation Material will, directly or indirectly, contact any stockholder, director, officer, employee or agent of the Company, or any customer or supplier of the Company, regarding the Evaluation Material or a Possible Transaction.
[71] Nothing contained herein shall prevent Participant or its Representatives from maintaining any contacts in the ordinary course of business unrelated to a Possible Transaction or from conducting consumer surveys or other due diligence, in each case, without disclosing or relying on any Evaluation Material.
[72] 10. Maintaining Privileges.
[73] If any Evaluation Material includes materials or information subject to the attorney-client privilege, work product doctrine or any other applicable privilege concerning pending or threatened legal proceedings or governmental investigations, each Party understands and agrees that the Parties have a commonality of interest with respect to such matters and it is the desire, intention and mutual understanding of the Parties that the sharing of such material is not intended to, and shall not, waive or diminish in any way the confidentiality of such material or its continued protection under the attorney-client privilege, work product doctrine or other applicable privilege.
[74] All Evaluation Material that is entitled to protection under the attorney-client privilege, work product doctrine or other applicable privilege shall remain entitled to such protection under these privileges, this Agreement, and under the joint defense doctrine.
[75] 11. Compliance with Securities Laws.
[76] Each Recipient acknowledges that the Evaluation Material may include material nonpublic information (within the meaning of the securities laws of the United States) with respect to Provider.
[77] Each Recipient agrees not to use and will cause its Representatives to agree not to use any Evaluation Material of Provider in violation of applicable securities laws.
[78] 12. Not a Transaction Agreement.
[79] Each Party understands and agrees that no contract or agreement providing for a Possible Transaction exists between the Parties unless and until a final definitive agreement for a Possible Transaction has been executed and delivered, and each Party hereby waives, in advance, any claims (including, without limitation, breach of contract) relating to the existence of a Possible Transaction unless and until both Parties shall have entered into a final definitive agreement for a Possible Transaction.
[80] Each Party also agrees that, unless and until a final definitive agreement regarding a Possible Transaction has been executed and delivered, neither Party will be under any legal obligation of any kind whatsoever with respect to such Possible Transaction by virtue of this Agreement except for the matters specifically agreed to herein.
[81] Neither Party is under any obligation to accept any proposal regarding a Possible Transaction and either Party may terminate discussions and negotiations with the other Party at any time.
[82] 13. No Representations or Warranties; No Obligation to Disclose.
[83] Each Recipient understands and acknowledges that neither Provider nor its Representatives makes any representation or warranty, express or implied, as to the accuracy or completeness of the Evaluation Material furnished by or on behalf of Provider and shall have no liability to Recipient, its Representatives or any other Person relating to or resulting from the use of the Evaluation Material furnished to a Recipient or its respective Representatives or any errors therein or omissions therefrom.
[84] As to the information delivered to Recipient, Provider will only be liable for those representations or warranties which are made in a final definitive agreement regarding a Possible Transaction, when, as and if executed, and subject to such limitations and restrictions as may be specified therein.
[85] Nothing in this Agreement shall be construed as obligating Provider to provide, or to continue to provide, any information to any Person.
[86] 14. Modifications and Waiver.
[87] No provision of this Agreement can be waived or amended in favor of either Party except by written consent of the other Party, which consent shall specifically refer to such provision and explicitly make such waiver or amendment.
[88] No failure or delay by either Party in exercising any right, power or privilege hereunder shall operate as a waiver thereof, nor shall any single or partial exercise thereof preclude any other or future exercise thereof or the exercise of any other right, power or privilege hereunder.
[89] 15. Remedies.
[90] Each Party understands and agrees that money damages may not be a sufficient remedy for any breach of this Agreement by either Party or any of its Representatives and that the Party against which such breach is committed shall be entitled to seek equitable relief, including injunction and specific performance, as a remedy for any such breach or threat thereof.
[91] Such remedies shall not be deemed to be the exclusive remedies for a breach by either Party of this Agreement, but shall be in addition to all other remedies available at law or equity to the Party against which such breach is committed.
[92] 16. Legal Fees.
[93] In the event of litigation relating to this Agreement, if a court of competent jurisdiction determines that either Party or its Representatives has breached this Agreement, then the Party which is, or the Party whose Representatives are, determined to have so breached shall be liable and pay to the other Party the reasonable legal fees and costs incurred by the other Party in connection with such litigation, including any appeal therefrom.
[94] 17. Governing Law.
[95] This Agreement is for the benefit of each Party and shall be governed by and construed in accordance with the laws of the State of Delaware applicable to agreements made and to be performed entirely within such state.
[96] 18. Severability.
[97] If any term, provision, covenant or restriction contained in this Agreement is held by any court of competent jurisdiction to be invalid, void or unenforceable, the remainder of the terms, provisions, covenants or restrictions contained in this Agreement shall remain in full force and effect and shall in no way be affected, impaired or invalidated, and if a covenant or provision is determined to be unenforceable by reason of its extent, duration, scope or otherwise, then the Parties intend and hereby request that the court or other authority making that determination shall only modify such extent, duration, scope or other provision to the extent necessary to make it enforceable and enforce them in their modified form for all purposes of this Agreement.
[98] 19. Construction.
[99] The Parties have participated jointly in the negotiation and drafting of this Agreement.
[100] If an ambiguity or question of intent or interpretation arises, this Agreement shall be construed as if drafted jointly by the Parties and no presumption or burden of proof shall arise favoring or disfavoring either Party by virtue of the authorship at any of the provisions of this Agreement.
[101] 20. Term.
[102] This Agreement, and all obligations and other provisions hereunder, shall terminate two years after the date of this Agreement.
[103] 21. Entire Agreement.
[104] This Agreement contains the entire agreement between the Parties regarding the subject matter hereof and supersedes all prior agreements, understandings, arrangements and discussions between the Parties regarding such subject matter.
[105] 22. Counterparts.
[106] This Agreement may be signed in counterparts, each of which shall be deemed an original but all of which together shall be deemed to constitute a single instrument.
[107] 23. Consent to Representation.
[108] This agreement also constitutes notice to Participant that the Company has engaged DLA Piper LLP (US) and its affiliated firms as its legal counsel in connection with the Possible Transaction, and Participant hereby
[109] (i) consents to the continued representation of the Company by DLA Piper LLP (US) and its affiliated firms in relation to the Possible Transaction notwithstanding the fact that DLA Piper LLP (US) may have represented, and may currently or in the future represent, Participant and/or any of its respective affiliates with respect to unrelated matters and
[110] (ii) waive any actual or alleged conflict and actual or alleged violation of ethical or comparable rules applicable to DLA Piper LLP (US) and its affiliated firms that may arise from its representation of the Company in connection with the Possible Transaction, including but not limited to representing the Company against Participant and/or its affiliates in litigation, arbitration, or mediation in connection therewith.
[111] Notwithstanding the foregoing, in the event of any dispute (including litigation, arbitration, or mediation) between the Parties related to this Agreement, DLA Piper LLP (US) and its affiliated firms will not represent either Party.
[112] In addition, Participant hereby acknowledges that the consent and waiver under this paragraph is voluntary and informed, and that Participant has obtained independent legal advice with respect to this consent and waiver.
[113] Participant further agrees that they are each aware of the extent of their respective relationships, if any, with DLA Piper LLP (US) and its affiliate firms, and do not require additional information from DLA Piper LLP (US) in order to understand the nature of this consent.
[114] Each of DLA Piper LLP (US) and its affiliated firms are an express third party beneficiary of this paragraph.
[115] IN WITNESS WHEREOF, each of the undersigned entities has caused this Agreement to be signed by its duly authorized representative as of the date written below.
[116] JAMBA, INC.
[117] FOCUS BRANDS INC.
[118] By: /s/ David Pace By: /s/ Sarah Powell
[119] Name: Dave Pace Name: Sarah Powell
[120] Title: CEO Title: EVP, General Counsel & Secretary
[121] Date: March 30, 2018 Date: March 29, 2018

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information.

Q2 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement.

Q3 [TERM, about the base NDA] CONTRACT TERM: Agreement shall not grant Receiving Party any right to Confidential Information.

Q4 [TERM, about the base NDA] CONTRACT TERM: All Confidential Information shall be expressly identified by the Disclosing Party.

Q5 [TERM, about the base NDA] CONTRACT TERM: Confidential Information shall only include technical information.

Q6 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that Agreement was agreed or negotiated.

Q7 [TERM, about the base NDA] CONTRACT TERM: Some obligations of Agreement may survive termination of Agreement.

Q8 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may independently develop information similar to Confidential Information.

Q9 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may retain some Confidential Information even after the return or destruction of Confidential Information.

Q10 [TERM, about the base NDA] CONTRACT TERM: Confidential Information may include verbally conveyed information.

Q11 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may create a copy of some Confidential Information in some circumstances.

Q12 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some third-parties (including consultants, agents and professional advisors).

Q13 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not solicit some of Disclosing Party's representatives.

Q14 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall notify Disclosing Party in case Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.

Q15 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may acquire information similar to Confidential Information from a third party.

Q16 [TERM, about the base NDA] CONTRACT TERM: Receiving Party may share some Confidential Information with some of Receiving Party's employees.

Q17 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in Agreement.
