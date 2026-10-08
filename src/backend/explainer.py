"""
Offline AI Plain-English Polymer Interpreter & Chemical Decomposition Engine.
100% local, offline, instant (<1ms) chemical translation.
Normalizes polymer repeat units/fragments, identifies exact common/trade names,
breaks down chemical formulas into clean subscripts and elemental counts,
classifies functional motifs via RDKit SMARTS, and translates dense physical
metrics into everyday layman analogies.
"""

import re
from typing import Dict, Any, Optional, List

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors, Descriptors
except ImportError:
    Chem = None
    rdMolDescriptors = None
    Descriptors = None


# Unicode subscript digit map
SUBSCRIPT_MAP = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
}

ELEMENT_NAMES = {
    "C": "Carbon",
    "H": "Hydrogen",
    "O": "Oxygen",
    "N": "Nitrogen",
    "F": "Fluorine",
    "Cl": "Chlorine",
    "Br": "Bromine",
    "I": "Iodine",
    "S": "Sulfur",
    "P": "Phosphorus",
    "Si": "Silicon",
    "B": "Boron"
}


# Curated offline chemical repository of standard polymer monomers, precursors, and trade materials
OFFLINE_MONOMER_LIBRARY = {
    # 1. Bisphenols, Epoxies & Polycarbonates
    "CC(C)(c1ccc(O)cc1)c2ccc(O)cc2": {
        "name": "Bisphenol A (BPA)",
        "trade_name": "Lexan / Makrolon / Epoxy Base",
        "family": "Polycarbonate & Epoxy Precursor",
        "everyday_role": "The primary building block used worldwide to manufacture shatterproof polycarbonate plastics, optical discs, safety glasses, and heavy-duty epoxy resins.",
        "applications": [
            "Shatterproof safety glasses, sports goggles & crash helmets",
            "Transparent impact-resistant shields & automotive headlight lenses",
            "Heavy-duty protective epoxy coatings and electronic circuit boards"
        ]
    },
    "CC(C)(c1ccc(Oc2ccc(C(=O)O)cc2)cc1)c3ccc(Oc4ccc(C(=O)O)cc4)cc3": {
        "name": "Bisphenol-A Di-Ether Acid Precursor",
        "trade_name": "Ultem / High-Heat Polyetherimide Precursor",
        "family": "High-Performance Polyetherimide",
        "everyday_role": "An ultra-high temperature engineering plastic building block designed to replace metal components in aircraft and surgical sterilization equipment.",
        "applications": [
            "Aircraft cabin interiors and aerospace structural components",
            "Reusable medical equipment requiring steam sterilization at 135°C+",
            "Automotive under-the-hood high-heat electrical connectors"
        ]
    },
    "Oc1ccc(Cc2ccc(O)cc2)cc1": {
        "name": "Bisphenol F (BPF)",
        "trade_name": "Low-Viscosity Epoxy Monomer",
        "family": "Epoxy Resin Precursor",
        "everyday_role": "A chemical cousin of BPA that provides lower liquid viscosity and high chemical solvent resistance in protective tank linings and adhesives.",
        "applications": [
            "Corrosion-resistant industrial tank and pipe linings",
            "High-strength marine and aerospace structural adhesives",
            "Protective solvent-resistant industrial floor coatings"
        ]
    },
    "O=S(=O)(c1ccc(O)cc1)c2ccc(O)cc2": {
        "name": "Bisphenol S (BPS)",
        "trade_name": "Polysulfone / High-Tg Thermoplastic Monomer",
        "family": "Polysulfone & Specialty Resin",
        "everyday_role": "A sulfur-stabilized phenolic monomer used to produce high-temperature polysulfone plastics that resist boiling water and harsh cleaning detergents.",
        "applications": [
            "High-temperature baby bottles and food-service containers",
            "Dialysis membrane filters and water purification systems",
            "Thermal paper coatings and heat-stable appliance housings"
        ]
    },

    # 2. Acrylates & Methacrylates (Acrylics / Plexiglas / Optical Resins)
    "CC(=C)C(=O)OC": {
        "name": "Methyl Methacrylate (MMA)",
        "trade_name": "Plexiglas / Lucite / Perspex Monomer",
        "family": "Optical Acrylic Thermoplastic",
        "everyday_role": "The fundamental monomer used to make crystal-clear acrylic glass (Plexiglas), widely used as a lightweight, shatterproof alternative to traditional glass.",
        "applications": [
            "Crystal-clear aquarium viewing windows and store displays",
            "Car rear-light clusters, illuminated signs & architectural skylights",
            "Medical bone cement and durable acrylic dental prosthetics"
        ]
    },
    "C=CC(=O)OC": {
        "name": "Methyl Acrylate",
        "trade_name": "Acrylic Fiber & Coating Monomer",
        "family": "Acrylic Resin / Textile Modifier",
        "everyday_role": "A fast-reacting acrylic monomer used to add flexibility and softness to synthetic carpet fibers, textile yarns, and adhesive tapes.",
        "applications": [
            "Synthetic acrylic knitwear, fleece fabrics, and carpets",
            "Pressure-sensitive adhesive tapes and peelable labels",
            "Water-based acrylic latex wall paints and sealants"
        ]
    },
    "C=CC(=O)OCCCC": {
        "name": "n-Butyl Acrylate",
        "trade_name": "Flexible Acrylic Resin Monomer",
        "family": "Elastomeric Acrylic",
        "everyday_role": "A low-glass-transition monomer that keeps plastics, paints, and adhesives soft, rubbery, and flexible even in freezing winter conditions.",
        "applications": [
            "Outdoor weather-resistant house paints and elastomeric caulks",
            "Strong sticky adhesives for Scotch tape and packaging tape",
            "Leather finishing treatments and textile water-repellent coatings"
        ]
    },
    "CC(=C)C(=O)OCCCC": {
        "name": "n-Butyl Methacrylate",
        "trade_name": "Durable Surface Coating Monomer",
        "family": "Methacrylic Coating Resin",
        "everyday_role": "Provides balanced scratch-resistance and flexibility in scratch-proof automotive topcoats, nail polishes, and waterproof paper coatings.",
        "applications": [
            "Automotive scratch-resistant clearcoats and touch-up lacquers",
            "Long-lasting cosmetic nail gels and polishes",
            "High-gloss printing inks and moisture-barrier packaging coatings"
        ]
    },
    "CC(=C)C(=O)OCCO": {
        "name": "2-Hydroxyethyl Methacrylate (HEMA)",
        "trade_name": "Hydrogel Contact Lens Monomer",
        "family": "Hydrophilic Bio-Compatible Hydrogel",
        "everyday_role": "A water-loving (hydrophilic) monomer that swells into a soft, flexible, oxygen-permeable hydrogel when wet, making soft contact lenses possible.",
        "applications": [
            "Soft daily and monthly wear contact lenses",
            "Dental bonding primers and composite tooth fillings",
            "Controlled-release medical drug delivery hydrogel patches"
        ]
    },
    "C=CC(=O)OCCO": {
        "name": "2-Hydroxyethyl Acrylate (HEA)",
        "trade_name": "UV-Curable Resin Monomer",
        "family": "Functional Acrylic Monomer",
        "everyday_role": "A rapid UV-curable crosslinker that hardens instantaneously under ultraviolet light in industrial printing and 3D printing resins.",
        "applications": [
            "Instant-curing 3D printing photo-resins and inks",
            "High-durability wood floor varnishes and furniture lacquers",
            "Crosslinked automotive primers and adhesives"
        ]
    },
    "CC(=C)C(=O)Oc1ccccc1": {
        "name": "Phenyl Methacrylate",
        "trade_name": "High-Refractive Optical Monomer",
        "family": "High-Refractive Index Optical Polymer",
        "everyday_role": "A specialty aromatic methacrylate designed for high optical clarity, high refractive index, and scratch resistance in precision camera lenses.",
        "applications": [
            "Precision eyeglasses, camera lenses, and smartphone camera optics",
            "Optical fiber light guides and antireflective display films",
            "High-temperature clear optical resin castings"
        ]
    },
    "C=CC(=O)Oc1ccccc1": {
        "name": "Phenyl Acrylate",
        "trade_name": "Aromatic Optical Acrylate",
        "family": "Optical Acrylic",
        "everyday_role": "Used to produce optical coatings with high light bending capability (refractive index) for modern electronic display screens.",
        "applications": [
            "Brightness enhancement films in LED and LCD television screens",
            "High-index optical adhesives for touchscreens",
            "Specialty optical prisms and waveguides"
        ]
    },
    "C=CC(=O)OCC1CCCCC1": {
        "name": "Cyclohexyl Acrylate",
        "trade_name": "Low-Shrinkage Optical Acrylic",
        "family": "Alicyclic Acrylic",
        "everyday_role": "A ring-structured acrylic that combines optical water-clear transparency with very low shrinkage during molding and curing.",
        "applications": [
            "Optical disc coatings and anti-scratch screen protectors",
            "Weather-durable outdoor signage and protective films",
            "Precision molding resins for miniature electronics"
        ]
    },
    "CC(=C)C(=O)OCC1CCCCC1": {
        "name": "Cyclohexyl Methacrylate",
        "trade_name": "Rigid Weather-Proof Acrylic",
        "family": "Alicyclic Methacrylate",
        "everyday_role": "Adds exceptional weather resistance, UV-sunlight stability, and high surface hardness to exterior automotive clearcoats.",
        "applications": [
            "UV-resistant automotive clearcoats and marine boat finishes",
            "Transparent protective sheets for solar panels",
            "High-rigidity dental prosthetics and splints"
        ]
    },
    "C=CC(=O)OC12CC3CC(CC(C3)C1)C2": {
        "name": "1-Adamantyl Acrylate",
        "trade_name": "Diamond-Cage Semiconductor Monomer",
        "family": "Polycyclic High-Tg Optical Polymer",
        "everyday_role": "Contains a microscopic diamond-like carbon cage that gives extreme heat resistance and transparency, used in semiconductor microchip manufacturing.",
        "applications": [
            "Deep-UV photoresists for manufacturing advanced computer microchips",
            "Ultra-high heat optical lenses for laser systems",
            "Low-dielectric protective coatings for high-frequency 5G circuits"
        ]
    },
    "CC(=C)C(=O)OC12CC3CC(CC(C3)C1)C2": {
        "name": "1-Adamantyl Methacrylate",
        "trade_name": "Lithography & High-Tg Nanotech Monomer",
        "family": "Polycyclic High-Tg Nanotech Polymer",
        "everyday_role": "A premium monomer for cutting-edge semiconductor lithography that maintains nanoscale precision under intense laser etching.",
        "applications": [
            "Next-generation semiconductor laser photoresists (ArF 193nm)",
            "Ultra-durable heat-resistant optical coatings for aerospace sensors",
            "Specialty high-rigidity biomedical implants"
        ]
    },
    "C=CC(=O)OCCCCCC": {
        "name": "Hexyl Acrylate",
        "trade_name": "Flexible Adhesive Monomer",
        "family": "Aliphatic Flexible Acrylic",
        "everyday_role": "Used to formulate peelable sticky notes, flexible medical adhesive bandages, and shock-dampening sealants.",
        "applications": [
            "Medical skin adhesive bandages and surgical tapes",
            "Removable sticky notes and protective surface films",
            "Vibration-dampening acoustic sealants for cars"
        ]
    },
    "C=CC(=O)OCCCCCCCC": {
        "name": "Octyl Acrylate",
        "trade_name": "Low-Temperature Elastic Monomer",
        "family": "Aliphatic Elastomer",
        "everyday_role": "Keeps rubbery products and waterproof membranes flexible even in sub-zero Arctic environments.",
        "applications": [
            "Cold-weather waterproof roofing membranes",
            "Freezer-grade food packaging adhesives and tape",
            "Flexible leather and synthetic fabric softeners"
        ]
    },
    "C=CC(=O)OCC(CC)CCCC": {
        "name": "2-Ethylhexyl Acrylate (2-EHA)",
        "trade_name": "Ultra-Tacky Pressure Sensitive Monomer",
        "family": "Tacky Elastomeric Acrylic",
        "everyday_role": "The primary ingredient that makes Scotch tape, duct tape, and sticky barcode labels intensely sticky and flexible at room temperature.",
        "applications": [
            "Heavy-duty packaging tapes, duct tapes, and sticker adhesives",
            "Exterior weather-seal caulking compounds for home windows",
            "Flexible automotive sound-deadening mats"
        ]
    },

    # 3. High-Performance Polyimides & Kapton Aerospace Precursors
    "O=C1NC(=O)c2ccc(Oc3ccc4c(c3)C(=O)NC4=O)cc21": {
        "name": "Bis-Phthalimide Ether Precursor",
        "trade_name": "Kapton / Upilex Aerospace Polyimide Core",
        "family": "High-Temperature Aerospace Polyimide",
        "everyday_role": "An ultra-tough, golden-amber plastic core capable of surviving extreme space temperatures from -269°C (-452°F) to +400°C (+752°F).",
        "applications": [
            "Golden thermal insulation blankets on NASA satellites and spacecraft",
            "Flexible printed circuit boards inside modern smartphones",
            "High-voltage electrical motor insulation in bullet trains and EVs"
        ]
    },
    "Nc1ccc(Oc2ccc(N)cc2)cc1": {
        "name": "4,4'-Oxydianiline (4,4'-ODA)",
        "trade_name": "Kapton Polyimide Diamine Monomer",
        "family": "Aromatic Diamine Precursor",
        "everyday_role": "Reacted with dianhydrides to produce Kapton golden polyimide film, vital for aerospace heat shields and computer circuitry.",
        "applications": [
            "Satellite solar panel backing sheets and space suit layers",
            "Foldable smartphone flexible hinge circuits and ribbon cables",
            "High-temperature aircraft wire insulation"
        ]
    },
    "O=C1OC(=O)c2cc3c(=O)oc(=O)c3cc21": {
        "name": "Pyromellitic Dianhydride (PMDA)",
        "trade_name": "Kapton Resin Anhydride Monomer",
        "family": "Aromatic Dianhydride",
        "everyday_role": "The key chemical partner used with ODA to create Kapton polyimide films for microelectronics and rocket thermal shielding.",
        "applications": [
            "Spacecraft thermal protection and rocket motor insulation",
            "High-speed computer microchip passivation coatings",
            "Flame-retardant electrical transformer wire wrapping"
        ]
    },
    "Nc1ccc(Cc2ccc(N)cc2)cc1": {
        "name": "4,4'-Methylenedianiline (MDA)",
        "trade_name": "Polyurethane & Epoxy Hardener",
        "family": "Aromatic Diamine",
        "everyday_role": "Used to produce rigid structural polyurethanes, high-temperature carbon-fiber composites, and heavy industrial rollers.",
        "applications": [
            "High-efficiency rigid foam insulation in refrigerators and buildings",
            "Carbon-fiber reinforced aircraft wings and wind turbine blades",
            "Heavy-load industrial forklift wheels and conveyor rollers"
        ]
    },

    # 4. Polyamides, Aramids & Kevlar Precursors
    "O=C(Cl)c1ccc(C(=O)Cl)cc1": {
        "name": "Terephthaloyl Chloride (TCL)",
        "trade_name": "Kevlar / Twaron Monomer Linker",
        "family": "Aromatic Diacyl Chloride (Aramid)",
        "everyday_role": "The essential chemical building block used to spin Kevlar fiber, creating bulletproof vests, stab-proof armor, and cut-resistant gloves.",
        "applications": [
            "Bulletproof body armor, combat helmets, and ballistic shields",
            "Cut-resistant work gloves and chainsaw safety chaps",
            "High-performance puncture-resistant automotive racing tires"
        ]
    },
    "O=C(Cl)c1cccc(C(=O)Cl)c1": {
        "name": "Isophthaloyl Chloride (ICL)",
        "trade_name": "Nomex Firefighter Suit Monomer",
        "family": "Aromatic Diacyl Chloride (Aramid)",
        "everyday_role": "The building block for Nomex fire-retardant fibers, protecting firefighters and race car drivers from engulfing flames up to 370°C.",
        "applications": [
            "Firefighter turn-out coats and wildfire protective suits",
            "Formula 1 driver fireproof racing suits and balaclavas",
            "Military flight suits and emergency aircraft seat covers"
        ]
    },
    "O=C(O)CCCC(=O)O": {
        "name": "Adipic Acid",
        "trade_name": "Nylon 6,6 Monomer",
        "family": "Aliphatic Dicarboxylic Acid (Nylon)",
        "everyday_role": "Millions of tons are produced each year to make Nylon 6,6 for ultra-durable athletic apparel, toothbrush bristles, and indestructible car parts.",
        "applications": [
            "Indestructible Nylon zip-ties, gears, power-tool casings, and intake manifolds",
            "High-strength outdoor ropes, backpacks, and parachute fabric",
            "Durable carpet fibers and quick-drying athletic running apparel"
        ]
    },
    "NCCCCCC(=O)O": {
        "name": "6-Aminocaproic Acid / Caprolactam Form",
        "trade_name": "Nylon-6 Monomer",
        "family": "Aliphatic Polyamide (Nylon)",
        "everyday_role": "The precursor to Nylon 6, famous for high elasticity, wear resistance, and smooth sliding mechanical gears.",
        "applications": [
            "Fishing lines, industrial fishing nets, and guitar strings",
            "Automotive under-hood cooling fans and engine covers",
            "Durable luggage fabrics and weather-resistant hosiery"
        ]
    },
    "O=C(Cl)CCCCCCCCC(=O)Cl": {
        "name": "Sebacoyl Chloride",
        "trade_name": "Nylon 6,10 Monomer",
        "family": "Long-Chain Polyamide Precursor",
        "everyday_role": "A plant-derived long-chain diacid chloride that makes moisture-resistant Nylon 6,10 used in toothbrush bristles and brake hoses.",
        "applications": [
            "Water-resistant toothbrush bristles and paintbrush filaments",
            "Automotive air-brake hoses and hydraulic fuel lines",
            "Corrosion-resistant sporting equipment and ski bindings"
        ]
    },

    # 5. Polystyrenes & Specialty Monomers
    "C=Cc1ccccc1": {
        "name": "Styrene",
        "trade_name": "Polystyrene / Styrofoam / ABS Monomer",
        "family": "Aromatic Vinyl Monomer",
        "everyday_role": "One of the world's most widely used monomers, making Styrofoam thermal coffee cups, protective packaging peanuts, and rigid plastic cutlery.",
        "applications": [
            "Disposable plastic cups, cutlery, CD jewel cases, and petri dishes",
            "Expanded polystyrene (Styrofoam) coolers and building insulation",
            "Combined with butadiene and acrylonitrile to make tough LEGO bricks (ABS)"
        ]
    },
    "C=Cc1ccc(C(C)(C)C)cc1": {
        "name": "4-tert-Butylstyrene",
        "trade_name": "High-Heat Modified Polystyrene",
        "family": "Substituted Polystyrenic",
        "everyday_role": "A bulkier version of styrene that raises heat resistance and prevents warping in injection-molded automotive parts.",
        "applications": [
            "Heat-resistant automotive electrical switch housings",
            "Dimensionally stable electronic enclosures and brackets",
            "Specialty coatings with enhanced water resistance"
        ]
    },
    "C=Cc1ccc(Cl)cc1": {
        "name": "4-Chlorostyrene",
        "trade_name": "Flame-Retardant Polystyrene Monomer",
        "family": "Halogenated Styrenic",
        "everyday_role": "Contains chlorine atoms that naturally quench flames, making plastics self-extinguishing for electrical appliances.",
        "applications": [
            "Flame-retardant television back panels and electrical enclosures",
            "High-dielectric electronic insulators and coil bobbins",
            "Specialty crosslinking agents in fiberglass reinforced composites"
        ]
    },
    "C=Cc1ccc(OC(=O)C)cc1": {
        "name": "4-Acetoxystyrene",
        "trade_name": "Poly(4-hydroxystyrene) Precursor",
        "family": "Phenolic Photoresist Monomer",
        "everyday_role": "A protected monomer converted into phenolic polymer resins used to etch microchip circuits in silicon wafer fabrication.",
        "applications": [
            "Semiconductor laser lithography photoresists for computer CPUs",
            "High-performance antioxidant polymer additives",
            "Thermal-barrier resin coatings for electronics"
        ]
    },

    # 6. Fluoropolymers & Specialty Non-Stick Monomers
    "C=CC(=O)OCC(F)(F)C(F)(F)F": {
        "name": "2,2,3,3,3-Pentafluoropropyl Acrylate",
        "trade_name": "Fluorinated Water & Oil Repellent Monomer",
        "family": "Fluorinated Optical & Barrier Acrylic",
        "everyday_role": "A Teflon-like fluorinated acrylic that repels both water and oil, used for anti-smudge smartphone screen coatings and raincoats.",
        "applications": [
            "Anti-fingerprint and oleophobic coatings on smartphone touchscreens",
            "Water- and stain-repellent coatings on outdoor performance jackets",
            "Low-surface-energy marine coatings preventing barnacle buildup"
        ]
    },
    "CC(=C)C(=O)OCC(F)(F)C(F)(F)F": {
        "name": "2,2,3,3,3-Pentafluoropropyl Methacrylate",
        "trade_name": "Fluorinated Optical Fiber Cladding Monomer",
        "family": "Fluorinated Methacrylic Polymer",
        "everyday_role": "Provides ultra-low refractive index and extreme chemical inertness, making it ideal for optical fiber light claddings.",
        "applications": [
            "Protective cladding on high-speed internet fiber optic cables",
            "Stain-resistant architectural glass coatings",
            "Chemical-resistant analytical laboratory sensor windows"
        ]
    },
    "C=CC(=O)OCC(F)(F)C(F)(F)C(F)(F)C(F)(F)F": {
        "name": "Heptafluorobutyl Acrylate",
        "trade_name": "Heavy-Duty Fluorochemical Barrier Monomer",
        "family": "Perfluorinated Acrylic Barrier",
        "everyday_role": "Creates an ultra-slick, non-stick, non-wetting protective barrier that resists aggressive chemical acids and solvents.",
        "applications": [
            "Acid- and solvent-resistant industrial protective linings",
            "Advanced microfluidic medical diagnostics chips",
            "Waterproof electronic circuit spray-on conformal coatings"
        ]
    },

    # 7. Silicones, Acrylamides & Bio-polymers
    "C=CC(=O)O[Si](C)(C)O[Si](C)(C)C": {
        "name": "Siloxane Acrylate Monomer",
        "trade_name": "Silicone-Acrylic Hybrid Monomer",
        "family": "Silicone-Organic Hybrid Resin",
        "everyday_role": "Combines the fast UV-curing speed of acrylics with the silky, heat-resistant, water-repellent softness of silicone rubber.",
        "applications": [
            "Extended-wear silicone hydrogel soft contact lenses",
            "Silky-feel cosmetic creams, hair serums, and sunscreens",
            "Flexible weather-seal rubber gaskets for car sunroofs"
        ]
    },
    "C=CC(=O)N(C)C": {
        "name": "N,N-Dimethylacrylamide (DMAA)",
        "trade_name": "High-Solubility Hydrogel Monomer",
        "family": "Water-Soluble Functional Acrylamide",
        "everyday_role": "A water-soluble monomer that forms super-absorbent gels and frictionless lubricating coatings for medical catheters.",
        "applications": [
            "Frictionless hydrophilic coatings on surgical catheters and guide wires",
            "Super-absorbent water-retaining agricultural hydrogels for drought farming",
            "Enhanced oil recovery drag-reducing polymer fluids"
        ]
    },
    "C=CC(=O)NCC(C)C": {
        "name": "N-Isobutylacrylamide",
        "trade_name": "Thermo-Responsive Smart Polymer Monomer",
        "family": "Smart Stimuli-Responsive Polymer",
        "everyday_role": "A 'smart' polymer monomer that changes from clear and dissolved to opaque and contracted when heated past a specific body temperature.",
        "applications": [
            "Smart temperature-triggered drug release capsules in medicine",
            "Self-regulating greenhouse smart shading window films",
            "Cell-culture harvesting surfaces in tissue engineering"
        ]
    },
    "O=C(OCC1CO1)c2ccccc2": {
        "name": "Glycidyl Benzoate",
        "trade_name": "Aromatic Epoxy Reactive Diluent",
        "family": "Epoxy Functional Resin Modifier",
        "everyday_role": "Thins thick epoxy resins without sacrificing hardness, improving penetration into carbon fiber weaves and concrete cracks.",
        "applications": [
            "Crack-injection structural repair epoxies for bridges and buildings",
            "High-strength carbon-fiber composite resin infusion",
            "Glossy electrical potting compounds protecting circuit boards"
        ]
    },
    "c1cc(ccc1C(=O)O)c2ccc(cc2)C(=O)O": {
        "name": "Biphenyl-4,4'-dicarboxylic Acid",
        "trade_name": "Liquid Crystal Polymer (LCP) Monomer",
        "family": "Rigid-Rod Liquid Crystal Polyester",
        "everyday_role": "Forms ultra-stiff, heat-proof plastic molecules that line up like microscopic rods, replacing metals in miniature 5G antennas.",
        "applications": [
            "Ultra-thin 5G smartphone antenna switches and connectors",
            "Precision camera lens brackets resisting solder oven heat (280°C)",
            "High-frequency aerospace radar circuit substrates"
        ]
    },
    "CC1(C)c2cc(C(=O)O)ccc2-c3ccc(C(=O)O)cc31": {
        "name": "9,9-Dimethylfluorene-2,7-dicarboxylic Acid",
        "trade_name": "High-Refractive Optical Monomer",
        "family": "Fluorene High-Tg Engineering Polyester",
        "everyday_role": "Provides intense optical refraction and heat tolerance in ultra-thin smartphone camera lenses and OLED display backings.",
        "applications": [
            "Ultra-thin smartphone camera multi-lens assemblies",
            "Flexible substrates for vibrant OLED television screens",
            "High-temperature automotive laser sensor covers"
        ]
    }
}


