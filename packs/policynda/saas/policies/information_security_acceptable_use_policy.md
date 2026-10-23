# Information Security Acceptable Use Policy

**Company:** Northwind Cloud, Inc.
**Document owner:** Chief Information Security Officer
**Policy number:** SEC-001
**Effective date:** February 10, 2025
**Applies to:** All employees, contractors, interns and temporary workers, and every device, account and network used for Northwind business

---

## 1. Purpose

Northwind Cloud, Inc. ("Northwind") runs a service that thousands of businesses rely on every day. The security of that service depends on thousands of small decisions made by the people who build, operate, sell and support it: which password to choose, which link to click, which device to carry, which tool to install. This Policy tells workers what is expected of them when they use Northwind's technology, so that they can do their jobs freely while keeping the company, its customers and themselves safe.

## 2. Scope

This Policy applies to all workers and to all information systems owned, leased or operated by Northwind, including laptops, phones, servers, cloud accounts, source-control platforms, collaboration tools, network equipment, badges and any personal device that is enrolled for business use. It applies in Northwind offices, at home and while traveling.

## 3. Definitions

- **Worker** means any employee, officer, contractor, consultant, intern or temporary worker with access to Northwind systems.
- **Company system** means any hardware, software, account, network or service provided or paid for by Northwind.
- **Endpoint** means a laptop, desktop, tablet or phone used to access company systems.
- **Privileged access** means administrative access that can change the configuration or security of a system.
- **MFA** means multi-factor authentication.
- **Security team** means the CISO's organization, including the Security Operations Center (SOC).
- **Shadow IT** means any application or service used for company work that has not been approved by the Security team.

## 4. General Principles

1. Company systems exist for business use. Limited, occasional personal use is allowed if it does not interfere with work, consume significant resources or break the rules in this Policy.
2. Workers are responsible for activity that takes place under their accounts.
3. Workers have no expectation of privacy in company systems, which may be monitored in line with law and the Employee Privacy Notice.
4. Security is everyone's job. Workers must report anything suspicious at once.

## 5. Accounts and Authentication

### 5.1 Unique accounts and single sign-on

Each worker receives a unique account. Shared accounts are not permitted except for approved service accounts managed in the secrets vault. Applications must use the company's single sign-on provider wherever supported.

### 5.2 Passwords and passkeys

Passwords must be at least 14 characters long and must not be reused across systems. Workers should use the company password manager and, where supported, passkeys. Passwords must never be written down, shared or sent by email or chat.

### 5.3 Multi-factor authentication

MFA is required for all remote access, all administrative access, email, the code repository and any system containing Restricted data. Hardware security keys are required for production administrators and for the finance and payroll teams.

### 5.4 Privileged access

Privileged access is granted for a specific need, for a limited period, on approval by the system owner and the Security team. Privileged accounts are separate from daily-use accounts, and privileged sessions to production are logged and may be recorded. Access is reviewed every quarter.

## 6. Devices

### 6.1 Company devices

Workers must use company-issued, centrally managed endpoints for company work. These are enrolled in device management, which enforces disk encryption, screen locks after five minutes, operating system updates and endpoint detection software. Workers must not disable or tamper with these controls.

### 6.2 Personal devices

Personal phones and tablets may be used to access email, calendar and the messaging tool if they are enrolled in mobile application management, which separates company data from personal data and permits the company to wipe only company data. Personal laptops may not be used to access production systems or source code.

### 6.3 Lost or stolen devices

A worker whose device is lost, stolen or suspected to be compromised must tell the Security team immediately and in any case within one hour of noticing. The Security team will lock or wipe the device remotely.

### 6.4 Removable media

USB drives and external disks must not be connected to company endpoints unless issued by IT and encrypted. Workers must not use found media.

### 6.5 Travel

Workers traveling to countries on the Security team's high-risk list must use loaner devices, must not carry production credentials and must report any border inspection that involved their devices. Workers should avoid public Wi-Fi and use the company VPN when they cannot.

## 7. Software and Services

### 7.1 Approved software

