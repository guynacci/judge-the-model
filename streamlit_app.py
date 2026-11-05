"""M11 clinical lead app. Every displayed numerical result comes from results/ through m11."""
import pandas as pd
import streamlit as st
import m11

st.set_page_config(page_title="Judge the Model | M11", layout="wide")
SECTIONS = ["1. Beyond Accuracy", "2. A Threshold for the Job", "3. Training vs. Test"]

@st.cache_data
def load_result(name):
    return m11.load(name)

def pct(value):
    return "undefined" if value is None else f"{value:.1%}"

def num(value):
    return "undefined" if value is None else f"{value:.3f}"

def per100(value):
    return "undefined" if value is None else f"{value:.1f}"

def matrix(c, heading="Test confusion matrix"):
    st.markdown(f"**{heading}**. Rows: actual outcome; columns: model prediction")
    data = pd.DataFrame(
        [[c["tn"], c["fp"]], [c["fn"], c["tp"]]],
        index=["Actual: no outcome", "Actual: outcome"],
        columns=["Predicted: no outcome", "Predicted: outcome"],
    )
    st.table(data)
    st.caption(
        f"Test patients: true negatives {c['tn']:,} · false positives (false alarms) {c['fp']:,} · "
        f"false negatives (missed cases) {c['fn']:,} · true positives (caught cases) {c['tp']:,}"
    )

def get_metrics(res, model, threshold):
    p, y = m11.preds(res, model, "test")
    c = m11.confusion(p, y, threshold)
    return c, m11.metrics(c)

def comparison_row(res, model, threshold):
    c, met = get_metrics(res, model, threshold)
    return {
        "Model": m11.MODEL_LABEL[model],
        "Test accuracy": pct(met["accuracy"]),
        "Test sensitivity / recall": pct(met["sensitivity"]),
        "Test specificity": pct(met["specificity"]),
        "Test FPR": pct(met["fpr"]),
        "Test precision": pct(met["precision"]),
        "Test F1": num(met["f1"]),
    }

def beyond_accuracy(res, model):
    st.write("**Clinical question:** how many actual cases does the model catch, even when accuracy looks high?")
    p, y = m11.preds(res, model, "test")
    c = m11.confusion(p, y, 0.50)
    met = m11.metrics(c)
    prevalence = met["prevalence"]
    # m11.majority_accuracy receives the true labels, as specified in its helper contract.
    baseline_acc = m11.majority_accuracy(y)
    a, b, d = st.columns(3)
    a.metric("Test prevalence", pct(prevalence), help="Of all test patients, the share who actually had the outcome")
    b.metric("Test majority-class accuracy", pct(baseline_acc), help="Accuracy if the most common outcome is predicted for everybody")
    d.metric("Selected model · Test accuracy", pct(met["accuracy"]))
    matrix(c, f"Test confusion matrix · {m11.MODEL_LABEL[model]} · threshold 0.50")
    st.subheader("What these Test metrics mean")
    st.write(f"**Sensitivity (recall): {pct(met['sensitivity'])}**. Of the Test patients **who had** the outcome, the share flagged.")
    st.write(f"**Specificity: {pct(met['specificity'])}**. Of the Test patients **who did not have** the outcome, the share not flagged.")
    st.write(f"**Precision: {pct(met['precision'])}**. Of the Test patients **flagged by this model**, the share who really had the outcome.")
    st.subheader("All five models · Test · threshold 0.50")
    st.dataframe(pd.DataFrame([comparison_row(res, k, 0.50) for k in m11.MODELS if k in res["models"]]), hide_index=True, use_container_width=True)
    st.subheader("Each model's Test confusion matrix · threshold 0.50")
    cols = st.columns(2)
    for i, k in enumerate(m11.MODELS):
        if k not in res["models"]:
            continue
        conf, _ = get_metrics(res, k, 0.50)
        with cols[i % 2]:
            st.markdown(f"**{m11.MODEL_LABEL[k]}, Test**")
            st.table(pd.DataFrame([[conf['tn'], conf['fp']], [conf['fn'], conf['tp']]], index=["Actual no", "Actual yes"], columns=["Pred no", "Pred yes"]))
    st.caption("Undefined metrics (division by zero) are displayed as 'undefined', not zero.")

