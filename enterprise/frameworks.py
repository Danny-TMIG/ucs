"""frameworks.py — reference frames for enterprise classification.

Three canonical enterprise taxonomies, encoded as data:

  Forbes Global 2000 sectors  — 12 broad sectors, 60+ industries
  Fortune 500 functional orgs — 14 standard C-suite functions
  Gartner technology stack    — 9 layers, 40+ categories
  Gartner Hype Cycle phases   — 5 phases

Each is a fixed, finite list. Every artifact on disk gets classified
against each frame by rules over its path and content.
"""

from __future__ import annotations

# ── Forbes Global 2000 sectors ────────────────────────────────────────
FORBES_SECTORS = {
    "Aerospace & Defense": ["Aerospace", "Defense", "Space"],
    "Business Services & Supplies": [
        "Consulting",
        "Outsourcing",
        "Staffing",
        "Printing",
        "Office",
    ],
    "Capital Goods": [
        "Industrial Machinery",
        "Electrical Equipment",
        "Construction",
        "Engineering",
        "Heavy Equipment",
    ],
    "Chemicals": ["Basic Chemicals", "Specialty Chemicals", "Agrochemicals"],
    "Conglomerates": ["Diversified Holdings"],
    "Construction": ["Building Materials", "Homebuilding", "Infrastructure"],
    "Consumer Durables": ["Appliances", "Electronics", "Furniture", "Textiles"],
    "Diversified Financials": [
        "Banking",
        "Insurance",
        "Asset Mgmt",
        "Payments",
        "Capital Markets",
    ],
    "Energy": ["Oil & Gas", "Renewables", "Utilities", "Pipelines"],
    "Food, Drink & Tobacco": ["Food", "Beverages", "Tobacco", "Agriculture"],
    "Healthcare": [
        "Pharma",
        "Biotech",
        "Medical Devices",
        "Providers",
        "Health Insurers",
        "Life Sciences",
    ],
    "Hotels, Restaurants & Leisure": [
        "Hotels",
        "Restaurants",
        "Travel",
        "Gaming",
        "Cruise",
    ],
    "Household & Personal Products": ["Consumer Packaged Goods", "Cosmetics"],
    "Insurance": ["Life", "Property", "Reinsurance", "Brokers"],
    "Materials": ["Metals", "Mining", "Forestry", "Paper"],
    "Media": ["Publishing", "Broadcasting", "Entertainment", "Advertising"],
    "Oil & Gas Operations": ["Upstream", "Midstream", "Downstream"],
    "Retailing": ["Apparel", "Specialty", "Discount", "E-commerce", "Grocery"],
    "Semiconductors": ["Design", "Foundry", "Equipment", "EDA", "IP"],
    "Software & Services": [
        "SaaS",
        "Infrastructure",
        "Applications",
        "Security",
        "Data",
        "AI/ML",
    ],
    "Technology Hardware": ["Computers", "Storage", "Networking", "Peripherals"],
    "Telecommunications": ["Carriers", "Equipment", "Satellite"],
    "Transportation": ["Airlines", "Rail", "Trucking", "Shipping", "Logistics"],
    "Trading Companies": ["Wholesale", "Distribution"],
    "Utilities": ["Electric", "Gas", "Water", "Renewables"],
}

# ── Fortune 500 functional orgs (C-suite) ─────────────────────────────
FORTUNE_FUNCTIONS = {
    "CEO": ["Strategy", "Corporate Development", "Investor Relations"],
    "CFO": ["Finance", "Accounting", "Treasury", "Tax", "Audit"],
    "COO": ["Operations", "Supply Chain", "Manufacturing", "Logistics"],
    "CTO": ["Technology", "Engineering", "Architecture", "Platform"],
    "CIO": ["IT", "Infrastructure", "Applications", "Data Center"],
    "CISO": ["Security", "Compliance", "Risk", "Privacy"],
    "CDO": ["Data", "Analytics", "AI/ML", "Insights"],
    "CMO": ["Marketing", "Brand", "Demand Gen", "Comms"],
    "CRO": ["Revenue", "Sales", "Partnerships", "Channels"],
    "CHRO": ["People", "Talent", "HR", "Culture"],
    "CLO": ["Legal", "Contracts", "IP", "Regulatory"],
    "CPO": ["Product", "Design", "Roadmap", "UX"],
    "CSO": ["Sustainability", "ESG", "Public Policy"],
    "CKO": ["Knowledge", "Documentation", "Learning", "Enablement"],
}

# ── Gartner technology stack ──────────────────────────────────────────
GARTNER_LAYERS = {
    "Infrastructure": [
        "Compute",
        "Storage",
        "Network",
        "Edge",
        "Data Center",
        "Cloud",
        "IaaS",
    ],
    "Platform": [
        "PaaS",
        "Containers",
        "Serverless",
        "Orchestration",
        "Integration",
        "API Management",
        "iPaaS",
    ],
    "Data": [
        "DBMS",
        "Data Warehouse",
        "Data Lake",
        "Lakehouse",
        "Streaming",
        "Vector DB",
        "Graph DB",
    ],
    "Application": [
        "ERP",
        "CRM",
        "HCM",
        "SCM",
        "Vertical SaaS",
        "Custom Apps",
        "Low-Code",
    ],
    "AI/ML": [
        "Foundation Models",
        "MLOps",
        "Feature Stores",
        "Vector Search",
        "Agents",
        "RAG",
        "Governance",
    ],
    "Security": [
        "IAM",
        "Endpoint",
        "Network",
        "Cloud Security",
        "Zero Trust",
        "SIEM",
        "SOAR",
        "Data Security",
    ],
    "Observability": ["APM", "Logs", "Metrics", "Traces", "AIOps"],
    "DevOps": [
        "CI/CD",
        "Source Control",
        "Artifacts",
        "Testing",
        "IaC",
        "Secrets",
        "SRE",
    ],
    "End-User": ["Endpoints", "Collaboration", "Productivity", "Browsers", "VDI"],
}

# ── Gartner Hype Cycle phases ─────────────────────────────────────────
HYPE_PHASES = [
    "Innovation Trigger",
    "Peak of Inflated Expectations",
    "Trough of Disillusionment",
    "Slope of Enlightenment",
    "Plateau of Productivity",
]

# ── Market position quadrant (Magic Quadrant) ─────────────────────────
MAGIC_QUADRANT = [
    "Leaders",
    "Challengers",
    "Visionaries",
    "Niche Players",
]