Workers may install only software from the approved catalog. Requests for new software are submitted through the IT service desk and reviewed by the Security team within five business days. Browser extensions, plug-ins and integrations that request access to company accounts require the same review.

### 7.2 Shadow IT

Workers must not sign up for services using their company email address unless the service has been approved. The Security team scans for unsanctioned use and will contact the worker and manager if it is found.

### 7.3 Open source and developer tools

Developer tools and open source libraries must follow the Open Source Software Policy. Workers must not publish company code to public repositories without approval.

### 7.4 Generative AI tools

Workers may use only approved generative AI tools, and may not enter Restricted data or personal data into them unless the Security team and the Privacy Office have approved the use. Output must be reviewed before it is used in production or sent to a customer.

## 8. Email, Messaging and Internet Use

### 8.1 Email and messaging

Workers must use company email and the approved chat platform for business communications. Automatic forwarding of company email to personal accounts is prohibited. Messages must be professional, since they may be retained and produced in a legal matter.

### 8.2 Phishing

Workers must treat unexpected links, attachments and requests for credentials or payments with suspicion. They should use the "Report phish" button. The Security team runs phishing simulations monthly. Repeated failures lead to additional training and, in the case of privileged users, to review of access.

### 8.3 Internet use

Workers must not visit sites that are illegal, sexually explicit, hateful or used for malware distribution while using company systems or networks. Web filtering blocks known harmful categories.

### 8.4 Social media

Workers must not post anything that suggests the company has endorsed their personal views. They must not post screenshots of internal systems, code, customer data or product plans. The Code of Business Conduct sets out further rules on public statements.

## 9. Network and Physical Security

### 9.1 Network access

Only company-managed devices may connect to the corporate network. Guest Wi-Fi is provided for visitors and personal devices. Workers must not install routers, access points or network extenders.

### 9.2 Remote access

Remote access to company resources must use the zero-trust access broker, which checks the posture of the device and the identity of the worker before each session.

### 9.3 Physical access

Office access is controlled by badge. Workers must wear their badges, must not allow others to tailgate and must report lost badges at once. Server rooms are accessible only to authorized IT staff, and data center access is arranged through the cloud provider's processes.

### 9.4 Clean desk and screen

Workers must lock their screens whenever they step away and must keep papers containing sensitive information out of sight. Meeting-room whiteboards must be erased after use.

## 10. Vulnerability and Patch Management

The Security team scans systems continuously and rates findings by severity. Owners must remediate vulnerabilities within the following periods, measured from the date the fix or mitigation is available.

| Severity | Maximum time to remediate |
|---|---|
| Critical (actively exploited or internet-facing remote code execution) | 7 days |
| High | 30 days |
| Medium | 90 days |
| Low | Next maintenance cycle |

Exceptions require the written approval of the CISO and must include compensating controls and an expiry date.

## 11. Logging and Monitoring

Company systems generate logs of authentication, administrative actions, network flows and data access. The SOC monitors these logs for signs of misuse or attack. Logs are retained as set out in the Records Retention and Disposal Policy and are accessible only to authorized Security staff and Internal Audit.

## 12. Prohibited Activities

Workers must not:

- attempt to bypass, probe or disable security controls, except in sanctioned testing;
- access systems or data they are not authorized to see, even if technical controls would allow it;
- install malware, cryptocurrency miners or hacking tools;
- use company systems to harass, defame or discriminate against others;
- use company systems for outside business ventures or political fundraising;
- copy, transmit or store company data on unapproved devices or services; or
- share credentials with anyone, including IT staff and managers.

## 13. Security Awareness

All workers complete security awareness training within two weeks of joining and annually. Engineers complete secure-coding training, and administrators complete training on privileged access. The Security team publishes a monthly bulletin and runs an annual security week.

## 14. Reporting

Workers must report suspected security events, policy violations or vulnerabilities to the Security team through the security mailbox, the incident hotline or the "Report phish" button. Reports made in good faith, including about the worker's own mistakes, are welcomed and will not result in discipline. The Incident Response Policy describes what happens next.

## 15. Roles and Responsibilities

