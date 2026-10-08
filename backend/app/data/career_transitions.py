from typing import TypedDict


class TransitionSkill(TypedDict):
    label: str
    profile_skills: list[str]
    partial_skills: list[str]
    profile_interests: list[str]


TRANSITION_SKILLS: dict[str, dict[str, list[TransitionSkill] | str]] = {
    "product-analyst": {
        "education": "No additional degree is generally required in this illustrative pathway; product analytics projects and cross-functional experience may help.",
        "responsibilities": "Analyze product usage, define measures, and partner with product teams on evidence-led decisions.",
        "requirements": [
            {"label": "Product metrics", "profile_skills": ["data_analysis", "statistics", "spreadsheets"], "partial_skills": ["problem_solving"], "profile_interests": ["analytics"]},
            {"label": "Product strategy", "profile_skills": [], "partial_skills": ["problem_solving", "data_analysis"], "profile_interests": ["business_strategy", "technology"]},
            {"label": "Communication", "profile_skills": ["communication", "writing"], "partial_skills": ["teamwork"], "profile_interests": ["communication"]},
            {"label": "Experimentation", "profile_skills": ["statistics", "data_analysis"], "partial_skills": ["problem_solving", "research"], "profile_interests": ["analytics", "research"]},
            {"label": "Stakeholder management", "profile_skills": ["communication", "teamwork"], "partial_skills": ["organization"], "profile_interests": ["leadership", "communication"]},
        ],
    },
    "product-manager": {
        "education": "An additional degree is not necessarily required in this illustrative pathway; product/business skills and relevant delivery experience are emphasized.",
        "responsibilities": "Frame customer problems, set product direction, coordinate a team, and evaluate outcomes.",
        "requirements": [
            {"label": "Product strategy", "profile_skills": [], "partial_skills": ["problem_solving", "data_analysis"], "profile_interests": ["business_strategy", "technology"]},
            {"label": "Roadmapping and prioritization", "profile_skills": ["organization"], "partial_skills": ["problem_solving", "teamwork"], "profile_interests": []},
            {"label": "Stakeholder management", "profile_skills": ["communication", "teamwork"], "partial_skills": ["organization"], "profile_interests": ["leadership", "communication"]},
            {"label": "Product metrics", "profile_skills": ["data_analysis", "statistics", "spreadsheets"], "partial_skills": ["problem_solving"], "profile_interests": ["analytics"]},
            {"label": "User research", "profile_skills": ["research", "communication"], "partial_skills": ["writing", "problem_solving"], "profile_interests": ["research", "helping_people"]},
            {"label": "Team leadership", "profile_skills": ["teamwork", "communication"], "partial_skills": ["organization"], "profile_interests": ["leadership"]},
        ],
    },
    "data-analyst": {
        "education": "A degree may be requested by some employers; requirements vary by role and employer. A portfolio can demonstrate applied analysis.",
        "responsibilities": "Prepare, analyze, and explain data to support operational or business decisions.",
        "requirements": [
            {"label": "Data analysis", "profile_skills": ["data_analysis", "statistics", "spreadsheets"], "partial_skills": ["problem_solving"], "profile_interests": ["analytics"]},
            {"label": "SQL / data tools", "profile_skills": ["coding", "data_analysis"], "partial_skills": ["statistics", "spreadsheets"], "profile_interests": ["technology"]},
            {"label": "Data communication", "profile_skills": ["communication", "writing"], "partial_skills": ["teamwork"], "profile_interests": ["communication"]},
            {"label": "Problem solving", "profile_skills": ["problem_solving"], "partial_skills": ["statistics", "research"], "profile_interests": ["analytics"]},
        ],
    },
    "business-analyst": {
        "education": "A related degree may be requested for some roles, but requirements vary; business-analysis methods and experience are also valued.",
        "responsibilities": "Clarify business needs, document processes, and help teams assess options.",
        "requirements": [
            {"label": "Requirements analysis", "profile_skills": ["problem_solving", "research"], "partial_skills": ["data_analysis", "writing"], "profile_interests": ["business_strategy"]},
            {"label": "Stakeholder communication", "profile_skills": ["communication", "teamwork"], "partial_skills": ["writing", "organization"], "profile_interests": ["communication"]},
            {"label": "Process and business analysis", "profile_skills": ["organization", "spreadsheets"], "partial_skills": ["problem_solving", "data_analysis"], "profile_interests": ["business_strategy", "analytics"]},
            {"label": "Documentation", "profile_skills": ["writing", "organization"], "partial_skills": ["communication"], "profile_interests": ["business_strategy"]},
        ],
    },
    "software-developer": {
        "education": "A computer science degree is not the only entry route, though some employers request one; a demonstrable technical portfolio is useful.",
        "responsibilities": "Design, implement, test, and maintain software systems.",
        "requirements": [
            {"label": "Programming", "profile_skills": ["coding"], "partial_skills": ["statistics", "problem_solving"], "profile_interests": ["technology"]},
            {"label": "Technical problem solving", "profile_skills": ["problem_solving", "statistics"], "partial_skills": ["data_analysis"], "profile_interests": ["technology", "analytics"]},
            {"label": "Testing and collaboration", "profile_skills": ["teamwork", "organization"], "partial_skills": ["problem_solving"], "profile_interests": ["technology"]},
        ],
    },
    "project-manager": {
        "education": "A degree or project-management certification can be requested by some employers, but requirements vary by sector and seniority.",
        "responsibilities": "Coordinate scope, timelines, risks, resources, and communication across a delivery team.",
        "requirements": [
            {"label": "Planning and organization", "profile_skills": ["organization"], "partial_skills": ["problem_solving", "spreadsheets"], "profile_interests": ["leadership"]},
            {"label": "Stakeholder communication", "profile_skills": ["communication", "teamwork"], "partial_skills": ["writing"], "profile_interests": ["communication", "leadership"]},
            {"label": "Risk and problem solving", "profile_skills": ["problem_solving"], "partial_skills": ["research", "organization"], "profile_interests": ["business_strategy"]},
            {"label": "Delivery coordination", "profile_skills": ["teamwork", "organization"], "partial_skills": ["communication"], "profile_interests": ["leadership"]},
        ],
    },
    "ux-researcher": {
        "education": "A research, design, psychology, or related background may help; requirements vary and a research portfolio can demonstrate methods.",
        "responsibilities": "Plan and conduct user research, synthesize findings, and communicate implications to product teams.",
        "requirements": [
            {"label": "User research", "profile_skills": ["research"], "partial_skills": ["writing", "data_analysis"], "profile_interests": ["research", "helping_people"]},
            {"label": "Research communication", "profile_skills": ["communication", "writing"], "partial_skills": ["teamwork"], "profile_interests": ["communication"]},
            {"label": "Synthesis and problem solving", "profile_skills": ["problem_solving", "data_analysis"], "partial_skills": ["research"], "profile_interests": ["analytics"]},
        ],
    },
    "marketing-strategist": {
        "education": "A marketing, communications, or related degree may be requested by some employers; campaign evidence and a portfolio are also relevant.",
        "responsibilities": "Research audiences, plan campaigns, and use performance data to refine messaging and channels.",
        "requirements": [
            {"label": "Audience research", "profile_skills": ["research"], "partial_skills": ["data_analysis", "communication"], "profile_interests": ["research"]},
            {"label": "Marketing communication", "profile_skills": ["writing", "communication"], "partial_skills": ["visual_design"], "profile_interests": ["communication", "design_creativity"]},
            {"label": "Campaign analytics", "profile_skills": ["data_analysis", "statistics"], "partial_skills": ["spreadsheets"], "profile_interests": ["analytics"]},
            {"label": "Planning and experimentation", "profile_skills": ["organization", "problem_solving"], "partial_skills": ["research"], "profile_interests": ["business_strategy"]},
        ],
    },
    "digital-marketing-manager": {
        "education": "A marketing-related degree may be requested by some employers; campaign evidence, analytics, and team experience can also be relevant.",
        "responsibilities": "Plan digital channel strategy, evaluate campaigns, and guide teams using audience and performance evidence.",
        "requirements": [
            {"label": "Campaign analytics", "profile_skills": ["data_analysis", "statistics"], "partial_skills": ["spreadsheets"], "profile_interests": ["analytics"]},
            {"label": "Digital content strategy", "profile_skills": ["writing", "visual_design"], "partial_skills": ["communication", "research"], "profile_interests": ["communication", "design_creativity"]},
            {"label": "Channel planning", "profile_skills": ["organization", "research"], "partial_skills": ["problem_solving"], "profile_interests": ["business_strategy"]},
            {"label": "Team and stakeholder leadership", "profile_skills": ["teamwork", "communication"], "partial_skills": ["organization"], "profile_interests": ["leadership"]},
        ],
    },
    "hr-analyst": {
        "education": "A business, psychology, human-resources, or quantitative background may help; requirements vary by employer and role.",
        "responsibilities": "Analyze workforce information, support people processes, and communicate careful, privacy-aware insights.",
        "requirements": [
            {"label": "People and workforce analysis", "profile_skills": ["data_analysis", "spreadsheets", "statistics"], "partial_skills": ["problem_solving"], "profile_interests": ["analytics"]},
            {"label": "Research and data care", "profile_skills": ["research", "organization"], "partial_skills": ["problem_solving"], "profile_interests": ["research"]},
            {"label": "People communication", "profile_skills": ["communication", "writing"], "partial_skills": ["teamwork"], "profile_interests": ["helping_people", "communication"]},
            {"label": "Process improvement", "profile_skills": ["organization", "problem_solving"], "partial_skills": ["data_analysis"], "profile_interests": ["business_strategy"]},
        ],
    },
    "data-scientist": {
        "education": "Quantitative or computing study may support some roles; requirements vary. Portfolio evidence and statistical reasoning are relevant in this illustrative pathway.",
        "responsibilities": "Explore data, build and evaluate statistical or machine-learning models, and communicate limitations and findings.",
        "requirements": [
            {"label": "Statistical analysis", "profile_skills": ["statistics", "data_analysis"], "partial_skills": ["problem_solving"], "profile_interests": ["analytics", "research"]},
            {"label": "Programming and data tools", "profile_skills": ["coding", "data_analysis"], "partial_skills": ["statistics", "spreadsheets"], "profile_interests": ["technology"]},
            {"label": "Model evaluation", "profile_skills": ["statistics", "problem_solving"], "partial_skills": ["research", "data_analysis"], "profile_interests": ["analytics"]},
            {"label": "Communicating uncertainty", "profile_skills": ["communication", "writing"], "partial_skills": ["teamwork"], "profile_interests": ["communication"]},
        ],
    },
    "financial-analyst": {
        "education": "Finance, accounting, business, or quantitative study may help; requirements vary by employer and role. Spreadsheet and financial analysis evidence is relevant in this illustrative pathway.",
        "responsibilities": "Analyze financial performance, prepare forecasts and scenarios, and communicate assumptions to decision makers.",
        "requirements": [
            {"label": "Spreadsheet and financial analysis", "profile_skills": ["spreadsheets", "data_analysis"], "partial_skills": ["statistics"], "profile_interests": ["analytics"]},
            {"label": "Forecasting and assumptions", "profile_skills": ["statistics", "problem_solving"], "partial_skills": ["research", "data_analysis"], "profile_interests": ["business_strategy"]},
            {"label": "Business communication", "profile_skills": ["communication", "writing"], "partial_skills": ["teamwork"], "profile_interests": ["communication"]},
            {"label": "Data quality and documentation", "profile_skills": ["organization", "research"], "partial_skills": ["spreadsheets"], "profile_interests": ["research"]},
        ],
    },
    "management-consultant": {
        "education": "Relevant degrees and postgraduate qualifications may be requested by some employers; requirements vary. Structured problem solving, communication, and evidence of delivery are relevant in this illustrative pathway.",
        "responsibilities": "Frame organizational questions, analyze evidence, facilitate stakeholder discussions, and support practical change plans.",
        "requirements": [
            {"label": "Structured problem solving", "profile_skills": ["problem_solving", "research"], "partial_skills": ["data_analysis", "statistics"], "profile_interests": ["business_strategy", "analytics"]},
            {"label": "Client communication", "profile_skills": ["communication", "writing"], "partial_skills": ["teamwork"], "profile_interests": ["communication"]},
            {"label": "Quantitative and business analysis", "profile_skills": ["data_analysis", "spreadsheets"], "partial_skills": ["statistics", "problem_solving"], "profile_interests": ["analytics", "business_strategy"]},
            {"label": "Facilitation and change", "profile_skills": ["teamwork", "organization"], "partial_skills": ["communication"], "profile_interests": ["leadership"]},
        ],
    },
}


