# AI Polymer Generation

## Overview

**AI Polymer Generation** is a software project that combines artificial intelligence, cheminformatics, molecular representation, and polymer-property analysis to support the generation and evaluation of polymer structures.

The project is designed around the idea of using computational methods to work with molecular structures and their associated properties. Instead of relying entirely on traditional manual approaches, the system provides a structured computational workflow for handling molecular inputs, validating structures, generating or evaluating polymer-related information, and storing relevant results.

The project brings together several components, including molecular validation, AI/model-related resources, property prediction, database organization, testing, and a graphical application environment.

The repository is organized into separate directories for source code, models, assets, and tests, making the project easier to maintain and extend.

---

## Table of Contents

* [Project Overview](#overview)
* [Motivation](#motivation)
* [Objectives](#objectives)
* [Key Features](#key-features)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [Molecular Representation](#molecular-representation)
* [Molecule Validation](#molecule-validation)
* [Property Prediction](#property-prediction)
* [Database Design](#database-design)
* [Validation and Error Logging](#validation-and-error-logging)
* [Testing](#testing)
* [Installation](#installation)
* [Running the Project](#running-the-project)
* [General Workflow](#general-workflow)
* [Applications](#applications)
* [Advantages](#advantages)
* [Limitations](#limitations)
* [Future Scope](#future-scope)
* [Project Team](#project-team)
* [Contribution](#contribution)
* [Acknowledgements](#acknowledgements)
* [License](#license)

---

# Motivation

Polymer science involves working with complex molecular structures and a large number of possible material combinations. Exploring these structures manually can require significant time and computational effort.

Artificial intelligence and computational chemistry can assist researchers and developers by providing tools for molecular generation, structure validation, property analysis, and data organization.

This project explores how an AI-based computational workflow can be applied to polymer-related molecular structures.

The goal is not simply to generate molecular structures, but to provide an organized environment in which molecular information can be processed, validated, analyzed, and stored.

---

# Objectives

The major objectives of the project are:

* To develop a computational platform related to AI-based polymer generation.
* To work with molecular structures using machine-readable representations.
* To validate molecular inputs before further processing.
* To support property prediction and analysis.
* To organize molecular information using a relational database.
* To maintain validation and exception logs.
* To provide a structured and maintainable project architecture.
* To create a foundation that can be extended with additional AI and machine-learning models.
* To make polymer-related computational workflows easier to experiment with and understand.

---

# Key Features

## 1. AI-Based Polymer Generation

The project focuses on the use of computational intelligence for polymer-related molecular generation and analysis.

AI and machine-learning techniques can potentially help explore a large chemical design space and identify molecular structures that satisfy particular requirements.

---

## 2. Molecular Structure Handling

The project works with molecular structures represented in a machine-readable form.

One important representation used in cheminformatics is **SMILES (Simplified Molecular Input Line Entry System)**.

SMILES allows a molecular structure to be represented as a text string.

For example:

```text
CCO
```

represents ethanol.

Using textual molecular representations makes it possible for software systems to store, validate, compare, and process molecular structures.

---

## 3. Molecular Validation

Before a molecular structure is used for further processing, it is important to determine whether the input is valid.

The project includes a validation-oriented database structure that records:

* Input molecular representation
* Validation status
* Validation stage
* Error message
* Timestamp

This helps identify invalid inputs and makes debugging easier.

---

## 4. Property Prediction

The database design supports storing predicted molecular/polymer properties.

Each prediction can be associated with:

* A molecule
* Property name
* Predicted value
* Unit
* Model version
* Creation timestamp

This allows multiple properties to be associated with the same molecular structure.

For example, the schema provides examples such as:

* Glass Transition Temperature (Tg)
* Density

The system is therefore structured so that additional properties can be incorporated in the future.

---

## 5. Synthetic Accessibility Information

The molecular database includes a field for a **Synthetic Accessibility Score**.

Synthetic accessibility is useful because a computationally generated molecule may be interesting theoretically but difficult to synthesize in practice.

Including such information can help move computational molecular design toward more practically relevant candidates.

---

## 6. Database Organization

The project includes an SQL database schema designed to organize molecular information.

The database separates molecular records, property predictions, and validation logs into different tables.

This makes the stored information easier to manage and query.

---

# Technology Stack

The project currently includes the following technologies and tools:

### Python

Python is used as the primary programming language for the project.

Python is widely used in artificial intelligence, machine learning, scientific computing, and cheminformatics because of its large ecosystem of libraries.

### PyQt6

**PyQt6** is included in the project's dependencies.

It provides tools for creating graphical user interfaces using Python.

This can be used to build desktop-based interfaces for interacting with the project.

### RDKit

**RDKit** is included in the project dependencies.

RDKit is a cheminformatics toolkit that provides functionality for working with molecular structures.

It can be used for tasks such as molecular representation, structure processing, validation, and calculation of molecular information.

### Pytest

**pytest** is included as a testing dependency.

It provides a framework for creating and running automated tests for Python code.

### SQL / SQLite

The repository contains a `schema.sql` file defining a relational database structure.

The schema uses SQLite-style SQL features and organizes information into relational tables.

---

# Project Structure

The repository is organized into the following major components:

```text
AI-Polymer-Generation/
│
├── .vscode/
│
├── assets/
│
├── model/
│
├── src/
│
├── tests/
│
├── .gitignore
│
├── requirements.txt
│
└── schema.sql
```

---

## `.vscode`

The `.vscode` directory contains Visual Studio Code-specific project configuration.

Such configuration can help developers maintain consistent development settings when working on the project using VS Code.

---

## `assets`

The `assets` directory contains supporting resources used by the application/project.

Assets can include files required for the interface, visual resources, or other supporting project materials.

---

## `model`

The `model` directory is intended for model-related components.

This separates AI/model resources from the main source-code implementation and provides a dedicated location for model-related files.

---

## `src`

The `src` directory contains the main source code of the project.

This is the primary implementation area where the application's functionality is developed.

Separating source code into a dedicated directory keeps the repository organized and makes the project easier to maintain.

---

## `tests`

The `tests` directory contains testing-related files.

Tests are important because they help verify that individual components behave as expected and that future modifications do not unintentionally break existing functionality.

---

## `requirements.txt`

The `requirements.txt` file lists the Python dependencies required by the project.

The current repository specifies:

```text
PyQt6>=6.5.0
rdkit>=2023.3.1
pytest>=7.4.0
```

These dependencies provide the GUI, cheminformatics, and testing functionality required by the project.

---

## `schema.sql`

The `schema.sql` file defines the relational database structure used by the project.

It contains tables for molecular information, property predictions, and validation logs.

---

# Molecular Representation

Molecular structures need to be represented in a format that software can process.

The project uses the concept of a **SMILES string** for storing molecular structures.

A SMILES string provides a compact textual representation of a chemical structure.

The database stores both:

* `smiles_string`
* `canonical_smiles`

The canonical representation can help ensure that equivalent molecular structures can be represented consistently.

The database also enforces uniqueness for canonical SMILES values, helping prevent duplicate molecular entries.

---

# Database Design

The database consists of three major tables.

## 1. Molecules

The `Molecules` table stores the core information about molecular structures.

Important fields include:

| Field              | Purpose                                 |
| ------------------ | --------------------------------------- |
| `molecule_id`      | Unique identifier                       |
| `smiles_string`    | Original molecular representation       |
| `canonical_smiles` | Canonical molecular representation      |
| `sa_score`         | Synthetic accessibility score           |
| `is_valid`         | Indicates whether the molecule is valid |
| `created_at`       | Record creation time                    |

The molecule ID acts as the primary key.

The canonical SMILES field is also marked as unique.

---

## 2. PropertyPredictions

The `PropertyPredictions` table stores predicted properties associated with molecules.

Important fields include:

| Field             | Purpose                                 |
| ----------------- | --------------------------------------- |
| `prediction_id`   | Unique prediction identifier            |
| `molecule_id`     | Molecule associated with the prediction |
| `property_name`   | Name of predicted property              |
| `predicted_value` | Predicted numerical value               |
| `unit`            | Unit of measurement                     |
| `model_version`   | Version of model used                   |
| `created_at`      | Prediction creation time                |

A molecule can have multiple property predictions.

For example, one molecule could have predictions for density, glass transition temperature, or other properties.

---

## 3. ValidationLogs

The `ValidationLogs` table stores information about molecular validation.

Important fields include:

| Field           | Purpose                       |
| --------------- | ----------------------------- |
| `log_id`        | Unique log identifier         |
| `smiles_input`  | Input molecular string        |
| `is_valid`      | Validation result             |
| `error_stage`   | Stage where an error occurred |
| `error_message` | Description of the error      |
| `logged_at`     | Time of validation            |

This provides a useful record of invalid inputs and makes troubleshooting easier.

---

# Database Relationships

The project uses a relationship between molecules and property predictions.

Conceptually:

```text
             Molecules
                 │
                 │
                 │ 1
                 │
                 │
                 │ Many
                 ▼
       PropertyPredictions
```

One molecule can have multiple property predictions.

The `molecule_id` in the `PropertyPredictions` table references the corresponding molecule in the `Molecules` table.

The schema also uses cascading deletion so that dependent property predictions are removed when their associated molecule is deleted.

---

# Validation and Error Logging

Validation is an important part of a molecular-generation workflow.

An AI system may generate a structure that is syntactically incorrect, chemically invalid, or unsuitable for further processing.

Therefore, validation can be performed before a generated structure is accepted into the system.

The project database provides separate logging for validation failures.

Possible validation stages represented in the schema include:

* Syntax Check
* Sanitization
* Valence

Keeping these errors in a database makes it easier to investigate failures and improve the system.

---

# Testing

Testing is an important part of software development.

The project includes a dedicated `tests` directory and uses **pytest** as one of its development dependencies.

Automated testing can help verify:

* Molecular validation
* Input handling
* Application functionality
* Model-related components
* Database interactions
* Error-handling behavior

Testing also makes future development safer because changes can be checked against previously defined expected behavior.

---

# Installation

## Step 1: Clone the repository

```bash
git clone https://github.com/ShoryaRanjan0507/AI-Polymer-Generation.git
```

## Step 2: Open the project directory

```bash
cd AI-Polymer-Generation
```

## Step 3: Create a virtual environment

It is recommended to use a virtual environment so that project dependencies remain isolated.

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

## Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

The repository currently specifies PyQt6, RDKit, and pytest as dependencies.

---

# Running the Project

The exact execution command depends on the entry-point provided by the source code.

After installing the dependencies, the appropriate Python file inside the `src` directory can be executed according to the project's implementation.

For example:

```bash
python <entry_file>.py
```

Replace `<entry_file>.py` with the actual application entry point.

---

# Running Tests

Tests can be executed using pytest.

```bash
pytest
```

This searches the project for test files and runs the available automated tests.

A successful test run helps confirm that the implemented functionality is behaving according to the expected test cases.

---

# General Workflow

A simplified conceptual workflow of the project can be represented as:

```text
                User / Input
                     │
                     ▼
             Molecular Structure
                     │
                     ▼
              Input Validation
                     │
              ┌──────┴──────┐
              │             │
           Invalid        Valid
              │             │
              ▼             ▼
       Validation Log    Processing
                            │
                            ▼
                     AI / Model Layer
                            │
                            ▼
                    Property Prediction
                            │
                            ▼
                     Result Storage
                            │
                            ▼
                       Database
```

This structure provides a clear separation between input handling, validation, model-related processing, prediction, and data storage.

---

# Applications

AI-assisted polymer generation and property analysis can have applications in several areas of materials science.

Potential application areas include:

* Polymer material discovery
* Computational chemistry
* Materials informatics
* Molecular design
* Property prediction
* Research and experimentation
* AI-assisted chemical analysis
* Exploration of candidate polymer structures

The ability to computationally explore molecular structures can help researchers investigate a wider design space before moving toward laboratory experimentation.

---

# Advantages

## Faster Computational Exploration

Computational approaches can help explore many possible molecular structures without requiring every candidate to be physically synthesized.

## Structured Molecular Data

The relational database provides a structured way of storing molecular structures and their predicted properties.

## Validation Support

Validation logging helps identify problematic molecular inputs and provides information about where validation failed.

## Extensibility

The separation between source code, models, assets, tests, and database schema makes the project easier to extend.

## Property-Oriented Design

The property prediction table allows multiple properties to be associated with the same molecular structure.

## Testing Support

The use of pytest provides a foundation for automated software testing.

---

# Limitations

AI-generated molecular structures should not automatically be considered experimentally feasible or chemically optimal.

Computational predictions depend on the quality of the underlying data, algorithms, models, and validation procedures.

A predicted property is not necessarily identical to the experimentally measured value.

Therefore, computational results should be interpreted as part of a larger scientific workflow rather than as a replacement for experimental validation.

---

# Future Scope

The project can potentially be extended in several directions.

### Improved AI Models

More advanced generative models could be incorporated to improve molecular generation and exploration.

### Additional Polymer Properties

Additional properties could be added to the prediction framework, depending on the project's requirements.

Possible examples include:

* Mechanical properties
* Thermal properties
* Optical properties
* Electrical properties
* Chemical stability
* Density
* Glass transition temperature

### Better Visualization

The graphical interface could be extended with molecular structure visualization, prediction charts, and interactive results.

### Larger Datasets

The system could be trained or evaluated using larger and more diverse polymer datasets.

### Model Comparison

Different machine-learning or generative approaches could be compared using consistent evaluation metrics.

### Improved Validation

Additional chemical validity checks could be introduced to improve the quality of generated structures.

### Experimental Integration

In a future research-oriented version, computational predictions could be combined with experimental datasets to create a feedback loop between predicted and observed polymer properties.

---

# Project Team

This project was developed as a collaborative group project.

### Team Members

* **Shorya Ranjan** — Project Repository / Development
* **[Teammate Name]** — Development / AI & Model
* **[Teammate Name]** — Development / Testing
* **Palak Mitruka** — Documentation & Project Support
* **[Teammate Name]** — [Role]

> Replace the placeholder names and roles with the actual team members and responsibilities before committing this README.

---

# Contribution

This project was developed collaboratively, with different team members contributing to different aspects of the system.

Contributions may include:

* Software development
* AI/model implementation
* Molecular processing
* Database design
* Testing
* Documentation
* Project organization
* Presentation and project explanation

The README and project documentation are maintained as part of the project's documentation effort.

---

# Acknowledgements

We would like to acknowledge the open-source technologies and libraries that make this project possible.

Special thanks to the developers and communities behind:

* Python
* PyQt6
* RDKit
* pytest
* SQLite

These tools provide important building blocks for developing scientific, cheminformatics, and AI-based applications.

---

# Conclusion

AI Polymer Generation represents an intersection of artificial intelligence, software engineering, cheminformatics, and polymer science.

The project provides a structured foundation for working with molecular structures and their predicted properties while maintaining validation records and organized project components.

By combining molecular representation, validation, AI/model components, property prediction, database management, and testing, the project creates a foundation that can be further developed for computational polymer discovery and materials informatics.

Future development can expand the system with more advanced generative models, additional polymer properties, improved visualization, larger datasets, and stronger validation methods.

---

## Repository

GitHub Repository:

https://github.com/ShoryaRanjan0507/AI-Polymer-Generation

---

## License

License information should be added here according to the license selected for the project.

If no license has been selected yet, the project maintainers should decide on an appropriate open-source license before publishing the final version.
