import streamlit as st
import joblib
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

# ==================== CONFIG ====================
MODEL_PATH = "models/lightgbm_model.pkl"
X_TRAIN_PATH = "data/processed/X_train.pkl"
X_TEST_PATH = "data/processed/X_test.pkl"
Y_TRAIN_PATH = "data/processed/y_train.pkl"

# THRESHOLD CONFIGURATION
APPROVAL_THRESHOLD = 0.65  # 65% repayment probability required for approval

st.set_page_config(
    page_title="Credit Decision Support",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1f2937; }
    .sub-header { font-size: 1.1rem; color: #6b7280; margin-bottom: 1.5rem; }
    .prediction-box { 
        padding: 2rem; border-radius: 16px; 
        color: white; text-align: center; margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    .prediction-value { font-size: 3rem; font-weight: 800; }
    .feature-card { 
        background: #f9fafb; padding: 1rem; border-radius: 8px;
        border-left: 4px solid #667eea; margin: 0.5rem 0;
    }
    .metric-box {
        background: white; padding: 1.5rem; border-radius: 12px;
        border: 1px solid #e5e7eb; text-align: center;
    }
    .threshold-box {
        background: #f3f4f6; padding: 1rem; border-radius: 8px;
        text-align: center; border: 2px dashed #9ca3af; margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .stTabs [data-baseweb="tab"] { font-size: 1rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==================== LOAD RESOURCES ====================
@st.cache_resource
def load_resources():
    resources = {"model": None, "X_train": None, "X_test": None, "y_train": None, "feature_names": None, "is_classifier": False, "error": None}
    
    if os.path.exists(MODEL_PATH):
        try:
            resources["model"] = joblib.load(MODEL_PATH)
            if hasattr(resources["model"], "predict_proba"):
                resources["is_classifier"] = True
            elif hasattr(resources["model"], "classes_"):
                resources["is_classifier"] = True
        except Exception as e:
            resources["error"] = f"Model load error: {e}"
    else:
        resources["error"] = f"Model not found at `{MODEL_PATH}`"
    
    for path, key in [(X_TRAIN_PATH, "X_train"), (X_TEST_PATH, "X_test"), (Y_TRAIN_PATH, "y_train")]:
        if os.path.exists(path):
            try:
                resources[key] = joblib.load(path)
            except:
                pass
    
    if resources["X_train"] is not None:
        if isinstance(resources["X_train"], pd.DataFrame):
            resources["feature_names"] = list(resources["X_train"].columns)
        elif isinstance(resources["X_train"], np.ndarray):
            resources["feature_names"] = [f"feature_{i}" for i in range(resources["X_train"].shape[1])]
    elif resources["X_test"] is not None:
        if isinstance(resources["X_test"], pd.DataFrame):
            resources["feature_names"] = list(resources["X_test"].columns)
        elif isinstance(resources["X_test"], np.ndarray):
            resources["feature_names"] = [f"feature_{i}" for i in range(resources["X_test"].shape[1])]
    
    return resources

resources = load_resources()
model = resources["model"]
feature_names = resources["feature_names"]
X_train = resources["X_train"]
X_test = resources["X_test"]
y_train = resources["y_train"]
is_classifier = resources["is_classifier"]

# ==================== HEADER ====================
st.markdown('<p class="main-header">💳 Intelligent Credit Decision Support</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered credit risk prediction with full explainability</p>', unsafe_allow_html=True)

if resources.get("error"):
    st.error(f"⚠️ {resources['error']}")
    st.info("The app is running in **demo mode**. Upload your model/training data to enable predictions.")

# ==================== HELPER: BUILD INPUTS ====================
def build_input_form(features, train_df=None):
    inputs = {}
    
    financial_keywords = ["income", "amount", "loan", "debt", "dti", "ratio", "interest", "rate", "payment", "installment", "annual", "monthly"]
    credit_keywords = ["credit", "score", "delinq", "inq", "bankrupt", "tax", "lien", "pub", "record", "derog", "default"]
    personal_keywords = ["emp", "home", "own", "rent", "verif", "purpose", "term", "grade", "sub", "addr", "zip", "state"]
    
    financial = [f for f in features if any(k in f.lower() for k in financial_keywords)]
    credit = [f for f in features if any(k in f.lower() for k in credit_keywords)]
    personal = [f for f in features if any(k in f.lower() for k in personal_keywords)]
    other = [f for f in features if f not in financial + credit + personal]
    
    def get_default(f, train_df):
        if train_df is not None and f in train_df.columns:
            col = train_df[f]
            if pd.api.types.is_numeric_dtype(col):
                return col.median()
            else:
                return col.mode()[0] if len(col.mode()) > 0 else col.iloc[0]
        return 0
    
    def get_range(f, train_df):
        if train_df is not None and f in train_df.columns:
            col = train_df[f].dropna()
            if pd.api.types.is_numeric_dtype(col):
                return float(col.min()), float(col.max()), float(col.median())
        return 0.0, 1000000.0, 0.0
    
    with st.sidebar:
        st.header("📝 Applicant Details")
        
        if financial:
            with st.expander("💰 Financial Info", expanded=True):
                for f in financial:
                    mn, mx, md = get_range(f, train_df)
                    if any(k in f.lower() for k in ["ratio", "rate", "interest"]):
                        inputs[f] = st.slider(f.replace("_", " ").title(), float(max(0, mn)), float(min(1, mx)), float(md), 0.01, key=f"fin_{f}")
                    else:
                        inputs[f] = st.number_input(f.replace("_", " ").title(), float(max(0, mn)), float(mx), float(md), step=1000.0, key=f"fin_{f}")
        
        if credit:
            with st.expander("📊 Credit Profile", expanded=True):
                for f in credit:
                    mn, mx, md = get_range(f, train_df)
                    if "score" in f.lower():
                        inputs[f] = st.slider(f.replace("_", " ").title(), 300, 850, int(md), key=f"cred_{f}")
                    else:
                        inputs[f] = st.number_input(f.replace("_", " ").title(), int(max(0, mn)), int(mx), int(md), key=f"cred_{f}")
        
        if personal:
            with st.expander("🏠 Personal Info", expanded=False):
                for f in personal:
                    if train_df is not None and f in train_df.columns and not pd.api.types.is_numeric_dtype(train_df[f]):
                        options = train_df[f].dropna().unique().tolist()
                        inputs[f] = st.selectbox(f.replace("_", " ").title(), options, key=f"per_{f}")
                    else:
                        mn, mx, md = get_range(f, train_df)
                        inputs[f] = st.number_input(f.replace("_", " ").title(), float(mn), float(mx), float(md), key=f"per_{f}")
        
        if other:
            with st.expander("🔧 Other Features", expanded=False):
                for f in other:
                    mn, mx, md = get_range(f, train_df)
                    inputs[f] = st.number_input(f.replace("_", " ").title(), float(mn), float(mx), float(md), key=f"oth_{f}")
        
        st.markdown("---")
        predict_btn = st.button("🔮 Predict", type="primary", width="stretch")
    
    return inputs, predict_btn

# ==================== BUILD INPUTS ====================
if feature_names:
    train_df = X_train if isinstance(X_train, pd.DataFrame) else None
    inputs, predict_btn = build_input_form(feature_names, train_df)
    input_df = pd.DataFrame([inputs])
else:
    st.sidebar.header("📝 Applicant Details")
    with st.sidebar.expander("💰 Financial Info", expanded=True):
        annual_income = st.number_input("Annual Income", 0, 5000000, 50000, 1000)
        loan_amount = st.number_input("Loan Amount", 0, 2000000, 10000, 500)
    predict_btn = st.sidebar.button("🔮 Predict", type="primary", width="stretch")
    input_df = pd.DataFrame([{"annual_income": annual_income, "loan_amount": loan_amount}])
    feature_names = list(input_df.columns)

# ==================== TABS ====================
tab1, tab2, tab3 = st.tabs(["📊 Prediction", "🔍 SHAP Explainability", "📈 Feature Importance"])

# ==================== TAB 1: PREDICTION ====================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📋 Input Summary")
        display_df = input_df.T.rename(columns={0: "Value"})
        display_df.index.name = "Feature"
        st.dataframe(display_df, width="stretch")
    
    with col2:
        if predict_btn:
            if model is None:
                st.error("❌ Model not loaded. Cannot make predictions.")
            else:
                with st.spinner("Running prediction..."):
                    try:
                        if feature_names and hasattr(model, "feature_name_"):
                            try:
                                model_features = model.feature_name_
                                input_df = input_df[model_features]
                            except:
                                pass
                        elif feature_names:
                            input_df = input_df[feature_names]
                        
                        prediction = model.predict(input_df)[0]
                        
                        if is_classifier:
                            proba = model.predict_proba(input_df)[0]
                            
                            if hasattr(model, "classes_"):
                                classes = model.classes_
                            else:
                                classes = [0, 1]
                            
                            if len(classes) == 2:
                                pos_idx = 1
                                neg_idx = 0
                                repayment_prob = proba[pos_idx]
                                default_prob = proba[neg_idx]
                                
                                # THRESHOLD LOGIC: Approve only if repayment probability >= 65%
                                is_approved = repayment_prob >= APPROVAL_THRESHOLD
                                
                                if is_approved:
                                    st.markdown(
                                        f'''<div class="prediction-box" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                                        <div style="font-size: 1.3rem; font-weight: 600;">✅ APPROVED</div>
                                        <div class="prediction-value">{repayment_prob*100:.1f}%</div>
                                        <div style="font-size: 0.95rem; opacity: 0.9; margin-top: 0.5rem;">Repayment Probability</div>
                                        </div>''', unsafe_allow_html=True
                                    )
                                else:
                                    st.markdown(
                                        f'''<div class="prediction-box" style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);">
                                        <div style="font-size: 1.3rem; font-weight: 600;">❌ REJECTED</div>
                                        <div class="prediction-value">{repayment_prob*100:.1f}%</div>
                                        <div style="font-size: 0.95rem; opacity: 0.9; margin-top: 0.5rem;">Repayment Probability (Below {APPROVAL_THRESHOLD*100:.0f}% Threshold)</div>
                                        </div>''', unsafe_allow_html=True
                                    )
                                
                                # Threshold indicator
                                st.markdown(
                                    f'''<div class="threshold-box">
                                    <div style="font-size: 0.9rem; color: #6b7280;">Decision Threshold</div>
                                    <div style="font-size: 1.2rem; font-weight: 700; color: #374151;">Approve if repayment probability ≥ {APPROVAL_THRESHOLD*100:.0f}%</div>
                                    </div>''', unsafe_allow_html=True
                                )
                                
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f'''<div class="metric-box"><div style="color:#6b7280;font-size:0.9rem;">Repayment Probability</div><div style="font-size:1.8rem;font-weight:700;color:#11998e;">{repayment_prob*100:.2f}%</div></div>''', unsafe_allow_html=True)
                                with c2:
                                    st.markdown(f'''<div class="metric-box"><div style="color:#6b7280;font-size:0.9rem;">Default Probability</div><div style="font-size:1.8rem;font-weight:700;color:#eb3349;">{default_prob*100:.2f}%</div></div>''', unsafe_allow_html=True)
                            else:
                                st.markdown(f'''<div class="prediction-box"><div>Predicted Class: {prediction}</div></div>''', unsafe_allow_html=True)
                                st.bar_chart(pd.Series(proba, index=[str(c) for c in classes]))
                        else:
                            st.markdown(
                                f'''<div class="prediction-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                                <div style="font-size: 1.3rem; font-weight: 600;">📊 Predicted Value</div>
                                <div class="prediction-value">{prediction:,.2f}</div>
                                </div>''', unsafe_allow_html=True
                            )
                            
                    except Exception as e:
                        st.error(f"Prediction failed: {e}")
                        st.info("Ensure input features match the model training exactly (order, names, types).")
        else:
            st.info("👈 Fill in the applicant details and click **Predict** to see results.")

# ==================== TAB 2: SHAP ====================
with tab2:
    st.markdown("### 🔍 SHAP Explainability")
    st.markdown("Understand *why* the model made this decision — which features pushed the prediction up or down.")
    
    if predict_btn and model is not None:
        try:
            import shap
            import matplotlib.pyplot as plt
            
            with st.spinner("Computing SHAP values..."):
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(input_df)
                
                if isinstance(shap_values, list):
                    if is_classifier and len(shap_values) == 2:
                        pred_class = model.predict(input_df)[0]
                        if hasattr(model, "classes_"):
                            class_idx = list(model.classes_).index(pred_class)
                        else:
                            class_idx = int(pred_class) if pred_class in [0, 1] else 1
                        sv = shap_values[class_idx]
                        base_val = explainer.expected_value[class_idx] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value
                    else:
                        sv = shap_values[0]
                        base_val = explainer.expected_value[0] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value
                else:
                    sv = shap_values
                    base_val = explainer.expected_value
                
                col_shap1, col_shap2 = st.columns(2)
                
                with col_shap1:
                    st.markdown("#### Waterfall Plot")
                    fig, ax = plt.subplots(figsize=(10, 7))
                    shap.waterfall_plot(shap.Explanation(
                        values=sv[0],
                        base_values=base_val,
                        data=input_df.iloc[0].values,
                        feature_names=input_df.columns.tolist()
                    ), show=False)
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                    plt.close()
                
                with col_shap2:
                    st.markdown("#### Force Plot")
                    fig, ax = plt.subplots(figsize=(10, 4))
                    shap.force_plot(base_val, sv[0], input_df.iloc[0].values,
                                   feature_names=input_df.columns.tolist(), matplotlib=True, show=False)
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                    plt.close()
                
                st.markdown("#### Feature Impact Breakdown")
                shap_df = pd.DataFrame({
                    "Feature": input_df.columns,
                    "Input Value": input_df.iloc[0].values,
                    "SHAP Impact": sv[0]
                }).sort_values("SHAP Impact", key=abs, ascending=False)
                
                def color_shap(val):
                    return "background-color: #dcfce7" if val > 0 else "background-color: #fee2e2"
                
                st.dataframe(shap_df.style.applymap(color_shap, subset=["SHAP Impact"]), width="stretch")
                
        except ImportError:
            st.error("SHAP not installed. Run: `pip install shap`")
        except Exception as e:
            st.error(f"SHAP computation failed: {e}")
            st.info("Some models need special handling. Ensure your model is a tree-based model (LightGBM, XGBoost, etc.).")
    else:
        st.info("Run a prediction first to see SHAP explanations.")

# ==================== TAB 3: FEATURE IMPORTANCE ====================
with tab3:
    st.markdown("### 📈 Global Feature Importance")
    st.markdown("How much each feature contributes to the model overall.")
    
    if model is not None:
        try:
            if hasattr(model, "feature_importances_"):
                importance = model.feature_importances_
                imp_type = "Built-in Importance"
            elif hasattr(model, "booster_"):
                importance = model.booster_.feature_importance(importance_type="gain")
                imp_type = "Gain-based Importance"
            elif hasattr(model, "feature_importances"):
                importance = model.feature_importances
                imp_type = "Feature Importance"
            else:
                importance = None
            
            if importance is not None and feature_names:
                n_feats = len(feature_names)
                if len(importance) > n_feats:
                    importance = importance[:n_feats]
                elif len(importance) < n_feats:
                    importance = np.pad(importance, (0, n_feats - len(importance)))
                
                imp_df = pd.DataFrame({
                    "Feature": feature_names,
                    "Importance": importance
                }).sort_values("Importance", ascending=True)
                
                col_imp1, col_imp2 = st.columns([2, 1])
                
                with col_imp1:
                    try:
                        import plotly.express as px
                        fig = px.bar(
                            imp_df, x="Importance", y="Feature", orientation="h",
                            color="Importance", color_continuous_scale="Viridis",
                            title=f"Feature Importance ({imp_type})"
                        )
                        fig.update_layout(height=600, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        st.bar_chart(imp_df.set_index("Feature")["Importance"])
                
                with col_imp2:
                    st.markdown("#### Top 5 Features")
                    for idx, row in imp_df.tail(5).iloc[::-1].iterrows():
                        st.markdown(
                            f'''<div class="feature-card">
                            <strong>{row["Feature"]}</strong><br/>
                            <span style="color: #667eea; font-size: 1.3rem; font-weight: 700;">{row["Importance"]:.4f}</span>
                            </div>''', unsafe_allow_html=True
                        )
            else:
                st.warning("Could not extract feature importance from this model.")
                
        except Exception as e:
            st.error(f"Feature importance failed: {e}")
    else:
        st.warning("Model not loaded. Cannot show feature importance.")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("Built with Streamlit • SHAP • LightGBM | Intelligent Credit Decision Support")