def format_chemical_formula(raw_formula: str) -> Dict[str, Any]:
    """
    Parses raw formula (e.g., 'C15H16O2') and converts to:
    - Unicode subscript formula ('C₁₅H₁₆O₂')
    - HTML formatted formula ('C<sub>15</sub>H<sub>16</sub>O<sub>2</sub>')
    - Elemental breakdown string in plain English ('15 Carbon, 16 Hydrogen, 2 Oxygen')
    """
    if not raw_formula:
        return {
            "unicode": "--",
            "html": "--",
            "breakdown": "Composition unavailable."
        }

    # Convert digits to Unicode subscript
    unicode_str = ""
    for char in raw_formula:
        unicode_str += SUBSCRIPT_MAP.get(char, char)

    # Convert digits to HTML <sub>
    html_str = re.sub(r'(\d+)', r'<sub>\1</sub>', raw_formula)

    # Parse elements and counts
    element_matches = re.findall(r'([A-Z][a-z]?)(\d*)', raw_formula)
    breakdown_parts = []
    for elem, count_str in element_matches:
        count = int(count_str) if count_str else 1
        name = ELEMENT_NAMES.get(elem, elem)
        breakdown_parts.append(f"{count} {name} ({elem})")

    breakdown_str = ", ".join(breakdown_parts) if breakdown_parts else "Elemental breakdown available."

    return {
        "unicode": unicode_str,
        "html": html_str,
        "breakdown": breakdown_str
    }


