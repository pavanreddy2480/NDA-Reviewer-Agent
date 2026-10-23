# Open Source Software Policy

**Company:** Northwind Cloud, Inc.
**Document owner:** Open Source Program Office (OSPO), with IP Counsel
**Policy number:** ENG-006
**Effective date:** April 22, 2025
**Applies to:** All engineers, product managers and contractors who write, review, build or ship software for Northwind Cloud, Inc.

---

## 1. Purpose

Open source software is part of almost everything Northwind builds. Our platform runs on open source operating systems, databases, message queues, web frameworks and thousands of smaller libraries. This brings speed, quality and community support, but it also brings obligations: licenses that must be followed, vulnerabilities that must be patched and maintainers who may stop maintaining their work. This Policy sets how Northwind selects, approves, uses, tracks and contributes to open source software.

## 2. Scope

The Policy applies to all open source software used in or with Northwind products, internal tools, build systems and infrastructure, and to all contributions Northwind workers make to open source projects, whether on company time or in a capacity connected with their work. It covers source code, binaries, container images, packages, models and datasets released under open licenses.

## 3. Definitions

- **Open source software (OSS)** means software distributed under a license approved by the Open Source Initiative or a license with equivalent conditions that allow use, modification and redistribution.
- **Permissive license** means a license such as MIT, BSD, ISC or Apache 2.0 that places few conditions on redistribution.
- **Weak copyleft license** means a license such as LGPL, MPL or EPL that requires changes to the licensed component, but not to the whole product that uses it, to be shared.
- **Strong copyleft license** means a license such as GPL or AGPL that can require the source code of a combined work to be shared.
- **Network copyleft** means a license, such as AGPL, whose conditions apply when users interact with the software over a network.
- **Source-available license** means a license that publishes source but restricts use, such as the Business Source License or the Server Side Public License. These are not treated as open source.
- **SBOM** means a software bill of materials listing every component in a build.
- **OSPO** means the Open Source Program Office.
- **Component** means any library, framework, tool or image obtained from outside Northwind.

## 4. License Categories and Approval

### 4.1 Categories

| Category | Examples | Rule |
|---|---|---|
| Green | MIT, BSD-2, BSD-3, ISC, Apache 2.0, Unlicense, CC0 | May be used in any product after registration in the component catalog |
| Yellow | LGPL, MPL 2.0, EPL, CDDL | May be used if linked dynamically or isolated, with OSPO approval |
| Red | GPL, AGPL, SSPL, BSL, commercial-use restrictions, no license | Not used in distributed or hosted products without approval by the OSPO and IP Counsel |

### 4.2 Registration

Before a new component is added to a product, the engineer registers it in the component catalog with its name, version, license, source and purpose. Green components are approved automatically. Yellow and red components are routed to the OSPO.

### 4.3 Approval of red components

An engineer who wants to use a red component must show that no alternative exists, explain how it will be isolated, and document the licensing analysis. IP Counsel and the OSPO decide jointly. Approvals are time-limited and recorded in the catalog.

### 4.4 Components without a license

Code that is publicly visible but has no license is not open source and is protected by copyright. It must not be copied, adapted or built into any product.

### 4.5 Code from the internet

Engineers must not copy code snippets from forums, blogs, gists or generative tools into the code base without checking their license. Snippets longer than ten lines require a registered source and a license check.

## 5. Security and Maintenance

### 5.1 Vulnerability scanning

Every build is scanned by software composition analysis tools. Newly disclosed vulnerabilities in used components are triaged by the owning team within two business days. Fix timelines follow the Information Security Acceptable Use Policy.

### 5.2 Version pinning

Dependencies must be pinned to explicit versions or hashes in lock files. Automatic upgrades are allowed only in non-production environments or after the build passes tests.

### 5.3 Maintenance health

Before adopting a component, engineers consider its health: how recently it was updated, how many maintainers it has, how quickly issues are fixed, the number of known vulnerabilities and the size of its community. Components that are abandoned must be replaced, forked or removed within a quarter of the abandonment being noticed.

### 5.4 Supply chain integrity

Packages must come from approved registries through the company's artifact proxy, which verifies signatures and checksums. Engineers must not download packages directly from unknown mirrors or install from untrusted URLs. Build pipelines produce an SBOM for each release and store it with the release record.

## 6. Compliance Obligations

### 6.1 Attribution and notices

Where a license requires attribution or a notice, the release process includes the required text in the product documentation, in-app notices or an open source acknowledgements file. The OSPO maintains templates and checks them before each major release.

### 6.2 Source offers

If a license requires making source code available for a component Northwind has distributed, the OSPO publishes the required source code on request or in a public repository. Engineers must tell the OSPO before shipping such a component.

### 6.3 Modifications

Modifications to open source components used in production are tracked in forks in the company's source repository. Engineers should upstream general-purpose fixes where possible, following Part 7.

### 6.4 Redistribution of images and models

Container images, pre-trained models and datasets inherit the licenses of their contents. Before using or distributing them, engineers must check the model license, the dataset license and any acceptable-use restrictions.

## 7. Contributing to Open Source

### 7.1 Contributions on behalf of Northwind

Workers may contribute to open source projects as part of their work if their manager and the OSPO have approved the contribution. Approval is automatic for small bug fixes to projects on the pre-approved list. For new features, new projects or significant contributions, the IP Review Board must approve.

### 7.2 Contribution rules

Contributions must be made using the worker's company account, must not include proprietary code, credentials, customer data or information about security vulnerabilities, and must comply with the project's contributor license or developer certificate of origin. Workers sign a contributor license only after OSPO review.