# Directed edges describe supported adjacent-role transitions in this prototype.
CAREER_TRANSITION_EDGES: dict[str, list[str]] = {
    "data-analyst": ["product-analyst", "product-manager", "business-analyst", "software-developer", "data-scientist", "financial-analyst", "management-consultant"],
    "product-analyst": ["product-manager", "data-analyst", "business-analyst", "data-scientist", "management-consultant"],
    "business-analyst": ["product-manager", "product-analyst", "project-manager", "marketing-strategist", "hr-analyst", "financial-analyst", "management-consultant"],
    "software-developer": ["product-analyst", "project-manager"],
    "ux-researcher": ["product-analyst", "marketing-strategist"],
    "project-manager": ["product-manager", "business-analyst", "marketing-strategist", "hr-analyst"],
    "marketing-strategist": ["product-analyst", "project-manager", "business-analyst", "digital-marketing-manager"],
    "digital-marketing-manager": ["marketing-strategist", "product-analyst", "business-analyst", "project-manager"],
    "hr-analyst": ["business-analyst", "project-manager", "financial-analyst"],
    "product-manager": ["product-analyst", "project-manager", "business-analyst", "management-consultant"],
    "data-scientist": ["data-analyst", "product-analyst", "financial-analyst", "management-consultant"],
    "financial-analyst": ["business-analyst", "data-analyst", "management-consultant"],
    "management-consultant": ["business-analyst", "project-manager", "financial-analyst", "product-manager"],
}

PREFERRED_TRANSITION_PATHS: dict[tuple[str, str], list[str]] = {
    ("data-analyst", "product-manager"): ["data-analyst", "product-analyst", "product-manager"],
}