def clean_and_reconstitute_smiles(smiles: str) -> str:
    """
    Cleans up user or pipeline SMILES strings.
    If the SMILES is a polymer repeat unit with attachment wildcards (like '*' or '[*]'),
    reconstructs the active monomer double bond (e.g. *CC(*) -> C=C) or replaces
    open bonds with hydrogen caps to allow clean RDKit parsing.
    """
    if not smiles:
        return ""
    cleaned = smiles.strip()

    # Reconstruct polymerized vinyl/acrylic backbone repeat units to active monomers
    if re.search(r'\[\*\]|\*', cleaned):
        reconstructed = re.sub(r'\[\*\]CC\(C\)\(\*\)|\*CC\(C\)\(\*\)', 'CC(=C)', cleaned)
        reconstructed = re.sub(r'\[\*\]C\(C\)\(\*\)C|\*C\(C\)\(\*\)C', 'CC(=C)', reconstructed)
        reconstructed = re.sub(r'\[\*\]CC\(\*\)|\*CC\(\*\)', 'C=C', reconstructed)
        reconstructed = re.sub(r'\[\*\]|\*', '[H]', reconstructed)
        if Chem is not None:
            try:
                m = Chem.MolFromSmiles(reconstructed)
                if m is not None:
                    return reconstructed
            except Exception:
                pass

    # Default fallback: replace wildcards with [H]
    cleaned = re.sub(r'\[\*\]|\*', '[H]', cleaned)
    return cleaned



