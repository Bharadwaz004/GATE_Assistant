"""
GATE subject and topic data for study plan generation.
Maps each branch to its subjects and subtopics with weights.
"""

# ── Subject → Topics mapping for major GATE branches ─────────
GATE_SUBJECTS = {
    "CSE": {
        "Engineering Mathematics": {
            "topics": [
                "Linear Algebra", "Calculus", "Probability & Statistics",
                "Discrete Mathematics", "Graph Theory", "Combinatorics",
            ],
            "weight": 13,
        },
        "Digital Logic": {
            "topics": [
                "Boolean Algebra", "Combinational Circuits", "Sequential Circuits",
                "Number Systems", "Minimization",
            ],
            "weight": 3,
        },
        "Computer Organization & Architecture": {
            "topics": [
                "Machine Instructions", "Addressing Modes", "ALU & Data Path",
                "CPU Control Design", "Memory Hierarchy", "Cache", "I/O Interface",
                "Pipelining",
            ],
            "weight": 8,
        },
        "Programming & Data Structures": {
            "topics": [
                "C Programming", "Arrays", "Linked Lists", "Stacks & Queues",
                "Trees", "Binary Search Trees", "Graphs", "Hashing",
                "Recursion", "Sorting & Searching",
            ],
            "weight": 10,
        },
        "Algorithms": {
            "topics": [
                "Asymptotic Analysis", "Divide and Conquer", "Greedy",
                "Dynamic Programming", "Graph Algorithms", "Shortest Paths",
                "MST", "NP-Completeness",
            ],
            "weight": 10,
        },
        "Theory of Computation": {
            "topics": [
                "Regular Languages & FA", "Context-Free Grammars & PDA",
                "Turing Machines", "Decidability", "Regular Expressions",
            ],
            "weight": 6,
        },
        "Compiler Design": {
            "topics": [
                "Lexical Analysis", "Parsing", "Syntax-Directed Translation",
                "Intermediate Code", "Code Optimization", "Runtime Environments",
            ],
            "weight": 6,
        },
        "Operating Systems": {
            "topics": [
                "Process Management", "Threads", "CPU Scheduling",
                "Synchronization", "Deadlocks", "Memory Management",
                "Virtual Memory", "File Systems", "Disk Scheduling",
            ],
            "weight": 10,
        },
        "Databases": {
            "topics": [
                "ER Model", "Relational Model", "SQL", "Normalization",
                "Transactions & Concurrency", "Indexing", "File Organization",
            ],
            "weight": 8,
        },
        "Computer Networks": {
            "topics": [
                "OSI & TCP/IP Models", "Data Link Layer", "Network Layer",
                "Routing Algorithms", "Transport Layer", "TCP/UDP",
                "Application Layer", "Network Security Basics",
            ],
            "weight": 8,
        },
        "Aptitude": {
            "topics": [
                "Verbal Ability", "Numerical Ability", "Logical Reasoning",
                "Data Interpretation",
            ],
            "weight": 15,
        },
    },
    "DA": {
        "Probability and Statistics": {
            "topics": [
                "Counting", "Probability Axioms", "Conditional Probability",
                "Random Variables", "Distributions", "Joint Distributions",
                "Limit Theorems", "Hypothesis Testing", "Estimation",
            ],
            "weight": 15,
        },
        "Linear Algebra": {
            "topics": [
                "Vector Spaces", "Eigenvalues & Eigenvectors",
                "Matrix Decomposition", "Linear Transformations",
                "Systems of Linear Equations",
            ],
            "weight": 10,
        },
        "Calculus & Optimization": {
            "topics": [
                "Single Variable Calculus", "Multivariable Calculus",
                "Convex Optimization", "Gradient Descent", "Constrained Optimization",
            ],
            "weight": 10,
        },
        "Programming & Data Structures": {
            "topics": [
                "Python Programming", "Arrays & Linked Lists",
                "Trees & Graphs", "Hashing", "Sorting",
            ],
            "weight": 10,
        },
        "Machine Learning": {
            "topics": [
                "Supervised Learning", "Regression", "Classification",
                "SVM", "Decision Trees", "Ensemble Methods",
                "Unsupervised Learning", "Clustering", "Dimensionality Reduction",
                "Neural Networks Basics",
            ],
            "weight": 20,
        },
        "AI": {
            "topics": [
                "Search Algorithms", "Logic & Reasoning",
                "Planning", "Probabilistic Reasoning",
            ],
            "weight": 10,
        },
        "Databases & SQL": {
            "topics": [
                "Relational Model", "SQL Queries", "Normalization",
                "NoSQL Basics", "Data Warehousing",
            ],
            "weight": 10,
        },
        "Aptitude": {
            "topics": [
                "Verbal Ability", "Numerical Ability", "Logical Reasoning",
                "Data Interpretation",
            ],
            "weight": 15,
        },
    },
    "ECE": {
        "Engineering Mathematics": {
            "topics": [
                "Linear Algebra", "Calculus", "Differential Equations",
                "Complex Analysis", "Probability & Statistics",
                "Numerical Methods",
            ],
            "weight": 13,
        },
        "Networks, Signals & Systems": {
            "topics": [
                "Network Analysis", "Signal Representation",
                "LTI Systems", "Fourier Transform", "Laplace Transform",
                "Z-Transform", "Sampling Theorem",
            ],
            "weight": 12,
        },
        "Electronic Devices": {
            "topics": [
                "Energy Bands", "Carrier Transport", "P-N Junction",
                "BJT", "MOSFET", "Photodiodes & LEDs",
            ],
            "weight": 8,
        },
        "Analog Circuits": {
            "topics": [
                "Small Signal Models", "Amplifiers", "Op-Amps",
                "Feedback & Oscillators", "Active Filters",
            ],
            "weight": 10,
        },
        "Digital Circuits": {
            "topics": [
                "Boolean Algebra", "Combinational Logic", "Sequential Logic",
                "Data Converters", "Semiconductor Memories",
            ],
            "weight": 8,
        },
        "Control Systems": {
            "topics": [
                "Transfer Function", "Block Diagrams", "Stability Analysis",
                "Root Locus", "Bode Plot", "State Space",
            ],
            "weight": 8,
        },
        "Communications": {
            "topics": [
                "Analog Modulation", "Digital Modulation", "Information Theory",
                "Error Correction Codes", "Spread Spectrum",
            ],
            "weight": 12,
        },
        "Electromagnetics": {
            "topics": [
                "Maxwell's Equations", "Plane Waves", "Transmission Lines",
                "Waveguides", "Antennas Basics",
            ],
            "weight": 10,
        },
        "Aptitude": {
            "topics": [
                "Verbal Ability", "Numerical Ability", "Logical Reasoning",
                "Data Interpretation",
            ],
            "weight": 15,
        },
    },
}

# Default fallback for branches not explicitly mapped
DEFAULT_SUBJECTS = {
    "Engineering Mathematics": {
        "topics": [
            "Linear Algebra", "Calculus", "Differential Equations",
            "Probability & Statistics", "Discrete Mathematics",
        ],
        "weight": 15,
    },
    "Aptitude": {
        "topics": [
            "Verbal Ability", "Numerical Ability", "Logical Reasoning",
        ],
        "weight": 15,
    },
}


def get_subjects_for_branch(branch: str) -> dict:
    """Return the subject→topics mapping for a given branch."""
    return GATE_SUBJECTS.get(branch.upper(), DEFAULT_SUBJECTS)


def get_topics_for_subject(branch: str, subject: str) -> list:
    """Return topics for a specific subject within a branch."""
    subjects = get_subjects_for_branch(branch)
    subject_data = subjects.get(subject, {})
    return subject_data.get("topics", [])
