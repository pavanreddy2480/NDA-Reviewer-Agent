# US law pack: official text for the checkers

Pulled on 16 Oct 2026 so the two checkers per provision only need to **confirm**, not research. For each
provision: the operative text, where it comes from, and what to check in `us_law_pack.yaml`. Open the source
link and compare the text yourself before adding your name to `checked_by`; the excerpts below came through a
web reader and are split into quoted pieces.

**Points to decide** are things the draft pack gets roughly right but that the checkers should settle.

---

## LAW-DTSA-1833B: whistleblower immunity notice
Source: 18 U.S.C. §1833(b), https://www.law.cornell.edu/uscode/text/18/1833

> (b)(3)(A) "An employer shall provide notice of the immunity set forth in this subsection" "in any contract or
> agreement with an employee" "that governs the use of a trade secret" "or other confidential information."
>
> (b)(3)(B) "An employer shall be considered to be in compliance with the notice requirement in subparagraph (A)"
> "if the employer provides a cross-reference to a policy document provided to the employee" "that sets forth the
> employer's reporting policy for a suspected violation of law."
>
> (b)(3)(C) "If an employer does not comply with the notice requirement in subparagraph (A), the employer may not be
> awarded" "exemplary damages or attorney fees" ... "in an action against an employee to whom notice was not provided."
>
> (b)(4) "the term 'employee' includes any individual" "performing work as a contractor or consultant for an employer."

The summary matches. **Points to decide:**
- A cross-reference to a reporting-policy document also counts as notice. Add this to `risk_pattern`, so the
  checker does not flag NDAs that use it.
- "Employee" includes individual contractors and consultants, but `applies_if: counterparty == 'employee'` misses an
  individual consultant engaged as a vendor. This is fine for the benchmark if we say so.

## LAW-SEC-21F17: no impeding reports to the SEC
Source: 17 C.F.R. §240.21F-17(a), https://www.law.cornell.edu/cfr/text/17/240.21F-17

> "No person may take any action to impede an individual from communicating directly with the Commission staff"
> about a possible securities law violation, "including enforcing, or threatening to enforce, a confidentiality
> agreement", with an exception for certain information about a client's legal representation (§240.21F-4(b)(4)(i)-(ii)).
> *(Text after the first quote is paraphrased by the web reader. Read the full paragraph at the link.)*

The summary matches. `possible_risk` is right, because enforcement targets SEC-regulated companies.

## LAW-SPEAK-OUT: pre-dispute NDAs and sexual harassment
Source: 42 U.S.C. §19403, https://www.law.cornell.edu/uscode/text/42/19403

> (a) "With respect to a sexual assault dispute or sexual harassment dispute, no nondisclosure clause or
> nondisparagement clause" "agreed to before the dispute arises shall be judicially enforceable in instances in which
> conduct" "is alleged to have violated Federal, Tribal, or State law."

The summary matches. **Point to decide:** the Act is **not limited to employment**. `applies_if: counterparty ==
'employee'` is a scoping choice, so keep it and state it, or drop the condition.

## LAW-CA-BPC-16600 and LAW-CA-BPC-16600-NONSOLICIT
Source: Cal. Bus. & Prof. Code §16600, official site https://leginfo.legislature.ca.gov (blocked from our cloud
machine); text read from https://law.justia.com/codes/california/code-bpc/division-7/part-2/chapter-1/section-16600

> (a) "Except as provided in this chapter, every contract by which anyone is restrained from engaging in a lawful
> profession" "trade, or business of any kind is to that extent void."
>
> (b)(1) "This section shall be read broadly, in accordance with Edwards v. Arthur Andersen LLP (2008) 44 Cal.4th
> 937," "to void the application of any noncompete agreement in an employment context," ... "no matter how narrowly
> tailored," "that does not satisfy an exception in this chapter."
>
> (c) "This section shall not be limited to contracts where the person being restrained ... is a party to the contract."
>
> History: "(Amended by Stats. 2023, Ch. 828, Sec. 1. (AB 1076) Effective January 1, 2024.)"

The non-compete summary matches. **Points to decide:**
- The summary cites §16600.5 (SB 699, 2023). Confirm it from the bill text at https://legiscan.com/CA/text/SB699/2023.
- Employee non-solicits are case law (AMN Healthcare v. Aya, 2018), not statute text. Find the opinion, or drop the provision.

## LAW-PENALTY: liquidated damages that are a penalty
Current source_url: https://www.law.cornell.edu/wex/liquidated_damages. **This page does not cite Restatement
(Second) of Contracts §356.** It only says courts won't enforce a clause that is "punitive, illegal, unconscionable,
or contrary to public policy."

A citable statutory version for sales of goods is UCC §2-718(1), https://www.law.cornell.edu/ucc/2/2-718:

> "A term fixing unreasonably large liquidated damages is void as a penalty." (The amount must be reasonable in light
> of the anticipated or actual harm, the difficulty of proof of loss, and the inconvenience or nonfeasibility of
> otherwise obtaining an adequate remedy.)

**Point to decide:** NDAs are not sales of goods, so the rule is common law (Restatement §356, which is not free
online). Keep `possible_risk`, cite UCC §2-718 as the "codified analogue" plus Restatement §356, and change
source_url to a page that states the test.

## LAW-CCPA-SP: service-provider contract terms
Source: Cal. Civ. Code §1798.100(d) and §1798.140 (service provider). Official site blocked; text read from
Sidley's CCPA text, https://www.sidley.com/en/sidley-pages/ccpa-text

§1798.100(d): a business that sells or discloses personal information to a third party, service provider or
contractor must have a contract that:
1. limits the sale or disclosure to "limited and specified purposes";
2. obliges the recipient to "comply with applicable obligations under this title" and give the same level of
   privacy protection;
3. lets the business take reasonable steps to ensure the information is used consistently with the business's obligations;
4. requires the recipient to notify the business if it can no longer meet its obligations;
5. lets the business, on notice, stop and remediate unauthorized use.

§1798.140 (service provider): the contract "prohibits the entity receiving the information from retaining, using,
or disclosing" it for any purpose other than the contracted services.

**Point to decide:** the summary covers terms 1 and the §1798.140 prohibition, but not terms 2–5. For the
benchmark, keep `risk_pattern` to the purpose limit plus the no-sale/no-sharing term (what NDAs can plausibly contain), and say so.
