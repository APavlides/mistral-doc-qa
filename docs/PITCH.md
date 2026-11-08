# Pitch: Document Q&A

**One-liner:** Ask your document a question, get the answer in seconds, with its source.

**Opening question:** "How long does finding one rule in your handbook take?"

1. **Problem:** For around 300 staff, people dig through policies or email HR, and answers are slow.
2. **Solution:** Staff ask in plain words; answers come from your document.
3. **What I built:** Let me show you. *(switch to the app)*
4. **Next steps:** Today: one plain-text document. A 3-week pilot proves accuracy.
5. **Thank you:** Instant answers, always with the source.

**Demo:**
1. Paste the text below, click **Save document**.
2. Ask `How many days can I work from abroad each year?` and click **Ask**.
3. Show the answer (20 days) and **Sources**.
4. Ask `What is the dress code?`: it says the document doesn't cover it.

```
Northwind Travel – Staff Handbook (extract)

Annual leave. Full-time staff receive 25 days of paid annual leave per calendar year, plus public holidays. Up to 5 unused days may be carried over to the next year, but they must be used by 31 March. Leave requests should be submitted in the HR portal at least two weeks in advance, and are approved by your line manager.

Sick leave. If you are unwell, tell your manager before 9:30 on the first day of absence. For absences longer than 3 consecutive working days, a doctor's note is required. Sick leave is paid in full for up to 10 days per year.

Expenses. Claims must be submitted within 30 days of the purchase, with a receipt attached. Meals while travelling are reimbursed up to 40 euros per day. Taxis are reimbursed only after 21:00 or when no public transport is available.

Remote work. Staff may work from home up to 3 days per week, agreed with their manager. Working from abroad is allowed for up to 20 working days per year, and must be approved by HR at least one month before travel, because of tax and insurance rules.

Equipment. Every employee receives a laptop and headset. Lost or damaged equipment must be reported to IT within 24 hours.
```

**Likely questions:**
- *Is our data safe?* It's stored on our server and processed via Mistral's API; Mistral's open-weight models can run on your infrastructure.
- *How accurate is it?* It answers only from the 3 best passages, says when the answer isn't there, and shows sources. The pilot scores it on real questions.
- *Why Mistral?* Mistral Embed matches by meaning; Mistral Small answers fast and cheaply.
- *Does it scale?* Production adds multiple documents, PDFs and access control.

**Close:** "Can we start a 3-week pilot on your staff handbook next month?"
