# Judge task nda_59eb9b11

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

[0] UNILATERAL NON-DISCLOSURE AGREEMENT
[1] BETWEEN
[2] Nordic Knowledge Partners ApS
[3] Central Business Register (CVR) number: 36428198
[4] Dampfærgevej 9, 1.
[5] 2100-DK Copenhagen
[6] (hereafter the "Service provider" or "NKP" or "Recipient")
[7] AND
[8] You the subject-matter expert
[9] (hereafter the "Subject-matter expert" or "Expert" or "Recipient")
[10] Each of Discloser and Recipient hereafter are also referred to as "Party" and collectively as the
[11] "Parties".
[12] 1. CONTACT PERSONS
[13] 1.1. Any notice given under or in relation to the Agreement shall be given in writing and for the attention to:
[14] a) If to Discloser:
[15] Att.: Andreas von Buchwald
[16] avb@nordicknowledgepartners.com
[17] b) If to Recipient:
[18] Att: You
[19] 3. DEFINITIONS AND INTERPRETATION
[20] 3.1. In the agreement, the following capitalised words and expressions have the following meaning:
[21] 3.2. "Affiliate" means with respect to any person, any other person directly or indirectly, through one or more intermediaries, Controlling, or Controlled by, or under common Control with such person, where control has the meaning of the power to direct the management of a person (directly or indirectly), whether through ownership of securities, by contract or otherwise and shall be presumed to exist in relation to a controlled person when another person holds
[22] (i) a majority of the voting rights,
[23] (ii) the right to control more than half of the voting rights by virtue of an agreement,
[24] (iii) the right to direct the financial and operational management by virtue of articles of association or agreement,
[25] (iv) the right to appoint or remove the majority of the members of the supreme governing body having a controlling influence, or
[26] (v) possession of the actual majority of votes at general meetings or equivalent governance forum and thereby an actual controlling interest in such person; and "Controlled" and "Controlling" shall be construed accordingly.
[27] 3.3. "Agreement" means this non-disclosure agreement including all appendices (if any).
[28] 3.4. "Client" means any customers or business partners of the Party;
[29] 3.5. "Confidential information" means any information of whatever form relating to the Project or Discloser or any of its Affiliates or Clients, supplied or made available by Discloser or on its behalf to recipient or Recipient Representatives, copies of any such information regardless of whether such information is identified as confidential or not; and information regarding:
[30] 3.5.1. The existence of the Project;
[31] 3.5.2. The identity of the Discloser and the willingness of the Discloser to enter into discussions and/or negotiations regarding the Project;
[32] 3.5.3. Any information including those parts of analyses, compilations, studies and other documents which contain, reflect or are derived from such information referred to in this Clause 3.4 or discussions and negotiations relating to the project.
[33] 3.6. "Effective Date" means the date when the last of the Parties signed the Agreement.
[34] 3.7. "Project" has the meaning ascribed to it in Clause 4.1.
[35] 3.8. "Representatives" means, in relation to a Party to the extent involved in the Project,
[36] (a) its Affiliates;
[37] (b) its contractors / suppliers of any tier and
[38] (c) all of the aforementioned entities' employees, directors, senior executives, professional advisors and consultants.
[39] 4. BACKGROUND
[40] 4.1. The Parties intend to engage in a Project/Projects where the Discloser will facilitate consultation(s) (in-person or remote, e.g. via telephone conference) between its Client and the Recipient ("Subject-matter expert consultations").
[41] The Parties will as part of the Project disclose to each other certain non-public Confidential Information, subject to the terms and conditions set out in this Agreement, which both Parties hereby accept.
[42] 5. CONFIDENTIALITY AND RESTRICTED USE
[43] 5.1. Recipient shall:
[44] 5.1.1. hold Confidential Information in confidence and protect it by using at least the same degree of care, but no less than a reasonable degree of care, as Recipient uses to safeguard its own confidential or proprietary information of a like nature from unauthorized use, disclosure or dissemination;
[45] 5.1.2. use Confidential Information only for the Project;
[46] 5.1.3. not copy or reproduce (or permit to be copied or reproduced) any Confidential Information, or directly or indirectly disclose or distribute any of it to any person other than those of its Representatives who are strictly required to perform Recipient's work in relation to the Project.
[47] 5.2. The obligations in Clause 5.1 shall not apply for Confidential Information that:
[48] 5.2.1. was, at the time of its disclosure, in the public domain or which, after Discloser's disclosure, comes into the public domain, unless it is in the public domain as a result of:
[49] a) a breach by Recipient of its obligations contained in this Agreement (or by any person to whom disclosure of information is made as permitted under this Agreement); or
[50] b) a breach by a third party of any other obligation or duty of confidentiality or non-disclosure relating to that information that Recipient is or ought to be aware of;
[51] 5.2.2. was or becomes available to Recipient on a non-confidential basis provided that the source is not known to Recipient to be bound by a confidentiality agreement and is not otherwise in breach of any obligation of confidentiality or restricted use;
[52] 5.2.3. is otherwise agreed in writing by Discloser to no longer being confidential and/or restricted; or
[53] 5.2.4. is required to be disclosed by law, regulation or any competent governmental, judicial or regulatory authority, or by a recognized stock exchange, or in response to a request from a regulatory body with a supervisory role over Recipient or any of its Affiliates, in which case Recipient will (or, if Recipient's Representative is subject to the disclosure obligation, Recipient will procure that such Representative will), in each case to the extent permitted by law, regulation or the relevant authority:
[54] a) inform
[55] Discloser of the circumstances of the disclosure and the information that will be disclosed as soon as reasonably practicable;
[56] b) permit Discloser in its absolute discretion to seek to obtain an injunction or take other appropriate action to protect the Confidential Information;
[57] c) take all such steps as may be reasonable and practicable in the circumstances to agree the form, contents and timing of such disclosure with Discloser before making such disclosure, provided that Recipient shall not be required to take any action under this Clause which it considers in good faith to be contrary to any of its legal or regulatory obligations;
[58] d) consult with Discloser as to possible steps to prevent or limit such disclosure and take those steps to the extent reasonably practicable in the circumstances, provided that Recipient shall not be required to take any action under this Clause which it considers in good faith to be contrary to any of its legal or regulatory obligations; and
[59] e) request assurances as to confidentiality from anybody to which the Confidential Information is to be disclosed.
[60] 5.2.5. Either Party must promptly inform the other Party after becoming aware of any breach of this Agreement whether committed by Recipient itself or its Representatives.
[61] 5.3. Ownership – no rights intended
[62] 5.3.1. All Confidential Information shall remain the property of Discloser or its relevant Representative, as applicable.
[63] 5.3.2. The disclosure of Confidential Information to Recipient or its Representatives shall not give Recipient or its Representatives any licence or other rights in relation to that Confidential Information beyond the rights contained in this Agreement.
[64] 5.3.3. Recipient shall not be entitled to file for patents or other statutory protection in any country based on any Confidential Information received hereunder.
[65] The disclosure of Confidential Information does not constitute any rights of prior use for Recipient
[66] 5.4. As is
[67] 5.4.1. With respect to the Confidential Information disclosed, Discloser provides the information "as is" and makes no representation or warranty, express or implied, to Recipient as to its condition, merchantability, design, operation, fitness, or use for the Project or any other matter.
[68] 6. REPRESENTATIVES
[69] 6.1. If Recipient discloses or distributes Confidential Information to any of its Representatives, such Representatives shall be subject to the same confidentiality and restricted use obligations as Recipient.
[70] 6.2. Recipient shall be liable for its Representatives' acts and omissions as if such acts or omissions had been its own acts or omissions, even when such persons/entities cease to be (as the case may be) employee, director, senior executive, professional advisor, consultant, Affiliate or supplier of any tier in relation to Recipient.
[71] 7. DURATION AND TERMINATION
[72] 7.1. Duration
[73] 7.1.1. The obligations contained in this Agreement shall start at the Effective Date and shall automatically terminate when the Project is terminated or completed.
[74] 7.2. Termination
[75] 7.2.1. Each Party may terminate the Agreement by giving one month prior written notice to the other Party.
[76] 7.3. Continuing Obligations
[77] 7.3.1. The obligations of confidentiality, non-disclosure and non-use set forth in this Confidentiality Agreement shall survive the termination or expiration of this Confidentiality Agreement
[78] (i) with respect to any Confidential Information that constitutes a trade secret under applicable law, for so long as such item shall continue to constitute a trade secret under applicable law, and
[79] (ii) with respect to any Confidential Information that does not constitute a trade secret under applicable law, for a period of 5 (five) years from and after the date of disclosure of such Confidential Information.
[80] 8. RETURN OF CONFIDENTIAL INFORMATION
[81] 8.1.1. Upon Discloser's request, Recipient shall promptly, and in any case within five (5) days from such request, return all documentation and other materials containing any Confidential Information of Discloser without retaining any copies thereof.
[82] Alternatively, at Discloser's option and request, Recipient shall destroy and/or erase all such materials and documentation and shall provide a written certification that all such materials and documentation have been destroyed and/or erased.
[83] 8.1.2. Clause 8.1 shall not apply to Confidential Information which
[84] i) must be stored by Recipient according to provisions of mandatory law or
[85] ii) was made as a matter of routine backup provided that such Confidential Information and copies thereof shall be subject to an indefinite confidential obligation according to the terms and conditions set forth herein until returned and/or destroyed, as the case may be.
[86] 9. OTHER PROVISIONS
[87] 9.1. No Relationship Established
[88] 9.1.1. This Agreement shall not constitute any rights or obligations for any of the Parties to this Agreement, to continue discussions or further to enter into any contract regarding the Project, and any Party can cease to continue such discussions at any time.
[89] The Agreement does not grant Recipient any exclusivity, and Discloser and its Affiliates may purchase similar services, works or goods from other suppliers.
[90] 9.2. Public Statements
[91] 9.2.1. Neither Party may use the other Party's name or trademarks or refer to the other Party directly or indirectly in any media release, public announcement, or public disclosure relating to the Agreement or its subject matter, including, but not limited to, in any promotional or marketing material or business presentations without the other Party's prior written consent in each case, except for such publication which is required under public procurement rules.
[92] 9.3. Severability
[93] 9.3.1. If any term or provision of the Agreement is held to be illegal, void or unenforceable in whole or in part under any enactment of law, such term or provision will be deemed not to form part of the Agreement.
[94] The enforceability of the remainder of the Agreement will not be affected.
[95] 9.3.2. In the event that any term or provision of the Agreement, which is fundamental to the accomplishment of the purpose of the Agreement, is held to be illegal, void or unenforceable in accordance with Sub-Clause 9.3.1, the Parties shall immediately commence good-faith negotiations to reach an equitable agreement, which reflects the intent of the Parties.
[96] 9.4. Waiver and Cumulative Rights
[97] 9.4.1. The rights provided by the Agreement may be waived in writing only by the relevant Party in a manner that expressly indicates that a waiver is intended, and such waiver is only to apply to the specific circumstances referred to.
[98] Any failure to exercise or any delay in exercising a right by either Party will not constitute a waiver of that right or of any other rights.
[99] 9.4.2. Unless a right of a Party is expressed to be an exclusive right, the exercise of it by the Party is without prejudice to its other rights.
[100] 9.5. Cost
[101] 9.5.1. Each Party shall be responsible for their own costs incurred by themselves and their Representatives.
[102] 9.6. Written Modifications
[103] 9.6.1. All modifications to this Agreement must be made in writing and must be signed by an authorized representative of the Parties.
[104] 10. GOVERNING LAW AND DISPUTE RESOLUTION
[105] 10.1. Governing Law
[106] 10.1.1. The laws of Denmark govern the Agreement and any legal dispute arising out of or in relation to the Agreement must be solved in accordance with the laws of Denmark.
[107] 10.2. Dispute Resolution
[108] 10.2.1. The Parties will attempt to settle any dispute between them by entering into good-faith negotiations through the appropriate management level of governance in a timely manner.
[109] The Parties must as a minimum attend the first good-faith negotiations.
[110] 10.2.2. Any dispute, controversy or claim arising out of or in connection with the Agreement or any breach, termination or invalidity hereof which is not resolved by prior negotiations, shall be finally settled by arbitration by The Danish Institute of Arbitration in accordance with the relevant rules adapted by The Danish Institute of Arbitration and applicable at the time of opening of the arbitration.
[111] The arbitration tribunal must have three arbitrators appointed by the Danish Institute of Arbitration unless the Parties agree otherwise.
[112] The arbitrators elect, from among their members, the chairman of the arbitration tribunal.
[113] 10.2.3. The place of arbitration must be Copenhagen, and the language of the proceedings, including any written pleadings, must be in English, unless otherwise agreed by the Parties.
[114] 10.2.4. Notwithstanding this Clause 10, breach of this Agreement may be stopped by injunctive relief at the ordinary courts.
[115] Nothing in this Agreement shall be construed as prohibiting Discloser from pursuing any remedies available in addition to those remedies available under the terms of this Agreement.
[116] 11. SIGNATURE
[117] 11.1. The Parties may choose to exchange signatures of the Agreement by means of electronic communication (by fax, email, or other electronic transmissions) and the Agreement shall not be invalid or unenforceable because the documents are exchanged electronically.
[118] 11.2. The Agreement is executed as per your completion and submission of the form found on NKP's website https://www.nordicknowledgepartners.com/compliance.

## Questions

Q1 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information.

Q2 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement.

Q3 [TERM, about the base NDA] CONTRACT TERM: Confidential Information shall only include technical information.

Q4 [TERM, about the base NDA] CONTRACT TERM: Receiving Party shall not disclose the fact that Agreement was agreed or negotiated.

Q5 [TERM, about the base NDA] CONTRACT TERM: Agreement shall not grant Receiving Party any right to Confidential Information.

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