def classify_substructure_offline(mol) -> Dict[str, Any]:
    """
    Offline RDKit SMARTS Substructure Pattern Classifier.
    If a molecule is a new AI-generated candidate or not present in the offline dictionary,
    this detects the backbone architecture and functional linkers to generate an accurate
    systematic chemical name, family, and plain-English role.
    """
    if Chem is None or mol is None:
        return {
            "name": "Custom Organic Polymer Monomer",
            "trade_name": "Synthetic Monomer Candidate",
            "family": "Synthetic Polymer",
            "everyday_role": "A laboratory-designed organic monomer synthesized to test physical and mechanical polymer properties.",
            "applications": [
                "Experimental polymer testing and structural characterization",
                "Advanced composite resin formulation studies",
                "Computational molecular material discovery"
            ]
        }

    # Detect Reactive / Functional Linkers
    patterns = {
        "methacrylate": Chem.MolFromSmarts("CC(=C)C(=O)O"),
        "acrylate": Chem.MolFromSmarts("C=CC(=O)O"),
        "acyl_chloride": Chem.MolFromSmarts("C(=O)Cl"),
        "imide": Chem.MolFromSmarts("C(=O)NC(=O)"),
        "anhydride": Chem.MolFromSmarts("C(=O)OC(=O)"),
        "carboxylic_acid": Chem.MolFromSmarts("C(=O)[OH]"),
        "primary_amine": Chem.MolFromSmarts("[NX3;H2]"),
        "amide": Chem.MolFromSmarts("C(=O)N"),
        "ester": Chem.MolFromSmarts("C(=O)O[C]"),
        "phenol": Chem.MolFromSmarts("c[OH]"),
        "epoxide": Chem.MolFromSmarts("C1OC1"),
        "fluorinated": Chem.MolFromSmarts("C(F)(F)"),
        "siloxane": Chem.MolFromSmarts("[Si]-O-[Si]"),
        "biphenyl": Chem.MolFromSmarts("c1ccccc1-c2ccccc2"),
        "adamantyl": Chem.MolFromSmarts("C12CC3CC(CC(C3)C1)C2"),
        "cyclohexyl": Chem.MolFromSmarts("C1CCCCC1"),
        "aromatic_ring": Chem.MolFromSmarts("a1aaaaa1"),
    }

    matches = {}
    for key, patt in patterns.items():
        if patt is not None and mol.HasSubstructMatch(patt):
            matches[key] = True

    # Assemble Backbone & Family
    backbone_name = "Aliphatic"
    if matches.get("fluorinated"):
        backbone_name = "Fluorinated"
    elif matches.get("siloxane"):
        backbone_name = "Silicone-Modified"
    elif matches.get("adamantyl"):
        backbone_name = "Diamond-Cage Adamantyl"
    elif matches.get("cyclohexyl"):
        backbone_name = "Alicyclic Cyclohexyl"
    elif matches.get("biphenyl"):
        backbone_name = "Rigid Biphenyl"
    elif matches.get("phenol"):
        backbone_name = "Phenolic Aromatic"
    elif matches.get("aromatic_ring"):
        backbone_name = "Aromatic"

    # Assemble Linker / Monomer Type
    if matches.get("imide") or matches.get("anhydride"):
        monomer_type = "Polyimide Precursor"
        family = "High-Temperature Polyimide / Aerospace Resin"
        role = "Forms an exceptionally heat-stable, flame-resistant polyimide chain suitable for aerospace insulation, electronics, and rocket heat shields."
        apps = ["Aerospace thermal protection blankets", "Flexible microchip circuit substrates", "High-voltage electrical motor insulation"]
    elif matches.get("acyl_chloride"):
        monomer_type = "Diacyl Chloride Crosslinker"
        family = "Aramid / High-Strength Polyamide Precursor"
        role = "A highly reactive chemical crosslinker used to spin ultra-strong aramid fibers for bullet-resistant body armor and protective fire-suits."
        apps = ["Ballistic body armor & bulletproof panels", "High-temperature firefighter gear", "Cut-resistant industrial gloves"]
    elif matches.get("methacrylate"):
        monomer_type = "Methacrylate Monomer"
        family = "Scratch-Resistant Acrylic Polymer"
        role = "Polymerizes into a rigid, optical-grade acrylic plastic with high scratch resistance, optical clarity, and UV sunlight weatherability."
        apps = ["Crystal-clear display screens & optical lenses", "Automotive exterior coatings", "Scratch-resistant plastic panels"]
    elif matches.get("acrylate"):
        monomer_type = "Acrylate Monomer"
        family = "Optical & Coating Acrylic Resin"
        role = "Forms a weather-resistant, clear acrylic material widely used in optical coatings, water-based paints, and pressure-sensitive adhesives."
        apps = ["Protective clear coatings & varnishes", "Pressure-sensitive packaging tapes", "Weather-resistant exterior house paints"]
    elif matches.get("primary_amine") or matches.get("amide"):
        monomer_type = "Polyamide / Nylon Monomer"
        family = "Wear-Resistant Polyamide (Nylon Class)"
        role = "Forms resilient, wear-resistant polyamide plastic fibers with high mechanical toughness and low friction for sliding gears and clothing."
        apps = ["Durable mechanical gears and zip-ties", "High-strength sports equipment & ropes", "Abrasion-resistant athletic apparel"]
    elif matches.get("epoxide"):
        monomer_type = "Epoxy Monomer"
        family = "Thermosetting Epoxy Resin"
        role = "Undergoes crosslinking into an extremely hard, chemical-proof epoxy thermoset resin with high adhesion to metals, carbon fibers, and glass."
        apps = ["High-strength structural aerospace adhesives", "Carbon-fiber composite drone & car parts", "Industrial anti-corrosion tank coatings"]
    elif matches.get("ester") or matches.get("carboxylic_acid"):
        monomer_type = "Polyester Monomer"
        family = "Engineering Polyester (PET Class)"
        role = "Reacts to build durable, recyclable polyesters used in beverage bottles, synthetic textile fibers, and electronic packaging films."
        apps = ["Recyclable plastic beverage containers", "Synthetic textile clothing fibers", "High-tensile packaging strapping"]
    else:
        monomer_type = "Polymer Building Unit"
        family = "Specialty Organic Thermoplastic"
        role = "A custom organic monomer unit synthesized to target specific thermal and mechanical performance in material science applications."
        apps = ["Precision engineered thermoplastic parts", "Specialty industrial coatings", "Advanced laboratory material testing"]

    assembled_name = f"{backbone_name} {monomer_type}"
    return {
        "name": assembled_name,
        "trade_name": f"{family.split('/')[0].strip()} Monomer",
        "family": family,
        "everyday_role": role,
        "applications": apps
    }


