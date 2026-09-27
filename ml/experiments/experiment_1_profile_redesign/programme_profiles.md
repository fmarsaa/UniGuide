# Experiment 1 — Programme Profile Audit (all 40 programmes)

Locked template (see conversation for full derivation):

- **Academic pattern** — general tendency, not admission eligibility (real KUCCPS
  minimums stay exclusively in `programmes_catalog.py`, never restated here)
- **Interests** — field-level interests, Form-4-appropriate
- **Skills** — realistic abilities a Form-4 leaver could plausibly self-assess,
  not professional expertise they haven't acquired yet
- **Strengths** — broader personal/learning characteristics
- **Aspirations** — multiple plausible careers, deliberately NOT programme-exclusive
- **Confusable with** — explicitly acknowledged overlapping programmes
- **Distinguishing profile pattern** — a *combination* of signals, never a single
  giveaway feature

Three-tier characteristic model:
1. **Programme-associated** — the tags below, moderately-to-strongly weighted
2. **Shared characteristics** — see "Cross-cutting shared tags" section; legitimately
   common across many unrelated programmes, by design
3. **Individual variation** — every synthetic student receives a random subset of
   their programme's associated tags, not the full bundle (already how
   `_build_profile()`'s `k=random.randint(2,3)` sampling works)

**Mutuality check**: "Confusable with" listings were cross-checked pairwise
across all 40 (if A lists B, B lists A). 12 programmes needed correction —
some got a missing mutual link added (e.g. Nursing was missing Pharmacy/
Dental/Vet, which all already pointed to it); others had a one-directional,
weakly-realistic link removed instead of forced into symmetry (e.g. dropped
Civil Engineering from EEE's list rather than adding EEE to Civil's, since
electrical systems and infrastructure aren't a strong realistic overlap).

---

## Cluster 1: Medicine & Health Sciences

### Bachelor of Medicine and Bachelor of Surgery (MBChB) — LOCKED (round 3)
- Academic pattern: Strong performance in Biology and Chemistry, with generally strong Mathematics and other relevant science subjects.
- Interests: `human_health, biology_and_disease, patient_care, medical_science`
- Skills: `scientific_reasoning, analytical_thinking, attention_to_detail, communication, decision_making`
- Strengths: `resilience, empathy, composure_under_pressure, meticulousness`
- Aspirations: `physician, surgeon, medical_researcher, healthcare_professional`
- Confusable with: Pharmacy, Dental Surgery, Nursing, Veterinary Medicine
- Distinguishing profile pattern: Strong science performance combined with a genuine interest in human health, disease and patient care — distinct from neighbours' narrower foci (drugs for Pharmacy, oral health for Dental, ongoing bedside care for Nursing, animal health for Vet).

### Bachelor of Pharmacy (BPharm)
- Academic pattern: Strong performance in Chemistry and Biology, with generally strong Mathematics and other sciences.
- Interests: `pharmaceutical_science, medicines_and_drugs, chemistry_applications, healthcare`
- Skills: `chemical_reasoning, attention_to_detail, scientific_reasoning, analytical_thinking`
- Strengths: `precision, meticulousness, patience`
- Aspirations: `pharmacist, pharmaceutical_scientist, drug_researcher, healthcare_professional`
- Confusable with: Medicine, Dental Surgery, Industrial Chemistry, Nursing, Microbiology
- Distinguishing profile pattern: Strong chemistry/biology combined with specific interest in medicines, drug formulation and pharmaceutical science.

### Bachelor of Science in Nursing
- Academic pattern: Generally strong Biology and Chemistry, solid Mathematics and English.
- Interests: `patient_care, human_health, community_health, helping_others`
- Skills: `communication, attention_to_detail, teamwork, practical_care_orientation`
- Strengths: `empathy, resilience, composure_under_pressure`
- Aspirations: `nurse, clinical_care_specialist, public_health_officer, healthcare_professional`
- Confusable with: Medicine, Public Health, Nutrition and Dietetics, Pharmacy, Dental Surgery, Veterinary Medicine
- Distinguishing profile pattern: Strong science performance combined with an ongoing, hands-on patient-care orientation, rather than Medicine's diagnostic/surgical focus.

### Bachelor of Dental Surgery (BDS)
- Academic pattern: Strong Biology and Chemistry, generally strong Mathematics.
- Interests: `oral_health, human_health, biology_and_disease, patient_care`
- Skills: `attention_to_detail, manual_dexterity_interest, scientific_reasoning, communication`
- Strengths: `precision, patience, composure_under_pressure`
- Aspirations: `dentist, oral_health_professional, healthcare_professional`
- Confusable with: Medicine, Pharmacy, Nursing
- Distinguishing profile pattern: Strong science performance combined with specific interest in oral/dental health.

### Bachelor of Veterinary Medicine (BVM)
- Academic pattern: Generally strong Biology and Chemistry, solid Mathematics.
- Interests: `animal_health, biology_and_disease, agriculture_and_animals, science`
- Skills: `scientific_reasoning, attention_to_detail, practical_problem_solving, communication`
- Strengths: `empathy, resilience, composure_under_pressure`
- Aspirations: `veterinary_doctor, animal_health_officer, wildlife_health_professional`
- Confusable with: Medicine, Agriculture, Nursing
- Distinguishing profile pattern: Science-strong profile combined with an interest in animal (not human) health.

### Bachelor of Science in Food, Nutrition and Dietetics
- Academic pattern: Generally solid Biology and Chemistry, variable Mathematics.
- Interests: `food_and_nutrition, human_health, wellbeing, community_health`
- Skills: `analytical_thinking, communication, attention_to_detail, practical_problem_solving`
- Strengths: `empathy, organisation, communication`
- Aspirations: `nutritionist, dietitian, public_health_nutrition_officer, food_service_professional`
- Confusable with: Nursing, Public Health, Agriculture, Food Science and Technology
- Distinguishing profile pattern: Health-oriented profile centred specifically on food, diet and nutrition.

### Bachelor of Science in Public Health
- Academic pattern: Generally strong Biology and Chemistry, solid Mathematics and English.
- Interests: `community_health, disease_prevention, health_policy, social_wellbeing`
- Skills: `analytical_thinking, communication, community_engagement, attention_to_detail`
- Strengths: `empathy, organisation, communication`
- Aspirations: `public_health_officer, health_promotion_officer, epidemiologist, community_health_professional`
- Confusable with: Nursing, Nutrition and Dietetics, Sociology, Social Work
- Distinguishing profile pattern: Science background combined with a population/community-level (not individual clinical) health orientation.

---

## Cluster 9: Computing & Pure/Applied Sciences

### Bachelor of Science in Informatics and Computer Science (ICS)
- Academic pattern: Strong Mathematics, generally solid relevant technical/science subjects.
- Interests: `technology, computing_theory, artificial_intelligence, data_and_information`
- Skills: `programming, algorithmic_thinking, analytical_thinking, logical_reasoning`
- Strengths: `curiosity, logical_thinking, persistence`
- Aspirations: `software_developer, data_scientist, AI_specialist, systems_architect`
- Confusable with: Software Engineering, BBIT, Mathematics, Statistics
- Distinguishing profile pattern: Broad computing-theory and data-oriented interest, rather than SE's software-construction focus specifically.

### Bachelor of Science in Software Engineering — LOCKED (round 3)
- Academic pattern: Strong Mathematics, with generally solid performance in relevant technical/science subjects.
- Interests: `technology, software_development, digital_systems, problem_solving`
- Skills: `programming, debugging, algorithmic_thinking, structured_problem_solving`
- Strengths: `persistence, logical_thinking`
- Aspirations: `software_developer, mobile_app_developer, systems_developer, devops_engineer`
- Confusable with: ICS, BBIT
- Distinguishing profile pattern: Strong orientation toward designing, developing and maintaining software systems, with programming and structured technical problem-solving forming a central combination.

### Bachelor of Science in Business Information Technology (BBIT) — LOCKED (round 3)
- Academic pattern: Generally solid Mathematics and English performance; variable elsewhere.
- Interests: `technology, business_systems, organisational_processes, entrepreneurship`
- Skills: `business_process_analysis, organisational_technology_interest, communication, structured_problem_solving`
- Strengths: `practical_problem_solving, organisational_thinking`
- Aspirations: `IT_business_analyst, business_systems_administrator, IT_project_coordinator, entrepreneur`
- Confusable with: Software Engineering, ICS, BCom, Business Management
- Distinguishing profile pattern: Applying information technology to business and organisational processes, combining a genuine technical interest with business/organisational orientation.

### Bachelor of Science in Industrial Chemistry
- Academic pattern: Generally solid Mathematics, Physics and Chemistry.
- Interests: `chemistry_applications, industrial_processes, materials_science, laboratory_science`
- Skills: `chemical_reasoning, laboratory_technique_interest, analytical_thinking, attention_to_detail`
- Strengths: `precision, curiosity, methodical_thinking`
- Aspirations: `industrial_chemist, quality_control_analyst, chemical_process_professional`
- Confusable with: Pharmacy, Microbiology, Chemical Engineering
- Distinguishing profile pattern: Chemistry-centred interest applied to industrial/manufacturing processes rather than medicine or biological research.

### Bachelor of Science in Microbiology
- Academic pattern: Generally solid Mathematics, Biology and Chemistry.
- Interests: `microorganisms, laboratory_science, biology_and_disease, research`
- Skills: `scientific_reasoning, laboratory_technique_interest, analytical_thinking, attention_to_detail`
- Strengths: `curiosity, precision, methodical_thinking`
- Aspirations: `microbiologist, laboratory_scientist, research_scientist`
- Confusable with: Industrial Chemistry, Food Science and Technology, Pharmacy
- Distinguishing profile pattern: Biology/chemistry combination centred specifically on microorganisms and laboratory research.

### Bachelor of Science in Food Science and Technology
- Academic pattern: Generally solid Biology, Chemistry and Mathematics.
- Interests: `food_and_nutrition, industrial_processes, laboratory_science, quality_and_safety`
- Skills: `scientific_reasoning, analytical_thinking, attention_to_detail, practical_problem_solving`
- Strengths: `precision, curiosity, methodical_thinking`
- Aspirations: `food_technologist, quality_assurance_professional, product_development_scientist`
- Confusable with: Nutrition and Dietetics, Microbiology, Agriculture
- Distinguishing profile pattern: Science applied to food processing, safety and product development, rather than clinical nutrition or agricultural production.

### Bachelor of Science in Statistics
- Academic pattern: Strong Mathematics, generally solid relevant science subjects.
- Interests: `data_and_information, quantitative_analysis, research, probability_and_patterns`
- Skills: `quantitative_reasoning, analytical_thinking, logical_reasoning, attention_to_detail`
- Strengths: `curiosity, logical_thinking, persistence`
- Aspirations: `statistician, data_analyst, research_analyst`
- Confusable with: Mathematics, Actuarial Science, Economics, ICS
- Distinguishing profile pattern: Mathematical strength applied specifically to data/probability analysis.

### Bachelor of Science in Mathematics
- Academic pattern: Strong Mathematics, generally solid relevant science subjects.
- Interests: `abstract_reasoning, quantitative_analysis, problem_solving, patterns_and_structures`
- Skills: `quantitative_reasoning, logical_reasoning, analytical_thinking, abstract_thinking`
- Strengths: `curiosity, persistence, logical_thinking`
- Aspirations: `mathematician, data_analyst, statistician, research_analyst`
- Confusable with: Statistics, Economics, Actuarial Science, ICS
- Distinguishing profile pattern: Strong quantitative ability without a specific applied-domain interest (markets, computing, data specifically) — the "purer" mathematics profile among its confusable neighbours.

---

## Cluster 5: Engineering & Technology

### Bachelor of Science in Electrical and Electronic Engineering (EEE)
- Academic pattern: Strong Mathematics and Physics, generally solid Chemistry.
- Interests: `electrical_systems, electronics, technology, energy_systems`
- Skills: `mathematical_problem_solving, technical_reasoning, spatial_reasoning, practical_problem_solving`
- Strengths: `methodical_thinking, practical_engineering_mindset, curiosity`
- Aspirations: `electrical_engineer, electronics_engineer, telecommunications_engineer`
- Confusable with: Mechanical Engineering
- Distinguishing profile pattern: Orientation toward electrical/electronic systems and energy, distinct from Mechanical's motion/machines and Civil's static structures.

### Bachelor of Science in Civil Engineering — LOCKED (round 3)
- Academic pattern: Strong Mathematics and Physics, solid Chemistry.
- Interests: `built_environment, infrastructure, construction, urban_development`
- Skills: `spatial_reasoning, mathematical_problem_solving, visualising_structures, practical_problem_solving`
- Strengths: `methodical_thinking, practical_engineering_mindset`
- Aspirations: `structural_engineer, construction_project_engineer, infrastructure_planner`
- Confusable with: Mechanical Engineering, Architecture, Quantity Surveying, Geomatics and Geospatial Information Systems
- Distinguishing profile pattern: Orientation toward the built environment, infrastructure and structures, distinct from Mechanical's orientation toward machines, mechanisms and motion.

### Bachelor of Science in Mechanical Engineering
- Academic pattern: Strong Mathematics and Physics, generally solid Chemistry.
- Interests: `machines_and_mechanisms, motion_and_energy, manufacturing, technology`
- Skills: `mathematical_problem_solving, technical_reasoning, spatial_reasoning, practical_problem_solving`
- Strengths: `methodical_thinking, practical_engineering_mindset, curiosity`
- Aspirations: `mechanical_engineer, automotive_engineer, manufacturing_engineer`
- Confusable with: Civil Engineering, Electrical and Electronic Engineering, Chemical Engineering
- Distinguishing profile pattern: Orientation toward machines, mechanisms and motion, distinct from Civil's static infrastructure and EEE's electrical systems focus.

### Bachelor of Engineering in Chemical Engineering
- Academic pattern: Strong Mathematics, Physics and Chemistry.
- Interests: `chemical_processes, industrial_systems, energy_and_materials, technology`
- Skills: `mathematical_problem_solving, chemical_reasoning, technical_reasoning, practical_problem_solving`
- Strengths: `methodical_thinking, practical_engineering_mindset, curiosity`
- Aspirations: `chemical_engineer, process_engineer, manufacturing_engineer`
- Confusable with: Mechanical Engineering, Industrial Chemistry
- Distinguishing profile pattern: Combines strong chemistry with engineering/process-design orientation, distinct from Industrial Chemistry's more laboratory/analytical focus.

---

## Cluster 4: Built Environment & Geosciences

### Bachelor of Architecture
- Academic pattern: Generally solid Mathematics and Physics, variable elsewhere.
- Interests: `design, built_environment, aesthetics_and_function, urban_spaces`
- Skills: `spatial_reasoning, visualising_structures, creative_design_thinking, practical_problem_solving`
- Strengths: `creativity, methodical_thinking, attention_to_detail`
- Aspirations: `architect, urban_designer, interior_architect`
- Confusable with: Civil Engineering, Quantity Surveying, Urban and Regional Planning
- Distinguishing profile pattern: Design/aesthetic and spatial-creativity orientation toward buildings, distinct from Civil's structural-engineering focus and QS's cost focus.

### Bachelor of Quantity Surveying
- Academic pattern: Generally solid Mathematics and Physics, variable elsewhere.
- Interests: `construction_industry, cost_and_economics, built_environment, project_management`
- Skills: `quantitative_reasoning, attention_to_detail, analytical_thinking, practical_problem_solving`
- Strengths: `methodical_thinking, organisation, precision`
- Aspirations: `quantity_surveyor, construction_cost_consultant, project_estimator`
- Confusable with: Civil Engineering, Architecture, Real Estate Management
- Distinguishing profile pattern: Construction-industry interest centred on cost, measurement and contracts rather than structural design or aesthetics.

### Bachelor of Science in Real Estate Management
- Academic pattern: Generally solid Mathematics, variable elsewhere.
- Interests: `property_and_land, business_and_investment, built_environment, market_analysis`
- Skills: `quantitative_reasoning, communication, analytical_thinking, negotiation_interest`
- Strengths: `organisation, communication, practical_thinking`
- Aspirations: `real_estate_manager, property_valuer, facilities_manager`
- Confusable with: Quantity Surveying, Urban and Regional Planning
- Distinguishing profile pattern: Property/investment and market-analysis orientation, distinct from QS's construction-cost focus.

### Bachelor of Urban and Regional Planning
- Academic pattern: Generally solid Mathematics and Geography, variable elsewhere.
- Interests: `urban_development, built_environment, public_policy, community_spaces`
- Skills: `analytical_thinking, spatial_reasoning, communication, practical_problem_solving`
- Strengths: `methodical_thinking, communication, organisation`
- Aspirations: `urban_planner, regional_development_officer, policy_analyst`
- Confusable with: Architecture, Geomatics, Real Estate Management
- Distinguishing profile pattern: Public/community-level spatial planning orientation, distinct from Architecture's building-level design.

### Bachelor of Science in Geomatics and Geospatial Information Systems
- Academic pattern: Strong Mathematics and Physics, generally solid Geography.
- Interests: `land_and_mapping, geospatial_technology, surveying, data_and_information`
- Skills: `spatial_reasoning, quantitative_reasoning, technical_reasoning, attention_to_detail`
- Strengths: `precision, methodical_thinking, curiosity`
- Aspirations: `land_surveyor, GIS_analyst, remote_sensing_specialist`
- Confusable with: Civil Engineering, Urban and Regional Planning
- Distinguishing profile pattern: Combines spatial/mathematical strength with land-measurement and geospatial-data technology specifically.

---

## Cluster 6/7: Business, Finance & Mathematics-adjacent

### Bachelor of Science in Actuarial Science
- Academic pattern: Strong Mathematics, generally solid English.
- Interests: `risk_and_finance, quantitative_analysis, insurance_and_pensions, problem_solving`
- Skills: `quantitative_reasoning, analytical_thinking, logical_reasoning, attention_to_detail`
- Strengths: `precision, persistence, logical_thinking`
- Aspirations: `actuary, risk_analyst, investment_analyst`
- Confusable with: Mathematics, Statistics, Economics, BCom
- Distinguishing profile pattern: Very strong mathematics combined specifically with financial-risk and insurance interest.

### Bachelor of Commerce (BCom) - Finance & Accounting
- Academic pattern: Generally solid Mathematics and English, variable elsewhere.
- Interests: `business_and_finance, accounting, investment, organisations`
- Skills: `quantitative_reasoning, attention_to_detail, analytical_thinking, communication`
- Strengths: `organisation, precision, communication`
- Aspirations: `financial_analyst, accountant, investment_professional`
- Confusable with: Economics, Actuarial Science, Business Management, HR Management, BBIT, International Business Management
- Distinguishing profile pattern: Business/finance orientation centred on accounting and organisational finance rather than macro-level policy/markets (Economics) or people-management (HR).

### Bachelor of Economics — LOCKED (round 3)
- Academic pattern: Strong Mathematics, with varied performance across humanities/business-related subjects.
- Interests: `markets_economics, public_policy, national_development, social_systems`
- Skills: `quantitative_reasoning, interpreting_information, analytical_thinking, communicating_conclusions`
- Strengths: `analytical_reasoning, interest_in_current_affairs`
- Aspirations: `economist, policy_analyst, financial_analyst, development_researcher`
- Confusable with: Mathematics, Statistics, Actuarial Science, BCom
- Distinguishing profile pattern: Strong-but-not-necessarily-top-tier mathematics combined with a genuine interest in markets, policy and society.

### Bachelor of Business Management
- Academic pattern: Generally solid Mathematics and English, variable elsewhere.
- Interests: `business_and_organisations, leadership, entrepreneurship, management`
- Skills: `communication, organisation, analytical_thinking, leadership_interest`
- Strengths: `communication, organisation, adaptability`
- Aspirations: `business_manager, entrepreneur, management_trainee`
- Confusable with: BCom, BBIT, HR Management, International Business Management
- Distinguishing profile pattern: General organisational/leadership orientation without a specific finance, technology or people-management specialisation.

### Bachelor of Science in Human Resource Management
- Academic pattern: Generally solid English and Mathematics, variable elsewhere.
- Interests: `people_and_organisations, workplace_culture, business_and_organisations, communication`
- Skills: `communication, organisation, interpersonal_understanding, analytical_thinking`
- Strengths: `communication, empathy, organisation`
- Aspirations: `human_resource_officer, talent_professional, training_and_development_officer`
- Confusable with: Business Management, BCom, Counseling Psychology
- Distinguishing profile pattern: Business/organisational orientation specifically centred on people-management, recruitment and workplace culture.

### Bachelor of Science in International Business Management
- Academic pattern: Generally solid Mathematics and English, variable elsewhere.
- Interests: `global_trade, business_and_organisations, cultures_and_markets, economics`
- Skills: `communication, analytical_thinking, organisation, cross_cultural_interest`
- Strengths: `adaptability, communication, organisation`
- Aspirations: `international_trade_officer, global_business_analyst, export_import_manager`
- Confusable with: Business Management, BCom
- Distinguishing profile pattern: Business orientation specifically toward global/cross-border trade and markets, distinct from domestic-focused Business Management/BCom.

---

## Cluster 3: Law, Media & Social Sciences

### Bachelor of Laws (LLB)
- Academic pattern: Generally strong English and Kiswahili, solid Mathematics.
- Interests: `justice_and_rights, governance_and_policy, debate_and_argumentation, social_systems`
- Skills: `analytical_thinking, communication, persuasive_reasoning, attention_to_detail`
- Strengths: `critical_thinking, communication, persistence`
- Aspirations: `advocate, legal_counsel, policy_analyst`
- Confusable with: Journalism and Mass Communication, Sociology
- Distinguishing profile pattern: Strong language/communication ability combined with interest in justice, rights and formal argumentation specifically.

### Bachelor of Arts in Journalism and Mass Communication
- Academic pattern: Generally strong English and Kiswahili, variable elsewhere.
- Interests: `media_and_communication, current_affairs, storytelling, public_engagement`
- Skills: `communication, writing_and_reporting, research, creativity`
- Strengths: `communication, curiosity, adaptability`
- Aspirations: `journalist, broadcast_presenter, communications_professional`
- Confusable with: Law, Sociology
- Distinguishing profile pattern: Communication/writing strength applied to media, news and public storytelling rather than formal legal argumentation.

### Bachelor of Arts in Sociology
- Academic pattern: Generally solid English and Kiswahili, variable elsewhere.
- Interests: `society_and_culture, human_behaviour, community_issues, research`
- Skills: `analytical_thinking, research, communication, critical_thinking`
- Strengths: `curiosity, empathy, critical_thinking`
- Aspirations: `social_researcher, community_development_officer, policy_analyst`
- Confusable with: Social Work, Counseling Psychology, Public Health, Journalism and Mass Communication, Law
- Distinguishing profile pattern: Research/analytical orientation toward understanding society broadly, rather than direct case-based helping (Social Work) or individual psychology (Counseling).

### Bachelor of Social Work
- Academic pattern: Generally solid English and Kiswahili, variable elsewhere.
- Interests: `helping_others, community_welfare, social_justice, human_development`
- Skills: `communication, empathetic_listening, organisation, practical_problem_solving`
- Strengths: `empathy, resilience, communication`
- Aspirations: `social_worker, community_development_officer, case_management_professional`
- Confusable with: Sociology, Counseling Psychology, Public Health
- Distinguishing profile pattern: Direct, hands-on helping/case-management orientation rather than Sociology's broader research focus.

### Bachelor of Arts in Counseling Psychology
- Academic pattern: Generally solid English and Kiswahili, variable elsewhere.
- Interests: `human_behaviour, mental_wellbeing, helping_others, communication`
- Skills: `empathetic_listening, communication, analytical_thinking, interpersonal_understanding`
- Strengths: `empathy, patience, communication`
- Aspirations: `counselor, guidance_and_counseling_officer, mental_health_professional`
- Confusable with: Social Work, Sociology, Human Resource Management
- Distinguishing profile pattern: Individual-level psychological/emotional support orientation, distinct from Social Work's broader welfare/case-management scope.

---

## Cluster 8: Agriculture

### Bachelor of Science in Agriculture
- Academic pattern: Generally solid Biology and Chemistry, variable Mathematics.
- Interests: `agriculture_and_farming, food_production, environment_and_sustainability, rural_development`
- Skills: `scientific_reasoning, practical_problem_solving, analytical_thinking, field_research_interest`
- Strengths: `practical_thinking, resilience, curiosity`
- Aspirations: `agricultural_officer, agronomist, farm_manager`
- Confusable with: Veterinary Medicine, Food Science and Technology, Nutrition and Dietetics
- Distinguishing profile pattern: Science background applied to crop/livestock production and farming systems, distinct from Vet's clinical focus and Food Science's processing focus.

---

## Cluster 10: Education & Teacher Training

### Bachelor of Education (Science)
- Academic pattern: Generally solid Mathematics and at least one of Biology/Physics/Chemistry.
- Interests: `teaching_and_mentoring, science_communication, education, working_with_young_people`
- Skills: `communication, subject_mastery_interest, organisation, patience`
- Strengths: `patience, communication, leadership_interest`
- Aspirations: `science_teacher, curriculum_developer, education_officer`
- Confusable with: Bachelor of Education (Arts)
- Distinguishing profile pattern: Science academic strength combined specifically with a teaching/mentoring interest, rather than pursuing the science field professionally.

### Bachelor of Education (Arts)
- Academic pattern: Generally solid English and Kiswahili, variable elsewhere.
- Interests: `teaching_and_mentoring, humanities_and_languages, education, working_with_young_people`
- Skills: `communication, organisation, patience, subject_mastery_interest`
- Strengths: `patience, communication, leadership_interest`
- Aspirations: `humanities_teacher, curriculum_developer, guidance_and_counseling_officer`
- Confusable with: Bachelor of Education (Science)
- Distinguishing profile pattern: Humanities/language strength combined with a teaching/mentoring interest, distinct from pursuing the humanities field professionally.

---

## Cluster 11: Tourism & Hospitality Management

### Bachelor of Tourism Management
- Academic pattern: Generally solid English and Kiswahili, variable elsewhere.
- Interests: `travel_and_tourism, cultures_and_destinations, customer_experience, business`
- Skills: `communication, organisation, customer_service_orientation, planning`
- Strengths: `adaptability, communication, organisation`
- Aspirations: `tourism_officer, travel_consultant, destination_marketing_professional`
- Confusable with: Hospitality Management
- Distinguishing profile pattern: Travel/destination and customer-experience orientation, distinct from Hospitality's operations-within-a-venue focus.

### Bachelor of Science in Hospitality Management
- Academic pattern: Generally solid English and Kiswahili, variable elsewhere.
- Interests: `hospitality_and_service, customer_experience, events_and_operations, business`
- Skills: `communication, organisation, customer_service_orientation, teamwork`
- Strengths: `adaptability, communication, organisation`
- Aspirations: `hotel_manager, guest_relations_professional, events_coordinator`
- Confusable with: Tourism Management
- Distinguishing profile pattern: Operations/guest-service orientation within a hospitality venue, distinct from Tourism's broader destination/travel focus.

---

## Cross-cutting shared tags (tier 2 — deliberately common, not accidental genericness)

These appear across many unrelated programmes by design, per the locked
principle that shared characteristics are legitimate and expected, as long
as they're paired with genuinely distinguishing programme-specific tags
(never used alone as a programme's sole differentiator):

`analytical_thinking` — SE, ICS, Economics, Mathematics, Statistics, Actuarial,
Sociology, Law, Public Health, and more

`communication` — nearly every non-pure-technical programme; legitimately
universal

`organisation` — BCom, HR Management, Tourism, Hospitality, Education,
Real Estate, Quantity Surveying

`attention_to_detail` — Pharmacy, Dental, Quantity Surveying, Microbiology,
Industrial Chemistry, Geomatics

`practical_problem_solving` — all engineering/built-environment programmes,
Agriculture, Food Science

`empathy` — Nursing, Social Work, Counseling Psychology, HR Management,
Medicine, Veterinary Medicine

`methodical_thinking` — all engineering/built-environment programmes,
Microbiology, Industrial Chemistry, Geomatics

`curiosity` — Mathematics, Statistics, ICS, Microbiology, Industrial Chemistry,
Agriculture, Journalism

`precision` — Pharmacy, Dental, Actuarial Science, Quantity Surveying,
Geomatics, Industrial Chemistry, Microbiology

`persistence` — SE, ICS, Mathematics, Statistics, Actuarial Science
