# Decisions

<!-- Fill in each section at the step the activity website gives, then commit and push.
     Write each answer after its label. Keep the headings and labels exactly as they are:
     `python -m analysis` reads them. Limit: 150 words for Before results.
     Fill in Recommendations and Design choice and AI use last, once your app is built. -->

## Before results
For each dataset: positive class; which error matters more for the job (missed positive or false alarm) and why.
- readmission:The positive class is a patient being readmitted within 30 days after discharge. I think missing an actual readmission is more serious because that patient might miss out on follow-up care that could help prevent another hospitalization.
- diabetes:The positive class is a patient who has diabetes, based on a previous diagnosis or HbA1c of at least 6.5%. I think missing someone with diabetes is more serious because they could go without additional testing or care. False alarms matter too, but those can be checked with follow-up testing.

## Recommendations
- readmission: I would prioritize a model that catches more actual readmissions instead of choosing one based only on accuracy. The baseline had 91% test accuracy but missed all 359 readmitted patients. I would not recommend using that baseline model.
- diabetes: I would prioritize sensitivity because missing someone with diabetes could delay care. I would consider a lower decision threshold to catch more patients, while making sure the number of false alarms remains manageable. I would also want to verify the model on new patients before using it clinically.

## Design choice and AI use
A few sentences each. The design choice must be your own idea, not an AI tool's.
- design choice:  I wanted the app to clearly show missed cases alongside accuracy because accuracy alone can be misleading. I think showing the actual number of patients missed makes the results easier for someone without a technical background to understand.
- AI suggestion I turned down: I built this with Atlas, my AI coding assistant, which wrote the model code, the launcher, and the app sections while I made the decisions and wrote my own answers. Its first draft used em dashes through the on-screen text, and I had them replaced with commas and periods to keep the wording plain. Its install notes also said the code could not be tested against the starter, and I did not accept that, so we ran the full check end to end before submitting, and the analysis and all three app sections passed.