### 7.3 Personal contributions

Workers may contribute to open source projects in their own time using their own equipment if the contribution is unrelated to Northwind's business and does not use Northwind resources or non-public information. Where there is doubt about whether the work relates to Northwind's business, the worker should ask the OSPO.

### 7.4 Releasing Northwind projects

Northwind may release internal projects as open source if they have been reviewed by the OSPO and approved by the IP Review Board. The review confirms ownership of all code, scans for secrets and sensitive data, selects a license (usually Apache 2.0), prepares documentation and names maintainers. Each released project must have an owner and a security contact.

### 7.5 Trademarks and community conduct

Contributors represent Northwind in open source communities. They must follow the project's code of conduct, be courteous and avoid disparaging competitors. Use of Northwind's name and logo in a project requires approval from Marketing.

## 8. Dual Use and Commercial Open Source

Where a vendor offers a commercial edition of an open source product, procurement of that edition follows the Vendor and Third-Party Risk Policy. An engineer must not choose a source-available product for a production dependency without OSPO review, because a later change in the license could make continued use costly.

## 9. Roles and Responsibilities

- **Open Source Program Office** maintains the component catalog, approves yellow components, handles notices and runs training.
- **IP Counsel** advises on license analysis and approves red components jointly with the OSPO.
- **Chief Technology Officer** is accountable for the Policy within Engineering.
- **Engineering managers** make sure their teams register components and respond to alerts.
- **Security team** operates scanning and the artifact proxy.
- **Engineers** follow the Policy, register components, keep dependencies current and consult the OSPO when in doubt.
- **Internal Audit** reviews compliance annually.

## 10. Tooling

The OSPO provides: the component catalog and its approvals workflow; license scanning integrated with the continuous integration system; the artifact proxy; an SBOM generator; and a dashboard that shows each team's open vulnerabilities, license risks and stale dependencies. Teams are expected to keep their dashboard free of overdue items.

## 11. Metrics

The OSPO reports quarterly to the Chief Technology Officer on: percentage of components registered; red components in use; mean time to remediate vulnerabilities in dependencies; number of stale or abandoned components; contributions made upstream; and training completion.

## 12. Exceptions

Exceptions to this Policy are requested through the OSPO and approved by the OSPO and IP Counsel jointly. Exceptions are time-limited to no more than twelve months and are recorded in the catalog.

## 13. Enforcement

Use of components in breach of this Policy may require remediation before release and, in serious cases, withdrawal of a release. Repeated or intentional violations may result in discipline.

## 14. Training

New engineers complete OSS training in their first month. The OSPO offers an annual refresher, a monthly office hour and a guide with worked examples for common license questions.

## Appendix A. Decision Guide for Adding a New Dependency

1. **Is there already an approved component that does the job?** If so, use it.
2. **What is the license?** Look it up in the package metadata and in the repository. If the license is red, stop and talk to the OSPO.
3. **Is the project healthy?** Check commit history, number of maintainers, open issues and release frequency.
4. **How many transitive dependencies does it bring?** Prefer components with a small footprint.
5. **Are there known vulnerabilities?** Check the scanner's report for the version you plan to use.
6. **Is it needed in production?** Development-only tools carry less risk but must still be registered.
7. **Register it** in the component catalog and open a pull request that pins the version.

## Appendix B. Examples

**A team wants to use a popular reporting library under the GPL in a hosted service.** The GPL's conditions are triggered by distribution, but some variations such as the AGPL apply to network use. The team must ask the OSPO, which will analyze how the library is combined with Northwind's code and whether an alternative exists.

**An engineer wants to copy a 40-line function from a public repository with no license file.** Without a license, the code is protected by copyright and may not be copied. The engineer should write their own implementation or find a licensed alternative.

**A product team wants to ship a mobile app that includes a library under the Apache 2.0 license.** This is a green license. The team registers the component and ensures that the acknowledgements screen lists the library and includes its notice file.

**A data scientist wants to fine-tune an open-weights language model.** The data scientist checks the model license for restrictions on commercial use, size thresholds or field-of-use limits, registers the model and records the training data sources in the model registry.

## Appendix C. Typical Review Timeline

| Request type | Reviewer | Target response |
|---|---|---|
| Green component registration | Automatic | Immediate |
| Yellow component | OSPO | 3 business days |
| Red component | OSPO and IP Counsel | 10 business days |
| New contribution to an external project | OSPO | 5 business days |
| Release of a Northwind project as open source | IP Review Board | Next scheduled meeting, or 15 business days |
| Emergency vulnerability fix to a component | Security team and OSPO | 1 business day |

## Appendix D. Maintaining a Healthy Dependency Tree

Teams are expected to review their dependency dashboards at least every sprint. The OSPO recommends the following habits: update dependencies in small, frequent steps rather than large, rare ones; remove components that are no longer used; avoid pulling in large frameworks for small features; subscribe to security advisories for critical components; and test upgrades in staging. Teams that fall more than two major versions behind on a core framework must submit an upgrade plan to the Chief Technology Officer. The OSPO publishes an annual "state of our dependencies" report that identifies the most widely used components, the components with the greatest risk and recognizes teams with the cleanest dashboards.

## 15. Revision History

| Version | Date | Author | Summary of change |
|---|---|---|---|
| 1.0 | February 18, 2020 | OSPO | Initial issue |
| 1.4 | August 3, 2022 | OSPO | Added supply chain integrity requirements |
| 2.0 | March 14, 2024 | OSPO | Added AI model and dataset licensing |
| 2.1 | April 22, 2025 | OSPO | Revised license categories; expanded contribution rules |