- **CISO** owns this Policy, sets technical standards, approves exceptions and reports to the Audit Committee.
- **Security team** operates monitoring, response, vulnerability management and awareness programs.
- **IT** provisions and manages endpoints, accounts and software.
- **Managers** ensure that their teams complete training, request only the access they need and remove it promptly.
- **System owners** are accountable for the security of the systems they own.
- **Workers** comply with this Policy and report anything unusual.
- **Human Resources** applies disciplinary measures with the Security team's input.

## 16. Exceptions

Requests for exceptions are submitted to the Security team with a business reason, a risk assessment and compensating controls. The CISO decides. Exceptions are time-limited, not exceeding twelve months, and are tracked in the exceptions register.

## 17. Enforcement

Violations may result in disciplinary action, up to and including termination of employment or engagement, and in serious cases referral to law enforcement. Access may be suspended pending investigation.

## Appendix A. Quick Reference for Everyday Situations

**I need to share a large file with a customer.** Use the managed file transfer service or the customer portal. Do not use consumer file-sharing services or personal email.

**I received an email from my CEO asking for gift cards.** This is a well-known scam. Do not reply. Use the "Report phish" button.

**I want to try a new browser extension that organizes my tabs.** Request it through the IT service desk. Extensions can read everything you see in the browser, including company systems.

**My laptop is running slowly and I think it has a virus.** Disconnect from Wi-Fi if you can and call the incident hotline. Do not try to clean it yourself.

**I am working from a coffee shop.** Use the company VPN or the access broker, keep your screen out of view and lock it whenever you leave the table.

**A contractor needs access to a repository for a week.** The sponsoring manager requests a time-limited account through the IT service desk. Access ends automatically on the end date.

**I found a USB drive in the car park.** Do not plug it in. Hand it to the Security team.

## Appendix B. Baseline Technical Standards

| Area | Standard |
|---|---|
| Disk encryption | Full-disk encryption on all endpoints, with recovery keys escrowed to the device management system |
| Screen lock | Five minutes of inactivity at most |
| Operating system updates | Applied within fourteen days of release; critical security updates within seven |
| Endpoint detection | Installed on all laptops and servers and reporting to the SOC |
| Session length | Single sign-on sessions expire after twelve hours; privileged sessions after one hour |
| Production access | Only through the access broker with MFA and a ticket reference |
| Secrets | Stored only in the secrets vault; never in source code, tickets or chat |
| Cloud accounts | Created only by the platform team through infrastructure as code |
| Network segmentation | Production, staging, corporate and guest networks are isolated |
| Time synchronization | All systems use the approved time sources |

## Appendix C. Account Lifecycle

When a worker joins, Human Resources creates the identity record, and the identity system provisions a baseline set of accounts. Managers request additional access through the service desk with a business reason. When a worker changes role, access is reviewed and anything not needed in the new role is removed. When a worker leaves, Human Resources triggers deprovisioning, which disables the single sign-on identity, revokes tokens, wipes enrolled personal devices of company data and recovers equipment. Accounts of departed workers are deleted ninety days later, unless a legal hold requires otherwise. Service accounts have named owners, who must confirm that they are still needed every six months.

## Appendix D. Acceptable Use of Collaboration Tools

The chat platform is for work. Workers should use channels rather than direct messages where a discussion would benefit others, avoid pasting credentials, and be mindful that messages are retained. External guests may be invited to channels only by approved administrators and only to channels designated for external collaboration. Video meetings should use waiting rooms or authenticated access when external participants are invited. Recording meetings requires the consent of the participants and is subject to local law. Recordings are stored in the approved video platform and are deleted in line with the Records Retention and Disposal Policy.

## 18. Revision History

| Version | Date | Author | Summary of change |
|---|---|---|---|
| 1.0 | January 20, 2019 | Security team | Initial issue |
| 1.6 | March 3, 2022 | Security team | Added zero-trust access and passkeys |
| 2.0 | June 6, 2023 | Security team | Added generative AI rules; revised patch timelines |
| 2.1 | February 10, 2025 | Security team | Updated personal device and travel rules |