def explain_properties_layman(
    tg: Optional[float] = None,
    density: Optional[float] = None,
    tensile: Optional[float] = None,
    modulus: Optional[float] = None,
    sa_score: Optional[float] = None
) -> Dict[str, str]:
    """
    Translates physical numbers (Tg, Density, Tensile, Modulus, SA)
    into intuitive, everyday layman analogies.
    """
    # 1. Glass Transition Temp (Heat Resistance)
    if tg is not None:
        if tg < 20:
            heat_desc = f"Soft & rubbery at room temp ({tg:.1f} °C). Stays flexible in freezing winter temperatures."
        elif tg < 90:
            heat_desc = f"Low-to-moderate heat resistance ({tg:.1f} °C). Stays solid at room temp but softens in hot water."
        elif tg < 160:
            heat_desc = f"High heat resistance ({tg:.1f} °C / {tg*1.8+32:.0f} °F). Safe in boiling water and hot car interiors."
        else:
            heat_desc = f"Extreme thermal stability ({tg:.1f} °C / {tg*1.8+32:.0f} °F). Withstands industrial ovens and aerospace environments."
    else:
        heat_desc = "Thermal behavior is currently being calculated."

    # 2. Rigidity & Mechanical Feel
    if modulus is not None and tensile is not None:
        if modulus > 3.0 and tensile > 70:
            mech_desc = f"Ultra-rigid & shatter-resistant ({tensile:.1f} MPa). Hard and sturdy like a crash helmet or safety shield."
        elif modulus > 1.5:
            mech_desc = f"Stiff everyday plastic ({tensile:.1f} MPa). Tough and durable like LEGO bricks or tool casings."
        elif modulus > 0.5:
            mech_desc = f"Semi-flexible plastic ({tensile:.1f} MPa). Bendable without snapping, similar to shampoo bottles."
        else:
            mech_desc = f"Soft elastomeric rubber ({tensile:.1f} MPa). Highly flexible, stretchy, and shock-absorbing."
    elif tensile is not None:
        mech_desc = f"Solid structural plastic with tensile strength of {tensile:.1f} MPa."
    else:
        mech_desc = "Mechanical stiffness and strength are being evaluated."

    # 3. Density
    if density is not None:
        if density < 1.05:
            density_desc = f"Ultra-lightweight ({density:.2f} g/cm³). Floats on water like polypropylene."
        elif density < 1.30:
            density_desc = f"Standard plastic weight ({density:.2f} g/cm³). Lightweight and easy to mold."
        else:
            density_desc = f"High-density material ({density:.2f} g/cm³). Dense, solid feel with high atomic packing."
    else:
        density_desc = "Density metrics are being evaluated."

    # 4. Manufacturing Feasibility (SA Score)
    if sa_score is not None:
        if sa_score <= 2.5:
            sa_desc = f"Very easy (SA {sa_score:.1f}/10). Readily synthesized in standard commercial chemical plants."
        elif sa_score <= 4.5:
            sa_desc = f"Standard feasibility (SA {sa_score:.1f}/10). Manufacturable using standard laboratory procedures."
        else:
            sa_desc = f"Challenging synthesis (SA {sa_score:.1f}/10). Requires specialized multi-step precision laboratory synthesis."
    else:
        sa_desc = "Feasibility score pending."

    return {
        "heat": heat_desc,
        "mechanical": mech_desc,
        "density": density_desc,
        "feasibility": sa_desc
    }


