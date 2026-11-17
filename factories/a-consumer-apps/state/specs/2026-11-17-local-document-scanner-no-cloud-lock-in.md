# Spec: ScanKeep (working name) — 2026-11-17-local-document-scanner-no-cloud-lock-in

**KILLED at spec stage (2026-11-17).** The verifier could not tell it from Apple's free built-in scanner within one minute, and the scout never reviewed that incumbent. Hook is mostly absences (no account, no cloud). Also internal contradictions: the library does not survive app deletion, and the hard paywall conflicts with the sourced complaint about export behind a subscription. An iOS item in a crowded category carries 4.3(b) account risk. Reopen only with sourced evidence on Apple's scanner and a positive capability.

**Job:** Lets a person who scans paper documents with their iPhone keep every scan as an ordinary PDF in a place they can see in the Files app, with no account and no cloud upload, so the scans survive a phone change and can be sent anywhere.

**Platform:** `ios`. The job starts with the phone camera (document capture), which a web page cannot do as well, and it is done on the move. Needs a native document-camera module in an EAS build; no extra credential.

**Differentiation statement:** Unlike Adobe Scan, Genius Scan and iScanner, this app stores each scan as a plain, searchable PDF in a folder visible in the Files app and shows exactly where scans live, which matters because reviewers report forced cloud upload (Adobe Scan, 2026-10-29 "uploading to adobe cloud THAT I DO NOT WANT"), lost libraries (Genius Scan 2026-11-07 "9 years of documents gone"; Adobe Scan 2026-10-05 "I changed phones and now nothing is available"; iScanner 2026-11-13 "Product wouldnt restore after reloading app") and unclear storage and awkward export (iScanner 2026-11-05 "No ability to verify where documents are stored"; Genius Scan 2026-10-19 mail only works with iOS Mail). Source: state/scout/2026-11-17-utilities.json, util-c1 (11 dated complaints, 3 apps). Quotes spot-checked against state/scout/reviews: found in the Genius Scan, Adobe Scan and iScanner files.

**Competitor table** (URLs from the scout file; "lacks" from sampled complaints only)
| App | URL | Lacks (per reviews) |
|---|---|---|
| Adobe Scan | https://apps.apple.com/us/app/adobe-scan-pdf-doc-scanner/id1199564834 | forced account and cloud upload, library gone after phone change |
| Genius Scan | https://apps.apple.com/us/app/scanner-app-genius-scan/id377672876 | library lost after offload, email only through iOS Mail |
| iScanner | https://apps.apple.com/us/app/iscanner-pdf-document-scanner/id1040093707 | cannot verify storage location, restore failed, email and USB export awkward |
| CamScanner | https://apps.apple.com/us/app/camscanner-pdf-scanner-app/id388627783 | read by the scout, no storage or export complaint sourced for this item |
Not in the table, not sourced: Apple's own Notes and Files scanner (the scout says it did not review Apple's Files app). It is free and local, so it is the real incumbent; this is the largest demand and 4.3(b) risk and is flagged in the run report. Only four named competitors are sourced, below the five-competitor reference point; I did not pad the table.

**Core features** (at most 3)
1. Scan with the document camera (multi-page, auto-crop) and save each document as a plain PDF in a folder shown in Files under the app's name; the library rebuilds itself from that folder on any install.
2. "Where my scans are" screen: exact location, file count, total size, and a one-tap "copy everything" to any Files location or share target.
3. Export or send any scan through the system share sheet to any mail app, messaging app or Files destination, with on-device text recognition so the PDF is searchable. No account to use any of this.

**Not building:** cloud sync, accounts, e-signatures, PDF editing, ID-card templates, OCR in other languages beyond what Apple Vision provides, advanced image controls, ads.

**Running cost:** no hosted AI and no server. Per-subscriber cost is the RevenueCat and store share only. No Supabase project needed beyond optional anonymous crash logs (none planned).

**Monetisation:** hard paywall after onboarding has shown a real scan saved and visible in Files. 7-day trial (reference default). Proposed price $3.99/month, an intention only. Competitor prices are not in the scout file (the scout recorded only that price complaints dominate), so the demand-test stage must read them from the store pages before the page shows a price. Nothing charged at the concept stage.

**How buyers find it:** ad angle "Your scans stay on your phone, as plain PDFs you can open in Files." Concept stage only.

**Target market:** United States first. The research notes say median payer value is higher in North America than elsewhere; the scout file contains no regional figure, so this is an assumption, not evidence.

**Demand test plan**
- Page promise: "Scan it. Keep it. No account, no cloud." Concept page, "in development / early access", nothing charged.
- 6 post angles: (1) "where did my scans go" after a phone upgrade; (2) forced sign-in at the first scan; (3) show a folder of plain PDFs in Files; (4) email a scan from a non-Apple mail app; (5) offload or reinstall: the folder is still there; (6) a before-you-switch-phones checklist for scans.

**Review risk (iOS):** 4.3(b), a crowded category with free native alternatives, so the Files-folder and rebuild-from-folder behaviour must be visible in onboarding; 5.1.1 camera permission text; 3.1.2 subscription terms visible before purchase; 2.1 completeness (a scanner that crashes on long documents is a known complaint class, util-c2). Do not claim data safety beyond what the build shows. Deleting the app removes its On My iPhone folder, so the app must prompt a copy-out; the spec must not promise survival of app deletion.

**Claims** (each needs evidence from the shipped build)
- "Your scans are ordinary PDFs in the Files app." — open the folder in Files on a device.
- "Works without an account." — complete a scan and export with no sign-in.
- "Reinstall the app and your library comes back." — only true if the folder survives the test (offload yes, delete no); evidence required before use.
- "Scans are not uploaded." — inspect network traffic during a scan; the purchase call to RevenueCat is separate and disclosed.
