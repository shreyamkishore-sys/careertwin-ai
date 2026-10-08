SIMULATION_MARKETS = {
    "IN": {
        "label": "India",
        "currency": "INR",
        "unit": "₹ lakh / year",
        "locale": "en-IN",
    },
    "US": {
        "label": "United States",
        "currency": "USD",
        "unit": "USD / year",
        "locale": "en-US",
    },
}

CAREER_SIMULATION_DATA = {
    "product-manager": {
        "stages": [
            {"year": 0, "role": "Associate Product Manager", "skills": ["Customer discovery", "Product metrics", "Communication"]},
            {"year": 2, "role": "Product Manager", "skills": ["Product strategy", "Roadmapping", "Stakeholder management"]},
            {"year": 4, "role": "Senior Product Manager", "skills": ["Experimentation", "Portfolio planning"]},
            {"year": 7, "role": "Group Product Manager", "skills": ["Team leadership", "Product portfolio strategy"]},
            {"year": 10, "role": "Product Director", "skills": ["Organization strategy", "Executive leadership"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 12, "high": 20}, {"year": 2, "low": 17, "high": 28}, {"year": 4, "low": 23, "high": 38}, {"year": 7, "low": 32, "high": 54}, {"year": 10, "low": 42, "high": 72}],
            "US": [{"year": 0, "low": 100000, "high": 150000}, {"year": 2, "low": 125000, "high": 185000}, {"year": 4, "low": 150000, "high": 225000}, {"year": 7, "low": 185000, "high": 280000}, {"year": 10, "low": 220000, "high": 340000}],
        },
    },
    "product-analyst": {
        "stages": [
            {"year": 0, "role": "Product Analyst", "skills": ["Product metrics", "SQL basics", "Data storytelling"]},
            {"year": 2, "role": "Product Analyst", "skills": ["Experiment design", "Stakeholder communication"]},
            {"year": 4, "role": "Senior Product Analyst", "skills": ["Product strategy", "Advanced analytics"]},
            {"year": 7, "role": "Product Manager", "skills": ["Roadmapping", "Cross-functional leadership"]},
            {"year": 10, "role": "Senior Product Manager", "skills": ["Portfolio strategy", "Team leadership"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 6, "high": 10}, {"year": 2, "low": 9, "high": 15}, {"year": 4, "low": 13, "high": 21}, {"year": 7, "low": 19, "high": 32}, {"year": 10, "low": 26, "high": 44}],
            "US": [{"year": 0, "low": 70000, "high": 105000}, {"year": 2, "low": 85000, "high": 125000}, {"year": 4, "low": 105000, "high": 155000}, {"year": 7, "low": 135000, "high": 200000}, {"year": 10, "low": 160000, "high": 240000}],
        },
    },
    "data-analyst": {
        "stages": [
            {"year": 0, "role": "Junior Data Analyst", "skills": ["Spreadsheets", "SQL basics", "Data visualization"]},
            {"year": 2, "role": "Data Analyst", "skills": ["SQL", "Dashboarding", "Business communication"]},
            {"year": 4, "role": "Senior Data Analyst", "skills": ["Statistical analysis", "Experimentation"]},
            {"year": 7, "role": "Analytics Lead", "skills": ["Analytics strategy", "Mentoring"]},
            {"year": 10, "role": "Analytics Manager", "skills": ["Team leadership", "Data governance"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 4, "high": 8}, {"year": 2, "low": 6, "high": 11}, {"year": 4, "low": 9, "high": 16}, {"year": 7, "low": 14, "high": 25}, {"year": 10, "low": 20, "high": 36}],
            "US": [{"year": 0, "low": 60000, "high": 90000}, {"year": 2, "low": 72000, "high": 108000}, {"year": 4, "low": 90000, "high": 135000}, {"year": 7, "low": 115000, "high": 175000}, {"year": 10, "low": 140000, "high": 210000}],
        },
    },
    "business-analyst": {
        "stages": [
            {"year": 0, "role": "Business Analyst", "skills": ["Requirements gathering", "Process mapping", "Spreadsheets"]},
            {"year": 2, "role": "Business Analyst", "skills": ["Facilitation", "Business cases"]},
            {"year": 4, "role": "Senior Business Analyst", "skills": ["Solution design", "Change management"]},
            {"year": 7, "role": "Business Analysis Lead", "skills": ["Practice leadership", "Portfolio planning"]},
            {"year": 10, "role": "Transformation Manager", "skills": ["Organizational strategy", "Executive communication"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 5, "high": 9}, {"year": 2, "low": 7, "high": 13}, {"year": 4, "low": 11, "high": 19}, {"year": 7, "low": 16, "high": 28}, {"year": 10, "low": 22, "high": 39}],
            "US": [{"year": 0, "low": 65000, "high": 95000}, {"year": 2, "low": 78000, "high": 115000}, {"year": 4, "low": 95000, "high": 145000}, {"year": 7, "low": 120000, "high": 180000}, {"year": 10, "low": 145000, "high": 220000}],
        },
    },
    "ux-researcher": {
        "stages": [
            {"year": 0, "role": "UX Research Assistant", "skills": ["Interviewing", "Usability testing", "Research ethics"]},
            {"year": 2, "role": "UX Researcher", "skills": ["Research planning", "Synthesis", "Workshop facilitation"]},
            {"year": 4, "role": "Senior UX Researcher", "skills": ["Mixed methods", "Research operations"]},
            {"year": 7, "role": "UX Research Lead", "skills": ["Research strategy", "Team mentorship"]},
            {"year": 10, "role": "Research Manager", "skills": ["Org-wide research practice", "People leadership"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 5, "high": 9}, {"year": 2, "low": 7, "high": 13}, {"year": 4, "low": 11, "high": 19}, {"year": 7, "low": 16, "high": 29}, {"year": 10, "low": 22, "high": 39}],
            "US": [{"year": 0, "low": 70000, "high": 105000}, {"year": 2, "low": 85000, "high": 125000}, {"year": 4, "low": 105000, "high": 155000}, {"year": 7, "low": 130000, "high": 195000}, {"year": 10, "low": 155000, "high": 230000}],
        },
    },
    "software-developer": {
        "stages": [
            {"year": 0, "role": "Junior Software Developer", "skills": ["Programming fundamentals", "Testing", "Version control"]},
            {"year": 2, "role": "Software Developer", "skills": ["System design basics", "Code review"]},
            {"year": 4, "role": "Senior Software Developer", "skills": ["Technical architecture", "Mentoring"]},
            {"year": 7, "role": "Staff Engineer", "skills": ["Technical strategy", "Cross-team influence"]},
            {"year": 10, "role": "Principal Engineer", "skills": ["Architecture leadership", "Long-term technical planning"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 5, "high": 10}, {"year": 2, "low": 8, "high": 15}, {"year": 4, "low": 13, "high": 24}, {"year": 7, "low": 21, "high": 40}, {"year": 10, "low": 30, "high": 58}],
            "US": [{"year": 0, "low": 75000, "high": 115000}, {"year": 2, "low": 95000, "high": 145000}, {"year": 4, "low": 125000, "high": 190000}, {"year": 7, "low": 165000, "high": 255000}, {"year": 10, "low": 200000, "high": 310000}],
        },
    },
    "project-manager": {
        "stages": [
            {"year": 0, "role": "Project Coordinator", "skills": ["Project planning", "Meeting facilitation", "Documentation"]},
            {"year": 2, "role": "Associate Project Manager", "skills": ["Risk tracking", "Budget basics"]},
            {"year": 4, "role": "Project Manager", "skills": ["Delivery leadership", "Stakeholder negotiation"]},
            {"year": 7, "role": "Senior Project Manager", "skills": ["Program management", "Change leadership"]},
            {"year": 10, "role": "Program Manager", "skills": ["Portfolio delivery", "Organizational leadership"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 5, "high": 9}, {"year": 2, "low": 7, "high": 13}, {"year": 4, "low": 11, "high": 20}, {"year": 7, "low": 16, "high": 30}, {"year": 10, "low": 23, "high": 42}],
            "US": [{"year": 0, "low": 65000, "high": 100000}, {"year": 2, "low": 80000, "high": 120000}, {"year": 4, "low": 100000, "high": 150000}, {"year": 7, "low": 125000, "high": 190000}, {"year": 10, "low": 150000, "high": 225000}],
        },
    },
    "marketing-strategist": {
        "stages": [
            {"year": 0, "role": "Marketing Associate", "skills": ["Audience research", "Copywriting", "Campaign basics"]},
            {"year": 2, "role": "Marketing Strategist", "skills": ["Channel planning", "Campaign analytics"]},
            {"year": 4, "role": "Senior Marketing Strategist", "skills": ["Brand strategy", "Budget ownership"]},
            {"year": 7, "role": "Marketing Manager", "skills": ["Team leadership", "Go-to-market planning"]},
            {"year": 10, "role": "Marketing Director", "skills": ["Business growth strategy", "Executive leadership"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 4, "high": 8}, {"year": 2, "low": 6, "high": 12}, {"year": 4, "low": 10, "high": 18}, {"year": 7, "low": 15, "high": 28}, {"year": 10, "low": 22, "high": 42}],
            "US": [{"year": 0, "low": 55000, "high": 85000}, {"year": 2, "low": 68000, "high": 105000}, {"year": 4, "low": 85000, "high": 135000}, {"year": 7, "low": 110000, "high": 180000}, {"year": 10, "low": 140000, "high": 230000}],
        },
    },
    "digital-marketing-manager": {
        "stages": [
            {"year": 0, "role": "Digital Marketing Specialist", "skills": ["Campaign analytics", "Audience research", "Channel basics"]},
            {"year": 2, "role": "Digital Marketing Manager", "skills": ["Channel strategy", "Experimentation", "AI-assisted campaign workflows"]},
            {"year": 4, "role": "Senior Digital Marketing Manager", "skills": ["Budget strategy", "Team leadership"]},
            {"year": 7, "role": "Growth Marketing Lead", "skills": ["Growth strategy", "Cross-channel planning"]},
            {"year": 10, "role": "Marketing Director", "skills": ["Business strategy", "Executive leadership"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 8, "high": 16}, {"year": 2, "low": 11, "high": 21}, {"year": 4, "low": 15, "high": 28}, {"year": 7, "low": 22, "high": 40}, {"year": 10, "low": 30, "high": 55}],
            "US": [{"year": 0, "low": 80000, "high": 130000}, {"year": 2, "low": 95000, "high": 150000}, {"year": 4, "low": 115000, "high": 180000}, {"year": 7, "low": 140000, "high": 220000}, {"year": 10, "low": 165000, "high": 260000}],
        },
    },
    "hr-analyst": {
        "stages": [
            {"year": 0, "role": "People Operations Analyst", "skills": ["Spreadsheets", "People processes", "Data privacy"]},
            {"year": 2, "role": "HR Analyst", "skills": ["People analytics", "HR systems", "Communication"]},
            {"year": 4, "role": "Senior HR Analyst", "skills": ["Workforce planning", "Data interpretation"]},
            {"year": 7, "role": "People Analytics Lead", "skills": ["Team leadership", "Workforce strategy"]},
            {"year": 10, "role": "People Analytics Manager", "skills": ["Organizational design", "Executive communication"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 5, "high": 10}, {"year": 2, "low": 7, "high": 13}, {"year": 4, "low": 10, "high": 18}, {"year": 7, "low": 15, "high": 27}, {"year": 10, "low": 21, "high": 38}],
            "US": [{"year": 0, "low": 65000, "high": 100000}, {"year": 2, "low": 75000, "high": 115000}, {"year": 4, "low": 90000, "high": 140000}, {"year": 7, "low": 110000, "high": 170000}, {"year": 10, "low": 130000, "high": 205000}],
        },
    },
    "data-scientist": {
        "stages": [
            {"year": 0, "role": "Junior Data Scientist", "skills": ["Python", "Statistics", "Data preparation"]},
            {"year": 2, "role": "Data Scientist", "skills": ["Model evaluation", "Experimentation"]},
            {"year": 4, "role": "Senior Data Scientist", "skills": ["Model design", "Business communication"]},
            {"year": 7, "role": "Lead Data Scientist", "skills": ["Technical leadership", "Model governance"]},
            {"year": 10, "role": "Data Science Manager", "skills": ["Team leadership", "Analytics strategy"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 7, "high": 14}, {"year": 2, "low": 10, "high": 20}, {"year": 4, "low": 15, "high": 29}, {"year": 7, "low": 23, "high": 43}, {"year": 10, "low": 32, "high": 60}],
            "US": [{"year": 0, "low": 95000, "high": 150000}, {"year": 2, "low": 115000, "high": 180000}, {"year": 4, "low": 140000, "high": 220000}, {"year": 7, "low": 175000, "high": 275000}, {"year": 10, "low": 210000, "high": 330000}],
        },
    },
    "financial-analyst": {
        "stages": [
            {"year": 0, "role": "Financial Analyst", "skills": ["Spreadsheets", "Financial reporting", "Business communication"]},
            {"year": 2, "role": "Senior Financial Analyst", "skills": ["Forecasting", "Financial modeling"]},
            {"year": 4, "role": "Finance Manager", "skills": ["Planning", "Stakeholder communication"]},
            {"year": 7, "role": "Finance Lead", "skills": ["Team leadership", "Strategic planning"]},
            {"year": 10, "role": "Finance Director", "skills": ["Portfolio oversight", "Executive communication"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 5, "high": 10}, {"year": 2, "low": 7, "high": 14}, {"year": 4, "low": 11, "high": 21}, {"year": 7, "low": 17, "high": 32}, {"year": 10, "low": 24, "high": 45}],
            "US": [{"year": 0, "low": 70000, "high": 110000}, {"year": 2, "low": 85000, "high": 130000}, {"year": 4, "low": 105000, "high": 165000}, {"year": 7, "low": 135000, "high": 210000}, {"year": 10, "low": 165000, "high": 260000}],
        },
    },
    "management-consultant": {
        "stages": [
            {"year": 0, "role": "Associate Consultant", "skills": ["Research", "Structured analysis", "Presentation"]},
            {"year": 2, "role": "Consultant", "skills": ["Client communication", "Problem framing"]},
            {"year": 4, "role": "Senior Consultant", "skills": ["Workstream leadership", "Change planning"]},
            {"year": 7, "role": "Engagement Manager", "skills": ["Team leadership", "Client strategy"]},
            {"year": 10, "role": "Principal Consultant", "skills": ["Portfolio strategy", "Executive advising"]},
        ],
        "salary": {
            "IN": [{"year": 0, "low": 8, "high": 16}, {"year": 2, "low": 12, "high": 23}, {"year": 4, "low": 18, "high": 34}, {"year": 7, "low": 27, "high": 50}, {"year": 10, "low": 38, "high": 70}],
            "US": [{"year": 0, "low": 90000, "high": 160000}, {"year": 2, "low": 115000, "high": 200000}, {"year": 4, "low": 150000, "high": 255000}, {"year": 7, "low": 200000, "high": 330000}, {"year": 10, "low": 250000, "high": 420000}],
        },
    },
}
