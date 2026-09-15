import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

print("Loading TgSS_enriched_cleaned.csv...")
try:
    df = pd.read_csv("TgSS_enriched_cleaned.csv")
    df = df.dropna(subset=['SMILES', 'Tg'])
except FileNotFoundError:
    print("Error: Could not find TgSS_enriched_cleaned.csv!")
    exit()

tensile_list = []
modulus_list = []

print("Simulating realistic mechanical properties using RDKit chemistry rules...")
for index, row in df.iterrows():
    smiles = str(row['SMILES'])
    tg = row['Tg']
    mol = Chem.MolFromSmiles(smiles)
    
    if mol is not None:
        # Chemical Features
        mol_wt = Descriptors.MolWt(mol)
        aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
        rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
        
        # Synthetic Tensile Strength (MPa)
        # Base of 30, increases with weight and aromatic rigidity, decreases with flexibility
        tensile = 30.0 + (mol_wt * 0.05) + (aromatic_rings * 15.0) - (rotatable_bonds * 2.0)
        
        # Scale based on Tg (High Tg usually correlates with higher strength)
        tensile = tensile + (tg * 0.1)
        
        # Synthetic Elastic Modulus (GPa)
        # Base of 1.0, scales up with rigidity
        modulus = 1.0 + (aromatic_rings * 0.8) + (tg * 0.005) - (rotatable_bonds * 0.05)
        
        # Add a tiny bit of random noise for realism
        tensile = max(5.0, tensile * np.random.uniform(0.9, 1.1))
        modulus = max(0.1, modulus * np.random.uniform(0.9, 1.1))
        
        tensile_list.append(round(tensile, 2))
        modulus_list.append(round(modulus, 2))
    else:
        tensile_list.append(None)
        modulus_list.append(None)

# Add the new columns to the dataframe
df['Tensile_Strength'] = tensile_list
df['Elastic_Modulus'] = modulus_list

# Drop any rows where RDKit failed
df = df.dropna(subset=['Tensile_Strength', 'Elastic_Modulus'])

# Save the final master dataset
output_filename = "polymer_master_data.csv"
df.to_csv(output_filename, index=False)

print(f"\nSuccess! Generated '{output_filename}' with {len(df)} rows.")
print("Columns ready for Multi-Model Training: 'SMILES', 'Tg', 'Tensile_Strength', 'Elastic_Modulus'")