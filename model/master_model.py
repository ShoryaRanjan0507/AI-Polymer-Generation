import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator, Descriptors, rdMolDescriptors
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
import joblib

# 1. Load your new synthetic master dataset
print("Loading polymer_master_data.csv...")
df = pd.read_csv("polymer_master_data.csv")

# 2. Define the properties we want to train AI for, and their output file names
target_properties = {
    "Tg": "tg_predictor_gb.pkl",
    "Tensile_Strength": "tensile_predictor_gb.pkl",
    "Elastic_Modulus": "modulus_predictor_gb.pkl"
}

mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

# 3. Train a dedicated AI for each physical property
for property_name, filename in target_properties.items():
    print(f"\n--- Training AI Model for {property_name} ---")
    
    X_list = []
    y_list = []
    
    for index, row in df.iterrows():
        mol = Chem.MolFromSmiles(str(row['SMILES']))
        if mol is not None:
            fingerprint = list(mfpgen.GetFingerprint(mol))
            
            # Calculate physical traits
            mol_wt = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            tpsa = Descriptors.TPSA(mol)
            hbd = rdMolDescriptors.CalcNumHBD(mol)
            hba = rdMolDescriptors.CalcNumHBA(mol)
            rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
            
            physical_traits = [mol_wt, logp, tpsa, hbd, hba, rotatable]
            X_list.append(fingerprint + physical_traits)
            y_list.append(row[property_name])
            
    X = np.array(X_list)
    y = np.array(y_list)
    
    # Split data and train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    gb_model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.1, random_state=42)
    gb_model.fit(X_train, y_train)
    
    # Check accuracy and save
    score = gb_model.score(X_test, y_test)
    print(f"Accuracy (R-Squared) for {property_name}: {score:.3f}")
    
    joblib.dump(gb_model, filename)
    print(f"Saved model to: {filename}")