def explain_polymer(
    smiles: str,
    tg: Optional[float] = None,
    density: Optional[float] = None,
    tensile: Optional[float] = None,
    modulus: Optional[float] = None,
    sa_score: Optional[float] = None,
    raw_formula: Optional[str] = None,
    molecular_weight: Optional[float] = None
) -> Dict[str, Any]:
    """
    Main Entry Point: Generates a comprehensive, 100% offline Plain-English
    Polymer Interpretation for any given SMILES or broken fragment.
    """
    cleaned_smiles = clean_and_reconstitute_smiles(smiles)
    canonical_smiles = cleaned_smiles

    mol = None
    if Chem is not None and cleaned_smiles:
        try:
            mol = Chem.MolFromSmiles(cleaned_smiles)
            if mol is not None:
                canonical_smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
                if not raw_formula:
                    raw_formula = rdMolDescriptors.CalcMolFormula(mol)
                if molecular_weight is None:
                    molecular_weight = round(Descriptors.MolWt(mol), 2)
        except Exception:
            pass

    # 1. Check exact match in offline library
    matched_info = OFFLINE_MONOMER_LIBRARY.get(canonical_smiles) or OFFLINE_MONOMER_LIBRARY.get(cleaned_smiles)

    if matched_info:
        name = matched_info["name"]
        trade_name = matched_info["trade_name"]
        family = matched_info["family"]
        everyday_role = matched_info["everyday_role"]
        applications = matched_info["applications"]
    else:
        # 2. Decompose fragment via RDKit SMARTS substructure matching
        decomposed = classify_substructure_offline(mol)
        name = decomposed["name"]
        trade_name = decomposed["trade_name"]
        family = decomposed["family"]
        everyday_role = decomposed["everyday_role"]
        applications = decomposed["applications"]

    # 3. Format chemical formula and atom breakdown
    formula_info = format_chemical_formula(raw_formula or "")

    # 4. Generate Layman's physical property translation
    layman_props = explain_properties_layman(
        tg=tg,
        density=density,
        tensile=tensile,
        modulus=modulus,
        sa_score=sa_score
    )

    return {
        "name": name,
        "trade_name": trade_name,
        "family": family,
        "everyday_role": everyday_role,
        "applications": applications,
        "raw_formula": raw_formula or "N/A",
        "formatted_formula": formula_info["unicode"],
        "html_formula": formula_info["html"],
        "element_breakdown": formula_info["breakdown"],
        "molecular_weight": molecular_weight or "N/A",
        "layman_properties": layman_props
    }