def threshold_section(res, model, key):
    st.write("The threshold decides which probability counts as a positive prediction; moving it does not change the probabilities or AUROC.")
    threshold = st.slider("Decision threshold", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
    c_old, m_old = get_metrics(res, model, 0.5)
    c_new, m_new = get_metrics(res, model, threshold)
    st.subheader("Test · default versus your threshold")
    def line(label, met, c, t):
        return {"Test threshold": f"{t:.2f}", "Test caught cases (TP)": c["tp"], "Test missed cases (FN)": c["fn"], "Test false alarms (FP)": c["fp"], "Test correctly unflagged (TN)": c["tn"], "Test sensitivity": pct(met["sensitivity"]), "Test specificity": pct(met["specificity"]), "Test precision": pct(met["precision"]), "Test accuracy": pct(met["accuracy"]), "Test flagged per 100": per100(met["flagged_per_100"])}
    st.dataframe(pd.DataFrame([line("Default", m_old, c_old, 0.5), line("Chosen", m_new, c_new, threshold)]), hide_index=True, use_container_width=True)
    left, right = st.columns(2)
    with left:
        matrix(c_old, "Test · threshold 0.50")
    with right:
        matrix(c_new, f"Test · threshold {threshold:.2f}")
    diff_flagged = m_new['flagged_per_100'] - m_old['flagged_per_100']
    st.write(f"**Test trade-off:** {c_new['tp'] - c_old['tp']:+,} caught cases, {c_new['fn'] - c_old['fn']:+,} missed cases, {c_new['fp'] - c_old['fp']:+,} false alarms, and {diff_flagged:+.1f} people flagged per 100, compared with 0.50.")
    if key == "diabetes":
        st.info("Diabetes screening job: sensitivity target ≥ 90%. Compare the false alarms and follow-up workload required to meet that target.")
        if m_new["sensitivity"] is not None:
            st.write("Target reached on Test patients? **" + ("Yes" if m_new["sensitivity"] >= 0.90 else "No") + "**")
    else:
        st.info("Readmission has no fixed sensitivity target. Consider the burden of missed readmissions versus extra follow-up.")

def train_vs_test(res, model):
    st.write("Training patients were used to learn the model. Test patients were held out and better represent how it might rank new patients.")
    c1, c2 = st.columns(2)
    c1.metric("Training patients", f"{res['train']['n']:,}")
    c2.metric("Test patients", f"{res['test']['n']:,}")
    s = m11.auroc_summary(res)
    rows = [{"Model": m11.MODEL_LABEL[k], "Training AUROC": num(v["train"]), "Test AUROC": num(v["test"]), "Training − Test gap": num(v["gap"])} for k, v in s.items()]
    st.subheader("Training and Test AUROC · all models")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("AUROC measures ranking of positive versus negative patients, not classification accuracy. A large training-to-test decline can suggest overfitting.")
    if model in s:
        v = s[model]
        st.info(f"**{m11.MODEL_LABEL[model]}:** Training AUROC {num(v['train'])}; Test AUROC {num(v['test'])}; Training − Test gap {num(v['gap'])}.")

st.title("Judge the Model")
st.caption("M11 take-home activity · Decide whether a classifier fits the clinical job")
decisions = load_result("decisions") or {}
recs = decisions.get("recommendations", {})
with st.container(border=True):
    st.subheader("Clinical recommendations")
    if any(recs.values()):
        for k in m11.DATASETS:
            st.markdown(f"**{m11.DATASET_LABEL[k]}:** {recs.get(k) or 'Not written yet'}")
    else:
        st.caption("Not written yet. Add your own recommendations to DECISIONS.md, rerun python -m analysis, and publish the new results.")
section = st.sidebar.radio("App section", SECTIONS)
key = st.sidebar.selectbox("Clinical job / dataset", m11.DATASETS, format_func=lambda k: m11.DATASET_LABEL[k])
res = load_result(key)
if res is None:
    st.error("Results missing. Restore the starter's results/ or run python -m analysis.")
    st.stop()
model = st.sidebar.selectbox("Classifier", m11.MODELS, format_func=lambda k: m11.MODEL_LABEL[k] + ("" if k in res["models"] else " (not trained yet)"))
st.header(section)
st.caption(f"{m11.DATASET_LABEL[key]} · Training {res['train']['n']:,} patients, {res['train']['n_pos']:,} positive · Test {res['test']['n']:,} patients, {res['test']['n_pos']:,} positive")
if key == "readmission":
    st.write("**Positive class:** a readmission within 30 days after discharge.")
else:
    st.write("**Positive class:** diabetes by doctor diagnosis or HbA1c ≥ 6.5%; screening is meant to guide follow-up testing.")
if model not in res["models"]:
    st.warning("This model has no exported probabilities yet. First complete Before results in DECISIONS.md, then run python -m analysis.")
    st.stop()
if section == SECTIONS[0]:
    beyond_accuracy(res, model)
elif section == SECTIONS[1]:
    threshold_section(res, model, key)
else:
    train_vs_test(res, model)
