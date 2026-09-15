import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator, Descriptors, rdMolDescriptors
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# 1. Load the New Diverse Dataset
print("Loading diverse dataset...")
df = pd.read_csv("TgSS_enriched_cleaned.csv")

# Only drop rows missing the SMILES or Tg columns
df = df.dropna(subset=['SMILES', 'Tg'])

# 2. Extract Features (Fingerprints + On-the-fly Descriptors)
print("Translating SMILES and calculating physical traits dynamically (This may take a minute)...")
mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

X_list = []
y_list = []

for index, row in df.iterrows():
    smiles = row['SMILES']
    tg = row['Tg']
    mol = Chem.MolFromSmiles(str(smiles))
    
    if mol is not None:
        # Get structural fingerprint (2048 binary values)
        fingerprint = list(mfpgen.GetFingerprint(mol))
        
        # Calculate physical descriptors dynamically from the molecule
        mol_wt = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
        
        physical_traits = [mol_wt, logp, tpsa, hbd, hba, rotatable]
        
        # Fuse them together into one massive feature array (2054 values)
        combined_features = fingerprint + physical_traits
        
        X_list.append(combined_features)
        y_list.append(tg)

X = np.array(X_list)
y = np.array(y_list)

print(f"Successfully fused {X.shape[1]} features for {len(X)} valid polymers.")

# 3. Split the Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

# 4. Train the Gradient Boosting Regressor
print("Training the HistGradientBoosting Regressor...")
gb_model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.1, random_state=42)
gb_model.fit(X_train, y_train)

# 5. Evaluate the Model
print("Evaluating Model Accuracy...")
y_pred = gb_model.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"R-Squared (Accuracy Score): {r2:.3f}")
print(f"Root Mean Square Error: {rmse:.2f} °C")

# 6. Export the Trained Model
output_filename = "tg_predictor_gb.pkl"
joblib.dump(gb_model, output_filename)
print(f"Success! Unbiased model saved to {output_filename}")