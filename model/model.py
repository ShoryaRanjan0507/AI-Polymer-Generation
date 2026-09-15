import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# 1. Load the Dataset
print("Loading dataset...")
df = pd.read_csv("polymers_descriptors.csv")

# Ensure we only use rows that actually have a SMILES string and a Tg value
df = df.dropna(subset=['SMILES', 'Tg'])

# 2. Convert SMILES to Machine-Readable Fingerprints
print("Translating SMILES to Morgan Fingerprints (This may take a minute)...")
X_list = []
y_list = []

for index, row in df.iterrows():
    smiles = row['SMILES']
    tg = row['Tg']
    
    # Let RDKit parse the SMILES
    mol = Chem.MolFromSmiles(smiles)
    
    if mol is not None:
        # Convert valid molecules into a 2048-bit array (Morgan Fingerprint)
        fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        X_list.append(np.array(fingerprint))
        y_list.append(tg)

# Convert to standard NumPy arrays for Scikit-Learn
X = np.array(X_list)
y = np.array(y_list)

print(f"Successfully processed {len(X)} valid polymer structures.")

# 3. Split the Data (80% Training, 20% Testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

# 4. Train the Random Forest Regressor
print("Training the Random Forest Regressor...")
rf_model = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)

# 5. Evaluate the Model
print("Evaluating Model Accuracy...")
y_pred = rf_model.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"R-Squared (Accuracy Score): {r2:.3f} (1.0 is perfect)")
print(f"Root Mean Square Error: {rmse:.2f} °C (Average prediction error)")

# 6. Export the Trained Model
output_filename = "tg_predictor_rf.pkl"
joblib.dump(rf_model, output_filename)
print(f"Success! Model saved to {output_filename}")